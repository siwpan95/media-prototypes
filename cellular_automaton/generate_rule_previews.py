"""Rule Preview Generator — simulate all rules, take screenshots, generate videos.

For each rule:
  1. Simulate for N generations (default 120)
  2. Capture frames at regular intervals (every 2 generations)
  3. Save a final screenshot as PNG
  4. Compile frames into a MP4 video using ffmpeg

Output directory structure:
  previews/
  ├── screenshots/          ← one PNG per rule
  │   ├── game_of_life.png
  │   ├── highlife.png
  │   └── ...
  ├── videos/               ← one MP4 per rule
  │   ├── game_of_life.mp4
  │   ├── highlife.mp4
  │   └── ...
  └── frames/               ← temporary frame PNGs (cleaned up after video)
      ├── game_of_life/
      │   ├── frame_000.png
      │   ├── frame_002.png
      │   └── ...
      └── ...

Usage:
  python generate_rule_previews.py [--generations 120] [--fps 15]
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pygame

from core import CellularAutomaton
from config import Config
from rules import RULES, list_rules, list_rules_by_category, get_description, get_category
from rendering.renderer import Renderer
from rendering.color_themes import get_theme

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Grid dimensions for preview (smaller than full screen for faster rendering)
_ROWS: int = 80
_COLS: int = 120
_CELL_SIZE: int = 6
_SCREEN_WIDTH: int = _COLS * _CELL_SIZE  # 720
_SCREEN_HEIGHT: int = _ROWS * _CELL_SIZE  # 480

# Simulation parameters
_DEFAULT_GENERATIONS: int = 120
_FRAME_INTERVAL: int = 2  # capture every N generations
_VIDEO_FPS: int = 15

# Output directories
_OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "previews")
_SCREENSHOT_DIR: str = os.path.join(_OUTPUT_DIR, "screenshots")
_VIDEO_DIR: str = os.path.join(_OUTPUT_DIR, "videos")
_FRAME_DIR: str = os.path.join(_OUTPUT_DIR, "frames")

# Theme for previews (neon looks great)
_PREVIEW_THEME: str = "neon"


def _render_frame_to_surface(
    ca: CellularAutomaton,
    renderer: Renderer,
    generation: int,
) -> pygame.Surface:
    """Render a CA frame and return the surface."""
    renderer.draw(ca=ca, paused=False, generation=generation, fps=30.0)
    return renderer.screen.copy()


def _save_frame_as_png(surface: pygame.Surface, filepath: str) -> None:
    """Save a pygame surface as PNG."""
    pygame.image.save(surface, filepath)


def _generate_video_from_frames(
    frames_dir: str,
    output_path: str,
    fps: int = _VIDEO_FPS,
) -> bool:
    """Generate an MP4 video from PNG frames using ffmpeg."""
    # Check ffmpeg availability
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%03d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        "-preset", "medium",
        "-vf", f"scale={_SCREEN_WIDTH}:{_SCREEN_HEIGHT}:flags=lanczos",
        output_path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"    ffmpeg error: {result.stderr[:200]}")
            return False
        return True
    except FileNotFoundError:
        print("    ffmpeg not found, skipping video")
        return False
    except subprocess.TimeoutExpired:
        print("    ffmpeg timeout, skipping video")
        return False


def generate_all_previews(
    generations: int = _DEFAULT_GENERATIONS,
    video_fps: int = _VIDEO_FPS,
    theme: str = _PREVIEW_THEME,
) -> None:
    """Generate previews for all registered rules."""

    # Create output directories
    os.makedirs(_SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(_VIDEO_DIR, exist_ok=True)

    # Initialize pygame (headless-friendly)
    pygame.init()
    screen = pygame.display.set_mode(
        (_SCREEN_WIDTH, _SCREEN_HEIGHT), pygame.HIDDEN,
    )
    pygame.display.set_caption("Rule Preview Generator")

    # Get all rule names sorted by category
    rules_by_cat = list_rules_by_category()
    all_rules = list_rules()
    total = len(all_rules)

    # Stats
    success_count = 0
    fail_count = 0
    video_count = 0
    stats_by_cat: dict[str, dict] = {}

    print("=" * 70)
    print(f"  Rule Preview Generator")
    print(f"  {total} rules, {generations} generations each, {video_fps} FPS video")
    print(f"  Theme: {theme}, Grid: {_ROWS}×{_COLS}")
    print("=" * 70)

    for i, rule_name in enumerate(all_rules):
        cat = get_category(rule_name)
        desc = get_description(rule_name)
        print(f"\n[{i+1}/{total}] {rule_name} ({cat}): {desc}")

        # Create per-rule frame directory
        rule_frame_dir = os.path.join(_FRAME_DIR, rule_name)
        os.makedirs(rule_frame_dir, exist_ok=True)

        try:
            # Create config and CA for this rule
            config = Config(
                rule_name=rule_name,
                cell_size=_CELL_SIZE,
                color_theme=theme,
                show_grid=False,
                glow_enabled=True,
                smooth_scale=True,
                vsync=False,
                fullscreen=False,
                window_width=_SCREEN_WIDTH,
                window_height=_SCREEN_HEIGHT,
                initial_density=0.25,
            )

            # Some rules need different initial density
            if rule_name in ("seeds", "live_free_or_die", "serviettes", "gnarl"):
                config.initial_density = 0.15
            elif rule_name.startswith("gray_scott"):
                config.initial_density = 0.5
            elif rule_name in ("langtons_loop",):
                config.initial_density = 0.01
            elif rule_name.startswith("elementary_1d") or rule_name.startswith("wolfram"):
                config.initial_density = 0.01
            elif rule_name in ("sandpile",):
                config.initial_density = 0.3
            elif cat == "complex" and rule_name.startswith(("cyclic", "hodgepodge", "snowflake")):
                config.initial_density = 0.5

            ca = CellularAutomaton(
                rows=_ROWS,
                cols=_COLS,
                rule_name=rule_name,
                initial_density=config.initial_density,
                trail_length=config.trail_length,
            )

            # Create renderer
            renderer = Renderer(screen=screen, ca=ca, config=config)

            # For 1D rules, we need a single seed in the center
            if rule_name.startswith("elementary_1d") or rule_name.startswith("wolfram"):
                ca.clear()
                ca.grid[0, _COLS // 2] = 1

            # Simulate and capture frames
            frame_count = 0
            for gen in range(generations):
                ca.step()

                if gen % _FRAME_INTERVAL == 0:
                    surface = _render_frame_to_surface(ca, renderer, gen)
                    frame_path = os.path.join(rule_frame_dir, f"frame_{frame_count:03d}.png")
                    _save_frame_as_png(surface, frame_path)
                    frame_count += 1

            # Save final screenshot (higher quality)
            final_surface = _render_frame_to_surface(ca, renderer, generations)
            screenshot_path = os.path.join(_SCREENSHOT_DIR, f"{rule_name}.png")
            _save_frame_as_png(final_surface, screenshot_path)
            print(f"    ✓ {frame_count} frames, screenshot saved")

            # Generate video
            video_path = os.path.join(_VIDEO_DIR, f"{rule_name}.mp4")
            if _generate_video_from_frames(rule_frame_dir, video_path, video_fps):
                video_count += 1
                print(f"    ✓ Video saved: {video_path}")
            else:
                print(f"    ⚠ Video skipped")

            # Clean up frames to save disk space
            shutil.rmtree(rule_frame_dir, ignore_errors=True)

            success_count += 1
            cat_stats = stats_by_cat.setdefault(cat, {"success": 0, "fail": 0, "videos": 0})
            cat_stats["success"] += 1
            cat_stats["videos"] += 1

        except Exception as e:
            print(f"    ✗ FAILED: {e}")
            fail_count += 1
            cat_stats = stats_by_cat.setdefault(cat, {"success": 0, "fail": 0, "videos": 0})
            cat_stats["fail"] += 1
            # Clean up on failure
            shutil.rmtree(rule_frame_dir, ignore_errors=True)

    # Print summary
    print("\n" + "=" * 70)
    print("  PREVIEW GENERATION SUMMARY")
    print("=" * 70)
    print(f"  Total rules: {total}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Videos generated: {video_count}")
    print(f"  Screenshots saved: {success_count}")
    print()
    for cat, stats in sorted(stats_by_cat.items()):
        print(f"  {cat}: {stats['success']} ok, {stats['fail']} fail, {stats['videos']} videos")
    print()
    print(f"  Screenshots: {_SCREENSHOT_DIR}")
    print(f"  Videos: {_VIDEO_DIR}")
    print("=" * 70)

    pygame.quit()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Generate rule preview screenshots and videos")
    parser.add_argument("--generations", type=int, default=_DEFAULT_GENERATIONS,
                        help=f"Number of generations to simulate (default {_DEFAULT_GENERATIONS})")
    parser.add_argument("--fps", type=int, default=_VIDEO_FPS,
                        help=f"Video FPS (default {_VIDEO_FPS})")
    parser.add_argument("--theme", type=str, default=_PREVIEW_THEME,
                        help=f"Color theme for previews (default {_PREVIEW_THEME})")
    args = parser.parse_args()

    generate_all_previews(
        generations=args.generations,
        video_fps=args.fps,
        theme=args.theme,
    )


if __name__ == "__main__":
    main()
