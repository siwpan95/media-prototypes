# -*- coding: utf-8 -*-
"""
Game Controller - Main game loop and event coordination.
"""

import pygame
from tkinter import Tk, filedialog
from typing import Optional

from model import GridModel, FormulaLoader
from view import Renderer, UIManager
from config import FPS, GRID_W, GRID_H


class GameController:
    """Main game controller coordinating MVC components."""

    def __init__(self):
        # Initialize MVC components
        self.grid = GridModel()
        self.formula = FormulaLoader()
        self.renderer = Renderer()
        self.ui = UIManager()

        # Setup callbacks
        self._setup_callbacks()

        # Running state
        self.running = True

    def _setup_callbacks(self) -> None:
        """Setup UI button callbacks."""
        self.ui.set_callback('load', self.on_load_formula)
        self.ui.set_callback('template', self.on_generate_template)
        self.ui.set_callback('default', self.on_restore_default)

    def on_load_formula(self) -> None:
        """Handle load formula button."""
        success, msg = self._show_file_dialog("Select Python Formula File")
        if success:
            self.grid.reset()

    def on_generate_template(self) -> None:
        """Handle generate template button."""
        self._show_save_dialog("Save Formula Template")

    def on_restore_default(self) -> None:
        """Handle restore default button."""
        self.formula.restore_default()
        self.grid.reset()
        self.ui.set_formula_name(self.formula.formula_name)
        self.renderer.clear_error()

    def _show_file_dialog(self, title: str) -> tuple:
        """Show file open dialog."""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Python files", "*.py")]
        )
        root.destroy()

        if not file_path:
            return False, "Cancelled"

        success, msg = self.formula.load_from_file(file_path)
        if success:
            self.ui.set_formula_name(self.formula.formula_name)
            self.renderer.clear_error()
            print(f"Loaded formula: {self.formula.formula_name}")
        else:
            self.ui.set_error(msg)
            self.renderer.set_error(msg)
            print(f"Load error: {msg}")

        return success, msg

    def _show_save_dialog(self, title: str) -> None:
        """Show file save dialog."""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".py",
            filetypes=[("Python files", "*.py")],
            initialfile="my_formula.py"
        )
        root.destroy()

        if not file_path:
            return

        template_content = '''# Custom Cellular Automata Formula
NAME = "My Model"   # Optional, displayed on the UI

def update(u, v, Du, Dv, F, k, dt, dx):
    """
    Called every frame, return new (u, v)
    Parameters:
        u, v : current state (2D numpy arrays)
        Du, Dv, F, k, dt, dx : predefined parameters (can be ignored)
    Notes:
        - Do not hardcode grid size, use u.shape
        - Return values will be clipped to [0, 1] (optional)
    """
    # Example: simple diffusion + reaction
    Lu = (np.roll(u, 1, 0) + np.roll(u, -1, 0) +
          np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4*u) / dx**2
    new_u = u + Du * Lu * dt
    new_v = v * 0.99  # slow decay
    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)

# Optional: custom display content (default displays v)
# def get_display(v):
#     return v * 0.5  # can return u, v, u*v, etc.

# Optional: custom initial state
# def init_state(H, W):
#     u = np.random.rand(H, W)
#     v = np.zeros((H, W))
#     v[H//2-5:H//2+5, W//2-5:W//2+5] = 1.0
#     return u, v
'''

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        self.ui.set_formula_name("Template Generated")
        print(f"Template saved to: {file_path}")

    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            self.ui.process_events(event)

    def update_simulation(self) -> None:
        """Update simulation state."""
        try:
            if not self.grid.validate():
                raise ValueError("Grid validation failed")

            new_u, new_v = self.formula.update(self.grid.u, self.grid.v)

            valid, msg = self.formula.validate_output(new_u, new_v)
            if not valid:
                raise ValueError(msg)

            self.grid.u = new_u
            self.grid.v = new_v
            self.grid.increment_iteration()
            self.renderer.clear_error()

        except Exception as e:
            self.renderer.set_error(f"Error: {str(e)}")

    def render(self) -> None:
        """Render the current state."""
        self.renderer.clear()
        self.renderer.render_preview(self.formula.get_display_array(self.grid.v))
        self.renderer.render_sidebar()
        self.renderer.render_info(self.renderer.get_fps(), self.grid.iteration)
        self.renderer.flip()

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            time_delta = self.renderer.tick(FPS)

            self.handle_events()
            self.update_simulation()
            self.render()
            self.ui.update(time_delta)

        self.renderer.quit()

    def quit(self) -> None:
        """Quit the application."""
        self.running = False
