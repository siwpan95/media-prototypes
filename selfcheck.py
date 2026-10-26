#!/usr/bin/env python3
"""wave4 — 无头自检入口。

只使用标准库 + 本项目自身模块（numpy 为项目声明依赖），不新增任何依赖。

验证点：
  1. 6 种生成方法：形状 / dtype / 零均值 / std≈intensity / 同种子可复现 / 换种子相异。
  2. fBm-fGn 理论不变量：fGn 自协方差解析式、H 对 γ(1) 符号的影响、
     原始路径首点为 0、增量方差≈1（σ²=γ(0)=1）。
  3. 序列化往返：.npy / .npz（含 metadata）/ .csv 存盘再读回完全一致。
  4. 错误契约：未知 method、beta 与 H 互斥、npy 不支持 metadata、未知格式。
  5. 质量分析（需 scipy，若缺失则显式跳过）：DFA / PSD 反推的 Hurst 恢复。

用法：python selfcheck.py   （成功退出 0，失败打印 FAIL 并退出 1）
"""

import os
import sys
import tempfile

_FAILS = []
_SKIPPED = []


def check(name, fn):
    try:
        detail = fn()
        if detail is False:
            raise AssertionError("检查返回 False")
        print(f"  [ok] {name}" + (f" — {detail}" if isinstance(detail, str) else ""))
    except Exception as exc:  # noqa: BLE001 - 自检需要兜住一切失败
        _FAILS.append(f"{name}: {type(exc).__name__}: {exc}")
        print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")


def approx(a, b, tol):
    if abs(float(a) - float(b)) > tol:
        raise AssertionError(f"期望 {b} ±{tol}，实际 {a}")


METHODS = ("basic", "freq", "iir", "fractal", "davies_harte", "hosking")


# ═══════════════════════════════════════════════════════════════
#  0. 确认测的是仓库内源码，而非别处安装的副本
# ═══════════════════════════════════════════════════════════════
def check_imports_local_package():
    import wave4

    pkg_dir = os.path.dirname(os.path.abspath(wave4.__file__))
    root = os.path.dirname(os.path.abspath(__file__))
    if os.path.normcase(os.path.dirname(pkg_dir)) != os.path.normcase(root):
        raise AssertionError(f"导入的 wave4 不在本仓库内：{pkg_dir}（仓库根 {root}）")
    return f"wave4 {wave4.__version__} @ {pkg_dir}"


# ═══════════════════════════════════════════════════════════════
#  1. 六种生成方法 + 可复现性
# ═══════════════════════════════════════════════════════════════
def check_generators():
    import numpy as np
    from wave4 import BrownianNoiseGenerator

    n, intensity = 1024, 2.0
    for method in METHODS:
        kwargs = {"H": 0.7} if method in ("davies_harte", "hosking") else {}
        g = BrownianNoiseGenerator(method)
        x = g.generate(n, fs=1000.0, intensity=intensity, seed=42, **kwargs)

        if x.shape != (n,):
            raise AssertionError(f"{method}: shape 应为 ({n},)，实际 {x.shape}")
        if x.dtype != np.float64:
            raise AssertionError(f"{method}: dtype 应为 float64，实际 {x.dtype}")
        if not np.all(np.isfinite(x)):
            raise AssertionError(f"{method}: 输出含 NaN/Inf")
        approx(np.mean(x), 0.0, 1e-9)          # 归一化保证严格零均值
        approx(np.std(x, ddof=0), intensity, 1e-9)  # ddof=0 归一化，std 精确等于 intensity

        # 同种子必须逐位复现
        y = BrownianNoiseGenerator(method).generate(
            n, fs=1000.0, intensity=intensity, seed=42, **kwargs)
        if not np.array_equal(x, y):
            raise AssertionError(f"{method}: 同种子结果不可复现")

        # 换种子必须得到不同序列（排除“常量输出”式假实现）
        z = BrownianNoiseGenerator(method).generate(
            n, fs=1000.0, intensity=intensity, seed=43, **kwargs)
        if np.array_equal(x, z):
            raise AssertionError(f"{method}: 不同种子产生了相同序列")

    # 未知方法必须拒绝
    try:
        BrownianNoiseGenerator("nope")
    except ValueError:
        pass
    else:
        raise AssertionError("未知 method 应抛 ValueError")

    return f"6 方法形状/dtype/零均值/std={intensity}/可复现 全部通过"


# ═══════════════════════════════════════════════════════════════
#  2. fBm / fGn 理论不变量
# ═══════════════════════════════════════════════════════════════
def check_theory_invariants():
    import numpy as np
    from wave4 import BrownianNoiseGenerator, fgng_acov, gen_davies_harte, gen_hosking

    # γ(0)=1 对所有 H 成立；H=0.5 退化为白噪声（γ(k)=0, k>=1）
    for H in (0.1, 0.3, 0.5, 0.7, 0.9):
        approx(fgng_acov(H, 1)[0], 1.0, 1e-12)
    acov_half = fgng_acov(0.5, 16)
    approx(acov_half[0], 1.0, 1e-12)
    if np.max(np.abs(acov_half[1:])) > 1e-12:
        raise AssertionError("H=0.5 时 fGn 应为白噪声（γ(k)=0 for k>=1）")

    # γ(1) 的符号区分长程正/负相关：H>0.5 为正，H<0.5 为负，且随 H 单调
    g1 = [float(fgng_acov(H, 2)[1]) for H in (0.2, 0.3, 0.5, 0.7, 0.8)]
    if not (g1[0] < 0 and g1[1] < 0 and abs(g1[2]) < 1e-12 and g1[3] > 0 and g1[4] > 0):
        raise AssertionError(f"γ(1) 符号未随 H 变化：{g1}")
    if any(b <= a for a, b in zip(g1, g1[1:])):
        raise AssertionError(f"γ(1) 未随 H 单调递增：{g1}")

    # 原始 fBm 路径：首点为 0，其增量(fGn)方差 ≈ γ(0) = 1（未归一化）
    rng = np.random.RandomState(0)
    path = gen_davies_harte(rng, 4096, H=0.6, raw=True)
    if float(path[0]) != 0.0:
        raise AssertionError(f"原始 fBm 路径首点应为 0，实际 {path[0]}")
    fgn = np.diff(path)
    approx(np.var(fgn, ddof=0), 1.0, 0.05)

    # Hosking 与 Davies–Harte 同 H、同种子应给出同量级的标准化统计量
    a = BrownianNoiseGenerator("davies_harte").generate(2048, H=0.7, seed=11)
    b = gen_hosking(np.random.RandomState(11), 2048, H=0.7)
    approx(np.std(a, ddof=0), 1.0, 1e-9)
    approx(np.std(b, ddof=0), 1.0, 1e-9)

    # beta 与 H 互斥（构造参数一致语义）
    g = BrownianNoiseGenerator("davies_harte")
    try:
        g.generate(256, H=0.7, beta=2.4, seed=1)
    except ValueError:
        pass
    else:
        raise AssertionError("同时给 beta 与 H 应抛 ValueError")

    # beta 经 H=(beta-1)/2 反推：beta=2.4 → H=0.7，与显式 H=0.7 结果一致
    x1 = BrownianNoiseGenerator("davies_harte").generate(512, H=0.7, seed=5)
    x2 = BrownianNoiseGenerator("davies_harte").generate(512, beta=2.4, seed=5)
    if not np.array_equal(x1, x2):
        raise AssertionError("beta=2.4 与 H=0.7 应等价")

    return "fGn 自协方差解析式、γ(1) 随 H 变号/单调、fBm 首点 0、增量方差≈1、beta↔H 等价"


# ═══════════════════════════════════════════════════════════════
#  3. 序列化往返
# ═══════════════════════════════════════════════════════════════
def check_serialization():
    import numpy as np
    from wave4.io.serialize import load_noise, save_noise

    x = np.random.RandomState(3).randn(256)
    tmpdir = tempfile.mkdtemp(prefix="wave4_selfcheck_")
    try:
        # npy：精确往返，无 metadata
        p = os.path.join(tmpdir, "a.npy")
        save_noise(x, p, fmt="npy")
        y, meta = load_noise(p)
        if not np.array_equal(x, y) or meta != {}:
            raise AssertionError("npy 往返不一致")

        # npz：精确往返 + metadata 还原为原始键名
        p = os.path.join(tmpdir, "a.npz")
        save_noise(x, p, fmt="npz", metadata={"H": 0.7, "seed": 42, "tags": ["a", "b"]})
        y, meta = load_noise(p)
        if not np.array_equal(x, y):
            raise AssertionError("npz 往返数据不一致")
        if set(meta) != {"H", "seed", "tags"}:
            raise AssertionError(f"npz metadata 键名未还原：{sorted(meta)}")
        approx(meta["H"], 0.7, 1e-12)
        if int(meta["seed"]) != 42:
            raise AssertionError(f"npz metadata seed 错误：{meta['seed']}")
        if list(meta["tags"]) != ["a", "b"]:
            raise AssertionError(f"npz metadata tags 错误：{meta['tags']}")

        # csv：文本往返，按数值近似比较
        p = os.path.join(tmpdir, "a.csv")
        save_noise(x, p, fmt="csv")
        y, meta = load_noise(p)
        if y.shape != x.shape or not np.allclose(x, y):
            raise AssertionError("csv 往返数值不一致")
        if meta != {}:
            raise AssertionError("csv 不应带 metadata")

        # 错误契约
        try:
            save_noise(x, os.path.join(tmpdir, "bad.npy"), fmt="npy", metadata={"a": 1})
        except ValueError:
            pass
        else:
            raise AssertionError("npy + metadata 应抛 ValueError")
        try:
            save_noise(x, os.path.join(tmpdir, "bad.xyz"), fmt="xyz")
        except ValueError:
            pass
        else:
            raise AssertionError("未知格式应抛 ValueError")
        try:
            load_noise(os.path.join(tmpdir, "bad.xyz"))
        except ValueError:
            pass
        else:
            raise AssertionError("未知后缀加载应抛 ValueError")

        return "npy/npz(含 metadata)/csv 往返一致，非法格式与非法 metadata 均被拒绝"
    finally:
        for name in os.listdir(tmpdir):
            try:
                os.remove(os.path.join(tmpdir, name))
            except OSError:
                pass
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════
#  4. 质量分析：Hurst 恢复（依赖 scipy.signal.welch）
# ═══════════════════════════════════════════════════════════════
def check_analysis_metrics():
    import numpy as np
    from wave4 import BrownianNoiseGenerator
    from wave4.analysis.metrics import (
        estimate_h_from_psd,
        hurst_dfa,
        variance_scaling_exponent,
    )

    recovered = {}
    for H in (0.25, 0.5, 0.8):
        fbm = BrownianNoiseGenerator("davies_harte").generate(4096, H=H, seed=7)
        fgn = np.diff(fbm)

        h_dfa = hurst_dfa(fgn)
        h_psd = estimate_h_from_psd(fgn)
        vse = variance_scaling_exponent(fbm)  # 理论上 = 2H

        approx(h_dfa, H, 0.12)                 # DFA 在 4096 点上误差约 ±0.05
        approx(h_psd, H, 0.15)                 # PSD 斜率法噪声较大
        approx(vse, 2.0 * H, 0.20)             # 方差标度指数 = 2H
        recovered[H] = (round(h_dfa, 3), round(h_psd, 3), round(vse, 3))

    # 单调性：H 越大，估计值必须越大（排除常量返回式假实现）
    hs = sorted(recovered)
    for key, idx in (("dfa", 0), ("psd", 1), ("vse", 2)):
        vals = [recovered[h][idx] for h in hs]
        if any(b <= a for a, b in zip(vals, vals[1:])):
            raise AssertionError(f"{key} 估计未随真实 H 单调：{vals}")

    return "DFA/PSD/方差标度 在 H=0.25/0.5/0.8 上恢复误差内且单调"


def main():
    print("wave4 无头自检（仅标准库 + numpy/scipy）")
    check("导入自本仓库", check_imports_local_package)
    check("六种生成方法与可复现性", check_generators)
    check("fBm/fGn 理论不变量", check_theory_invariants)
    check("序列化往返", check_serialization)

    try:
        import scipy.signal  # noqa: F401
    except ImportError:
        _SKIPPED.append("质量分析（scipy 不可用，无法 import wave4.analysis.metrics）")
        print("  [skip] 质量分析 — 当前解释器缺 scipy，跳过 DFA/PSD/Hurst 恢复检查")
    else:
        check("质量分析（Hurst 恢复）", check_analysis_metrics)

    if _FAILS:
        print(f"FAIL: {len(_FAILS)} 项检查未通过")
        for f in _FAILS:
            print(f"  - {f}")
        return 1

    what = ("6 种生成算法可复现 + fGn 自协方差理论不变量 + npy/npz/csv 序列化往返")
    if not _SKIPPED:
        what += " + DFA/PSD/方差标度 Hurst 恢复"
    print(f"selfcheck ok: {what}")
    for s in _SKIPPED:
        print(f"（已跳过：{s}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
