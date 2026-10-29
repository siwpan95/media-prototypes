"""错误处理测试：未知 method 构造/生成抛 ValueError；beta 与 H 同时传入抛 ValueError。"""
import pytest

import numpy as np

from wave4 import BrownianNoiseGenerator


def test_unknown_method_construct():
    with pytest.raises(ValueError):
        BrownianNoiseGenerator("not_a_method")


def test_unknown_method_generate():
    """构造时方法合法，但包不允许的 method 字符串在构造阶段即拦截。"""
    with pytest.raises(ValueError):
        BrownianNoiseGenerator("xyz")


def test_beta_and_h_conflict_davies_harte():
    g = BrownianNoiseGenerator("davies_harte")
    with pytest.raises(ValueError):
        g.generate(1000, beta=2.5, H=0.5)


def test_beta_and_h_conflict_hosking():
    g = BrownianNoiseGenerator("hosking")
    with pytest.raises(ValueError):
        g.generate(1000, beta=2.5, H=0.5)


def test_valid_beta_only_davies_harte():
    """仅给 beta（不含 H）应正常工作，beta 经 H=(beta-1)/2 反推。"""
    g = BrownianNoiseGenerator("davies_harte")
    x = g.generate(1000, beta=2.5, seed=1)
    assert x.shape == (1000,)
    assert x.dtype == np.float64


def test_valid_h_only_hosking():
    g = BrownianNoiseGenerator("hosking")
    x = g.generate(1000, H=0.5, seed=1)
    assert x.shape == (1000,)


def test_io_unsupported_format_raises():
    from wave4.io.serialize import save_noise
    import tempfile, os

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.unknown")
        with pytest.raises(ValueError):
            save_noise(np.zeros(3), path, fmt="unknown")
