"""质量分析演示：自相关 / PSD / Hurst(R/S, DFA) / 增量方差标度。

直接运行：  python examples/analysis_demo.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from wave4 import gen_davies_harte
from wave4.analysis.metrics import (
    autocorr,
    estimate_h_from_psd,
    estimate_psd,
    hurst_dfa,
    hurst_rs,
    variance_scaling_exponent,
)

H = 0.7


def main() -> None:
    rng = np.random.RandomState(3)
    fbm = gen_davies_harte(rng, 6000, H=H, raw=True)  # 原始 fBm 路径（首点 0）
    fgn = np.diff(fbm)                                # 其增量即 fGn

    print(f"fGn(H={H}): var={np.var(fgn, ddof=0):.3f}  lag1_acf={autocorr(fgn, 1)[1]:.3f}")
    print(f"  estimate_h_from_psd (on fGn) = {estimate_h_from_psd(fgn):.3f}  (真值 {H})")
    print(f"  hurst_rs   (on fGn)         = {hurst_rs(fgn):.3f}  (真值 {H})")
    print(f"  hurst_dfa  (on fGn)         = {hurst_dfa(fgn):.3f}  (真值 {H})")
    print(f"  variance_scaling (on fBm)   = {variance_scaling_exponent(fbm):.3f}  (理论 2H={2 * H:.2f})")

    ac = autocorr(fgn, 20)
    print(f"  fGn lag-1..3 acf = {ac[1]:.3f}, {ac[2]:.3f}, {ac[3]:.3f}")

    f, Pxx = estimate_psd(fgn)
    plt.figure(figsize=(10, 4))
    plt.semilogy(f[f > 0], Pxx[f > 0])
    plt.title('fGn PSD (Welch)')
    plt.xlabel('频率')
    plt.ylabel('PSD')
    plt.grid(True, which='both', alpha=0.3)
    plt.show()


if __name__ == '__main__':
    main()
