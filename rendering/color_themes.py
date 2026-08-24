"""Color theme definitions for the Cellular Automaton Wallpaper.

Each theme provides:
  - bg:            background RGB tuple
  - alive_colors:  list of RGB tuples; index selected by cell age (cycles)
  - trail_colors:  list of RGB tuples; index selected by trail age
  - state_colors:  list of RGB tuples; colors for each state in multi-state CA
  - grid_color:    RGB tuple for optional grid lines
  - hud_color:     RGB tuple for HUD text overlay
"""

from __future__ import annotations

from typing import Final, Optional


def _lerp_color(
    c1: tuple[int, int, int], c2: tuple[int, int, int], t: float,
) -> tuple[int, int, int]:
    """Linearly interpolate between two RGB colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _build_gradient(
    anchors: list[tuple[int, int, int]], steps: int,
) -> list[tuple[int, int, int]]:
    """Build a gradient palette with *steps* entries from anchor colors."""
    if len(anchors) < 2:
        return anchors * steps
    palette: list[tuple[int, int, int]] = []
    segments = len(anchors) - 1
    steps_per_seg = max(steps // segments, 1)
    for i in range(segments):
        for s in range(steps_per_seg):
            t = s / steps_per_seg
            palette.append(_lerp_color(anchors[i], anchors[i + 1], t))
    while len(palette) < steps:
        palette.append(anchors[-1])
    return palette[:steps]


# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

_MAX_AGE_DEFAULT: Final[int] = 80
_TRAIL_STEPS: Final[int] = 12

# Default state colors — extended to 8 states for Langton's Loop etc.
_DEFAULT_STATE_COLORS: Final[list[tuple[int, int, int]]] = [
    (5, 5, 15),         # 0: empty
    (0, 255, 200),      # 1: conductor / alive
    (255, 255, 0),      # 2: signal → / electron head
    (255, 120, 0),      # 3: signal ↓
    (255, 0, 100),      # 4: signal ← / electron tail
    (200, 0, 255),      # 5: signal ↑
    (100, 100, 255),    # 6: phagocyte
    (255, 200, 100),    # 7: phagocyte+signal
]


class Theme:
    """Container for a single color theme's palette data."""

    def __init__(
        self,
        name: str,
        bg: tuple[int, int, int],
        alive_anchors: list[tuple[int, int, int]],
        trail_anchors: list[tuple[int, int, int]],
        grid_color: tuple[int, int, int],
        hud_color: tuple[int, int, int],
        max_age: int = _MAX_AGE_DEFAULT,
        trail_length: int = _TRAIL_STEPS,
        state_colors: Optional[list[tuple[int, int, int]]] = None,
    ) -> None:
        self.name = name
        self.bg = bg
        self.alive_colors = _build_gradient(alive_anchors, max_age)
        self.trail_colors = _build_gradient(trail_anchors, trail_length)
        self.grid_color = grid_color
        self.hud_color = hud_color
        self.max_age = max_age
        self.trail_length = trail_length
        self.state_colors = state_colors if state_colors is not None else _DEFAULT_STATE_COLORS


_THEMES: dict[str, Theme] = {}


def _register(theme: Theme) -> None:
    _THEMES[theme.name] = theme


# --- Neon ---
_register(Theme(
    name="neon",
    bg=(5, 5, 15),
    alive_anchors=[
        (0, 255, 200), (200, 50, 255),
        (255, 20, 100), (0, 255, 200),
    ],
    trail_anchors=[(0, 80, 60), (10, 10, 20)],
    grid_color=(20, 20, 35),
    hud_color=(0, 220, 180),
    state_colors=[
        (5, 5, 15), (0, 255, 200), (255, 255, 0),
        (255, 120, 0), (255, 20, 100), (200, 50, 255),
        (100, 100, 255), (255, 200, 100),
    ],
))

# --- Ocean ---
_register(Theme(
    name="ocean",
    bg=(2, 8, 20),
    alive_anchors=[
        (100, 200, 255), (20, 80, 200),
        (0, 200, 180), (100, 200, 255),
    ],
    trail_anchors=[(10, 30, 60), (2, 8, 20)],
    grid_color=(10, 20, 40),
    hud_color=(80, 180, 255),
    state_colors=[
        (2, 8, 20), (0, 200, 180), (255, 255, 0),
        (255, 150, 50), (100, 200, 255), (20, 80, 200),
        (100, 150, 255), (255, 200, 150),
    ],
))

# --- Ember ---
_register(Theme(
    name="ember",
    bg=(12, 5, 2),
    alive_anchors=[
        (255, 240, 60), (255, 120, 0),
        (180, 20, 20), (255, 240, 60),
    ],
    trail_anchors=[(60, 15, 5), (12, 5, 2)],
    grid_color=(25, 12, 8),
    hud_color=(255, 160, 40),
    state_colors=[
        (12, 5, 2), (255, 120, 0), (255, 255, 0),
        (255, 80, 0), (255, 240, 60), (180, 20, 20),
        (255, 150, 80), (255, 220, 120),
    ],
))

# --- Matrix ---
_register(Theme(
    name="matrix",
    bg=(0, 4, 0),
    alive_anchors=[
        (0, 255, 0), (0, 180, 0),
        (0, 100, 0), (0, 255, 0),
    ],
    trail_anchors=[(0, 40, 0), (0, 4, 0)],
    grid_color=(0, 15, 0),
    hud_color=(0, 230, 0),
    state_colors=[
        (0, 4, 0), (0, 200, 0), (200, 255, 0),
        (150, 200, 0), (0, 255, 0), (0, 120, 0),
        (80, 200, 80), (200, 255, 80),
    ],
))

# --- Aurora ---
_register(Theme(
    name="aurora",
    bg=(4, 2, 15),
    alive_anchors=[
        (120, 255, 200), (200, 100, 255),
        (255, 120, 180), (100, 180, 255),
        (120, 255, 200),
    ],
    trail_anchors=[(30, 15, 50), (4, 2, 15)],
    grid_color=(15, 10, 30),
    hud_color=(180, 140, 255),
    state_colors=[
        (4, 2, 15), (120, 255, 200), (255, 255, 100),
        (255, 150, 80), (255, 120, 180), (200, 100, 255),
        (150, 150, 255), (255, 220, 150),
    ],
))

# --- Plasma ---
_register(Theme(
    name="plasma",
    bg=(8, 0, 12),
    alive_anchors=[
        (255, 0, 128), (180, 0, 255),
        (0, 200, 255), (255, 200, 0),
        (255, 0, 128),
    ],
    trail_anchors=[(40, 0, 30), (8, 0, 12)],
    grid_color=(20, 5, 25),
    hud_color=(255, 100, 200),
    state_colors=[
        (8, 0, 12), (255, 0, 128), (180, 0, 255),
        (0, 200, 255), (255, 200, 0), (255, 100, 0),
        (100, 0, 255), (255, 255, 100),
    ],
))

# --- Sunset ---
_register(Theme(
    name="sunset",
    bg=(15, 5, 10),
    alive_anchors=[
        (255, 80, 40), (255, 180, 50),
        (200, 40, 100), (255, 80, 40),
    ],
    trail_anchors=[(50, 15, 20), (15, 5, 10)],
    grid_color=(30, 10, 15),
    hud_color=(255, 200, 100),
    state_colors=[
        (15, 5, 10), (255, 80, 40), (255, 180, 50),
        (200, 40, 100), (255, 120, 80), (180, 60, 120),
        (255, 200, 120), (255, 100, 60),
    ],
))


def get_theme(
    name: str,
    max_age: int = _MAX_AGE_DEFAULT,
    trail_length: int = _TRAIL_STEPS,
) -> Theme:
    """Retrieve a theme by name, rebuilding palettes if needed."""
    base = _THEMES.get(name)
    if base is None:
        base = _THEMES["neon"]
    if base.max_age != max_age or base.trail_length != trail_length:
        alive_anchors = [
            base.alive_colors[0],
            base.alive_colors[max_age // 3],
            base.alive_colors[2 * max_age // 3],
            base.alive_colors[-1],
        ]
        trail_anchors = [base.trail_colors[0], base.trail_colors[-1]]
        return Theme(
            name=base.name, bg=base.bg,
            alive_anchors=alive_anchors, trail_anchors=trail_anchors,
            grid_color=base.grid_color, hud_color=base.hud_color,
            max_age=max_age, trail_length=trail_length,
            state_colors=base.state_colors,
        )
    return base


def available_themes() -> list[str]:
    """Return a list of all registered theme names."""
    return list(_THEMES.keys())
