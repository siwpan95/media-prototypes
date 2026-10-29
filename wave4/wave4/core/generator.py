"""BrownianNoiseGenerator —— 薄分发器。

仅负责：持有 ``rng``、处理 per-call ``seed``、分派到 ``wave4.core.generators``
中的纯函数。公开 API 与原 ``wave4.py`` 完全一致；新增 ``davies_harte`` /
``hosking`` 两种精确 fBm 生成法分支。
"""
from __future__ import annotations

import numpy as np

from .generators import (
    gen_basic,
    gen_davies_harte,
    gen_fractal,
    gen_freq,
    gen_hosking,
    gen_iir,
)

_VALID_METHODS = ('basic', 'freq', 'iir', 'fractal', 'davies_harte', 'hosking')


class BrownianNoiseGenerator:
    """布朗噪声 / 分数阶布朗运动生成器（薄分发器）。

    属性：
        method: 当前生成方法（见 ``_VALID_METHODS``）
        rng:    持有的 ``np.random.RandomState``（保证给定 seed 可复现）

    方法：
        set_seed(seed): 重置 rng 种子
        generate(N, fs, intensity, **kwargs): 生成噪声，返回 float64、shape (N,) 数组
    """

    def __init__(self, method: str = 'basic') -> None:
        if method not in _VALID_METHODS:
            raise ValueError(
                f"未知方法: {method}（可选：{', '.join(_VALID_METHODS)}）"
            )
        # 沿用原实现：使用 RandomState（非 default_rng），保证可复现与回归一致
        self.method = method
        self.rng = np.random.RandomState()

    def set_seed(self, seed: int) -> None:
        """设置（重置）随机种子。"""
        self.rng.seed(seed)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _resolve_beta_h(self, kwargs: dict) -> float:
        """解析 Hurst 指数 H：``beta`` 经 ``H=(beta-1)/2`` 反推，与显式 ``H`` 互斥。

        二者同给 → 抛 ValueError。
        """
        H = kwargs.get('H', 0.5)
        beta = kwargs.get('beta', None)
        if beta is not None and 'H' in kwargs:
            raise ValueError("参数 'beta' 与 'H' 互斥，请勿同时给定")
        if beta is not None:
            H = (beta - 1) / 2.0
        return H

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------
    def generate(self, N: int, fs: float = 1.0, intensity: float = 1.0,
                 **kwargs) -> np.ndarray:
        """生成噪声数组（float64, shape (N,), 零均值, std≈intensity）。

        参数：
            N: 采样点数
            fs: 采样率（basic / iir 忽略，沿用原行为）
            intensity: 强度系数（输出 std≈intensity）
            seed: 本次生成前重置 rng 的种子（复现关键；非空才 reseed）
            其余 kwargs 透传给对应生成算法（如 f_min/f_max/alpha/beta/H）。

        复现要点（与原 wave4.py 一致）：若提供 per-call ``seed``，先
        ``self.rng.seed(seed)`` 再抽样；否则沿用当前 rng 状态。
        """
        seed = kwargs.pop('seed', None)
        if seed is not None:
            self.rng.seed(seed)

        method = self.method
        if method == 'basic':
            return gen_basic(self.rng, N, intensity=intensity)
        if method == 'freq':
            return gen_freq(self.rng, N, fs=fs, intensity=intensity,
                            f_min=kwargs.get('f_min'), f_max=kwargs.get('f_max'))
        if method == 'iir':
            return gen_iir(self.rng, N, intensity=intensity,
                           alpha=kwargs.get('alpha', 0.99))
        if method == 'fractal':
            return gen_fractal(self.rng, N, fs=fs, intensity=intensity,
                               beta=kwargs.get('beta', 2.0))
        if method == 'davies_harte':
            H = self._resolve_beta_h(kwargs)
            return gen_davies_harte(self.rng, N, H=H, fs=fs, intensity=intensity)
        if method == 'hosking':
            H = self._resolve_beta_h(kwargs)
            return gen_hosking(self.rng, N, H=H, fs=fs, intensity=intensity)

        raise ValueError(
            f"未知方法: {method}（可选：{', '.join(_VALID_METHODS)}）"
        )
