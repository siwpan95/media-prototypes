"""Davies–Harte 精确 fBm 生成 + Hurst 反估演示。

直接运行：  python examples/davies_harte_demo.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from wave4 import BrownianNoiseGenerator, gen_davies_harte
from wave4.analysis.metrics import autocorr, estimate_h_from_psd, hurst_rs
from wave4.viz.plot import plot_noise, plot_psd

H = 0.75


def main() -> None:
    # raw=True 返回未归一化的 fBm 路径（首点 0，方差随时间增长）；
    # fGn 是其增量序列：fbm 的差分。
    rng = np.random.RandomState(7)
    fbm = gen_davies_harte(rng, 4000, H=H, raw=True)
    fgn = np.diff(fbm)
    print(f"fGn(H={H}): var={np.var(fgn, ddof=0):.4f}  lag1_acf={autocorr(fgn, 1)[1]:.4f}")

    # 归一化 fBm 路径
    g = BrownianNoiseGenerator('davies_harte')
    fbm = g.generate(4000, H=H, seed=7)
    print(f"fBm(H={H}): mean={fbm.mean():.4f} std={fbm.std():.4f}")

    # Hurst 反估：PSD 反推 / R/S 应用于 fGn（即 fBm 的增量 np.diff(fbm)）
    print(f"H 估计 (estimate_h_from_psd on fGn) = {estimate_h_from_psd(np.diff(fbm)):.3f}  (真值 {H})")
    print(f"H 估计 (hurst_rs on fGn)            = {hurst_rs(np.diff(fbm)):.3f}  (真值 {H})")

    plot_noise(fbm[:1000], title=f'Davies-Harte fBm (H={H})')
    plot_psd(fbm, title='D-H fBm PSD')
    plt.show()


if __name__ == '__main__':
    main()
