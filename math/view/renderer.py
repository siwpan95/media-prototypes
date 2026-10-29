# -*- coding: utf-8 -*-
"""
Renderer - Handles all pygame rendering.
"""

import pygame
import numpy as np
from config import (WIDTH, HEIGHT, PANEL_WIDTH, PREVIEW_W,
                    BG_DARK, PANEL_BG, ACCENT_COLOR, TEXT_COLOR)


class Renderer:
    """Handles all rendering operations."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cellular Automata - Formula Lab")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 14)

        # State
        self.error_msg = ""

    def clear(self) -> None:
        """Clear the screen."""
        self.screen.fill(BG_DARK)

    def render_preview(self, display_array: np.ndarray) -> None:
        """Render the grid preview area."""
        # Convert to display surface
        display_array = (np.clip(display_array, 0, 1) * 255).astype(np.uint8)
        surface = pygame.surfarray.make_surface(
            np.stack([display_array] * 3, axis=-1)
        )
        surface = pygame.transform.scale(surface, (PREVIEW_W, HEIGHT))
        self.screen.blit(surface, (0, 0))

    def render_sidebar(self) -> None:
        """Render the sidebar background and dividers."""
        # Sidebar background
        panel_rect = pygame.Rect((PREVIEW_W, 0), (PANEL_WIDTH, HEIGHT))
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)

        # Left border line
        pygame.draw.line(self.screen, ACCENT_COLOR,
                        (PREVIEW_W, 0), (PREVIEW_W, HEIGHT), 2)

        # Dividers
        divider_color = (70, 70, 90)
        pygame.draw.line(self.screen, divider_color,
                        (PREVIEW_W + 15, 108), (PREVIEW_W + PANEL_WIDTH - 15, 108), 1)
        pygame.draw.line(self.screen, divider_color,
                        (PREVIEW_W + 15, 248), (PREVIEW_W + PANEL_WIDTH - 15, 248), 1)
        pygame.draw.line(self.screen, divider_color,
                        (PREVIEW_W + 15, 380), (PREVIEW_W + PANEL_WIDTH - 15, 380), 1)

    def render_info(self, fps: float, iteration: int) -> None:
        """Render FPS and iteration info."""
        fps_text = self.font.render(f"FPS: {int(fps)}", True, TEXT_COLOR)
        self.screen.blit(fps_text, (5, 5))

        iter_text = self.font.render(f"Iter: {iteration}", True, TEXT_COLOR)
        self.screen.blit(iter_text, (5, 28))

        if self.error_msg:
            err_surf = self.font.render(self.error_msg, True, (255, 100, 100))
            self.screen.blit(err_surf, (5, 51))

    def set_error(self, msg: str) -> None:
        """Set error message."""
        self.error_msg = msg

    def clear_error(self) -> None:
        """Clear error message."""
        self.error_msg = ""

    def tick(self, fps_limit: int) -> float:
        """Tick the clock and return delta time."""
        return self.clock.tick(fps_limit) / 1000.0

    def get_fps(self) -> float:
        """Get current FPS."""
        return self.clock.get_fps()

    def flip(self) -> None:
        """Flip the display."""
        pygame.display.flip()

    def quit(self) -> None:
        """Quit pygame."""
        pygame.quit()
