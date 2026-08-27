"""多方法对比图。

直接运行：  python examples/comparison_methods.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib.pyplot as plt

from wave4 import BrownianNoiseGenerator
from wave4.viz.plot import plot_comparison

METHODS = ['basic', 'freq', 'iir', 'fractal', 'davies_harte', 'hosking']


def main() -> None:
    N = 3000
    results = {}
    for m in METHODS:
        g = BrownianNoiseGenerator(m)
        kw = {'seed': 42}
        if m == 'freq':
            kw.update(f_min=1, f_max=100)
        if m in ('davies_harte', 'hosking'):
            kw.update(H=0.7)
        results[m] = g.generate(N, fs=1000, **kw)

    fig = plot_comparison(results, fs=1000, n_show=800)
    fig.suptitle('各方法布朗噪声对比 (前 800 点)')

    # PSD 对比（log-log）
    plt.figure(figsize=(8, 5))
    for m, x in results.items():
        from wave4.analysis.metrics import estimate_psd
        f, Pxx = estimate_psd(x)
        plt.loglog(f[f > 0], Pxx[f > 0], label=m, alpha=0.8)
    plt.xlabel('频率 (Hz)')
    plt.ylabel('PSD')
    plt.title('各方法 PSD 对比')
    plt.legend()
    plt.grid(True, which='both', alpha=0.3)

    plt.show()


if __name__ == '__main__':
    main()
