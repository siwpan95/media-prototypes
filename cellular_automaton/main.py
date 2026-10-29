"""Unified entry point for the Cellular Automaton application.

Supports both normal mode and wallpaper mode.
Wallpaper mode is activated via --wallpaper flag or config file.
"""

from __future__ import annotations

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from audio import AudioManager
from config import Config, config_from_cli
from core import CellularAutomaton
from rendering import Renderer
from rules import list_rules_by_category, total_count

# ── Normal mode ───────────────────────────────────────────────────
from ui import InputHandler

# ── Wallpaper mode ──────────────────────────────────────────────
from ui.wallpaper_handler import WallpaperInputHandler, WallpaperRunner
from rendering.wallpaper_hud import draw_wallpaper_hud
from desktop_wallpaper import DesktopWallpaper


def _init_pygame_and_ca(config: Config) -> tuple[
    pygame.Surface, CellularAutomaton, AudioManager, Renderer,
]:
    """Initialize pygame, create CA model, audio, and renderer."""
    pygame.init()

    display_info = pygame.display.Info()
    if config.fullscreen:
        screen_width = display_info.current_w
        screen_height = display_info.current_h
    else:
        screen_width = config.window_width
        screen_height = config.window_height

    flags = 0
    if config.fullscreen:
        flags |= pygame.FULLSCREEN
    if config.vsync:
        flags |= pygame.SCALED

    screen = pygame.display.set_mode(
        (screen_width, screen_height), flags, vsync=1 if config.vsync else 0,
    )
    pygame.display.set_caption("Cellular Automaton")

    cell_size = max(config.cell_size, 1)
    cols = screen_width // cell_size
    rows = screen_height // cell_size

    ca = CellularAutomaton(
        rows=rows,
        cols=cols,
        rule_name=config.rule_name,
        initial_density=config.initial_density,
        trail_length=config.trail_length,
    )

    audio = AudioManager(
        volume=config.audio_volume,
        enabled=config.audio_enabled,
    )
    audio.initialize()

    renderer = Renderer(screen=screen, ca=ca, config=config)

    return screen, ca, audio, renderer


def _print_startup_info() -> None:
    from rules import list_rules_by_category, total_count
    cats = list_rules_by_category()
    print("=" * 60)
    print("  Cellular Automaton")
    print(f"  {len(cats)} categories, {total_count} rules available")
    for cat, names in cats.items():
        print(f"    {cat}: {len(names)} rules")
    print("=" * 60)


def run_normal_mode(config: Config) -> None:
    """Run in normal interactive mode."""
    screen, ca, audio, renderer = _init_pygame_and_ca(config)

    input_handler = InputHandler(
        config=config, renderer=renderer, audio_manager=audio,
    )

    clock = pygame.time.Clock()
    running: bool = True
    paused: bool = False
    generation: int = 0
    current_fps: float = 0.0

    _print_startup_info()

    while running:
        running, paused, generation = input_handler.handle_events(
            ca, paused, generation,
        )
        if not running:
            break

        # Auto-cycle check (normal mode)
        new_rule = input_handler.check_auto_cycle(ca, paused)
        if new_rule is not None:
            generation = 0
            print(f"[Auto] Switched to rule: {new_rule}")

        if not paused:
            ca.step()
            generation += 1

        audio.update(ca.alive_count / (ca.rows * ca.cols))
        renderer.draw(ca=ca, paused=paused, generation=generation, fps=current_fps)
        pygame.display.flip()
        clock.tick(config.fps)
        current_fps = clock.get_fps()

    audio.shutdown()
    pygame.quit()
    sys.exit(0)


def run_wallpaper_mode(config: Config) -> None:
    """Run in desktop wallpaper mode."""
    # Override defaults for wallpaper mode
    config.fullscreen = True
    config.show_grid = False
    config.vsync = True
    config.smooth_scale = True
    config.glow_enabled = True
    config.lang = "zh"

    screen, ca, audio, renderer = _init_pygame_and_ca(config)

    # Desktop wallpaper embedding
    wallpaper_mgr = DesktopWallpaper(screen)
    wallpaper_enabled = (
        config.wallpaper_mode and config.fullscreen
        and sys.platform == "win32"
    )
    if wallpaper_enabled:
        wallpaper_mgr.activate()

    # Wallpaper runner and input handler
    runner = WallpaperRunner(config)
    input_handler = WallpaperInputHandler(
        config=config, renderer=renderer, runner=runner, audio_manager=audio,
    )

    clock = pygame.time.Clock()
    running: bool = True
    paused: bool = False
    generation: int = 0
    current_fps: float = 0.0

    print("=" * 60)
    print("  Cellular Automaton Wallpaper")
    print("  Press H for HUD, S for screenshot, ESC to quit")
    print("=" * 60)

    while running:
        wall_time = time.monotonic()

        running, paused, generation = input_handler.handle_events(
            ca, paused, generation,
        )
        if not running:
            break

        # Auto-cycle rules
        if not paused and runner.should_cycle_rule(wall_time):
            rule_name = input_handler.cycle_rule_auto(ca)
            generation = 0
            print(f"[Auto] Switched to rule: {rule_name}")

        # Auto-cycle themes
        if not paused and runner.should_cycle_theme(wall_time):
            theme_name = input_handler.cycle_theme_auto()
            print(f"[Auto] Switched to theme: {theme_name}")

        if not paused:
            ca.step()
            generation += 1

        audio.update(ca.alive_count / (ca.rows * ca.cols))
        renderer.draw(ca=ca, paused=paused, generation=generation, fps=current_fps)

        # Wallpaper HUD (only if visible)
        if runner.hud_visible:
            draw_wallpaper_hud(
                renderer, ca, generation, current_fps,
                ca.rule.name, config.color_theme, renderer._font,
            )

        pygame.display.flip()

        # Keep window pinned as desktop wallpaper
        wallpaper_mgr.repin()

        clock.tick(config.fps)
        current_fps = clock.get_fps()

    wallpaper_mgr.deactivate()
    audio.shutdown()
    pygame.quit()
    sys.exit(0)


def main() -> None:
    """Application entry point."""
    config = config_from_cli()

    if config.wallpaper_mode and sys.platform == "win32":
        run_wallpaper_mode(config)
    else:
        run_normal_mode(config)


if __name__ == "__main__":
    main()
