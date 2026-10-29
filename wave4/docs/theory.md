# 理论支撑与文献引用（wave4 增强模块）

> 供 `core.generators`（Davies–Harte / Hosking）与 `analysis.metrics`（Hurst / PSD / 标度）实现参考。

## 1. 谱关系

- **fBm（分数阶布朗运动）** 的功率谱密度（PSD）满足
  $$S_{fBm}(f) \propto \frac{1}{f^{2H+1}}$$
- **fGn（分数阶高斯噪声，fBm 的增量）** 的 PSD 满足
  $$S_{fGn}(f) \propto \frac{1}{f^{2H-1}}$$
- 由 fGn PSD 斜率 `β = −slope`，反推 Hurst 指数：`H = (β+1)/2`。

## 2. 原有 fractal 法的约定差异（待确认）

原 `wave4.py` 的 `fractal` 法对白噪声做 `1/f^(beta/2)` 频域滤波，PSD∝`1/f^beta`，并注释 `H=(beta−1)/2`。
这与上式 `fGn PSD ∝ 1/f^(2H−1)`（推出 `H=(beta+1)/2`）存在映射分歧。
**本期处理**：`fractal` 法内部沿用原 `H=(beta−1)/2` 以保持其行为不变；新方法以 `H` 为权威参数；`estimate_h_from_psd` 采用谱理论 `H=(β+1)/2`。差异在 README/本文档明示。

## 3. Davies–Harte / Wood–Chan（circulant embedding）

- 构造 2N 循环矩阵嵌入 fGn 协方差，用 FFT 求嵌入矩阵平方根，精确生成 fGn，再 `cumsum` 得 fBm。
- **Wood–Chan 修正**：当嵌入特征值出现负值时，对循环矩阵首行后半段施加 Bartlett（三角）窗 taper，使嵌入在更多 (H, N) 组合下非负定；仍为负则报错（H>0.95 且 N 很大时易触发）。
- 参考文献：
  - Davies, R. B., & Harte, D. S. (1987). *Tests for Hurst effect*. Biometrika, 74(1), 95–101.
  - Wood, A. T. A., & Chan, G. (1994). *Simulation of stationary Gaussian processes in [0,1]^d*. Journal of Computational and Graphical Statistics, 3(4), 409–432.
  - Hosking, J. R. M. (1984). *Modeling persistence in hydrological time series using fractional differencing*. Water Resources Research, 20(12), 1898–1908.

## 4. Hurst 估计方法

- **R/S（重标极差）**：对多时间尺度 `n` 计算 `RS(n)`，拟合 `log n – log RS(n)` 斜率得 H（经典方法，对小样本有偏）。
- **DFA（去趋势涨落分析）**：分段多项式（默认 1 阶）去趋势后计算涨落函数 `F(n)`，拟合 `log n – log F(n)` 得 H（对非线性趋势更稳健）。
- **增量方差标度**：`Var(X(t+Δ)−X(t)) ∝ Δ^(2H)`，拟合 `log Δ – log Var` 得指数 `e=2H`。

## 5. 参考实现（仅作算法对照，不引入依赖）

- `hurst-estimators`（Edes, 2024）
- `hurst`（Mottl）
- 自实现以 `numpy`/`scipy` 为主，保证零重依赖、可测试。
