"""Wallpaper-specific HUD drawing for Cellular Automaton.

Extracted from wallpaper.py to eliminate code duplication with main.py.
"""

from __future__ import annotations

import pygame

from config import Config
from core import CellularAutomaton
from rendering import Renderer


def draw_wallpaper_hud(
    renderer: Renderer,
    ca: CellularAutomaton,
    generation: int,
    fps: float,
    rule_name: str,
    theme_name: str,
    font: pygame.font.Font | None,
) -> None:
    """Draw a minimal HUD for wallpaper mode."""
    if font is None:
        return
    lines = [
        f"Rule: {rule_name}  Theme: {theme_name}",
        f"Gen: {generation}  Alive: {ca.alive_count}  FPS: {fps:.0f}",
        "ESC:Quit  H:Hide HUD  S:Screenshot  R:Reset  TAB:Rule  T:Theme",
    ]
    color = renderer.theme.hud_color
    y_offset = 8
    for line in lines:
        surf = font.render(line, True, color)
        bg_surf = pygame.Surface(
            (surf.get_width() + 8, surf.get_height() + 2), pygame.SRCALPHA,
        )
        bg_surf.fill((0, 0, 0, 120))
        renderer.screen.blit(bg_surf, (6, y_offset - 1))
        renderer.screen.blit(surf, (10, y_offset))
        y_offset += surf.get_height() + 4
