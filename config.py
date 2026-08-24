"""Configuration module for the Cellular Automaton Wallpaper program.

All configurable parameters are defined here as dataclass fields.
Users can override defaults via a JSON config file or command-line arguments.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Global configuration for the CA wallpaper application."""

    # --- Grid ---
    cell_size: int = 6
    """Pixel size of each cell."""

    initial_density: float = 0.25
    """Probability [0, 1] that a cell starts alive."""

    # --- Rules ---
    rule_name: str = "game_of_life"
    """Name of the CA rule to use.
    2-state: game_of_life, highlife, day_and_night, seeds, maze,
             34_life, long_life, replicator, anneal, diamoeba
    Multi-state: brians_brain, wireworld, forest_fire, crystal_growth
    Complex: langtons_loop, snowflake, cyclic, hodgepodge
    Continuous: gray_scott, gray_scott_spots, gray_scott_stripes,
                gray_scott_maze, gray_scott_waves, gray_scott_pulsating,
                lenia, lenia_hydro, smooth_life
    Larger than Life: larger_than_life, ltl_bugs2, ltl_brain,
                      ltl_sand, ltl_cities, ltl_worms
    1D Elementary: elementary_1d, wolfram_30, wolfram_90, wolfram_110
    BZ Reaction: bz_reaction
    """

    # --- Display ---
    color_theme: str = "neon"
    """Color theme name. Valid: neon, ocean, ember, matrix, aurora, plasma, sunset."""

    show_grid: bool = False
    """Whether to draw grid lines between cells."""

    fps: int = 60
    """Target frames per second."""

    fullscreen: bool = True
    """Start in fullscreen mode."""

    # --- Effects ---
    fade_speed: float = 0.08
    """Speed at which dead-cell trails fade out (0-1, higher = faster)."""

    max_age: int = 80
    """Maximum tracked cell age; colors cycle beyond this."""

    trail_enabled: bool = True
    """Enable fading trail effect for recently dead cells."""

    trail_length: int = 12
    """Number of frames a trail persists after cell death."""

    # --- Rendering pipeline ---
    smooth_scale: bool = True
    """Use anti-aliased smooth scaling (slower but much better visual quality)."""

    glow_enabled: bool = True
    """Enable bloom/glow post-processing effect for a luminous look."""

    glow_intensity: float = 0.35
    """Glow intensity (0.0 to 1.0; higher = brighter bloom)."""

    glow_blur_size: int = 8
    """Blur kernel size for the glow pass (odd number, larger = softer)."""

    vsync: bool = True
    """Enable vertical sync for tear-free rendering."""

    # --- Language ---
    lang: str = "en"
    """UI language: 'en' for English, 'zh' for Chinese."""

    # --- Audio ---
    audio_enabled: bool = True
    """Enable procedural ambient audio."""

    audio_volume: float = 0.12
    """Audio volume level (0.0 to 1.0)."""

    # --- Desktop wallpaper ---
    wallpaper_mode: bool = True
    """Enable true desktop wallpaper embedding (behind desktop icons).
    Set False to use fullscreen window instead."""

    # --- Auto-cycle ---
    auto_cycle_rules: bool = False
    """Auto-cycle CA rules at regular intervals."""

    auto_cycle_interval: float = 60.0
    """Seconds between auto rule changes."""

    auto_cycle_theme_interval: float = 90.0
    """Seconds between auto theme changes."""

    auto_cycle_pause_after_manual: float = 300.0
    """Seconds to pause auto-cycling after a manual switch."""

    # --- Windowed fallback ---
    window_width: int = 1280
    window_height: int = 720


def load_config_from_json(path: Path) -> dict[str, Any]:
    """Load configuration overrides from a JSON file."""
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data
    return {}


def build_config(args: argparse.Namespace | None = None, json_path: Path | None = None) -> Config:
    """Build a Config object by merging defaults, JSON file, and CLI args.

    Priority (highest wins): CLI args > JSON file > defaults.
    """
    cfg = Config()

    # Layer 1: JSON file
    if json_path is not None:
        overrides = load_config_from_json(json_path)
        _apply_overrides(cfg, overrides)

    # Layer 2: CLI args
    if args is not None:
        arg_dict = {k: v for k, v in vars(args).items() if v is not None}
        _apply_overrides(cfg, arg_dict)

    return cfg


def _apply_overrides(cfg: Config, overrides: dict[str, Any]) -> None:
    """Apply a dict of overrides to a Config dataclass instance."""
    valid_keys = {f.name for f in fields(cfg)}
    for key, value in overrides.items():
        if key in valid_keys:
            setattr(cfg, key, value)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Cellular Automaton Wallpaper"
    )
    parser.add_argument("--cell-size", type=int, help="Pixel size of each cell")
    parser.add_argument("--density", type=float, help="Initial cell density (0-1)")
    parser.add_argument("--rule", type=str, help="CA rule name")
    parser.add_argument("--theme", type=str, help="Color theme name")
    parser.add_argument("--fps", type=int, help="Target FPS")
    parser.add_argument("--lang", type=str, help="UI language (en/zh)")
    parser.add_argument(
        "--windowed", action="store_true", default=False,
        help="Run in windowed mode instead of fullscreen"
    )
    parser.add_argument(
        "--no-audio", action="store_true", default=False,
        help="Disable ambient audio"
    )
    parser.add_argument(
        "--audio-volume", type=float, default=None,
        help="Audio volume (0.0 - 1.0)"
    )
    parser.add_argument(
        "--no-smooth-scale", action="store_true", default=False,
        help="Disable anti-aliased smooth scaling"
    )
    parser.add_argument(
        "--no-glow", action="store_true", default=False,
        help="Disable glow/bloom post-processing"
    )
    parser.add_argument(
        "--glow-intensity", type=float, default=None,
        help="Glow intensity (0.0 - 1.0)"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to JSON config file"
    )
    parser.add_argument(
        "--no-wallpaper", action="store_true", default=False,
        help="Disable desktop wallpaper embedding (use fullscreen window instead)"
    )
    parser.add_argument(
        "--auto-cycle", action="store_true", default=False,
        help="Enable auto-cycling of rules and themes"
    )
    parser.add_argument(
        "--cycle-interval", type=float, default=None,
        help="Seconds between auto rule changes (default 60)"
    )
    return parser.parse_args()


def config_from_cli() -> Config:
    """Convenience: build Config entirely from CLI invocation."""
    args = parse_args()
    json_path = Path(args.config) if args.config else None

    # Map CLI arg names to Config field names
    mapping: dict[str, str] = {
        "cell_size": "cell_size",
        "density": "initial_density",
        "rule": "rule_name",
        "theme": "color_theme",
    }
    mapped: dict[str, Any] = {}
    for cli_key, cfg_key in mapping.items():
        val = getattr(args, cli_key, None)
        if val is not None:
            mapped[cfg_key] = val

    if args.fps is not None:
        mapped["fps"] = args.fps
    if args.lang is not None:
        mapped["lang"] = args.lang
    if args.windowed:
        mapped["fullscreen"] = False
    if args.no_audio:
        mapped["audio_enabled"] = False
    if args.audio_volume is not None:
        mapped["audio_volume"] = args.audio_volume
    if args.no_smooth_scale:
        mapped["smooth_scale"] = False
    if args.no_glow:
        mapped["glow_enabled"] = False
    if args.glow_intensity is not None:
        mapped["glow_intensity"] = args.glow_intensity

    if args.no_wallpaper:
        mapped["wallpaper_mode"] = False

    if args.auto_cycle:
        mapped["auto_cycle_rules"] = True
    if args.cycle_interval is not None:
        mapped["auto_cycle_interval"] = args.cycle_interval

    return build_config(argparse.Namespace(**mapped), json_path)
