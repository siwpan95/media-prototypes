"""analysis.metrics 单元测试。

- hurst_rs / hurst_dfa / estimate_h_from_psd 在已知 H 的 fGn 上恢复 H，误差<0.1
  （N≥2000、多 seed 取平均）。注意：R/S、DFA 须作用于平稳 fGn 增量。
- autocorr 返回长度=max_lag+1，lag0≈1。
- variance_scaling_exponent 在 fBm 路径上≈2H（误差<0.15）。
- estimate_psd 返回正频率与正功率。
"""
import numpy as np
import pytest

from wave4.core.generators import gen_davies_harte
from wave4.analysis.metrics import (
    autocorr,
    estimate_h_from_psd,
    estimate_psd,
    hurst_dfa,
    hurst_rs,
    variance_scaling_exponent,
)

N = 8000
N_SEEDS = 15


def _make_fgn(H, seed):
    """由 D-H 生成 raw fBm 再差分得到标准 fGn（已知 H）。"""
    rng = np.random.RandomState(seed)
    fbm = gen_davies_harte(rng, N, H=H, raw=True)
    return np.diff(fbm)


@pytest.mark.parametrize("H", [0.4, 0.5, 0.7, 0.8])
def test_hurst_recovery(H):
    rs, dfa, psd = [], [], []
    for s in range(N_SEEDS):
        fgn = _make_fgn(H, s)
        rs.append(hurst_rs(fgn))
        dfa.append(hurst_dfa(fgn))
        psd.append(estimate_h_from_psd(fgn))

    assert abs(float(np.mean(rs)) - H) < 0.1, (
        f"R/S 恢复 H={H} 误差过大: mean={np.mean(rs):.4f}"
    )
    assert abs(float(np.mean(dfa)) - H) < 0.1, (
        f"DFA 恢复 H={H} 误差过大: mean={np.mean(dfa):.4f}"
    )
    assert abs(float(np.mean(psd)) - H) < 0.1, (
        f"PSD 恢复 H={H} 误差过大: mean={np.mean(psd):.4f}"
    )


def test_autocorr_shape_and_lag0():
    rng = np.random.RandomState(0)
    x = rng.randn(500)
    a = autocorr(x, max_lag=10)
    assert a.shape == (11,)
    assert abs(a[0] - 1.0) < 1e-9
    # 白噪声 lag1 应≈0
    assert abs(a[1]) < 0.15


def test_variance_scaling_on_fbm():
    """variance_scaling_exponent 作用于 fBm 路径，斜率≈2H（误差<0.15）。"""
    for H in (0.5, 0.75):
        rng = np.random.RandomState(7)
        fbm = gen_davies_harte(rng, 20000, H=H, raw=True)
        v = variance_scaling_exponent(fbm)
        assert abs(v - 2 * H) < 0.15, f"fBm H={H} 标度指数={v:.4f}, want ~{2*H}"


def test_estimate_psd_positive():
    rng = np.random.RandomState(0)
    x = rng.randn(1024)
    f, Pxx = estimate_psd(x, fs=1.0)
    # welch 频率自 0（DC）起，故用 >= 0；非零频率应为正；功率恒正
    assert np.all(f >= 0)
    assert np.all(f[1:] > 0)
    assert np.all(Pxx > 0)


def test_hurst_on_fbm_is_not_h():
    """对 fBm 路径（非 fGn 增量）直接做 R/S/DFA 应得到≈H+1（数学预期，非 bug）。

    用于验证文档约定：指标须作用于平稳增量。
    """
    H = 0.5
    rng = np.random.RandomState(3)
    fbm = gen_davies_harte(rng, 4000, H=H, raw=True)
    # 直接对 fBm 调用：R/S 趋近 1、DFA 趋近 H+1（数学预期，非 bug）
    assert abs(hurst_rs(fbm) - 1.0) < 0.15
    assert abs(hurst_dfa(fbm) - (H + 1)) < 0.2
