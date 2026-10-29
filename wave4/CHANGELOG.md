# Changelog

## v0.2.0 — 模块化重构 + 联网增强
- 将单文件 `wave4.py` 重构为规范多模块包 `wave4`：
  - `wave4.core`：6 个纯函数生成器（`gen_*`）+ 薄分发器 `BrownianNoiseGenerator`（`generator.py`）
  - `wave4.analysis`：自相关、`estimate_psd`(Welch)、`estimate_h_from_psd`、R/S 与 DFA 的 Hurst 估计、增量方差标度
  - `wave4.viz`：中文字体感知的绘图（`plot_noise` / `plot_comparison` / `plot_psd`）
  - `wave4.io`：`.npy / .npz / .csv` 噪声序列化
- 原 4 法（`basic` / `freq` / `iir` / `fractal`）数值行为与 per-call `seed` 复现 **1:1 保留**（回归锚点）。
- 新增精确法：
  - `davies_harte`：Davies–Harte / Wood–Chan circulant embedding 精确 fBm 生成
  - `hosking`：Durbin–Levinson 精确 fGn 递推，作为 D-H 在 H>0.95 长序列失效时的兜底
- 新增质量分析能力（Hurst 估计、PSD 反推 H、增量方差标度）。
- 文献引用：Davies & Harte 1987、Wood & Chan 1994、Hosking 1984、Mandelbrot & Van Ness 1968、Majumdar & Oshanin 2018。

## v0.1.0 — 单文件原型
- `wave4.py`：basic / freq / iir / fractal 四种布朗噪声生成 + 绘图示例（保留为 `wave4_legacy.py` 供回归参考）。
