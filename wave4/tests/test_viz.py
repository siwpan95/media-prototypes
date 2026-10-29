"""viz 可视化测试：在 Agg 无头后端下调用绘图函数并 savefig，断言无异常且文件生成。

测试开头已强制 Agg 后端（conftest 也已设置），不触发任何显示器依赖。
"""
import os
import tempfile

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from wave4.viz.plot import plot_comparison, plot_noise, plot_psd


def _rand(N=1000, seed=0):
    rng = np.random.RandomState(seed)
    return rng.randn(N)


def test_plot_noise_saves():
    x = _rand(1000, seed=0)
    tmp = tempfile.mkdtemp()
    ax = plot_noise(x, title="t", n_show=200)
    path = os.path.join(tmp, "noise.png")
    ax.figure.savefig(path)
    plt.close("all")
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_plot_comparison_saves():
    x = _rand(1000, seed=1)
    tmp = tempfile.mkdtemp()
    fig = plot_comparison({"a": x, "b": x * 0.5}, n_show=200)
    path = os.path.join(tmp, "cmp.png")
    fig.savefig(path)
    plt.close("all")
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_plot_psd_saves():
    x = _rand(1000, seed=2)
    tmp = tempfile.mkdtemp()
    fig = plot_psd(x)
    path = os.path.join(tmp, "psd.png")
    fig.savefig(path)
    plt.close("all")
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
