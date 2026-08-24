"""Wallpaper-specific input handler and runner for Cellular Automaton.

Extracted from wallpaper.py to eliminate code duplication with main.py.
"""

from __future__ import annotations

import os
import sys
import time
import datetime

import pygame

from audio import AudioManager
from config import Config
from core import CellularAutomaton
from rendering import Renderer
from rendering.color_themes import available_themes
from rules import RULES


# --- Wallpaper-specific constants ---
_RULE_CYCLE_INTERVAL: float = 60.0   # seconds between auto rule changes
_THEME_CYCLE_INTERVAL: float = 90.0  # seconds between auto theme changes
_MANUAL_OVERRIDE_COOLDOWN: float = 300.0  # 5 min pause after manual switch
_SCREENSHOT_DIR: str = "screenshots"

# Rules that look best as wallpaper
_WALLPAPER_RULES: list[str] = [
    "game_of_life",
    "highlife",
    "brians_brain",
    "gray_scott_waves",
    "gray_scott_maze",
    "gray_scott_stripes",
    "lenia",
    "lenia_hydro",
    "smooth_life",
    "bz_reaction",
    "hodgepodge",
    "cyclic",
    "forest_fire",
    "day_and_night",
    "snowflake",
    "crystal_growth",
    "larger_than_life",
    "ltl_worms",
]

_WALLPAPER_THEMES: list[str] = [
    "neon",
    "ocean",
    "aurora",
    "plasma",
    "sunset",
    "ember",
    "matrix",
]


class WallpaperRunner:
    """Manages the wallpaper display with auto-cycling rules and themes."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._last_rule_change: float = time.monotonic()
        self._last_theme_change: float = time.monotonic()
        self._manual_override_until: float = 0.0
        self._hud_visible: bool = False
        self._screenshot_count: int = 0

    def should_cycle_rule(self, current_time: float) -> bool:
        """Check if it's time to auto-cycle to the next rule."""
        if current_time < self._manual_override_until:
            return False
        return (current_time - self._last_rule_change) >= _RULE_CYCLE_INTERVAL

    def should_cycle_theme(self, current_time: float) -> bool:
        """Check if it's time to auto-cycle to the next theme."""
        if current_time < self._manual_override_until:
            return False
        return (current_time - self._last_theme_change) >= _THEME_CYCLE_INTERVAL

    def on_rule_changed(self, current_time: float) -> None:
        self._last_rule_change = current_time

    def on_theme_changed(self, current_time: float) -> None:
        self._last_theme_change = current_time

    def on_manual_override(self, current_time: float) -> None:
        """Pause auto-cycling for the cooldown period."""
        self._manual_override_until = current_time + _MANUAL_OVERRIDE_COOLDOWN
        self._last_rule_change = current_time
        self._last_theme_change = current_time

    @property
    def hud_visible(self) -> bool:
        return self._hud_visible

    def toggle_hud(self) -> None:
        self._hud_visible = not self._hud_visible

    def save_screenshot(self, screen: pygame.Surface) -> str | None:
        """Save a screenshot to the screenshots directory."""
        ss_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", _SCREENSHOT_DIR,
        )
        ss_dir = os.path.normpath(ss_dir)
        os.makedirs(ss_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ca_wallpaper_{timestamp}.png"
        filepath = os.path.join(ss_dir, filename)
        try:
            pygame.image.save(screen, filepath)
            self._screenshot_count += 1
            return filepath
        except pygame.error:
            return None


class WallpaperInputHandler:
    """Lightweight input handler for wallpaper mode."""

    def __init__(
        self,
        config: Config,
        renderer: Renderer,
        runner: WallpaperRunner,
        audio_manager: AudioManager | None = None,
    ) -> None:
        self.config = config
        self.renderer = renderer
        self.runner = runner
        self.audio_manager = audio_manager
        self._rule_list = [r for r in _WALLPAPER_RULES if r in RULES]
        if not self._rule_list:
            self._rule_list = list(RULES.keys())
        self._rule_index: int = 0
        self._theme_list = [t for t in _WALLPAPER_THEMES if t in available_themes()]
        if not self._theme_list:
            self._theme_list = available_themes()
        self._theme_index: int = 0
        # Find current rule/theme index
        try:
            self._rule_index = self._rule_list.index(config.rule_name)
        except ValueError:
            self._rule_index = 0
        try:
            self._theme_index = self._theme_list.index(config.color_theme)
        except ValueError:
            self._theme_index = 0
        self._mouse_drawing = False
        self._mouse_alive = True

    def handle_events(
        self,
        ca: CellularAutomaton,
        paused: bool,
        generation: int,
    ) -> tuple[bool, bool, int]:
        """Process all pending pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, paused, generation
            if event.type == pygame.KEYDOWN:
                result = self._handle_key(event, ca, paused, generation)
                if result is not None:
                    return result
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event, ca)
            if event.type == pygame.MOUSEBUTTONUP:
                self._mouse_drawing = False
            if event.type == pygame.MOUSEMOTION and self._mouse_drawing:
                row, col = self.renderer.screen_to_grid(event.pos[0], event.pos[1])
                ca.set_cell(row, col, int(self._mouse_alive))
        return True, paused, generation

    def _handle_key(
        self,
        event: pygame.event.Event,
        ca: CellularAutomaton,
        paused: bool,
        generation: int,
    ) -> tuple[bool, bool, int] | None:
        """Handle a single key-down event. Returns None to continue."""
        if event.key == pygame.K_ESCAPE:
            return False, paused, generation
        if event.key == pygame.K_SPACE:
            paused = not paused
        if event.key == pygame.K_h:
            self.runner.toggle_hud()
        if event.key == pygame.K_s:
            filepath = self.runner.save_screenshot(self.renderer.screen)
            if filepath:
                print(f"Screenshot saved: {filepath}")
        if event.key == pygame.K_r:
            ca.randomize(self.config.initial_density)
            generation = 0
        if event.key == pygame.K_TAB:
            self._rule_index = (self._rule_index + 1) % len(self._rule_list)
            rule_name = self._rule_list[self._rule_index]
            ca.set_rule(rule_name)
            self.runner.on_manual_override(time.monotonic())
            print(f"Rule: {rule_name}")
        if event.key == pygame.K_t:
            self._theme_index = (self._theme_index + 1) % len(self._theme_list)
            theme_name = self._theme_list[self._theme_index]
            self.config.color_theme = theme_name
            self.renderer.update_theme(theme_name)
            self.runner.on_manual_override(time.monotonic())
            print(f"Theme: {theme_name}")
        if event.key == pygame.K_LEFTBRACKET:
            self.config.cell_size = max(1, self.config.cell_size - 1)
            print(f"Cell size: {self.config.cell_size}")
        if event.key == pygame.K_RIGHTBRACKET:
            self.config.cell_size = min(20, self.config.cell_size + 1)
            print(f"Cell size: {self.config.cell_size}")
        if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
            self.config.fps = max(5, self.config.fps - 5)
            print(f"FPS: {self.config.fps}")
        if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.config.fps = min(120, self.config.fps + 5)
            print(f"FPS: {self.config.fps}")
        if event.key == pygame.K_m and self.audio_manager is not None:
            self.audio_manager.enabled = not self.audio_manager.enabled
        return None

    def _handle_mouse_down(
        self, event: pygame.event.Event, ca: CellularAutomaton,
    ) -> None:
        if event.button in (1, 3):
            self._mouse_drawing = True
            row, col = self.renderer.screen_to_grid(event.pos[0], event.pos[1])
            if ca.num_states > 2:
                current_state = (
                    ca.grid[row, col]
                    if 0 <= row < ca.rows and 0 <= col < ca.cols
                    else 0
                )
                next_state = (int(current_state) + 1) % ca.num_states
                ca.set_cell(row, col, next_state)
                self._mouse_alive = bool(next_state)
            else:
                self._mouse_alive = event.button == 1
                ca.set_cell(row, col, int(self._mouse_alive))

    def cycle_rule_auto(self, ca: CellularAutomaton) -> str:
        """Auto-cycle to the next wallpaper rule."""
        self._rule_index = (self._rule_index + 1) % len(self._rule_list)
        rule_name = self._rule_list[self._rule_index]
        ca.set_rule(rule_name)
        ca.randomize(self.config.initial_density)
        self.runner.on_rule_changed(time.monotonic())
        return rule_name

    def cycle_theme_auto(self) -> str:
        """Auto-cycle to the next wallpaper theme."""
        self._theme_index = (self._theme_index + 1) % len(self._theme_list)
        theme_name = self._theme_list[self._theme_index]
        self.config.color_theme = theme_name
        self.renderer.update_theme(theme_name)
        self.runner.on_theme_changed(time.monotonic())
        return theme_name
