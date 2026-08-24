"""
Unit tests for the pure, I/O-free static helpers on AudioEngine.

``sounddevice`` is stubbed in conftest.py so the module imports cleanly in a
headless environment. ``saw`` and ``env`` are pure math/numpy and need no
audio device. Exact behavior was read from audio_engine.py.
"""

import numpy as np

from shikonghuaban.audio_engine import AudioEngine


# ── saw(t, f) = 2 * ((t * f) % 1.0) - 1 ──

def test_saw_range_within_minus_one_to_one():
    for f in (110.0, 261.63, 440.0, 2000.0):
        for t in (0.0, 0.001, 0.017, 0.5, 0.999, 1.0, 3.14159, 100.0):
            v = AudioEngine.saw(t, f)
            assert -1.0 <= v <= 1.0


def test_saw_at_zero_is_minus_one():
    assert AudioEngine.saw(0.0, 440.0) == -1.0
    assert AudioEngine.saw(0.0, 1000.0) == -1.0


def test_saw_is_periodic_in_t():
    f = 200.0
    period = 1.0 / f
    assert np.isclose(AudioEngine.saw(0.0, f), AudioEngine.saw(period, f))
    assert np.isclose(AudioEngine.saw(0.3, f), AudioEngine.saw(0.3 + period, f))


def test_saw_midpoint_is_zero():
    # t = 0.5 / f  =>  (t*f) % 1 = 0.5  =>  2*0.5 - 1 = 0
    f = 300.0
    assert np.isclose(AudioEngine.saw(0.5 / f, f), 0.0, atol=1e-9)


# ── env(n): attack/release envelope, np.ones(n) with ramps ──

def test_env_range_and_length():
    # Representative frame sizes (audio blocks are normally >= 1024).
    for n in (10, 100, 200, 1024, 44100):
        e = AudioEngine.env(n)
        assert e.shape == (n,)
        assert e.min() >= 0.0
        assert e.max() <= 1.0


def test_env_tiny_n_does_not_crash():
    # 小 n 不应崩溃：env 对 att/rel 取下限 1，返回合法包络。
    for n in (1, 4, 16):
        e = AudioEngine.env(n)
        assert e.shape == (n,)
        assert 0.0 <= e.min() <= e.max() <= 1.0


def test_env_peaks_at_one_in_body():
    e = AudioEngine.env(200)
    assert e.max() == 1.0
    assert np.isclose(e[20], 1.0)    # sustain region
    assert np.isclose(e[100], 1.0)   # sustain region


def test_env_attack_starts_at_zero():
    e = AudioEngine.env(200)
    assert np.isclose(e[0], 0.0)
    att = int(0.01 * 200)  # 2
    assert e[att - 1] > e[0]  # ramps up through the attack


def test_env_release_ends_at_zero():
    e = AudioEngine.env(200)
    rel = int(0.2 * 200)  # 40
    assert np.isclose(e[-1], 0.0)
    assert e[-rel] > e[-1]  # ramps down through the release
