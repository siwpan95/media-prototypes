"""各生成方法的单元测试：通用契约 + 方法专属数值检查。

通用契约（所有方法 generate 后）：dtype=float64、shape=(N,)、零均值、
std≈intensity。
方法专属：basic≈cumsum(白噪声)去均值；freq 的 DC 邻域=filter_response[1]；
iir 递推首点 x[0]=white[0]；fractal 的 PSD 斜率≈-beta；davies_harte 的 fGn
差分 var≈1、lag-1 acf 符号随 H 变化、H=0.99 抛 ValueError；hosking 不抛错、
fGn 差分 var≈1、lag-1 acf 符号随 H 一致。
"""
import numpy as np
import pytest

from wave4 import BrownianNoiseGenerator
from wave4.core.generators import gen_davies_harte, gen_hosking
from wave4.analysis.metrics import autocorr, estimate_psd


def _generic_checks(x, N, intensity):
    assert x.dtype == np.float64
    assert x.shape == (N,)
    assert abs(float(x.mean())) < 1e-6
    assert abs(float(x.std(ddof=0)) - intensity) < 1e-2


# --------------------------------------------------------------------------
# basic
# --------------------------------------------------------------------------
def test_basic_generic():
    g = BrownianNoiseGenerator("basic")
    x = g.generate(2000, intensity=2.0, seed=7)
    _generic_checks(x, 2000, 2.0)


def test_basic_matches_cumsum():
    """basic 应等于 cumsum(白噪声) 后去均值/归一化（固定 seed 复算对照）。"""
    N, seed, intensity = 2000, 123, 1.0
    g = BrownianNoiseGenerator("basic")
    out = g.generate(N, intensity=intensity, seed=seed)

    rng = np.random.RandomState()
    rng.seed(seed)
    white = rng.randn(N)
    brown = np.cumsum(white)
    ref = (brown - brown.mean()) / brown.std(ddof=0) * intensity
    assert np.allclose(out, ref, atol=1e-12)


# --------------------------------------------------------------------------
# freq
# --------------------------------------------------------------------------
def test_freq_generic():
    g = BrownianNoiseGenerator("freq")
    x = g.generate(2048, fs=1000, f_min=1, f_max=100, intensity=1.5, seed=9)
    _generic_checks(x, 2048, 1.5)


def test_freq_dc_convention():
    """频域法：DC 邻域应等于 filter_response[1]（低频被抑制约定）。

    通过重算参考实现（显式 filter_response[0]=filter_response[1]）并断言
    与生成器输出一致来验证该约定。
    """
    N, fs, seed = 2048, 1000, 11
    f_min, f_max = 1, 100
    g = BrownianNoiseGenerator("freq")
    out = g.generate(N, fs=fs, f_min=f_min, f_max=f_max, seed=seed)

    rng = np.random.RandomState()
    rng.seed(seed)
    white = rng.randn(N)
    noise_fft = np.fft.rfft(white)
    freq = np.fft.rfftfreq(N, 1.0 / fs)
    with np.errstate(divide="ignore", invalid="ignore"):
        fr = 1.0 / np.where(freq > 0, freq, np.inf)
        fr[0] = fr[1]  # DC 邻域复制 bin1
    fr[freq < f_min] = 0
    fr[freq > f_max] = 0
    brown = np.fft.irfft(noise_fft * fr, n=N)
    ref = (brown - brown.mean()) / brown.std(ddof=0)

    assert fr[0] == fr[1]  # 约定本身
    assert np.allclose(out, ref, atol=1e-10)


# --------------------------------------------------------------------------
# iir
# --------------------------------------------------------------------------
def test_iir_generic():
    g = BrownianNoiseGenerator("iir")
    x = g.generate(2000, alpha=0.95, intensity=3.0, seed=3)
    _generic_checks(x, 2000, 3.0)


def test_iir_recurrence_first_point():
    """iir 递推首点须为 white[0]（固定 seed 复算对照）。"""
    N, alpha, seed, intensity = 2000, 0.99, 5, 1.0
    g = BrownianNoiseGenerator("iir")
    out = g.generate(N, alpha=alpha, intensity=intensity, seed=seed)

    rng = np.random.RandomState()
    rng.seed(seed)
    white = rng.randn(N)
    brown = np.zeros(N)
    brown[0] = white[0]
    for i in range(1, N):
        brown[i] = alpha * brown[i - 1] + white[i]
    ref = (brown - brown.mean()) / brown.std(ddof=0) * intensity
    assert np.allclose(out, ref, atol=1e-10)


# --------------------------------------------------------------------------
# fractal
# --------------------------------------------------------------------------
def test_fractal_generic():
    g = BrownianNoiseGenerator("fractal")
    x = g.generate(2000, beta=2.0, intensity=0.5, seed=4)
    _generic_checks(x, 2000, 0.5)


def test_fractal_psd_slope():
    """fractal 的 PSD 在 log-log 空间斜率应 ≈ -beta（beta=2.5→≈-2.5）。"""
    N, beta = 20000, 2.5
    g = BrownianNoiseGenerator("fractal")
    x = g.generate(N, beta=beta, seed=3)

    f, Pxx = estimate_psd(x, fs=1.0, nperseg=2048)
    band = (f >= 1e-3) & (f <= 0.2)
    slope, _ = np.polyfit(np.log(f[band]), np.log(Pxx[band]), 1)
    assert abs(slope - (-beta)) < 0.3, f"PSD slope={slope:.4f}, want ~-{beta}"


# --------------------------------------------------------------------------
# davies_harte
# --------------------------------------------------------------------------
def test_davies_harte_generic():
    g = BrownianNoiseGenerator("davies_harte")
    x = g.generate(2000, H=0.7, intensity=1.0, seed=2)
    _generic_checks(x, 2000, 1.0)


def test_davies_harte_fgn_stats():
    """raw fBm 差分（fGn）var≈1（atol=0.1）；H>0.5 lag-1 acf>0，H<0.5 <0。"""
    N = 4096
    for H in (0.25, 0.75):
        rng = np.random.RandomState(0)
        fbm = gen_davies_harte(rng, N, H=H, raw=True)
        fgn = np.diff(fbm)
        assert abs(float(np.var(fgn, ddof=0)) - 1.0) < 0.1, (
            f"D-H H={H} fGn var={np.var(fgn):.4f}, want ~1"
        )
        a = autocorr(fgn, max_lag=1)
        if H > 0.5:
            assert a[1] > 0, f"D-H H={H} lag-1 acf 应>0, got {a[1]:.4f}"
        else:
            assert a[1] < 0, f"D-H H={H} lag-1 acf 应<0, got {a[1]:.4f}"


def test_davies_harte_h99_raises():
    """H=0.99 且序列较长时负特征值 → 抛 ValueError。"""
    g = BrownianNoiseGenerator("davies_harte")
    with pytest.raises(ValueError):
        g.generate(2048, H=0.99)

    # 纯函数路径同样应抛
    rng = np.random.RandomState(1)
    with pytest.raises(ValueError):
        gen_davies_harte(rng, 2048, H=0.99, raw=True)


# --------------------------------------------------------------------------
# hosking
# --------------------------------------------------------------------------
def test_hosking_generic():
    g = BrownianNoiseGenerator("hosking")
    x = g.generate(2000, H=0.6, intensity=1.0, seed=2)
    _generic_checks(x, 2000, 1.0)


def test_hosking_generates_no_error():
    """hosking 对任意 H∈{0.25,0.5,0.75} 都应能生成（不抛错）。"""
    for H in (0.25, 0.5, 0.75):
        g = BrownianNoiseGenerator("hosking")
        x = g.generate(1024, H=H, seed=1)
        assert x.shape == (1024,)
        assert x.dtype == np.float64


def test_hosking_fgn_variance():
    """raw fBm 差分（fGn）var≈1（atol=0.1）。"""
    N = 1024
    for H in (0.25, 0.5, 0.75):
        rng = np.random.RandomState(0)
        fbm = gen_hosking(rng, N, H=H, raw=True)
        fgn = np.diff(fbm)
        assert abs(float(np.var(fgn, ddof=0)) - 1.0) < 0.1, (
            f"Hosking H={H} fGn var={np.var(fgn):.4f}, want ~1"
        )


def test_hosking_fgn_acf_sign():
    """hosking fGn 差分 lag-1 acf 符号应与 H 一致（H<0.5→负, H>0.5→正）。"""
    N = 1024
    for H in (0.25, 0.5, 0.75):
        rng = np.random.RandomState(0)
        fbm = gen_hosking(rng, N, H=H, raw=True)
        fgn = np.diff(fbm)
        a1 = autocorr(fgn, max_lag=1)[1]
        if H < 0.5:
            assert a1 < 0, f"Hosking H={H} lag-1 acf 应<0, got {a1:+.4f}"
        elif H > 0.5:
            assert a1 > 0, f"Hosking H={H} lag-1 acf 应>0, got {a1:+.4f}"
