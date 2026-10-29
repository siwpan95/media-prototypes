import pygame
import numpy as np
from .sfx_layer import SFXLayer

class FaultAudio:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.sfx = SFXLayer()

    def bearing_fail(self, severity=1.0):
        t = np.linspace(0, 0.2, int(self.sample_rate * 0.2), False)
        base = np.sin(2 * np.pi * 120 * t)
        noise = np.random.randn(len(t)) * severity
        return base + noise * 0.3

    def blade_strike(self):
        t = np.linspace(0, 0.05, int(self.sample_rate * 0.05), False)
        return np.sin(2 * np.pi * 800 * t) * np.exp(-t * 30)

    def motor_overload(self):
        t = np.linspace(0, 0.3, int(self.sample_rate * 0.3), False)
        return np.sin(2 * np.pi * 50 * t) * np.exp(-t * 5)

    def to_sound(self, wave):
        wave = np.clip(wave, -1.0, 1.0)
        stereo = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(
            (stereo * 32767).astype(np.int16)
        )