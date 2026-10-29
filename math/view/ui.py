# -*- coding: utf-8 -*-
"""
UI Manager - Handles pygame_gui components.
"""

import pygame
import pygame_gui
import pygame_gui.core
from config import WIDTH, HEIGHT, PANEL_WIDTH, PREVIEW_W, Du, Dv, F, k, dt, GRID_W, GRID_H


class UIManager:
    """Manages UI elements using pygame_gui."""

    def __init__(self):
        self.manager = pygame_gui.UIManager((WIDTH, HEIGHT))

        # Create sidebar container
        self.sidebar_container = pygame_gui.core.UIContainer(
            relative_rect=pygame.Rect((PREVIEW_W, 0), (PANEL_WIDTH, HEIGHT)),
            manager=self.manager
        )

        # Create UI elements
        self._create_elements()

        # Event callbacks
        self.callbacks = {}

    def _create_elements(self) -> None:
        """Create all UI elements."""
        # Title
        self.label_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (PANEL_WIDTH - 20, 35)),
            text="CONTROL PANEL",
            manager=self.manager,
            container=self.sidebar_container
        )

        # Formula display
        self.label_formula = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 55), (PANEL_WIDTH - 20, 50)),
            text="Formula: Gray-Scott",
            manager=self.manager,
            container=self.sidebar_container
        )

        # Buttons
        self.btn_load = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 115), (PANEL_WIDTH - 20, 36)),
            text="Load Formula",
            manager=self.manager,
            container=self.sidebar_container
        )

        self.btn_template = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 160), (PANEL_WIDTH - 20, 36)),
            text="Generate Template",
            manager=self.manager,
            container=self.sidebar_container
        )

        self.btn_default = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 205), (PANEL_WIDTH - 20, 36)),
            text="Restore Default",
            manager=self.manager,
            container=self.sidebar_container
        )

        # Parameters section
        self.label_params_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 260), (PANEL_WIDTH - 20, 25)),
            text="Parameters",
            manager=self.manager,
            container=self.sidebar_container
        )

        self.label_params = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 285), (PANEL_WIDTH - 20, 80)),
            text=f"Du={Du}, Dv={Dv}\nF={F}, k={k}\ndt={dt}",
            manager=self.manager,
            container=self.sidebar_container
        )

        # Grid info section
        self.label_grid_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 385), (PANEL_WIDTH - 20, 25)),
            text="Grid Info",
            manager=self.manager,
            container=self.sidebar_container
        )

        self.label_grid = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 410), (PANEL_WIDTH - 20, 50)),
            text=f"Size: {GRID_W} x {GRID_H}",
            manager=self.manager,
            container=self.sidebar_container
        )

    def set_formula_name(self, name: str) -> None:
        """Update formula name display."""
        self.label_formula.set_text(f"Formula: {name}")

    def set_error(self, msg: str) -> None:
        """Set error message."""
        self.label_formula.set_text(msg)

    def set_callback(self, button_id: str, callback) -> None:
        """Register a callback for a button."""
        self.callbacks[button_id] = callback

    def process_events(self, event: pygame.event.Event) -> None:
        """Process pygame events."""
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_load:
                self.callbacks.get('load')()
            elif event.ui_element == self.btn_template:
                self.callbacks.get('template')()
            elif event.ui_element == self.btn_default:
                self.callbacks.get('default')()

    def update(self, time_delta: float) -> None:
        """Update UI manager."""
        self.manager.update(time_delta)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw UI elements."""
        self.manager.draw_ui(surface)
