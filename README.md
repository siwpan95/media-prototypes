# wave4 — 布朗噪声 / 分数阶布朗运动生成与分析工具包

`wave4` 是一个零重依赖（仅 `numpy` / `matplotlib` / `scipy`）的 Python 包，用于生成**布朗噪声**与**分数阶布朗运动（fBm）**，并提供 Hurst 指数估计、功率谱密度（PSD）分析与可视化能力。

---

## 1. 项目简介

- 6 种生成算法，可统一通过 `BrownianNoiseGenerator` 调用：
  - 经典 4 法（数值行为与原单文件 `wave4.py` 1:1 一致）：`basic`（积分）、`freq`（频域 `1/f` 带限）、`iir`（一阶递归）、`fractal`（分数阶 `1/f^(β/2)` 滤波）。
  - 2 种精确 fBm 生成法（基于联网检索确认的理论）：`davies_harte`（Davies–Harte / Wood–Chan circulant embedding）、`hosking`（Durbin–Levinson 递推兜底）。
- 配套分析：`autocorr`、`estimate_psd`、`estimate_h_from_psd`、`hurst_rs`、`hurst_dfa`、`variance_scaling_exponent`。
- 可视化（中文字体自动配置）与序列化（`.npy / .npz / .csv`）。

---

## 2. 理论背景

### 2.1 布朗运动与分数阶布朗运动

标准布朗运动（Wiener 过程）`B(t)` 是零均值高斯过程，增量独立、方差随时间间隔线性增长：

```
Var(B(t+Δ) − B(t)) = σ² · Δ
```

分数阶布朗运动（fBm, fractional Brownian motion）`B_H(t)` 由 **Hurst 指数** `H ∈ (0,1)` 控制其长程依赖与粗糙度：

```
Var(B_H(t+Δ) − B_H(t)) = σ² · |Δ|^(2H)
```

- `H = 0.5`：标准布朗运动（增量不相关）。
- `H > 0.5`：长程正相关（持久性，趋势更强）。
- `H < 0.5`：长程负相关（反持久性，更粗糙）。

其**增量序列**称为分数阶高斯噪声（fGn, fractional Gaussian noise），是原生成器输出（归一化后）的统计本质。

### 2.2 谱关系

- **fBm 的 PSD**：`S_fBm(f) ∝ 1 / f^(2H+1)`
- **fGn 的 PSD**：`S_fGn(f) ∝ 1 / f^(2H−1)`

因此由 PSD 在 log-log 空间的斜率 `s` 可反推 Hurst 指数：

```
s = −(2H − 1) = 1 − 2H   ⇒   H = (1 − s) / 2
```

### 2.3 方法对比中的谱指数说明

> ⚠️ **约定差异（已知）**：原 `fractal` 法对白噪声做 `1/f^(β/2)` 频域滤波，其 PSD∝`1/f^β`，内部注释 `H=(β−1)/2`。这与谱理论（fGn PSD∝`1/f^(2H−1)` ⇒ `H=(β+1)/2`）存在映射分歧。
> 为保持 `fractal` 法行为不变，本期沿用其原 `H=(β−1)/2` 内部约定；新增的 `davies_harte`/`hosking` 以 `H` 为权威参数；`estimate_h_from_psd` 采用谱理论 `H=(1−s)/2`。详见 `docs/theory.md`。

---

## 3. 安装

```bash
# 方式一：可编辑安装（推荐，便于开发）
pip install -e .

# 方式二：仅安装运行时依赖（固定版本，保障复现）
pip install -r requirements.txt

# 开发 / 测试（可选）
pip install -e ".[test]"
```

环境要求：Python ≥ 3.10（目标解释器 3.14），依赖 `numpy`、`matplotlib`、`scipy`。**不引入任何额外第三方库。**

---

## 4. 快速上手

```python
import numpy as np
from wave4 import BrownianNoiseGenerator, gen_davies_harte
from wave4.analysis.metrics import hurst_rs, estimate_h_from_psd

# 经典 4 法
g = BrownianNoiseGenerator('freq')
x = g.generate(2000, fs=1000, f_min=1, f_max=100, seed=42)
print(x.shape, x.mean(), x.std())   # (2000,)  ≈0  ≈1

# Davies–Harte 精确 fBm（H=0.75，长程依赖）
dh = BrownianNoiseGenerator('davies_harte')
y = dh.generate(2000, H=0.75, seed=7)
print(y.shape, y.mean())

# Hosking 兜底法
hk = BrownianNoiseGenerator('hosking')
z = hk.generate(2000, H=0.3, seed=9)

# 纯函数形式（可独立测试）
rng = np.random.RandomState(0)
fgn = gen_davies_harte(rng, 4096, H=0.6, raw=True)   # 原始 fGn（未归一化）
print('fGn var ≈', np.var(fgn, ddof=0))              # ≈ 1

# 质量分析
print('H (R/S)   =', hurst_rs(y))
print('H (PSD)   =', estimate_h_from_psd(np.diff(y)))  # 对 fGn 用 PSD 反推
```

---

## 5. API 参考

### 5.1 `BrownianNoiseGenerator`（薄分发器）

```python
BrownianNoiseGenerator(method: str = 'basic')
BrownianNoiseGenerator.set_seed(seed: int) -> None
BrownianNoiseGenerator.generate(N, fs=1.0, intensity=1.0, **kwargs) -> np.ndarray
```

- `method ∈ {'basic','freq','iir','fractal','davies_harte','hosking'}`；未知 method 抛 `ValueError`。
- 所有方法返回 `float64`、shape `(N,)`、零均值、标准差 ≈ `intensity` 的 1-D 数组。
- **复现约定**：构造后持有 `self.rng = np.random.RandomState()`；`set_seed(seed)` 重置 rng；`generate(..., seed=K)` 在生成前 `self.rng.seed(K)` 再抽样，故相同 `(method, N, seed)` 必得相同输出。
- 各法 `kwargs` 默认值：
  - `basic`：`seed`
  - `freq`：`f_min=None, f_max=None, seed`
  - `iir`：`alpha=0.99, seed`
  - `fractal`：`beta=2.0, seed`
  - `davies_harte` / `hosking`：`H=0.5, beta=None, seed`（`beta` 经 `H=(beta−1)/2` 反推，覆盖 `H`；`beta` 与 `H` 同给抛 `ValueError`）

### 5.2 生成纯函数（`wave4.core.generators`）

`gen_basic`、`gen_freq`、`gen_iir`、`gen_fractal` 与原 4 法一一对应；`gen_davies_harte(rng, N, H=0.5, fs=1.0, intensity=1.0, raw=False)`、`gen_hosking(rng, N, H=0.5, fs=1.0, intensity=1.0, raw=False)` 为精确法。均接收 `rng` 参数（不在函数内自建随机源）。`raw=True` 返回未归一化的 fBm 路径（首点 0）。

### 5.3 分析（`wave4.analysis.metrics`）

| 函数 | 说明 |
|------|------|
| `autocorr(x, max_lag)` | 返回 lag 0..`max_lag` 自相关系数 |
| `estimate_psd(x, fs=1.0, **welch_kwargs)` | Welch 法估计 PSD，返回 `(freq, psd)` |
| `estimate_h_from_psd(x, fs=1.0, fmin=None, fmax=None)` | 由 PSD 斜率反推 `H = (1−s)/2` |
| `hurst_rs(x, n_scales=None)` | R/S 重标极差法估计 `H` |
| `hurst_dfa(x, order=1, n_scales=None)` | DFA 去趋势涨落分析估计 `H` |
| `variance_scaling_exponent(x, step_range=None)` | 增量方差 `log Var(X(t+Δ)−X(t))` 对 `log Δ` 的斜率（理论 `2H`） |

### 5.4 可视化（`wave4.viz.plot`）

`plot_noise(x, title=None, fs=1.0, n_show=None) -> Axes`、`plot_comparison(series: dict, fs=1.0, n_show=None) -> Figure`、`plot_psd(x, fs=1.0, title=None) -> Figure`。绘图前自动调用 `configure_chinese_font()`；函数不阻塞，由调用方决定 `plt.show()` / `savefig`。

### 5.5 序列化（`wave4.io.serialize`）

`save_noise(x, path, fmt='npz', metadata=None)`、`load_noise(path) -> (array, metadata)`；`fmt ∈ {'npy','npz','csv'}`，仅用 `numpy`。

---

## 6. 方法对比表

| 方法 | 关键参数（默认） | 计算复杂度 | 适用场景 | 谱指数（PSD斜率） |
|------|------------------|-----------|----------|-------------------|
| `basic` | — | O(N) | 最快原型、标准布朗运动 | `−(2H+1) = −2`（H=0.5） |
| `freq` | `f_min, f_max` | O(N log N) | 带限布朗噪声、可控频段 | `−(2H+1)` |
| `iir` | `alpha=0.99` | O(N) | 一阶递归近似积分 | `−(2H+1)` |
| `fractal` | `beta=2.0` | O(N log N) | 分数阶噪声（按 β 调谱） | `−β`（内部 `H=(β−1)/2`） |
| `davies_harte` | `H=0.5` | O(N log N) | **精确** fBm，H∈(0,0.95) 稳定 | `−(2H+1)`（fBm 路径） |
| `hosking` | `H=0.5` | O(N²) | D-H 失效兜底（H 接近 1 / 长序列） | `−(2H+1)`（fBm 路径） |

> 注：`davies_harte` / `hosking` 返回的归一化数组是 fBm 路径（零均值、std≈intensity）；其增量即 fGn。`estimate_h_from_psd` 应用于 fGn（如 `np.diff(fbm)`）时反推 H，应用于 fBm 路径时因 PSD∝`1/f^(2H+1)` 会得到 `H+1`，请注意区分。

---

## 7. 引用文献

- Davies, R. B., & Harte, D. S. (1987). *Tests for Hurst effect*. Biometrika, 74(1), 95–101.
- Wood, A. T. A., & Chan, G. (1994). *Simulation of stationary Gaussian processes in [0,1]^d*. Journal of Computational and Graphical Statistics, 3(4), 409–432.
- Hosking, J. R. M. (1984). *Modeling persistence in hydrological time series using fractional differencing*. Water Resources Research, 20(12), 1898–1908.
- Mandelbrot, B. B., & Van Ness, J. W. (1968). *Fractional Brownian motions, fractional noises and applications*. SIAM Review, 10(4), 422–437.

> 注：Hurst 估计（R/S、DFA）实现参考了开源项目 `hurst-estimators`（Edes, 2024）与 `hurst`（Mottl）的算法思路，但未引入为依赖。

---

## 8. 中文字体说明

绘图函数（`wave4.viz.plot`）会在绘图前调用 `wave4._config.configure_chinese_font()`，将 `matplotlib` 字体设为 `['Microsoft YaHei', 'SimHei', 'sans-serif']` 并关闭 `unicode_minus`，以避免中文乱码与负号显示异常。该配置**仅在使用 viz 时触发**，不在 `import wave4` 时执行，因此无头 / 测试环境不会强依赖中文字体。

若运行环境缺少上述中文字体（如 Linux 服务器），中文标签可能回退为方框；可安装对应字体或自定义 `matplotlib.rcParams['font.family']`。

---

## 9. 许可

MIT（示例性）。
