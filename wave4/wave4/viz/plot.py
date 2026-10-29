"""可视化：中文字体感知的绘图函数。

绘图前调用 ``wave4._config.configure_chinese_font()`` 配置中文字体。
函数不阻塞：是否 ``plt.show()`` / ``savefig`` 由调用方决定（返回 fig / ax）。
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from .._config import configure_chinese_font
from ..analysis.metrics import estimate_psd


def plot_noise(x, title=None, fs: float = 1.0, n_show=None, ax=None):
    """绘制单条噪声轨迹，返回 ``matplotlib.axes.Axes``。

    若 ``ax`` 为 None 则新建 figure（与 ``plot_comparison`` / ``plot_psd`` 一致），
    避免抢占调用方已有的当前 axes。
    """
    configure_chinese_font()
    x = np.asarray(x, dtype=np.float64)
    if n_show is not None:
        x = x[:n_show]
    t = np.arange(x.size) / fs if fs else np.arange(x.size)

    if ax is None:
        _, ax = plt.subplots()
    ax.plot(t, x)
    ax.set_xlabel('时间 (s)' if fs else '采样点')
    ax.set_ylabel('幅度')
    ax.set_title(title if title else '噪声轨迹')
    ax.grid(True, alpha=0.3)
    return ax


def plot_comparison(series: dict, fs: float = 1.0, n_show=None):
    """多方法对比图。``series: {名称: 数组}``，返回 ``matplotlib.figure.Figure``。"""
    configure_chinese_font()
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, x in series.items():
        x = np.asarray(x, dtype=np.float64)
        if n_show is not None:
            x = x[:n_show]
        t = np.arange(x.size) / fs if fs else np.arange(x.size)
        ax.plot(t, x, label=str(name), alpha=0.85)
    ax.set_xlabel('时间 (s)' if fs else '采样点')
    ax.set_ylabel('幅度')
    ax.set_title('多方法布朗噪声对比')
    ax.legend()
    ax.grid(True, alpha=0.3)
    return fig


def plot_psd(x, fs: float = 1.0, title=None):
    """绘制 PSD（log-log），返回 ``matplotlib.figure.Figure``。内部调用 analysis.estimate_psd。"""
    configure_chinese_font()
    f, Pxx = estimate_psd(x, fs=fs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(f[f > 0], Pxx[f > 0])
    ax.set_xlabel('频率 (Hz)')
    ax.set_ylabel('PSD')
    ax.set_title(title if title else '功率谱密度 (PSD)')
    ax.grid(True, which='both', alpha=0.3)
    return fig
