"""Initial patterns library for Cellular Automaton.

Contains common CA patterns that can be loaded onto the grid.
Supports both 2-state and multi-state patterns.
"""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# 2-state patterns (Game of Life)
# ---------------------------------------------------------------------------

GLIDER: Final[NDArray[np.uint8]] = np.array([
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1],
], dtype=np.uint8)

GLIDER_GUN: Final[NDArray[np.uint8]] = np.array([
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
], dtype=np.uint8)

PULSAR: Final[NDArray[np.uint8]] = np.array([
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0],
    [0,0,0,1,1,1,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,0,0,0,1,1,1,0,0,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
], dtype=np.uint8)

BEACON: Final[NDArray[np.uint8]] = np.array([
    [1, 1, 0, 0],
    [1, 1, 0, 0],
    [0, 0, 1, 1],
    [0, 0, 1, 1],
], dtype=np.uint8)

BLINKER: Final[NDArray[np.uint8]] = np.array([
    [1, 1, 1],
], dtype=np.uint8)

BLOCK: Final[NDArray[np.uint8]] = np.array([
    [1, 1],
    [1, 1],
], dtype=np.uint8)

BEEHIVE: Final[NDArray[np.uint8]] = np.array([
    [0, 1, 1, 0],
    [1, 0, 0, 1],
    [0, 1, 1, 0],
], dtype=np.uint8)

LWSS: Final[NDArray[np.uint8]] = np.array([
    [0, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0],
], dtype=np.uint8)

MWSS: Final[NDArray[np.uint8]] = np.array([
    [0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0],
    [0, 1, 1, 1, 1],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 1, 0],
], dtype=np.uint8)

# ---------------------------------------------------------------------------
# Multi-state patterns
# ---------------------------------------------------------------------------

# Langton's Loop initial configuration (8-state, 10x15 cells)
LANGTON_LOOP: Final[NDArray[np.uint8]] = np.array([
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,2,2,2,2,2,2,2,2,2,2,2,2,2,0],
    [0,2,1,1,1,1,1,1,1,1,1,1,1,2,0],
    [0,2,1,1,1,1,1,1,1,1,1,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,1,1,1,0,1,1,1,1,1,2,0],
    [0,2,1,1,1,1,1,0,1,1,1,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,0,0,0,0,0,0,0,1,1,2,0],
    [0,2,1,1,1,1,1,1,1,1,1,1,1,2,0],
    [0,2,1,1,1,1,1,1,1,1,1,1,1,2,0],
    [0,2,2,2,2,2,2,2,2,2,2,2,2,2,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
], dtype=np.uint8)

# Wireworld patterns
WIRE_DIODE: Final[NDArray[np.uint8]] = np.array([
    [0,0,0,0,0,0,0],
    [0,1,1,1,2,3,1],
    [0,1,0,0,0,0,1],
    [0,1,1,1,1,1,1],
    [0,0,0,1,0,0,0],
    [0,0,0,1,0,0,0],
], dtype=np.uint8)


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

PATTERNS: Final[dict[str, NDArray[np.uint8]]] = {
    "glider": GLIDER,
    "glider_gun": GLIDER_GUN,
    "pulsar": PULSAR,
    "beacon": BEACON,
    "blinker": BLINKER,
    "block": BLOCK,
    "beehive": BEEHIVE,
    "lwss": LWSS,
    "mwss": MWSS,
    "langton_loop": LANGTON_LOOP,
    "wire_diode": WIRE_DIODE,
}


def get_pattern(name: str) -> NDArray[np.uint8] | None:
    """Get a pattern by name from the registry."""
    return PATTERNS.get(name)


def list_patterns() -> list[str]:
    """List all available pattern names."""
    return list(PATTERNS.keys())


def place_pattern(
    grid: NDArray[np.uint8],
    pattern: NDArray[np.uint8],
    row: int,
    col: int,
    clear_first: bool = True,
) -> NDArray[np.uint8]:
    """Place a pattern onto the grid at the specified position.

    Args:
        grid: The target grid (2D uint8 array)
        pattern: The pattern to place (2D uint8 array)
        row: Top row position
        col: Left column position
        clear_first: If True, clear the grid before placing

    Returns:
        The modified grid
    """
    if clear_first:
        grid[:] = 0
    p_rows, p_cols = pattern.shape
    g_rows, g_cols = grid.shape
    if row < 0 or col < 0 or row + p_rows > g_rows or col + p_cols > g_cols:
        raise ValueError(
            f"Pattern {pattern.shape} does not fit at ({row},{col}) "
            f"on grid {grid.shape}"
        )
    grid[row:row + p_rows, col:col + p_cols] = pattern
    return grid
