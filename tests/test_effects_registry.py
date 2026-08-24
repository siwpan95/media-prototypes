"""
F Effect 注册表单元测试 (headless)。

验证 ParticleEffectsManager 的特效已解耦为可插拔注册表：
  - 7 个特效按固定渲染层序注册
  - update_and_render 遍历注册表运行不抛异常（默认路径行为不变）
  - total_count 等于各特效粒子数之和
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from shikonghuaban.particle_effects import ParticleEffectsManager, Effect


def _make_screen():
    pygame.init()
    return pygame.Surface((64, 64))


def test_registry_has_seven_effects_in_render_order():
    fx = ParticleEffectsManager(_make_screen())
    names = [e.name for e in fx.effects]
    assert names == ["dust", "accretion", "singularity", "edge", "orbit", "photon", "pulse"]


def test_effects_are_effect_instances():
    fx = ParticleEffectsManager(_make_screen())
    assert all(isinstance(e, Effect) for e in fx.effects)


def test_update_and_render_runs_headless():
    fx = ParticleEffectsManager(_make_screen())
    # 不应抛异常；覆盖不同音量以触发分支
    for vol in (0.0, 0.3, 0.8, 1.0):
        fx.update_and_render(vol, 1234)
    assert fx.total_count >= 0


def test_total_count_matches_sum():
    fx = ParticleEffectsManager(_make_screen())
    fx.update_and_render(0.6, 999)
    expected = sum(e.ps.get_particle_count() for e in fx.effects)
    assert fx.total_count == expected
