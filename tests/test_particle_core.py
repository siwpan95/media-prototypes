"""
Unit tests for a pure helper in the particle toolkit (particle/core).

Only ``lerp_color`` is exercised — it is dependency-light (plain arithmetic,
no display). The ``core`` package is made importable by adding the ``particle/``
directory to sys.path, the same trick particle_effects.py uses. The module
imports numpy at top level but ``lerp_color`` itself needs no backend, and the
only pygame reference in the file is a guarded ``import pygame`` inside a method.
"""

from shikonghuaban.particle.core.particle import lerp_color


def test_lerp_color_at_zero_returns_first():
    assert lerp_color((0, 0, 0), (255, 255, 255), 0.0) == (0, 0, 0)


def test_lerp_color_at_one_returns_second():
    assert lerp_color((0, 0, 0), (255, 255, 255), 1.0) == (255, 255, 255)


def test_lerp_color_midpoint_truncates():
    # 0 + 255*0.5 = 127.5 -> int() truncates toward zero -> 127
    assert lerp_color((0, 0, 0), (255, 255, 255), 0.5) == (127, 127, 127)


def test_lerp_color_partial_mix():
    # t=0.25: (100*0.25, 200*0.25, 40*0.25) = (25, 50, 10)
    assert lerp_color((0, 0, 0), (100, 200, 40), 0.25) == (25, 50, 10)


def test_lerp_color_clamps_t_below_zero():
    assert lerp_color((10, 20, 30), (200, 100, 50), -1.0) == (10, 20, 30)


def test_lerp_color_clamps_t_above_one():
    assert lerp_color((10, 20, 30), (200, 100, 50), 2.0) == (200, 100, 50)
