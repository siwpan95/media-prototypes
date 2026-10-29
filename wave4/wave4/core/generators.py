"""纯函数形式的布朗噪声 / 分数阶布朗运动生成算法。

设计原则：
- 所有生成函数均为**纯函数**：随机源 ``rng`` 由调用方（``BrownianNoiseGenerator``）
  传入，函数内部不新建随机源，以保证可复现、可独立测试。
- 前 4 个函数（gen_basic / gen_freq / gen_iir / gen_fractal）的数值行为与原
  ``wave4.py`` **1:1 一致**（含 DC 处理、f_min/f_max 置零顺序、递推初值、默认参数）。
- 后 2 个（gen_davies_harte / gen_hosking）为新增的精确 fBm 生成法，基于 fGn
  自协方差（circulant embedding / Durbin–Levinson）。
"""
from __future__ import annotations

import numpy as np

from ._utils import fgng_acov, normalize


# ---------------------------------------------------------------------------
# 经典 4 法（数值行为与原 wave4.py 逐点一致）
# ---------------------------------------------------------------------------

def gen_basic(rng: np.random.RandomState, N: int, intensity: float = 1.0) -> np.ndarray:
    """基本积分法：cumsum(白噪声) 后归一化。

    对应原 ``_generate_basic``：先 ``rng.randn(N)``，再 ``cumsum``，最后归一化。
    """
    white_noise = rng.randn(N)
    brownian_noise = np.cumsum(white_noise)
    return normalize(brownian_noise, intensity)


def gen_freq(rng: np.random.RandomState, N: int, fs: float = 1.0, intensity: float = 1.0,
             f_min=None, f_max=None) -> np.ndarray:
    """频域滤波法：对白噪声做 1/f 带通滤波（积分），再归一化。

    对应原 ``_generate_freq``：DC 处 ``filter_response[0] = filter_response[1]``；
    f_min / f_max 置零顺序保持（先 f_min 后 f_max）。
    """
    white_noise = rng.randn(N)
    noise_fft = np.fft.rfft(white_noise)
    freq = np.fft.rfftfreq(N, 1.0 / fs)

    with np.errstate(divide='ignore', invalid='ignore'):
        filter_response = 1.0 / np.where(freq > 0, freq, np.inf)
        filter_response[0] = filter_response[1]

    if f_min is not None:
        filter_response[freq < f_min] = 0
    if f_max is not None:
        filter_response[freq > f_max] = 0

    brown_fft = noise_fft * filter_response
    brownian_noise = np.fft.irfft(brown_fft, n=N)
    return normalize(brownian_noise, intensity)


def gen_iir(rng: np.random.RandomState, N: int, intensity: float = 1.0,
            alpha: float = 0.99) -> np.ndarray:
    """IIR 滤波法：一阶递归积分 ``b[i] = alpha*b[i-1] + w[i]``。

    对应原 ``_generate_iir``：初值 ``brownian_noise[0] = white_noise[0]``，alpha 默认 0.99。
    """
    white_noise = rng.randn(N)
    brownian_noise = np.zeros(N)
    brownian_noise[0] = white_noise[0]

    for i in range(1, N):
        brownian_noise[i] = alpha * brownian_noise[i - 1] + white_noise[i]

    return normalize(brownian_noise, intensity)


def gen_fractal(rng: np.random.RandomState, N: int, fs: float = 1.0, intensity: float = 1.0,
                beta: float = 2.0) -> np.ndarray:
    """分数阶噪声法：对白噪声做 1/f^(beta/2) 频域滤波，再归一化。

    对应原 ``_generate_fractal``：DC 处 ``filter_response[~mask] = filter_response[1]``，
    beta 默认 2.0。

    谱关系说明（重要）：输出 PSD ∝ 1/f^beta。对照 fBm 谱关系 1/f^(2H+1) 得
    ``H = (beta - 1) / 2``（即本法的内部约定），故 fractal 输出的统计本质更接近
    **fBm 路径**而非 fGn。因此：

    - 对 fractal 输出做 ``estimate_h_from_psd``（其按 fGn 谱关系 1/f^(2H-1) 反推）
      会得到 ``H + 1``（因谱指数相差 2），属正常，非 bug。
    - 若要与 ``davies_harte`` / ``hosking`` 的 H 对齐，应先 ``np.diff`` 取增量再估计。
    - 详见 ``docs/theory.md`` §2。
    """
    white_noise = rng.randn(N)
    noise_fft = np.fft.rfft(white_noise)
    freq = np.fft.rfftfreq(N, 1.0 / fs)

    with np.errstate(divide='ignore', invalid='ignore'):
        filter_response = np.ones_like(freq)
        mask = freq > 0
        filter_response[mask] = 1.0 / (freq[mask] ** (beta / 2.0))
        filter_response[~mask] = filter_response[1]

    filtered_fft = noise_fft * filter_response
    fractal_noise = np.fft.irfft(filtered_fft, n=N)
    return normalize(fractal_noise, intensity)


# ---------------------------------------------------------------------------
# 新增精确法：Davies–Harte / Wood–Chan + Hosking
# ---------------------------------------------------------------------------

def _fgn_gamm(k: int, H: float) -> float:
    """标量 fGn 自协方差 γ(k)，用于 Hosking 递推内层循环。"""
    return 0.5 * (
        abs(k + 1.0) ** (2.0 * H)
        - 2.0 * abs(k) ** (2.0 * H)
        + abs(k - 1.0) ** (2.0 * H)
    )


def gen_davies_harte(rng: np.random.RandomState, N: int, H: float = 0.5, fs: float = 1.0,
                     intensity: float = 1.0, raw: bool = False) -> np.ndarray:
    """Davies–Harte / Wood–Chan circulant embedding 精确 fBm 生成。

    算法（见 docs/theory.md §3）：
      1. fGn 自协方差 γ(k), k=0..N-1（σ² = γ(0) = 1）。
      2. 构造 2N 循环矩阵首行 r：
            r[0]    = γ(0)
            r[k]    = γ(k),           1 ≤ k ≤ N-1
            r[N]    = 0
            r[2N-k] = γ(k)·(1 - k/N), 1 ≤ k ≤ N-1   （Wood–Chan 三角窗 taper）
      3. 特征值 λ = Re(FFT(r))；若 λ.min() < -1e-10·λ.max() 抛 ValueError（否则 clamp ≥ 0）。
      4. 复高斯 Z 共轭对称 → W = sqrt(λ/M)·Z → fGn = Re(IFFT(W))[:N]。
      5. fBm = cumsum(fGn)（首点置 0）。

    ``raw=True`` 返回未归一化 fBm 路径；否则对 fBm 做全局 ``normalize()``（保持 API 一致）。

    注意：H 接近 1 且序列很长时嵌入可能负定，此时应改用 ``method='hosking'``。
    """
    M = 2 * N
    g = fgng_acov(H, N)  # γ(0 .. N-1)

    r = np.zeros(M, dtype=np.float64)
    r[0] = g[0]
    r[1:N] = g[1:N]
    r[N] = 0.0
    # Wood–Chan Bartlett 三角窗：对环绕部分做 taper
    k = np.arange(1, N, dtype=int)
    r[2 * N - k] = g[k] * (1.0 - k / N)

    lam = np.real(np.fft.fft(r))
    if lam.min() < -1e-10 * lam.max():
        raise ValueError("Davies-Harte 负特征值，请改用 method='hosking'")
    lam = np.maximum(lam, 0.0)

    # 共轭对称复高斯 Z（长度 M）
    Z = np.zeros(M, dtype=complex)
    Z[0] = rng.randn()
    Z[1:N] = (rng.randn(N - 1) + 1j * rng.randn(N - 1)) / np.sqrt(2.0)
    Z[N] = rng.randn()
    for j in range(1, N):
        Z[M - j] = np.conj(Z[j])

    # 缩放约定（关键）：D-H 嵌入特征值为 lam = Re(FFT(r))，其和为 M·γ(0)。
    # numpy 的 ifft 自带 1/M 因子，故须用 W = sqrt(lam)·Z 并对 ifft 结果乘 sqrt(M)，
    # 才能使生成 fGn 的方差恰为 γ(0)=1、协方差恰为 γ(k)。
    # （若误用 W = sqrt(lam/M)·Z 且不加 sqrt(M)，方差会偏小 M² 倍。）
    W = np.sqrt(lam) * Z
    y = np.fft.ifft(W)
    fgn = np.sqrt(M) * np.real(y[:N])

    # fBm 路径：长度 N，首点 0（fbm[k] = fbm[k-1] + fgn[k-1]）
    fbm = np.zeros(N, dtype=np.float64)
    fbm[0] = 0.0
    fbm[1:] = np.cumsum(fgn)[:N - 1]

    if raw:
        return fbm
    return normalize(fbm, intensity)


def gen_hosking(rng: np.random.RandomState, N: int, H: float = 0.5, fs: float = 1.0,
                intensity: float = 1.0, raw: bool = False) -> np.ndarray:
    """Hosking (Durbin–Levinson) 精确 fGn 递推，作为 Davies–Harte 的兜底（始终有效）。

    基于 fGn 自协方差用 Durbin–Levinson 递推（O(N²)）逐点生成精确 fGn，再 cumsum 得 fBm。
    ``raw=True`` 返回未归一化 fBm 路径；否则 ``normalize()``。

    性能提示：三重 Python 循环，N=4096 约数秒、N=8192 约 20s+。长序列请优先用
    ``davies_harte``（O(N log N)）；仅当 D-H 因 H 接近 1 出现负特征值时才回退到本方法。
    """
    phi = np.zeros(N)
    v = np.zeros(N)
    fgn = np.zeros(N)

    v[0] = _fgn_gamm(0, H)
    fgn[0] = np.sqrt(v[0]) * rng.randn()

    for i in range(1, N):
        # 计算反射系数 phi[i]
        tmp = _fgn_gamm(i, H)
        for j in range(1, i):
            tmp -= phi[j] * _fgn_gamm(i - j, H)
        phi[i] = tmp / v[i - 1]

        # Durbin–Levinson：用副本做非原地更新，避免对称自配对（i-j==j）污染结果
        new_phi = phi.copy()
        for j in range(1, i):
            new_phi[j] = phi[j] - phi[i] * phi[i - j]
        phi[:i] = new_phi[:i]

        v[i] = v[i - 1] * (1.0 - phi[i] ** 2)

        # 生成第 i 个 fGn 样本：条件均值 X̂_i = Σ_{k=1}^{i} φ_{i,k}·X_{i-k}（含刚算出的反射系数 φ_{i,i}）
        # 注意索引：系数 φ_{i,k} 必须乘 X_{i-k}（即 X_{i-1}, X_{i-2}, ..., X_0），不可错位。
        s = 0.0
        for k in range(1, i + 1):
            s += phi[k] * fgn[i - k]
        fgn[i] = np.sqrt(v[i]) * rng.randn() + s

    # fBm 路径：长度 N，首点 0
    fbm = np.zeros(N, dtype=np.float64)
    fbm[0] = 0.0
    fbm[1:] = np.cumsum(fgn)[:N - 1]

    if raw:
        return fbm
    return normalize(fbm, intensity)
