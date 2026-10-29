# -*- coding: utf-8 -*-
"""
Grid Model - Handles grid state and default initialization.
"""

import numpy as np
from config import GRID_W, GRID_H


class GridModel:
    """Manages the cellular automata grid state."""

    def __init__(self):
        self.u: np.ndarray = None
        self.v: np.ndarray = None
        self.iteration: int = 0
        self.reset()

    def reset(self) -> None:
        """Reset grid to initial state with center perturbation."""
        self.u = np.ones((GRID_H, GRID_W))
        self.v = np.zeros((GRID_H, GRID_W))

        # Center square perturbation
        r = 10
        cx, cy = GRID_W // 2, GRID_H // 2
        self.v[cy - r:cy + r, cx - r:cx + r] = 1.0

        self.iteration = 0

    def set_state(self, u: np.ndarray, v: np.ndarray) -> None:
        """Set grid state from external data."""
        self.u = u
        self.v = v
        self.iteration = 0

    def increment_iteration(self) -> None:
        """Increment iteration counter."""
        self.iteration += 1

    @property
    def shape(self) -> tuple:
        """Get grid shape."""
        return self.u.shape

    def validate(self) -> bool:
        """Validate grid state."""
        return self.u.shape == self.v.shape
