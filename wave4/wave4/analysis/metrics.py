"""质量分析指标：自相关、PSD、Hurst 估计（R/S、DFA）、增量方差标度。

纯 numpy / scipy 实现，函数级可测。谱理论见 ``docs/theory.md``。
"""
from __future__ import annotations

import numpy as np
from scipy.signal import welch


def autocorr(x: np.ndarray, max_lag: int) -> np.ndarray:
    """返回 lag 0..max_lag 的自相关系数（有偏估计）。

    先零均值化，再用 ``dot(x[lag:], x[:n-lag]) / dot(x, x)`` 计算。
    分母用整体能量 ``dot(x, x)``（非随 lag 变化），因此是**有偏**自相关估计
    （随 lag 增大衰减偏快），与 ``np.corrcoef`` 的逐对去均值/样本方差定义不同。
    lag 0 恒为 1.0。
    """
    x = np.asarray(x, dtype=np.float64)
    x = x - np.mean(x)
    n = x.size
    denom = float(np.dot(x, x))
    if denom == 0.0:
        return np.zeros(max_lag + 1)
    out = np.empty(max_lag + 1)
    out[0] = 1.0
    for lag in range(1, max_lag + 1):
        out[lag] = float(np.dot(x[lag:], x[:n - lag])) / denom
    return out


def estimate_psd(x: np.ndarray, fs: float = 1.0, **kw) -> tuple[np.ndarray, np.ndarray]:
    """Welch 法估计功率谱密度（PSD）。

    参数：
        x: 输入信号
        fs: 采样率
        **kw: 透传给 ``scipy.signal.welch``（如 nperseg, noverlap, nfft）
    返回：
        (freq, psd)
    """
    x = np.asarray(x, dtype=np.float64)
    f, Pxx = welch(x, fs=fs, **kw)
    return f, Pxx


def estimate_h_from_psd(x: np.ndarray, fs: float = 1.0, fmin=None, fmax=None) -> float:
    """由 PSD 在 log-log 空间斜率反推 Hurst 指数 H。

    谱理论：fGn 的 PSD ∝ 1/f^(2H-1)，log-log 斜率 s = -(2H-1) = 1-2H，
    故 ``H = (1 - s) / 2``。

    注意：应用于 **fGn**（如 ``np.diff(fbm)``）时反推 H；应用于 fBm 路径时
    因 PSD∝1/f^(2H+1) 会得到 H+1，请区分。

    可选 ``fmin`` / ``fmax`` 限定拟合频带。
    """
    f, Pxx = estimate_psd(x, fs=fs)
    if fmin is not None:
        m = f >= fmin
        f, Pxx = f[m], Pxx[m]
    if fmax is not None:
        m = f <= fmax
        f, Pxx = f[m], Pxx[m]

    pos = (f > 0) & (Pxx > 0)
    f = np.log(f[pos])
    Pxx = np.log(Pxx[pos])
    if f.size < 2:
        return float('nan')

    slope, _ = np.polyfit(f, Pxx, 1)
    return (1.0 - slope) / 2.0


def hurst_rs(x: np.ndarray, n_scales=None) -> float:
    """R/S 重标极差法估计 Hurst 指数 H。

    对多个窗口尺寸 ``s`` 计算 ``R/S(s)``，拟合 ``log s – log R/S`` 斜率得 H。
    ``n_scales`` 为 None 时自动取 2 的幂次尺度。

    约定：输入应为**平稳增量序列 fGn**（如 ``np.diff(fbm)``）。若直接对
    已积分的 fBm 路径调用，R/S 会趋近 1（测得 H+1），属正常现象。
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n_scales is None:
        # 最小尺度 2^3=8：R/S 在过小窗口（如 4）统计量不稳定，故下界提到 8
        powers = np.arange(3, int(np.log2(n)) + 1)
        scales = (2 ** powers).astype(int)
        scales = scales[scales < n]
    else:
        scales = np.asarray(n_scales, dtype=int)
    scales = np.unique(scales)

    rs_vals = []
    valid = []
    for s in scales:
        if s < 2:
            continue
        m = n // s
        if m == 0:
            continue
        vals = []
        for start in range(m):
            seg = x[start * s:(start + 1) * s]
            mean = seg.mean()
            dev = np.cumsum(seg - mean)
            R = float(dev.max() - dev.min())
            S = float(seg.std(ddof=0))
            if S == 0.0:
                continue
            vals.append(R / S)
        if vals:
            rs_vals.append(float(np.mean(vals)))
            valid.append(int(s))

    if len(valid) < 2:
        return float('nan')

    slope, _ = np.polyfit(
        np.log(np.asarray(valid, dtype=float)),
        np.log(np.asarray(rs_vals, dtype=float)),
        1,
    )
    return float(slope)


def hurst_dfa(x: np.ndarray, order: int = 1, n_scales=None) -> float:
    """DFA 去趋势涨落分析估计 Hurst 指数 H。

    对累积剖面分段做 ``order`` 阶多项式去趋势，计算涨落函数 ``F(s)``，
    拟合 ``log s – log F`` 斜率即 H（默认 1 阶去趋势）。

    约定：输入应为**平稳增量序列 fGn**（如 ``np.diff(fbm)``）。对 fBm 路径
    直接调用会得到 H+1。
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.cumsum(x - np.mean(x))  # 累积剖面
    n = y.size
    if n_scales is None:
        # 最小尺度 2^3=8：DFA 在过小窗口统计量不稳定，故下界提到 8
        powers = np.arange(3, int(np.log2(n)) + 1)
        scales = (2 ** powers).astype(int)
        scales = scales[scales < max(2, n // 2)]
    else:
        scales = np.asarray(n_scales, dtype=int)
    scales = np.unique(scales)

    F = []
    valid = []
    for s in scales:
        if s < 2 or s >= n:
            continue
        m = n // s
        if m == 0:
            continue
        fluct = []
        for start in range(m):
            seg = y[start * s:(start + 1) * s]
            xs = np.arange(s)
            coeffs = np.polyfit(xs, seg, order)
            trend = np.polyval(coeffs, xs)
            fluct.append(np.sqrt(np.mean((seg - trend) ** 2)))
        if fluct:
            F.append(float(np.mean(fluct)))
            valid.append(int(s))

    if len(valid) < 2:
        return float('nan')

    slope, _ = np.polyfit(
        np.log(np.asarray(valid, dtype=float)),
        np.log(np.asarray(F, dtype=float)),
        1,
    )
    return float(slope)


def variance_scaling_exponent(x: np.ndarray, step_range=None) -> float:
    """增量方差标度指数：log Var(X(t+Δ)-X(t)) 对 log Δ 的斜率（理论 2H）。

    对 fBm 路径，``Var(B(t+Δ)-B(t)) ∝ Δ^(2H)``，故斜率 ≈ 2H。输入应为
    **fBm 路径**（已积分），而非 fGn。

    注意：大滞后（Δ 接近 N）会受 circulant embedding 周期边界影响而偏离幂律，
    故默认仅取 Δ ∈ [1, N/50] 的标度区；如需全滞后可显式传入 ``step_range``。
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if step_range is None:
        max_step = max(10, n // 50)
        steps = np.arange(1, max_step + 1)
    else:
        steps = np.asarray(step_range, dtype=int)
    steps = steps[steps >= 1]

    variances = []
    valid = []
    for d in steps:
        if d >= n:
            break
        inc = x[d:] - x[:-d]
        variances.append(float(np.var(inc, ddof=0)))
        valid.append(int(d))

    valid = np.asarray(valid, dtype=float)
    variances = np.asarray(variances, dtype=float)
    mask = variances > 0
    if mask.sum() < 2:
        return float('nan')

    slope, _ = np.polyfit(np.log(valid[mask]), np.log(variances[mask]), 1)
    return float(slope)
