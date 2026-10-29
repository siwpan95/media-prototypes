# -*- coding: utf-8 -*-
"""
Formula Loader - Handles formula loading and management.
"""

import os
import importlib.util
import inspect
from typing import Callable, Optional, Tuple, Any
import numpy as np

from config import Du, Dv, F, k, dt, dx


def laplacian(grid: np.ndarray, dx_val: float) -> np.ndarray:
    """Compute Laplacian of a grid."""
    return (np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
            np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) -
            4 * grid) / (dx_val ** 2)


def gray_scott_update(u: np.ndarray, v: np.ndarray, Du_val: float,
                      Dv_val: float, F_val: float, k_val: float,
                      dt_val: float, dx_val: float) -> Tuple[np.ndarray, np.ndarray]:
    """Default Gray-Scott reaction-diffusion update function."""
    Lu = laplacian(u, dx_val)
    Lv = laplacian(v, dx_val)
    uvv = u * v * v

    new_u = u + (Du_val * Lu - uvv + F_val * (1 - u)) * dt_val
    new_v = v + (Dv_val * Lv + uvv - (F_val + k_val) * v) * dt_val

    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)


class FormulaLoader:
    """Manages formula loading and execution."""

    def __init__(self):
        self.update_func: Callable = gray_scott_update
        self.formula_name: str = "Gray-Scott"
        self.display_func: Optional[Callable] = None
        self.init_func: Optional[Callable] = None

    def restore_default(self) -> None:
        """Restore default Gray-Scott formula."""
        self.update_func = gray_scott_update
        self.formula_name = "Gray-Scott"
        self.display_func = None
        self.init_func = None

    def load_from_file(self, file_path: str) -> Tuple[bool, str]:
        """Load formula from a Python file.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not file_path:
            return False, "No file selected"

        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                return False, "Invalid module spec"

            formula_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(formula_module)

            # Validate required update function
            if not hasattr(formula_module, 'update'):
                return False, "Formula file missing 'update' function"

            new_func = formula_module.update

            # Check function signature for 2-param wrapper
            sig = inspect.signature(new_func)
            params = list(sig.parameters.keys())

            if len(params) == 2:
                # Wrap 2-param function
                def wrapper(u, v, Du_val, Dv_val, F_val, k_val,
                           dt_val, dx_val):
                    return new_func(u, v)
                self.update_func = wrapper
            else:
                self.update_func = new_func

            # Load optional name
            if hasattr(formula_module, 'NAME'):
                self.formula_name = formula_module.NAME
            else:
                self.formula_name = os.path.basename(file_path)

            # Load optional display function
            if hasattr(formula_module, 'get_display'):
                self.display_func = formula_module.get_display
            else:
                self.display_func = None

            # Load optional init function
            if hasattr(formula_module, 'init_state'):
                self.init_func = formula_module.init_state
            else:
                self.init_func = None

            return True, f"Loaded: {self.formula_name}"

        except Exception as e:
            return False, f"Load error: {str(e)}"

    def get_init_params(self, height: int, width: int) -> Tuple[np.ndarray, np.ndarray]:
        """Get initial state from init function or default."""
        if self.init_func is not None:
            try:
                return self.init_func(height, width)
            except Exception:
                pass

        # Default initialization
        u = np.ones((height, width))
        v = np.zeros((height, width))
        r = 10
        cy, cx = height // 2, width // 2
        v[cy - r:cy + r, cx - r:cx + r] = 1.0
        return u, v

    def get_display_array(self, v: np.ndarray) -> np.ndarray:
        """Get display array from v, applying optional display function."""
        if self.display_func is not None:
            try:
                return self.display_func(v)
            except Exception:
                pass
        return v

    def update(self, u: np.ndarray, v: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Execute formula update."""
        new_u, new_v = self.update_func(u, v, Du, Dv, F, k, dt, dx)
        return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)

    def validate_output(self, new_u: np.ndarray, new_v: np.ndarray) -> Tuple[bool, str]:
        """Validate update output."""
        if new_u.shape != new_v.shape:
            return False, f"Shape mismatch: {new_u.shape} vs {new_v.shape}"

        if not (np.isfinite(new_u).all() and np.isfinite(new_v).all()):
            return False, "Output contains inf or nan"

        return True, ""
