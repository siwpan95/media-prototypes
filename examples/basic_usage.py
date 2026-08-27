"""基础用法：6 种方法生成 + seeding 复现演示。

直接运行：  python examples/basic_usage.py
（推荐先 ``pip install -e .`` 安装包；未安装时脚本会自动把仓库根加入 sys.path）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from wave4 import BrownianNoiseGenerator

METHODS = ['basic', 'freq', 'iir', 'fractal', 'davies_harte', 'hosking']


def main() -> None:
    print("=== 各方法生成 (N=2000, fs=1000, seed=42) ===")
    for m in METHODS:
        g = BrownianNoiseGenerator(m)
        kw = {'seed': 42}
        if m == 'freq':
            kw.update(f_min=1, f_max=100)
        if m == 'davies_harte':
            kw.update(H=0.7)
        if m == 'hosking':
            kw.update(H=0.3)
        x = g.generate(2000, fs=1000, **kw)
        print(f"{m:14s} shape={x.shape} mean={x.mean():.4f} std={x.std():.4f}")

    # seeding 复现演示
    g1 = BrownianNoiseGenerator('freq')
    g2 = BrownianNoiseGenerator('freq')
    a = g1.generate(1000, seed=7)
    b = g2.generate(1000, seed=7)
    print("\nseeding 复现 np.allclose:", np.allclose(a, b))

    # 绘图对比（前 500 点）
    plt.figure(figsize=(12, 8))
    for i, m in enumerate(METHODS):
        g = BrownianNoiseGenerator(m)
        kw = {'seed': 42}
        if m == 'freq':
            kw.update(f_min=1, f_max=100)
        if m == 'davies_harte':
            kw.update(H=0.7)
        if m == 'hosking':
            kw.update(H=0.3)
        x = g.generate(2000, fs=1000, **kw)
        plt.subplot(3, 2, i + 1)
        plt.plot(x[:500])
        plt.title(m)
        plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
