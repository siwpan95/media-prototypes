"""Input handler module — processes keyboard and mouse events.

Translates raw pygame events into application-level actions:
  - ESC:     quit
  - SPACE:   pause/resume
  - R:       randomize grid
  - C:       clear grid
  - G:       toggle grid lines
  - T:       cycle color theme
  - TAB:     cycle CA rule
  - A:       toggle auto-cycle rules/themes
  - M:       toggle audio on/off
  - LClick:  paint alive cells
  - RClick:  erase cells (paint dead)
  - Drag:    continuous painting

Auto-cycle mode (toggled with A key):
  When enabled, automatically switches to a new rule every N seconds
  and a new theme every M seconds. Manual TAB/T overrides pause
  auto-cycling for a cooldown period.
"""

from __future__ import annotations

import time
from typing import Final, TYPE_CHECKING

import pygame

from core.automaton import CellularAutomaton
from rules import RULES, list_rules_by_category
from rendering.color_themes import available_themes
from config import Config
from rendering.renderer import Renderer

if TYPE_CHECKING:
    from audio.audio_manager import AudioManager


_RULE_ORDER: Final[list[str]] = sorted(RULES.keys())


class AutoCycleState:
    """Manages auto-cycling of rules and themes."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.enabled: bool = config.auto_cycle_rules
        self._last_rule_change: float = time.monotonic()
        self._last_theme_change: float = time.monotonic()
        self._manual_override_until: float = 0.0

    def should_cycle_rule(self, current_time: float) -> bool:
        """Check if it's time to auto-cycle to the next rule."""
        if not self.enabled:
            return False
        if current_time < self._manual_override_until:
            return False
        return (current_time - self._last_rule_change) >= self.config.auto_cycle_interval

    def should_cycle_theme(self, current_time: float) -> bool:
        """Check if it's time to auto-cycle to the next theme."""
        if not self.enabled:
            return False
        if current_time < self._manual_override_until:
            return False
        return (current_time - self._last_theme_change) >= self.config.auto_cycle_theme_interval

    def on_rule_changed(self, current_time: float) -> None:
        self._last_rule_change = current_time

    def on_theme_changed(self, current_time: float) -> None:
        self._last_theme_change = current_time

    def on_manual_override(self, current_time: float) -> None:
        """Pause auto-cycling for the cooldown period after manual switch."""
        self._manual_override_until = current_time + self.config.auto_cycle_pause_after_manual
        self._last_rule_change = current_time
        self._last_theme_change = current_time

    def toggle(self) -> None:
        """Toggle auto-cycle on/off."""
        self.enabled = not self.enabled
        if self.enabled:
            now = time.monotonic()
            self._last_rule_change = now
            self._last_theme_change = now
            self._manual_override_until = 0.0


class InputHandler:
    """Handles all user input: keyboard shortcuts and mouse interaction."""

    def __init__(
        self,
        config: Config,
        renderer: Renderer,
        audio_manager: AudioManager | None = None,
    ) -> None:
        self.config = config
        self.renderer = renderer
        self.audio_manager = audio_manager
        self.rule_index: int = (
            _RULE_ORDER.index(config.rule_name)
            if config.rule_name in _RULE_ORDER
            else 0
        )
        self._rule_list = _RULE_ORDER
        self._theme_list = available_themes()
        self._theme_index: int = 0
        try:
            self._theme_index = self._theme_list.index(config.color_theme)
        except ValueError:
            self._theme_index = 0
        self._mouse_drawing: bool = False
        self._mouse_alive: bool = True
        self.auto_cycle = AutoCycleState(config)

    def handle_events(
        self,
        ca: CellularAutomaton,
        paused: bool,
        generation: int,
    ) -> tuple[bool, bool, int]:
        """Process all pending pygame events.

        Returns:
            (running, paused, generation) — updated application state.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, paused, generation
            if event.type == pygame.KEYDOWN:
                running, paused, generation = self._handle_key(
                    event, ca, paused, generation,
                )
                if not running:
                    return False, paused, generation
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event, ca)
            if event.type == pygame.MOUSEBUTTONUP:
                self._mouse_drawing = False
            if event.type == pygame.MOUSEMOTION and self._mouse_drawing:
                self._handle_mouse_motion(event, ca)
        return True, paused, generation

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def _handle_key(
        self,
        event: pygame.event.Event,
        ca: CellularAutomaton,
        paused: bool,
        generation: int,
    ) -> tuple[bool, bool, int]:
        """Handle a single key-down event."""
        if event.key == pygame.K_ESCAPE:
            return False, paused, generation
        if event.key == pygame.K_SPACE:
            paused = not paused
        if event.key == pygame.K_r:
            ca.randomize(self.config.initial_density)
            generation = 0
        if event.key == pygame.K_c:
            ca.clear()
            generation = 0
        if event.key == pygame.K_g:
            self.renderer.show_grid = not self.renderer.show_grid
        if event.key == pygame.K_t:
            self._theme_index = (self._theme_index + 1) % len(self._theme_list)
            theme_name = self._theme_list[self._theme_index]
            self.config.color_theme = theme_name
            self.renderer.update_theme(theme_name)
            self.auto_cycle.on_manual_override(time.monotonic())
        if event.key == pygame.K_TAB:
            self.rule_index = (self.rule_index + 1) % len(self._rule_list)
            rule_name = self._rule_list[self.rule_index]
            ca.set_rule(rule_name)
            self.auto_cycle.on_manual_override(time.monotonic())
        if event.key == pygame.K_a:
            self.auto_cycle.toggle()
            status = "ON" if self.auto_cycle.enabled else "OFF"
            print(f"[Auto-cycle] {status}")
        if event.key == pygame.K_m and self.audio_manager is not None:
            self.audio_manager.enabled = not self.audio_manager.enabled
        return True, paused, generation

    # ------------------------------------------------------------------
    # Auto-cycle
    # ------------------------------------------------------------------

    def check_auto_cycle(
        self,
        ca: CellularAutomaton,
        paused: bool,
    ) -> str | None:
        """Check and perform auto-cycle if needed. Returns new rule name or None."""
        now = time.monotonic()

        # Auto-cycle rules
        if not paused and self.auto_cycle.should_cycle_rule(now):
            self.rule_index = (self.rule_index + 1) % len(self._rule_list)
            rule_name = self._rule_list[self.rule_index]
            ca.set_rule(rule_name)
            ca.randomize(self.config.initial_density)
            self.auto_cycle.on_rule_changed(now)
            return rule_name

        # Auto-cycle themes
        if not paused and self.auto_cycle.should_cycle_theme(now):
            self._theme_index = (self._theme_index + 1) % len(self._theme_list)
            theme_name = self._theme_list[self._theme_index]
            self.config.color_theme = theme_name
            self.renderer.update_theme(theme_name)
            self.auto_cycle.on_theme_changed(now)

        return None

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def _handle_mouse_down(
        self, event: pygame.event.Event, ca: CellularAutomaton,
    ) -> None:
        """Handle mouse button press — start drawing."""
        if event.button in (1, 3):
            self._mouse_drawing = True
            row, col = self.renderer.screen_to_grid(event.pos[0], event.pos[1])
            if ca.num_states > 2:
                current_state = (
                    ca.grid[row, col]
                    if 0 <= row < ca.rows and 0 <= col < ca.cols
                    else 0
                )
                next_state = (current_state + 1) % ca.num_states
                ca.set_cell(row, col, next_state)
                self._mouse_alive = bool(next_state)
            else:
                self._mouse_alive = event.button == 1
                ca.set_cell(row, col, int(self._mouse_alive))

    def _handle_mouse_motion(
        self, event: pygame.event.Event, ca: CellularAutomaton,
    ) -> None:
        """Handle mouse motion while a button is held — paint cells."""
        row, col = self.renderer.screen_to_grid(event.pos[0], event.pos[1])
        if ca.num_states > 2:
            ca.set_cell(row, col, int(self._mouse_alive))
        else:
            ca.set_cell(row, col, int(self._mouse_alive))
