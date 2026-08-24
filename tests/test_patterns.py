"""Pattern library tests."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from rendering.patterns import (
    PATTERNS, get_pattern, list_patterns, place_pattern,
    GLIDER, GLIDER_GUN, PULSAR, BEACON, BLINKER, BLOCK, BEEHIVE,
    LWSS, MWSS, LANGTON_LOOP, WIRE_DIODE,
)


def test_pattern_count():
    """Test the number of registered patterns."""
    print("Testing pattern count...")
    names = list_patterns()
    assert len(names) == 11, f"Expected 11 patterns, got {len(names)}: {names}"
    print(f"  {len(names)} patterns: {names}")
    print("  PASSED")


def test_all_patterns_valid():
    """Test all patterns are valid numpy arrays."""
    print("Testing pattern validity...")
    for name, pattern in PATTERNS.items():
        assert isinstance(pattern, np.ndarray), f"{name} is not ndarray"
        assert pattern.dtype == np.uint8, f"{name}: expected uint8, got {pattern.dtype}"
        assert pattern.ndim == 2, f"{name}: expected 2D, got {pattern.ndim}D"
        assert pattern.min() >= 0
        assert pattern.max() <= 8  # Langton's loop has up to state 7
        print(f"    {name}: shape={pattern.shape}, dtype={pattern.dtype} OK")
    print("  PASSED")


def test_place_pattern():
    """Test place_pattern on a grid."""
    print("Testing place_pattern()...")
    grid = np.zeros((20, 20), dtype=np.uint8)

    # Place glider
    grid = place_pattern(grid, GLIDER, 5, 5)
    assert grid[5, 6] == 1
    assert grid[6, 7] == 1
    print("  glider placement OK")

    # Place block (don't clear first)
    grid = place_pattern(grid, BLOCK, 0, 0, clear_first=False)
    assert grid[0, 0] == 1
    assert grid[0, 1] == 1
    assert grid[5, 6] == 1  # glider still there
    print("  block overlay (no clear) OK")

    # Place pulsar (clear first)
    grid = place_pattern(grid, PULSAR, 2, 2)
    assert grid[0, 0] == 0  # previous patterns cleared
    # Pulsar's first live cells are at pattern row 1, cols [3,4,5,9,10,11]
    # Placed at (2,2): grid row 3, cols [5,6,7,11,12,13]
    assert grid[3, 5] == 1  # pulsar first row of live cells
    print("  pulsar placement OK")

    # Place Langton's Loop
    grid = place_pattern(grid, LANGTON_LOOP, 2, 2)
    # Loop's first row (row 0) is all 0; row 1 has signals at cols 1-13
    # Placed at (2,2): grid row 3, col 3 = state 2 (signal)
    assert grid[3, 3] == 2  # signal state in loop
    print("  langton_loop placement OK")

    print("  PASSED")


def test_bounds_check():
    """Test that oversized patterns raise ValueError."""
    print("Testing bounds check...")
    grid = np.zeros((5, 5), dtype=np.uint8)
    try:
        place_pattern(grid, PULSAR, 0, 0)  # pulsar is 15x17, too big
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("  oversize pattern raises ValueError OK")
    print("  PASSED")


def test_get_unknown_pattern():
    """Test getting an unknown pattern returns None."""
    print("Testing unknown pattern...")
    assert get_pattern("nonexistent") is None
    print("  PASSED")


def test_pattern_dimensions():
    """Test known pattern dimensions."""
    print("Testing pattern dimensions...")
    assert GLIDER.shape == (3, 3)
    assert GLIDER_GUN.shape == (11, 36)
    assert PULSAR.shape == (15, 17)
    assert BEACON.shape == (4, 4)
    assert BLINKER.shape == (1, 3)
    assert BLOCK.shape == (2, 2)
    assert BEEHIVE.shape == (3, 4)
    assert LWSS.shape == (4, 5)
    assert MWSS.shape == (7, 5)
    assert LANGTON_LOOP.shape == (17, 15)
    assert WIRE_DIODE.shape == (6, 7)
    print("  All dimensions correct")
    print("  PASSED")


def main():
    print("=" * 60)
    print("Cellular Automaton — Pattern Tests")
    print("=" * 60)
    print()
    try:
        test_pattern_count()
        print()
        test_all_patterns_valid()
        print()
        test_place_pattern()
        print()
        test_bounds_check()
        print()
        test_get_unknown_pattern()
        print()
        test_pattern_dimensions()
        print()
        print("=" * 60)
        print("All pattern tests PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
