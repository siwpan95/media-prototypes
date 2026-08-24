"""Config module tests."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, build_config


def test_default_config():
    """Test default config values."""
    print("Testing default Config...")
    cfg = Config()
    assert cfg.cell_size == 6
    assert cfg.initial_density == 0.25
    assert cfg.rule_name == "game_of_life"
    assert cfg.color_theme == "neon"
    assert cfg.fps == 60
    assert cfg.fullscreen is True
    assert cfg.show_grid is False
    assert cfg.trail_enabled is True
    assert cfg.trail_length == 12
    assert cfg.max_age == 80
    assert cfg.lang == "en"
    assert cfg.audio_enabled is True
    assert cfg.audio_volume == 0.12
    print("  PASSED")


def test_build_config_defaults():
    """Test build_config with no overrides."""
    print("Testing build_config() defaults...")
    cfg = build_config()
    assert isinstance(cfg, Config)
    assert cfg.cell_size == 6
    print("  PASSED")


def test_build_config_overrides():
    """Test build_config with CLI-like overrides."""
    print("Testing build_config() with overrides...")
    import argparse
    args = argparse.Namespace(
        cell_size=None,
        density=None,
        rule=None,
        theme=None,
        fps=30,
        lang="zh",
        windowed=True,
        no_audio=False,
        audio_volume=0.5,
        config=None,
    )
    # build_config uses Config field names directly from the namespace
    # So we need to pass the config field names
    from config import config_from_cli
    # Use a dict with proper config field names
    overrides = {
        "cell_size": 8,
        "initial_density": 0.5,
        "rule_name": "highlife",
        "color_theme": "ocean",
        "fps": 30,
        "lang": "zh",
        "fullscreen": False,
        "audio_volume": 0.5,
    }
    cfg = build_config(argparse.Namespace(**overrides))
    assert cfg.cell_size == 8
    assert cfg.initial_density == 0.5
    assert cfg.rule_name == "highlife"
    assert cfg.color_theme == "ocean"
    assert cfg.fps == 30
    assert cfg.lang == "zh"
    assert cfg.fullscreen is False
    assert cfg.audio_volume == 0.5
    print("  PASSED")


def test_config_modification():
    """Test modifying config at runtime."""
    print("Testing config modification...")
    cfg = Config()
    cfg.cell_size = 10
    cfg.rule_name = "wireworld"
    assert cfg.cell_size == 10
    assert cfg.rule_name == "wireworld"
    print("  PASSED")


def main():
    print("=" * 60)
    print("Cellular Automaton — Config Tests")
    print("=" * 60)
    print()
    try:
        test_default_config()
        print()
        test_build_config_defaults()
        print()
        test_build_config_overrides()
        print()
        test_config_modification()
        print()
        print("=" * 60)
        print("All config tests PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
