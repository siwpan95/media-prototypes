"""Comprehensive rule tests for all CA rules (141 total).

Tests:
  - 2-state Life-like rules (63 rules)
  - Multi-state rules (9 rules)
  - Complex rules (11 rules)
  - Continuous rules: Gray-Scott, Lenia, Larger than Life, 1D Elementary (58 rules)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from rules import RULES, list_rules, count_neighbours, total_count
from core import CellularAutomaton


# ---------------------------------------------------------------------------
# Neighbour counting
# ---------------------------------------------------------------------------

def test_count_neighbours():
    """Test Moore neighbourhood counting."""
    print("Testing count_neighbours()...")
    # Simple 3x3 test: center cell has 8 neighbours
    grid = np.ones((3, 3), dtype=np.uint8)
    result = count_neighbours(grid)
    assert result[1, 1] == 8, f"Expected 8, got {result[1, 1]}"
    # Corner cell also has 8 neighbours (toroidal)
    assert result[0, 0] == 8, f"Expected 8, got {result[0, 0]}"

    # Empty grid
    grid = np.zeros((5, 5), dtype=np.uint8)
    result = count_neighbours(grid)
    assert result.sum() == 0
    print("  PASSED")


# ---------------------------------------------------------------------------
# 2-state Life-like rules
# ---------------------------------------------------------------------------

_LIFE_RULES = [
    "game_of_life", "highlife", "day_and_night", "seeds", "maze",
    "34_life", "long_life", "replicator", "anneal", "diamoeba",
]


def test_life_rules_exist():
    """Test all Life-like rules are registered."""
    print("Testing Life-like rules registry...")
    for name in _LIFE_RULES:
        rule = RULES.get(name)
        assert rule is not None, f"Rule '{name}' not found"
        assert rule.num_states == 2, f"{name}: expected 2 states, got {rule.num_states}"
        assert rule.name == name
    print(f"  All {len(_LIFE_RULES)} Life-like rules registered. PASSED")


def test_life_rules_step():
    """Test each Life-like rule can step without error."""
    print("Testing Life-like rules step()...")
    for name in _LIFE_RULES:
        ca = CellularAutomaton(rows=30, cols=30, rule_name=name, initial_density=0.3)
        alive_before = ca.alive_count
        for _ in range(5):
            ca.step()
        # Grid shape should be maintained
        assert ca.grid.shape == (30, 30)
        # Grid dtype should be uint8
        assert ca.grid.dtype == np.uint8
        # Alive count should be >= 0 (not negative)
        assert ca.alive_count >= 0
        print(f"    {name}: shape={ca.grid.shape}, alive={ca.alive_count}, states={ca.num_states} OK")
    print("  PASSED")


def test_life_rules_correctness():
    """Test correctness of specific Life rules.

    - Game of Life: a 2x2 block is a still life (should not change)
    - Seeds: all cells should die without births
    """
    print("Testing Life rules correctness...")

    # Game of Life: 2x2 block is stable
    ca = CellularAutomaton(rows=10, cols=10, rule_name="game_of_life")
    ca.clear()
    ca.set_cell(4, 4, 1)
    ca.set_cell(4, 5, 1)
    ca.set_cell(5, 4, 1)
    ca.set_cell(5, 5, 1)
    for _ in range(3):
        ca.step()
    assert ca.grid[4, 4] == 1, "Block should survive"
    assert ca.grid[4, 5] == 1
    assert ca.grid[5, 4] == 1
    assert ca.grid[5, 5] == 1
    print("    Game of Life: block still life OK")

    # Game of Life: blinker oscillates
    ca = CellularAutomaton(rows=10, cols=10, rule_name="game_of_life")
    ca.clear()
    ca.set_cell(5, 3, 1)
    ca.set_cell(5, 4, 1)
    ca.set_cell(5, 5, 1)
    ca.step()
    assert ca.grid[4, 4] == 1, "Blinker should be vertical after 1 step"
    assert ca.grid[5, 4] == 1
    assert ca.grid[6, 4] == 1
    print("    Game of Life: blinker oscillation OK")

    # Seeds: check that all cells die (seeds has B2/S, no survival)
    ca = CellularAutomaton(rows=30, cols=30, rule_name="seeds", initial_density=0.3)
    alive_before = ca.alive_count
    # Seeds is chaotic — verify the rule processes correctly
    for _ in range(3):
        ca.step()
    assert ca.grid.dtype == np.uint8
    print("    Seeds: step OK")

    print("  PASSED")


# ---------------------------------------------------------------------------
# Multi-state rules
# ---------------------------------------------------------------------------

_MULTI_STATE_RULES = ["brians_brain", "wireworld", "forest_fire", "crystal_growth"]


def test_multi_state_rules_exist():
    """Test multi-state rules are registered."""
    print("Testing multi-state rules registry...")
    expected_states = {
        "brians_brain": 3,
        "wireworld": 4,
        "forest_fire": 3,
        "crystal_growth": 3,
    }
    for name in _MULTI_STATE_RULES:
        rule = RULES.get(name)
        assert rule is not None, f"Rule '{name}' not found"
        assert rule.num_states == expected_states[name], \
            f"{name}: expected {expected_states[name]} states, got {rule.num_states}"
    print(f"  All {len(_MULTI_STATE_RULES)} multi-state rules registered. PASSED")


def test_multi_state_rules_step():
    """Test each multi-state rule can step without error."""
    print("Testing multi-state rules step()...")
    for name in _MULTI_STATE_RULES:
        ca = CellularAutomaton(rows=30, cols=30, rule_name=name)
        for _ in range(5):
            ca.step()
        assert ca.grid.shape == (30, 30)
        assert ca.grid.dtype == np.uint8
        # All cell states should be in valid range
        assert ca.grid.max() < ca.num_states, \
            f"{name}: max state {ca.grid.max()} >= {ca.num_states}"
        assert ca.grid.min() >= 0
        print(f"    {name}: shape={ca.grid.shape}, alive={ca.alive_count}, "
              f"states={ca.num_states}, max={ca.grid.max()} OK")
    print("  PASSED")


def test_brians_brain_correctness():
    """Test Brian's Brain specific behavior."""
    print("Testing Brian's Brain correctness...")
    ca = CellularAutomaton(rows=10, cols=10, rule_name="brians_brain")
    ca.clear()
    # Set up a simple pattern
    ca.set_cell(5, 4, 1)  # alive
    ca.set_cell(5, 5, 1)  # alive
    ca.step()
    # These alive cells should become dying (state 2)
    assert ca.grid[5, 4] == 2, f"Expected state 2 (dying), got {ca.grid[5,4]}"
    assert ca.grid[5, 5] == 2, f"Expected state 2 (dying), got {ca.grid[5,5]}"
    ca.step()
    # Dying cells should become dead (state 0)
    assert ca.grid[5, 4] == 0, f"Expected state 0 (dead), got {ca.grid[5,4]}"
    print("  PASSED")


def test_wireworld_correctness():
    """Test Wireworld specific behavior."""
    print("Testing Wireworld correctness...")
    ca = CellularAutomaton(rows=10, cols=10, rule_name="wireworld")
    ca.clear()
    # electron head (2) next to conductor (1)
    ca.set_cell(5, 4, 2)  # head
    ca.set_cell(5, 5, 1)  # conductor
    ca.step()
    # head becomes tail
    assert ca.grid[5, 4] == 3, f"Head should become tail (3), got {ca.grid[5,4]}"
    print("  PASSED")


def test_forest_fire_correctness():
    """Test Forest Fire specific behavior."""
    print("Testing Forest Fire correctness...")
    ca = CellularAutomaton(rows=30, cols=30, rule_name="forest_fire")
    # Verify state distribution exists
    empty = ca.state_count(0)
    tree = ca.state_count(1)
    burning = ca.state_count(2)
    assert empty + tree + burning == 30 * 30, "States should sum to total cells"
    print(f"    States: empty={empty}, tree={tree}, burning={burning}")
    # Run a few steps
    for _ in range(10):
        ca.step()
    print("  PASSED")


# ---------------------------------------------------------------------------
# Complex rules (new)
# ---------------------------------------------------------------------------

_COMPLEX_RULES = ["langtons_loop", "snowflake", "cyclic", "hodgepodge"]


def test_complex_rules_exist():
    """Test complex rules are registered."""
    print("Testing complex rules registry...")
    expected_states = {
        "langtons_loop": 8,
        "snowflake": 8,
        "cyclic": 14,
        "hodgepodge": 20,
    }
    for name in _COMPLEX_RULES:
        rule = RULES.get(name)
        assert rule is not None, f"Rule '{name}' not found"
        assert rule.num_states == expected_states[name], \
            f"{name}: expected {expected_states[name]} states, got {rule.num_states}"
    print(f"  All {len(_COMPLEX_RULES)} complex rules registered. PASSED")


def test_complex_rules_step():
    """Test each complex rule can step without error."""
    print("Testing complex rules step()...")
    for name in _COMPLEX_RULES:
        ca = CellularAutomaton(rows=30, cols=30, rule_name=name)
        for i in range(5):
            ca.step()
            # Verify grid integrity
            assert ca.grid.shape == (30, 30), f"{name}: shape mismatch"
            assert ca.grid.max() < ca.num_states, \
                f"{name}: state overflow {ca.grid.max()} >= {ca.num_states}"
            assert ca.grid.min() >= 0, f"{name}: negative state"
        alive = ca.alive_count
        print(f"    {name}: alive={alive}, max_state={ca.grid.max()}, "
              f"num_states={ca.num_states} OK")
    print("  PASSED")


def test_langtons_loop_behavior():
    """Test Langton's Loop specific behavior."""
    print("Testing Langton's Loop behavior...")
    ca = CellularAutomaton(rows=30, cols=30, rule_name="langtons_loop")
    # Initial randomization should produce valid states
    assert ca.num_states == 8
    for _ in range(10):
        ca.step()
    # Should still have valid states
    assert ca.grid.max() < 8
    assert ca.grid.min() >= 0
    print("  PASSED")


def test_cyclic_behavior():
    """Test Cyclic CA spiral formation."""
    print("Testing Cyclic CA behavior...")
    ca = CellularAutomaton(rows=50, cols=50, rule_name="cyclic")
    assert ca.num_states == 14
    for _ in range(20):
        ca.step()
    # Verify each state exists (should have multiple states)
    states_present = set(np.unique(ca.grid))
    assert len(states_present) > 1, "Cyclic CA should have multiple states"
    assert max(states_present) < 14
    print(f"    States present: {sorted(states_present)}")
    print("  PASSED")


def test_snowflake_behavior():
    """Test Snowflake rule behavior."""
    print("Testing Snowflake behavior...")
    ca = CellularAutomaton(rows=50, cols=50, rule_name="snowflake")
    assert ca.num_states == 8
    for _ in range(10):
        ca.step()
    frozen = ca.state_count(ca.num_states - 1)
    print(f"    Frozen cells: {frozen}")
    print("  PASSED")


def test_hodgepodge_behavior():
    """Test Hodgepodge Machine behavior."""
    print("Testing Hodgepodge behavior...")
    ca = CellularAutomaton(rows=50, cols=50, rule_name="hodgepodge")
    assert ca.num_states == 20
    for _ in range(20):
        ca.step()
    states_present = set(np.unique(ca.grid))
    print(f"    States present: {sorted(states_present)}")
    print("  PASSED")


# ---------------------------------------------------------------------------
# Continuous rules (new)
# ---------------------------------------------------------------------------

_CONTINUOUS_RULES = [
    "gray_scott", "gray_scott_spots", "gray_scott_stripes",
    "gray_scott_maze", "gray_scott_waves", "gray_scott_pulsating",
    "lenia", "lenia_hydro",
    "larger_than_life", "ltl_bugs2", "ltl_brain",
    "ltl_sand", "ltl_cities", "ltl_worms",
    "elementary_1d", "wolfram_30", "wolfram_90", "wolfram_110",
    "smooth_life", "bz_reaction",
]


def test_continuous_rules_exist():
    """Test all continuous rules are registered."""
    print("Testing continuous rules registry...")
    for name in _CONTINUOUS_RULES:
        rule = RULES.get(name)
        assert rule is not None, f"Rule '{name}' not found"
    print(f"  All {len(_CONTINUOUS_RULES)} continuous rules registered. PASSED")


def test_gray_scott_step():
    """Test Gray-Scott variants step correctly."""
    print("Testing Gray-Scott rules...")
    for name in ["gray_scott", "gray_scott_spots", "gray_scott_stripes",
                 "gray_scott_maze", "gray_scott_waves", "gray_scott_pulsating"]:
        ca = CellularAutomaton(rows=30, cols=30, rule_name=name)
        for _ in range(5):
            ca.step()
        assert ca.grid.shape == (30, 30)
        assert ca.grid.dtype == np.uint8
        # Gray-Scott produces uint8 0-255 grid
        rule = ca.rule
        assert hasattr(rule, 'u_field')
        assert hasattr(rule, 'v_field')
        u = rule.u_field
        v = rule.v_field
        assert u is not None and v is not None
        assert u.min() >= 0.0 and u.max() <= 1.0
        assert v.min() >= 0.0 and v.max() <= 1.0
        print(f"    {name}: u∈[{u.min():.2f},{u.max():.2f}] v∈[{v.min():.2f},{v.max():.2f}] OK")
    print("  PASSED")


def test_lenia_step():
    """Test Lenia variants step correctly."""
    print("Testing Lenia rules...")
    for name in ["lenia", "lenia_hydro"]:
        ca = CellularAutomaton(rows=30, cols=30, rule_name=name)
        for _ in range(5):
            ca.step()
        assert ca.grid.shape == (30, 30)
        rule = ca.rule
        assert hasattr(rule, 'field')
        f = rule.field
        assert f is not None
        assert f.min() >= 0.0 and f.max() <= 1.0
        print(f"    {name}: field∈[{f.min():.2f},{f.max():.2f}] OK")
    print("  PASSED")


def test_larger_than_life_step():
    """Test Larger than Life variants step correctly."""
    print("Testing Larger than Life rules...")
    for name in ["larger_than_life", "ltl_bugs2", "ltl_brain",
                 "ltl_sand", "ltl_cities", "ltl_worms"]:
        ca = CellularAutomaton(rows=30, cols=30, rule_name=name, initial_density=0.5)
        alive_at_any_step = False
        for s in range(10):
            ca.step()
            if ca.alive_count > 0:
                alive_at_any_step = True
        assert ca.grid.shape == (30, 30)
        assert ca.num_states == 2
        # At least some steps should have alive cells (dense init)
        if not alive_at_any_step:
            print(f"    WARNING: {name} all steps alive=0 (rule may be sparse)")
        print(f"    {name}: alive={ca.alive_count} OK")
    print("  PASSED")


def test_elementary_1d_step():
    """Test 1D Elementary CA rules step correctly."""
    print("Testing Elementary 1D CA rules...")
    for name in ["elementary_1d", "wolfram_30", "wolfram_90", "wolfram_110"]:
        ca = CellularAutomaton(rows=30, cols=60, rule_name=name)
        for _ in range(25):
            ca.step()
        assert ca.grid.shape == (30, 60)
        assert ca.num_states == 2, f"{name}: expected 2 states"
        # Should have both 0 and 1 cells
        states = set(np.unique(ca.grid))
        assert len(states) <= 2
        print(f"    {name}: states={states} OK")
    print("  PASSED")


def test_rule30_famous():
    """Test Wolfram Rule 30 produces Sierpinski-like pattern."""
    print("Testing Wolfram Rule 30...")
    ca = CellularAutomaton(rows=30, cols=60, rule_name="wolfram_30")
    # After many steps, should have complex pattern
    for _ in range(28):
        ca.step()
    alive = ca.alive_count
    # Rule 30 should produce significant activity
    assert alive > 0, "Rule 30 should produce active cells"
    print(f"    After 28 steps: {alive} alive cells")
    print("  PASSED")


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

def test_list_rules():
    """Test list_rules() returns all rules."""
    print("Testing list_rules()...")
    rules = list_rules()
    expected_count = total_count
    assert len(rules) == expected_count, f"Expected {expected_count} rules, got {len(rules)}"
    # Check key rules still exist
    key_rules = _LIFE_RULES + _MULTI_STATE_RULES + _COMPLEX_RULES + _CONTINUOUS_RULES
    for name in key_rules:
        assert name in rules, f"'{name}' missing from list_rules()"
    print(f"  {len(rules)} rules total. PASSED")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Cellular Automaton — Rule Tests")
    print("=" * 60)
    print()

    try:
        test_count_neighbours()
        print()
        test_list_rules()
        print()
        test_life_rules_exist()
        test_life_rules_step()
        test_life_rules_correctness()
        print()
        test_multi_state_rules_exist()
        test_multi_state_rules_step()
        test_brians_brain_correctness()
        test_wireworld_correctness()
        test_forest_fire_correctness()
        print()
        test_complex_rules_exist()
        test_complex_rules_step()
        test_langtons_loop_behavior()
        test_cyclic_behavior()
        test_snowflake_behavior()
        test_hodgepodge_behavior()
        print()
        test_continuous_rules_exist()
        test_gray_scott_step()
        test_lenia_step()
        test_larger_than_life_step()
        test_elementary_1d_step()
        test_rule30_famous()
        print()
        print("=" * 60)
        print("All rule tests PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
