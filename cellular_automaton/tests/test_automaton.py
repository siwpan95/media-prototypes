"""Core automaton tests: grid operations, cell manipulation, evolution."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core import CellularAutomaton
from rules import RULES


def test_creation():
    """Test CellularAutomaton creation with various parameters."""
    print("Testing CellularAutomaton creation...")
    ca = CellularAutomaton(rows=50, cols=50, rule_name="game_of_life")
    assert ca.rows == 50
    assert ca.cols == 50
    assert ca.num_states == 2
    assert ca.grid.shape == (50, 50)
    assert ca.grid.dtype == np.uint8
    print("  Default creation OK")

    ca2 = CellularAutomaton(rows=30, cols=40, rule_name="wireworld", initial_density=0.5)
    assert ca2.rows == 30
    assert ca2.cols == 40
    assert ca2.num_states == 4
    print("  Custom creation OK")
    print("  PASSED")


def test_rule_fallback():
    """Test that invalid rule name falls back to game_of_life."""
    print("Testing rule fallback...")
    ca = CellularAutomaton(rows=10, cols=10, rule_name="nonexistent_rule")
    assert ca.rule.name == "game_of_life"
    assert ca.num_states == 2
    print("  PASSED")


def test_randomize():
    """Test randomize() with different densities and rule types."""
    print("Testing randomize()...")

    # 2-state
    ca = CellularAutomaton(rows=20, cols=20, rule_name="game_of_life")
    ca.randomize(0.5)
    alive_pct = ca.alive_count / 400
    # With density 0.5, expect roughly half alive (allow wide tolerance)
    assert 0.1 < alive_pct < 0.9, f"2-state density out of range: {alive_pct:.2f}"
    print(f"  2-state density=0.5 -> actual={alive_pct:.2%}")

    # 2-state with density 0
    ca.randomize(0.0)
    assert ca.alive_count == 0

    # 2-state with density 1
    ca.randomize(1.0)
    assert ca.alive_count == 400

    # Multi-state
    ca2 = CellularAutomaton(rows=20, cols=20, rule_name="brians_brain")
    assert ca2.num_states == 3
    states = set(np.unique(ca2.grid))
    print(f"  brians_brain states: {states}")

    # Wireworld
    ca3 = CellularAutomaton(rows=20, cols=20, rule_name="wireworld")
    assert ca3.num_states == 4
    print(f"  wireworld max state: {ca3.grid.max()}")

    print("  PASSED")


def test_clear():
    """Test clear() sets all cells to 0."""
    print("Testing clear()...")
    ca = CellularAutomaton(rows=20, cols=20, rule_name="game_of_life", initial_density=0.5)
    assert ca.alive_count > 0
    ca.clear()
    assert ca.alive_count == 0
    assert ca.grid.sum() == 0
    assert ca.age.sum() == 0
    assert ca.trail.sum() == 0
    print("  PASSED")


def test_cell_manipulation():
    """Test toggle_cell() and set_cell()."""
    print("Testing cell manipulation...")
    ca = CellularAutomaton(rows=10, cols=10, rule_name="game_of_life")
    ca.clear()

    # set_cell
    ca.set_cell(5, 5, 1)
    assert ca.grid[5, 5] == 1
    assert ca.age[5, 5] == 1

    # toggle_cell (2-state)
    ca.toggle_cell(5, 5)
    assert ca.grid[5, 5] == 0  # toggled back to 0
    ca.toggle_cell(5, 5)
    assert ca.grid[5, 5] == 1  # toggled back to 1

    # toggle_cell (multi-state)
    ca2 = CellularAutomaton(rows=10, cols=10, rule_name="wireworld")
    ca2.clear()
    ca2.toggle_cell(5, 5)
    assert ca2.grid[5, 5] == 1
    ca2.toggle_cell(5, 5)
    assert ca2.grid[5, 5] == 2
    ca2.toggle_cell(5, 5)
    assert ca2.grid[5, 5] == 3
    ca2.toggle_cell(5, 5)
    assert ca2.grid[5, 5] == 0  # wraps around

    # out of bounds
    ca.set_cell(100, 100, 1)  # should not crash
    ca.set_cell(-1, -1, 1)    # should not crash

    print("  PASSED")


def test_step():
    """Test that step() advances the automaton correctly."""
    print("Testing step()...")
    ca = CellularAutomaton(rows=20, cols=20, rule_name="game_of_life", initial_density=0.3)
    grid_before = ca.grid.copy()
    ca.step()
    grid_after = ca.grid.copy()

    # Grid should have changed (not identical, except in rare cases)
    # We can't guarantee it changed, but shape and dtype should be same
    assert grid_after.shape == grid_before.shape
    assert grid_after.dtype == np.uint8
    print("  PASSED")


def test_rule_switching():
    """Test set_rule() transitions between rules."""
    print("Testing rule switching...")
    ca = CellularAutomaton(rows=20, cols=20, rule_name="game_of_life")
    assert ca.num_states == 2

    ca.set_rule("brians_brain")
    assert ca.num_states == 3
    assert ca.rule.name == "brians_brain"

    ca.set_rule("wireworld")
    assert ca.num_states == 4

    ca.set_rule("langtons_loop")
    assert ca.num_states == 8

    ca.set_rule("snowflake")
    assert ca.num_states == 8

    ca.set_rule("cyclic")
    assert ca.num_states == 14

    ca.set_rule("hodgepodge")
    assert ca.num_states == 20

    # Switch to continuous rules
    ca.set_rule("gray_scott")
    assert ca.rule.name == "gray_scott"
    ca.step()  # should initialize internal state

    ca.set_rule("lenia")
    assert ca.rule.name == "lenia"
    ca.step()

    ca.set_rule("larger_than_life")
    assert ca.num_states == 2
    assert ca.rule.name == "larger_than_life"

    ca.set_rule("wolfram_110")
    assert ca.num_states == 2
    assert ca.rule.name == "wolfram_110"

    ca.set_rule("game_of_life")
    assert ca.num_states == 2
    print("  PASSED")


def test_state_count():
    """Test state_count() for multi-state CA."""
    print("Testing state_count()...")
    ca = CellularAutomaton(rows=20, cols=20, rule_name="wireworld")
    total = 0
    for s in range(ca.num_states):
        total += ca.state_count(s)
    assert total == 400, f"State counts should sum to total: {total}"

    ca2 = CellularAutomaton(rows=10, cols=10, rule_name="brians_brain")
    total2 = sum(ca2.state_count(s) for s in range(ca2.num_states))
    assert total2 == 100
    print("  PASSED")


def test_load_pattern():
    """Test load_pattern()."""
    print("Testing load_pattern()...")
    ca = CellularAutomaton(rows=30, cols=30, rule_name="game_of_life")

    # Load glider
    ca.load_pattern("glider", row=5, col=5)
    assert ca.grid[5, 6] == 1  # glider row 0, col 1
    assert ca.grid[6, 7] == 1  # glider row 1, col 2
    print("  glider loaded OK")

    # Load glider_gun (needs bigger grid; 36 cols wide)
    ca_big = CellularAutomaton(rows=30, cols=40, rule_name="game_of_life")
    ca_big.load_pattern("glider_gun", row=2, col=2)
    assert ca_big.grid[2, 26] == 1  # first live cell of glider gun
    print("  glider_gun loaded OK")

    # Unknown pattern should raise
    try:
        ca.load_pattern("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("  unknown pattern raises ValueError OK")

    print("  PASSED")


def test_alive_count():
    """Test alive_count property."""
    print("Testing alive_count...")
    ca = CellularAutomaton(rows=10, cols=10, rule_name="game_of_life")
    ca.clear()
    ca.set_cell(0, 0, 1)
    ca.set_cell(1, 1, 1)
    ca.set_cell(2, 2, 1)
    assert ca.alive_count == 3

    ca2 = CellularAutomaton(rows=10, cols=10, rule_name="wireworld")
    # All non-zero cells count as alive
    manual_count = int((ca2.grid > 0).sum())
    assert ca2.alive_count == manual_count
    print("  PASSED")


def test_age_tracking():
    """Test that cell age is tracked correctly."""
    print("Testing age tracking...")
    ca = CellularAutomaton(rows=10, cols=10, rule_name="game_of_life")
    ca.clear()
    ca.set_cell(5, 5, 1)
    assert ca.age[5, 5] == 1
    ca.step()
    # The cell may have died; check age system works
    assert ca.age[5, 5] >= 0
    print("  PASSED")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Cellular Automaton — Core Tests")
    print("=" * 60)
    print()
    try:
        test_creation()
        print()
        test_rule_fallback()
        print()
        test_randomize()
        print()
        test_clear()
        print()
        test_cell_manipulation()
        print()
        test_step()
        print()
        test_rule_switching()
        print()
        test_state_count()
        print()
        test_load_pattern()
        print()
        test_alive_count()
        print()
        test_age_tracking()
        print()
        print("=" * 60)
        print("All core tests PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
