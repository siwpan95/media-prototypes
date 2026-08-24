"""Renderer tests — color theme and renderer functionality.

Tests pygame-independent parts: theme loading, gradient building, etc.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from rendering.color_themes import (
    Theme, get_theme, available_themes, _lerp_color, _build_gradient,
)


def test_lerp_color():
    """Test color linear interpolation."""
    print("Testing _lerp_color()...")
    c1 = _lerp_color((0, 0, 0), (100, 100, 100), 0.0)
    assert c1 == (0, 0, 0)

    c2 = _lerp_color((0, 0, 0), (100, 100, 100), 1.0)
    assert c2 == (100, 100, 100)

    c3 = _lerp_color((0, 0, 0), (100, 0, 50), 0.5)
    assert c3 == (50, 0, 25)
    print("  PASSED")


def test_build_gradient():
    """Test gradient palette construction."""
    print("Testing _build_gradient()...")
    # Two anchors, with padding to reach exact step count
    grad = _build_gradient([(0, 0, 0), (100, 0, 0)], 5)
    assert len(grad) == 5
    assert grad[0] == (0, 0, 0)
    # Last step should approach (100,0,0) or be padded to it
    assert grad[-1][0] >= 80  # near max value

    # Single anchor
    grad2 = _build_gradient([(50, 50, 50)], 5)
    assert len(grad2) == 5
    assert all(c == (50, 50, 50) for c in grad2)
    print("  PASSED")


def test_theme_registry():
    """Test theme registration and retrieval."""
    print("Testing theme registry...")
    themes = available_themes()
    assert len(themes) == 7, f"Expected 7 themes, got {len(themes)}"
    expected = {"neon", "ocean", "ember", "matrix", "aurora", "plasma", "sunset"}
    assert set(themes) == expected, f"Theme mismatch: {set(themes)}"

    for name in themes:
        theme = get_theme(name)
        assert theme.name == name
        assert isinstance(theme.bg, tuple)
        assert len(theme.bg) == 3
        assert len(theme.alive_colors) > 0
        assert len(theme.trail_colors) > 0
        assert len(theme.state_colors) >= 4
        assert isinstance(theme.grid_color, tuple)
        assert isinstance(theme.hud_color, tuple)
        print(f"    {name}: alive={len(theme.alive_colors)}, trail={len(theme.trail_colors)}, "
              f"states={len(theme.state_colors)} OK")
    print("  PASSED")


def test_theme_custom_params():
    """Test theme with custom max_age and trail_length."""
    print("Testing theme with custom params...")
    theme = get_theme("neon", max_age=40, trail_length=6)
    assert theme.max_age == 40
    assert theme.trail_length == 6
    assert len(theme.alive_colors) == 40
    assert len(theme.trail_colors) == 6
    print("  PASSED")


def test_theme_fallback():
    """Test fallback for unknown theme name."""
    print("Testing theme fallback...")
    theme = get_theme("nonexistent_theme")
    assert theme.name == "neon"  # falls back to neon
    print("  PASSED")


def test_state_colors_coverage():
    """Test state_colors cover enough states for all rules."""
    print("Testing state_colors coverage...")
    # All themes should have at least 8 state colors (for Langton's Loop)
    for name in available_themes():
        theme = get_theme(name)
        assert len(theme.state_colors) >= 8, \
            f"{name}: only {len(theme.state_colors)} state colors, need >= 8"
    print("  All themes have >= 8 state colors. PASSED")


def test_theme_consistency():
    """Test that themes have consistent color tuples (3 uint8 values)."""
    print("Testing theme color consistency...")
    for name in available_themes():
        theme = get_theme(name)
        for c in theme.alive_colors:
            assert len(c) == 3
            assert all(0 <= v <= 255 for v in c), f"Invalid color in {name}: {c}"
        for c in theme.trail_colors:
            assert len(c) == 3
            assert all(0 <= v <= 255 for v in c), f"Invalid trail color in {name}: {c}"
        for c in theme.state_colors:
            assert len(c) == 3
            assert all(0 <= v <= 255 for v in c), f"Invalid state color in {name}: {c}"
    print("  All colors valid. PASSED")


def main():
    print("=" * 60)
    print("Cellular Automaton — Renderer Tests")
    print("=" * 60)
    print()
    try:
        test_lerp_color()
        print()
        test_build_gradient()
        print()
        test_theme_registry()
        print()
        test_theme_custom_params()
        print()
        test_theme_fallback()
        print()
        test_state_colors_coverage()
        print()
        test_theme_consistency()
        print()
        print("=" * 60)
        print("All renderer tests PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
