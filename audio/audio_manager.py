"""Procedural audio manager for Cellular Automaton Wallpaper.

Generates ambient drones that shift pitch in response to CA cell density.
Uses only pygame.mixer and numpy (no extra dependencies).

Key binding (via input_handler):
    M — Toggle audio on/off
"""

from __future__ import annotations

import numpy as np
import pygame


_TONE_PRESETS: list[tuple[float, float]] = [
    (55.0, 0.55),      # Sub-bass  A1
    (110.0, 0.30),     # Bass      A2
    (220.0, 0.12),     # Mid       A3
    (277.18, 0.06),    # C#4
    (329.63, 0.04),    # E4
]


class AudioManager:
    """Handles procedural ambient audio for the CA wallpaper.

    Usage::

        audio = AudioManager()
        audio.initialize()                  # after pygame.init()
        audio.update(alive_density=0.35)    # each frame
        audio.shutdown()                    # on exit
    """

    def __init__(
        self,
        sample_rate: int = 22050,
        volume: float = 0.12,
        enabled: bool = True,
    ) -> None:
        self._sample_rate = sample_rate
        self._volume = max(0.0, min(1.0, volume))
        self._enabled = enabled
        self._initialized: bool = False
        self._channel: pygame.mixer.Channel | None = None
        self._last_density: float = -1.0

    def initialize(self) -> None:
        """Set up the audio subsystem. Call once after ``pygame.init()``."""
        if self._initialized:
            return
        if not self._enabled:
            self._initialized = True
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=self._sample_rate, size=-16, channels=1,
                )
            else:
                freq, _fmt, _ch = pygame.mixer.get_init()  # type: ignore[misc]
                if freq:
                    self._sample_rate = freq
            self._channel = pygame.mixer.Channel(1)
            self._channel.set_volume(self._volume)
            self._initialized = True
        except pygame.error:
            self._enabled = False
            self._initialized = True

    def shutdown(self) -> None:
        """Stop all audio and release resources."""
        if self._channel:
            self._channel.stop()
        self._initialized = False

    def update(self, alive_density: float) -> None:
        """Regenerate the ambient tone when cell density changes."""
        if not self._enabled or not self._initialized or self._channel is None:
            return
        density = max(0.0, min(1.0, alive_density))
        if abs(density - self._last_density) < 0.03:
            return
        self._last_density = density
        self._regenerate_loop(density)

    # ------------------------------------------------------------------
    # Toggle / Volume
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if self._channel is None:
            return
        if value:
            if self._initialized:
                self._last_density = -1.0
        else:
            self._channel.stop()

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
        if self._channel:
            self._channel.set_volume(self._volume)

    # ------------------------------------------------------------------
    # Internal: waveform generation
    # ------------------------------------------------------------------

    def _regenerate_loop(self, density: float) -> None:
        """Build a short ambient loop whose pitch responds to *density*."""
        assert self._channel is not None
        duration_s = 3.0
        num_samples = int(self._sample_rate * duration_s)
        t = np.linspace(0, duration_s, num_samples, endpoint=False, dtype=np.float32)
        pitch = 1.0 + density * 0.6
        vol_env = 1.0 - density * 0.25
        waveform = np.zeros(num_samples, dtype=np.float32)
        for base_freq, amp in _TONE_PRESETS:
            freq = base_freq * pitch
            tremolo = 1.0 + 0.06 * np.sin(2.0 * np.pi * 0.37 * base_freq / 55.0 * t)
            waveform += amp * vol_env * tremolo * np.sin(2.0 * np.pi * freq * t)
        peak = float(np.max(np.abs(waveform)))
        if peak > 0:
            waveform /= peak
        samples_int = (waveform * 32767).astype(np.int16)
        try:
            sound = pygame.sndarray.make_sound(samples_int)
        except (pygame.error, ValueError):
            return
        self._channel.stop()
        self._channel.play(sound, loops=-1, fade_ms=80)
