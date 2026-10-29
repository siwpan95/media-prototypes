# -*- coding: utf-8 -*-
"""
Configuration settings for the application.
"""

# Window settings
WIDTH = 720
HEIGHT = 520
PANEL_WIDTH = 200
PREVIEW_W = WIDTH - PANEL_WIDTH
FPS = 60

# Grid settings
CELL_SIZE = 2
GRID_W = 200
GRID_H = 200

# Default reaction-diffusion parameters
Du = 0.16
Dv = 0.08
F = 0.035
k = 0.065
dt = 0.5
dx = CELL_SIZE

# Color theme
BG_DARK = (30, 30, 40)
PANEL_BG = (45, 45, 60)
ACCENT_COLOR = (80, 140, 200)
TEXT_COLOR = (220, 220, 230)
ERROR_COLOR = (255, 100, 100)

# File paths
BASE_DIR = "resources"
DEFAULT_FORMULA_NAME = "Gray-Scott"

# Get resource path for PyInstaller compatibility
def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    import sys
    import os

    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
