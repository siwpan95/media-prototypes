"""回归锚点：wave4 与 wave4_legacy 四法在相同 seed/参数下须逐点一致。

原 4 法（basic/freq/iir/fractal）数值行为应与旧实现 1:1 一致（工程师报告
basic/freq/iir 同 seed 与旧实现 max_abs_diff=0，fractal=4.44e-16）。
本测试是后续一切数值断言的回归基线，必须 100% 通过。
"""
import numpy as np
import pytest

import wave4
import wave4_legacy

METHODS = ["basic", "freq", "iir", "fractal"]


@pytest.mark.parametrize("method", METHODS)
def test_seed_regression(method):
    # 各法使用与需求一致的参数
    kwargs = {}
    if method == "freq":
        kwargs = dict(fs=1000, f_min=1, f_max=100)
    elif method == "iir":
        kwargs = dict(alpha=0.99)
    elif method == "fractal":
        kwargs = dict(beta=2.5)

    g_new = wave4.BrownianNoiseGenerator(method)
    g_old = wave4_legacy.BrownianNoiseGenerator(method)

    x_new = g_new.generate(2000, intensity=1.0, seed=42, **kwargs)
    x_old = g_old.generate(2000, intensity=1.0, seed=42, **kwargs)

    # 双方均应为 float64
    assert x_new.dtype == np.float64
    assert x_old.dtype == np.float64

    # 逐点一致（atol=1e-10 足够覆盖浮点重排误差）
    assert np.allclose(x_new, x_old, atol=1e-10), (
        f"method={method} 回归不一致: max_abs_diff="
        f"{np.max(np.abs(x_new - x_old))}"
    )


@pytest.mark.parametrize("method", METHODS)
def test_seed_reproducibility(method):
    """同一生成器 + 同一 seed 应可复现（per-call seed 生效）。"""
    kwargs = {}
    if method == "freq":
        kwargs = dict(fs=1000, f_min=1, f_max=100)
    elif method == "iir":
        kwargs = dict(alpha=0.99)
    elif method == "fractal":
        kwargs = dict(beta=2.5)

    g = wave4.BrownianNoiseGenerator(method)
    a = g.generate(1500, seed=7, **kwargs)
    b = g.generate(1500, seed=7, **kwargs)
    assert np.array_equal(a, b)
