"""Rendering module for the Cellular Automaton Wallpaper.

Draws the CA grid onto a pygame surface with color-coded cells, trails,
optional grid lines, and a minimal HUD overlay.

Rendering pipeline (enhanced):
  1. numpy pixel array  →  small Surface (1 px / cell)
  2. convert()           →  match display pixel format for fast blit
  3. smoothscale / scale →  upscale to screen resolution
  4. glow / bloom        →  additive blur pass for luminous look
  5. grid + HUD          →  overlay
  6. display.flip()      →  present
"""

from __future__ import annotations

import os
from typing import Final

import numpy as np
from numpy.typing import NDArray
import pygame

from core.automaton import CellularAutomaton
from rendering.color_themes import Theme, get_theme
from config import Config


# ---------------------------------------------------------------------------
# HUD translations
# ---------------------------------------------------------------------------

_HUD_TEXT: Final[dict[str, dict[str, str]]] = {
    "en": {
        "paused": "PAUSED",
        "gen": "Gen",
        "alive": "Alive",
        "rule": "Rule",
        "fps": "FPS",
        "help": "ESC:Quit  SPACE:Pause  R:Reset  G:Grid  T:Theme  TAB:Rule  Click:Draw",
    },
    "zh": {
        "paused": "PAUSED",
        "gen": "代",
        "alive": "存活",
        "rule": "规则",
        "fps": "FPS",
        "help": "ESC:退出  SPACE:暂停  R:重置  G:网格  T:主题  TAB:规则  点击:绘制",
    },
}


def get_local_font_path() -> str | None:
    """Return the path to the bundled local font, if it exists."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local = os.path.join(project_dir, "dinglieciweifont20250217-2.ttf")
    return local if os.path.isfile(local) else None


class Renderer:
    """Handles all pygame drawing for the CA wallpaper.

    Uses a pixel-buffer approach with vectorized numpy operations:
    build the full frame as a small (1px/cell) array, then scale up.

    Enhanced pipeline adds:
      - Anti-aliased smooth scaling (pygame.transform.smoothscale)
      - Bloom / glow post-processing via additive blurred pass
      - Surface caching to avoid per-frame allocation
      - Display-format conversion for fast blitting
    """

    def __init__(
        self, screen: pygame.Surface, ca: CellularAutomaton, config: Config,
    ) -> None:
        self.screen = screen
        self.ca = ca
        self.config = config
        self.cell_size = config.cell_size
        self.show_grid = config.show_grid
        self.lang = config.lang

        self.width: int = screen.get_width()
        self.height: int = screen.get_height()

        # Load theme
        self.theme: Theme = get_theme(
            config.color_theme,
            max_age=config.max_age,
            trail_length=config.trail_length,
        )

        # Font for HUD
        self._font: pygame.font.Font | None = None
        self._init_font()

        # --- Cached surfaces (avoid per-frame allocation) ---
        self._small_surface: pygame.Surface | None = None
        self._glow_surface: pygame.Surface | None = None
        self._frame_surface: pygame.Surface | None = None

        # Rendering options
        self._smooth_scale: bool = config.smooth_scale
        self._glow_enabled: bool = config.glow_enabled
        self._glow_intensity: float = max(0.0, min(1.0, config.glow_intensity))
        self._glow_blur: int = max(3, config.glow_blur_size | 1)  # ensure odd

    # ------------------------------------------------------------------
    # Font
    # ------------------------------------------------------------------

    def _init_font(self) -> None:
        """Load a TTF font for HUD text, prioritising local project fonts."""
        # 1) Priority: local project font(s) bundled with the application
        local_path = get_local_font_path()
        if local_path is not None:
            try:
                self._font = pygame.font.Font(local_path, 18)
                return
            except (FileNotFoundError, OSError):
                pass

        # 2) Fallback: common system monospace fonts
        system_candidates = [
            "consola.ttf",
            "Consolas.ttf",
            "DejaVuSansMono.ttf",
            "LiberationMono-Regular.ttf",
        ]
        for name in system_candidates:
            try:
                self._font = pygame.font.Font(name, 18)
                return
            except (FileNotFoundError, OSError):
                continue

        # 3) Last resort: pygame default font
        try:
            self._font = pygame.font.Font(None, 20)
        except Exception:
            self._font = None

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw(
        self,
        ca: CellularAutomaton,
        paused: bool,
        generation: int,
        fps: float,
    ) -> None:
        """Render one frame: cells, trails, glow, grid, HUD."""
        rows, cols = ca.rows, ca.cols
        img = self._build_pixel_array(ca, rows, cols)

        # Build small surface from numpy array, convert for fast blitting
        small = pygame.surfarray.make_surface(img)
        try:
            small = small.convert()
        except pygame.error:
            pass  # display not ready yet

        # Upscale to screen resolution
        if self._smooth_scale:
            scaled = pygame.transform.smoothscale(small, (self.width, self.height))
        else:
            scaled = pygame.transform.scale(small, (self.width, self.height))

        self.screen.blit(scaled, (0, 0))

        # Glow / bloom post-processing
        if self._glow_enabled:
            self._apply_glow(scaled)

        if self.show_grid and self.cell_size >= 4:
            self._draw_grid_lines()

        self._draw_hud(ca, paused, generation, fps)
        # NOTE: display.flip() is called by the caller (main.py),
        # not here, to allow additional drawing (e.g. wallpaper HUD)
        # between renderer.draw() and the final present.

    # ------------------------------------------------------------------
    # Glow / bloom post-processing
    # ------------------------------------------------------------------

    def _apply_glow(self, base_surface: pygame.Surface) -> None:
        """Add a bloom/glow effect via additive blurred pass.

        Downscale the base frame, blur it, scale back up, and
        additively blend onto the screen for a luminous bloom.
        """
        intensity = self._glow_intensity
        if intensity <= 0.01:
            return

        # Downscale for cheap blur
        glow_w = max(1, self.width // 4)
        glow_h = max(1, self.height // 4)
        small_glow = pygame.transform.smoothscale(base_surface, (glow_w, glow_h))

        # Multi-pass box blur approximation via repeated smoothscale
        for _ in range(2):
            small_glow = pygame.transform.smoothscale(
                small_glow, (max(1, glow_w * 2), max(1, glow_h * 2)),
            )
            small_glow = pygame.transform.smoothscale(small_glow, (glow_w, glow_h))

        # Scale back to full resolution
        glow_full = pygame.transform.smoothscale(small_glow, (self.width, self.height))

        # Modulate intensity
        alpha = int(255 * intensity)
        glow_full.set_alpha(alpha)

        # Additive blend onto screen
        self.screen.blit(glow_full, (0, 0), special_flags=pygame.BLEND_ADD)

    # ------------------------------------------------------------------
    # Pixel array builder (vectorized for performance)
    # ------------------------------------------------------------------

    def _build_pixel_array(
        self, ca: CellularAutomaton, rows: int, cols: int,
    ) -> NDArray[np.uint8]:
        """Construct a (cols, rows, 3) uint8 pixel array from CA state."""
        rule_name = ca.rule.name

        # --- Gray-Scott: special heatmap rendering ---
        if rule_name.startswith("gray_scott"):
            return self._build_gray_scott_pixels(ca, rows, cols)

        # --- Lenia: organic blue-green gradient ---
        if rule_name.startswith("lenia"):
            return self._build_lenia_pixels(ca, rows, cols)

        # --- SmoothLife: continuous field rendering ---
        if rule_name.startswith("smooth_life"):
            return self._build_smooth_life_pixels(ca, rows, cols)

        bg = self.theme.bg
        palette = self.theme.alive_colors
        trail_pal = self.theme.trail_colors
        state_colors = self.theme.state_colors
        max_age = self.theme.max_age
        trail_len = self.theme.trail_length

        pal_arr = np.array(palette, dtype=np.uint8)
        trail_arr = np.array(trail_pal, dtype=np.uint8)
        state_arr = np.array(state_colors, dtype=np.uint8)

        if ca.num_states > 2:
            state_idx = np.clip(ca.grid, 0, len(state_arr) - 1)
            img = state_arr[state_idx.T]
        else:
            img = np.full((cols, rows, 3), bg, dtype=np.uint8)
            alive_mask = ca.grid == 1
            if alive_mask.any():
                age_idx = np.clip(ca.age % max_age, 0, len(pal_arr) - 1).astype(np.intp)
                alive_colors = pal_arr[age_idx[alive_mask]]
                img[alive_mask.T] = alive_colors

            if self.config.trail_enabled:
                trail_mask = (ca.trail > 0) & ~alive_mask
                if trail_mask.any():
                    t_vals = ca.trail[trail_mask].astype(np.intp)
                    t_idx = np.clip(trail_len - t_vals, 0, len(trail_pal) - 1)
                    trail_colors = trail_arr[t_idx]
                    img[trail_mask.T] = trail_colors

        return img

    # ------------------------------------------------------------------
    # Special renderers for continuous CAs
    # ------------------------------------------------------------------

    def _build_gray_scott_pixels(
        self, ca: CellularAutomaton, rows: int, cols: int,
    ) -> NDArray[np.uint8]:
        """Build heatmap pixels for Gray-Scott U/V fields."""
        img = np.zeros((cols, rows, 3), dtype=np.uint8)
        rule = ca.rule
        if hasattr(rule, 'u_field') and hasattr(rule, 'v_field'):
            u = rule.u_field
            v = rule.v_field
            if u is not None and v is not None:
                # R = V (inhibitor), G = U (activator), B = combined
                r = np.clip(v.T * 255, 0, 255).astype(np.uint8)
                g = np.clip(u.T * 255, 0, 255).astype(np.uint8)
                b = np.clip((u - v).T * 200 + 30, 0, 255).astype(np.uint8)
                img[:, :, 0] = r
                img[:, :, 1] = g
                img[:, :, 2] = b
        return img

    def _build_lenia_pixels(
        self, ca: CellularAutomaton, rows: int, cols: int,
    ) -> NDArray[np.uint8]:
        """Build organic gradient pixels for Lenia continuous field."""
        img = np.zeros((cols, rows, 3), dtype=np.uint8)
        rule = ca.rule
        if hasattr(rule, 'field'):
            f = rule.field
            if f is not None:
                # Map field value to a cyan-magenta-yellow gradient
                val = f.T  # (cols, rows)
                # Low values: dark blue  ->  Mid: teal/cyan  ->  High: yellow/white
                r = np.clip(val * 180 + 20, 0, 255).astype(np.uint8)
                g = np.clip(val * 255, 0, 255).astype(np.uint8)
                b = np.clip((1.0 - val) * 200 + val * 100, 0, 255).astype(np.uint8)
                img[:, :, 0] = r
                img[:, :, 1] = g
                img[:, :, 2] = b
        return img

    def _build_smooth_life_pixels(
        self, ca: CellularAutomaton, rows: int, cols: int,
    ) -> NDArray[np.uint8]:
        """Build pixels for SmoothLife continuous field.

        Uses a warm gradient: dark red -> orange -> yellow -> white
        to emphasise the smooth, organic patterns.
        """
        img = np.zeros((cols, rows, 3), dtype=np.uint8)
        rule = ca.rule
        if hasattr(rule, 'field'):
            f = rule.field
            if f is not None:
                val = f.T  # (cols, rows)
                # Warm gradient: deep red -> orange -> yellow -> white
                r = np.clip(val * 255, 0, 255).astype(np.uint8)
                g = np.clip(val * val * 220 + val * 35, 0, 255).astype(np.uint8)
                b = np.clip(val * val * val * 180, 0, 255).astype(np.uint8)
                img[:, :, 0] = r
                img[:, :, 1] = g
                img[:, :, 2] = b
        return img

    # ------------------------------------------------------------------
    # Grid overlay
    # ------------------------------------------------------------------

    def _draw_grid_lines(self) -> None:
        """Draw thin grid lines between cells."""
        color = self.theme.grid_color
        cs = self.cell_size
        for x in range(0, self.width, cs):
            pygame.draw.line(self.screen, color, (x, 0), (x, self.height))
        for y in range(0, self.height, cs):
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))

    # ------------------------------------------------------------------
    # HUD overlay
    # ------------------------------------------------------------------

    def _draw_hud(
        self,
        ca: CellularAutomaton,
        paused: bool,
        generation: int,
        fps: float,
    ) -> None:
        """Draw a translucent heads-up display with stats."""
        if self._font is None:
            return
        lang = self.lang if self.lang in _HUD_TEXT else "en"
        t = _HUD_TEXT[lang]
        lines: list[str] = []
        if paused:
            lines.append(f"[ {t['paused']} ]")
        lines.append(
            f"{t['gen']}: {generation}  "
            f"{t['alive']}: {ca.alive_count}  "
            f"{t['rule']}: {ca.rule.name}  "
            f"{t['fps']}: {fps:.0f}"
        )
        lines.append(t["help"])
        color = self.theme.hud_color
        y_offset = 8
        for line in lines:
            surf = self._font.render(line, True, color)
            bg_surf = pygame.Surface(
                (surf.get_width() + 8, surf.get_height() + 2), pygame.SRCALPHA,
            )
            bg_surf.fill((0, 0, 0, 120))
            self.screen.blit(bg_surf, (6, y_offset - 1))
            self.screen.blit(surf, (10, y_offset))
            y_offset += surf.get_height() + 4

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def screen_to_grid(self, x: int, y: int) -> tuple[int, int]:
        """Convert screen pixel coordinates to grid (row, col)."""
        col = x * self.cols_on_screen() // self.width
        row = y * self.rows_on_screen() // self.height
        return row, col

    def cols_on_screen(self) -> int:
        return self.width // self.cell_size

    def rows_on_screen(self) -> int:
        return self.height // self.cell_size

    def update_theme(self, theme_name: str) -> None:
        """Switch to a different color theme."""
        self.theme = get_theme(
            theme_name,
            max_age=self.config.max_age,
            trail_length=self.config.trail_length,
        )
