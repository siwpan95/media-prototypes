"""
G 粒子力场 numpy 向量化单元测试 (headless)。

验证：
  - ForceField.get_force_numpy 对 attraction/vortex/turbulence/gravity/wind
    与标量 get_force 逐元素严格等价
  - ParticleSystem 向量化路径（默认）与标量 fallback 路径更新结果一致
    （使用手动确定粒子集 + 深拷贝，排除发射随机干扰，纯验力学等价）
"""

import copy
import random

import numpy as np
import pytest

from shikonghuaban.particle.core.particle import (
    ForceField, ParticleSystem, Particle, create_vortex, create_turbulence,
)


def _random_positions(n=50, seed=0):
    rng = np.random.default_rng(seed)
    return rng.uniform(-500, 500, size=(n, 2))


@pytest.mark.parametrize("field", [
    ForceField('attraction', x=100, y=100, strength=20.0),
    ForceField('vortex', x=0, y=0, strength=5.0, vortex_clockwise=True),
    ForceField('vortex', x=0, y=0, strength=5.0, vortex_clockwise=False),
    ForceField('turbulence', strength=0.6, turb_scale=50.0, turb_strength=0.5),
    ForceField('gravity', strength=9.8),
    ForceField('wind', strength=3.0),
])
def test_force_numpy_matches_scalar(field):
    pos = _random_positions(60)
    t = 1.23
    vec = field.get_force_numpy(pos, t)
    scal = np.array([field.get_force(float(x), float(y), t) for x, y in pos])
    assert vec.shape == scal.shape
    assert np.allclose(vec, scal, atol=1e-9)


def _make_particles(n, seed=7):
    random.seed(seed)
    return [
        Particle(
            x=random.uniform(-50, 50), y=random.uniform(-50, 50),
            vx=random.uniform(-5, 5), vy=random.uniform(-5, 5),
            life=1.0, max_life=3.0, size=2.0, color=(255, 0, 0),
        )
        for _ in range(n)
    ]


def _build(use_numpy, particles, force_fields):
    ParticleSystem.USE_NUMPY_FORCES = use_numpy
    ps = ParticleSystem(max_particles=300)
    # 复用同一组力场对象（含相同的 _noise_time_offset 随机种子）：
    # 确保 numpy 与标量两条路径对比的是“同一组力场的两种计算方式”，
    # 而非两个随机种子不同的湍流场（那会导致语义不等价，属于测试伪差而非实现差异）。
    ps.force_fields = copy.deepcopy(force_fields)
    # 直接用确定粒子集（深拷贝隔离两系统），不挂 Emitter，排除发射随机
    ps.particles = copy.deepcopy(particles)
    return ps


def test_system_numpy_matches_scalar_fallback():
    base = _make_particles(40)
    # 共享同一组力场（深拷贝给两套系统），消除随机偏移带来的伪差异
    shared_fields = [
        ForceField('attraction', x=0, y=0, strength=15.0),
        create_vortex(0, 0, strength=3.0, clockwise=True),
        create_turbulence(strength=0.5, scale=60.0),
    ]
    numpy_ps = _build(True, base, shared_fields)
    scalar_ps = _build(False, base, shared_fields)

    for _ in range(6):
        numpy_ps.update(1 / 60, audio_data={'rms': 0.5})
        scalar_ps.update(1 / 60, audio_data={'rms': 0.5})

    assert numpy_ps.get_particle_count() == scalar_ps.get_particle_count()
    n1 = np.array([[p.x, p.y, p.vx, p.vy] for p in numpy_ps.particles])
    n2 = np.array([[p.x, p.y, p.vx, p.vy] for p in scalar_ps.particles])
    # 力场严格一致时，两条路径在 double 精度下等效（仅浮点分组顺序差异，~1e-14）
    assert np.allclose(n1, n2, atol=1e-9)
