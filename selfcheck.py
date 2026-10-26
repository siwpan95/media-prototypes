#!/usr/bin/env python3
"""时空画板 (shikonghuaban) — 无头自检入口。

只 import 纯逻辑模块（blackhole_physics / config / state），
绝不 import 会初始化 pygame / PortAudio 的 main / visual_engine / audio_engine。

验证点：
  1. 黑洞物理：区域判定边界、时间膨胀、ISCO 轨道速度、阴影 alpha 单调性。
  2. 配置：派生量不变量、dict / TOML 往返、非法覆盖报错。
  3. 共享状态：音量/节拍写入可见，乐段编排引用的音符全部存在于 NOTES。

用法：python selfcheck.py   （成功退出 0，失败打印 FAIL 并退出 1）
"""

import math
import os
import sys
import tempfile

_FAILS = []


def check(name, fn):
    """执行单个检查点，异常/False 记为失败但不中断，便于一次看到全部问题。"""
    try:
        detail = fn()
        if detail is False:
            raise AssertionError("检查返回 False")
        print(f"  [ok] {name}" + (f" — {detail}" if isinstance(detail, str) else ""))
    except Exception as exc:  # noqa: BLE001 - 自检需要兜住一切失败
        _FAILS.append(f"{name}: {type(exc).__name__}: {exc}")
        print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")


def approx(a, b, tol=1e-9):
    if abs(a - b) > tol:
        raise AssertionError(f"期望 {b}，实际 {a}（容差 {tol}）")


# ═══════════════════════════════════════════════════════════════
#  1. 黑洞物理
# ═══════════════════════════════════════════════════════════════
def check_blackhole_physics():
    from shikonghuaban import blackhole_physics as bp
    from shikonghuaban.config import BL_SCHWARZSCHILD_R as RS

    # 区域判定：按半径从小到大应依次穿过 6 个区域
    expected = [
        (0.05 * RS, "singularity"),
        (0.50 * RS, "inside_horizon"),
        (1.20 * RS, "photon_sphere"),
        (2.00 * RS, "plunging"),
        (5.00 * RS, "disk"),
        (20.0 * RS, "outer"),
    ]
    for r, want in expected:
        got = bp.region_of(r)
        if got != want:
            raise AssertionError(f"region_of({r}) = {got!r}，期望 {want!r}")

    # 时间膨胀：视界内为 0，视界外随半径单调递增，r=2rs 处应为 sqrt(1/2)
    if bp.time_dilation(RS) != 0.0 or bp.time_dilation(0.5 * RS) != 0.0:
        raise AssertionError("视界内 time_dilation 应为 0")
    prev = -1.0
    for k in range(2, 40):
        td = bp.time_dilation(k * RS)
        if td <= prev:
            raise AssertionError(f"time_dilation 非单调递增，在 r={k}*rs 处")
        prev = td
    approx(bp.time_dilation(2 * RS), math.sqrt(0.5), 1e-12)

    # ISCO 处相对论轨道速度应为 0.5c；牛顿速度应为 sqrt(1/6)
    approx(bp.relativistic_orbital_speed(bp.BL_ISCO_R), 0.5, 1e-12)
    approx(bp.newtonian_orbital_speed(bp.BL_ISCO_R), math.sqrt(1.0 / 6.0), 1e-12)
    if bp.relativistic_orbital_speed(RS) != 0.0:
        raise AssertionError("视界处轨道速度应为 0（无类时圆轨道）")
    if not bp.is_stable_orbit(bp.BL_ISCO_R) or bp.is_stable_orbit(bp.BL_ISCO_R * 0.9):
        raise AssertionError("is_stable_orbit 在 ISCO 边界判定错误")

    # 阴影 alpha：视界内完全不透明，远处全透明；整条曲线上唯一的上升只能是
    # 光子球处「外发光环」接缝（<=30，见 shadow_alpha 实现），其余必须单调不增。
    if bp.shadow_alpha(0.5 * RS) != 255:
        raise AssertionError("视界内 shadow_alpha 应为 255")
    if bp.shadow_alpha(20 * RS) != 0:
        raise AssertionError("远区 shadow_alpha 应为 0")
    prev = 256
    seam = (bp.BL_PHOTON_SPHERE_R - 0.02 * RS, bp.BL_PHOTON_SPHERE_R + 0.02 * RS)
    for i in range(1, 4001):
        r = RS * 0.02 + (10.0 * RS - RS * 0.02) * i / 4000.0
        a = bp.shadow_alpha(r)
        if a > prev:
            if not (seam[0] <= r <= seam[1]):
                raise AssertionError(f"shadow_alpha 在 r={r:.1f} 出现非预期上升 {prev}->{a}")
            if a - prev > 30:
                raise AssertionError(f"光子球接缝跳变过大：{prev}->{a}")
        prev = a

    # 吸积盘温度：盘内归一化在 [0,1] 且随半径严格递减，ISCO 处最热，盘外为 0
    t_isco = bp.accretion_temperature(bp.BL_ISCO_R)
    if not (0.0 < t_isco <= 1.0):
        raise AssertionError(f"ISCO 盘温应在 (0,1]，实际 {t_isco}")
    prev = t_isco + 1.0
    for i in range(0, 501):
        r = bp.BL_ISCO_R + (bp.BL_DISK_OUTER_R - bp.BL_ISCO_R) * i / 500.0
        t = bp.accretion_temperature(r)
        if not (0.0 <= t <= 1.0):
            raise AssertionError(f"盘温在 r={r:.1f} 越界：{t}")
        if t > prev:
            raise AssertionError(f"盘温随半径非递减，在 r={r:.1f}: {prev}->{t}")
        prev = t
    if bp.accretion_temperature(bp.BL_ISCO_R * 0.5) != 0.0:
        raise AssertionError("ISCO 内侧温度应为 0")
    if bp.accretion_temperature(bp.BL_DISK_OUTER_R * 1.1) != 0.0:
        raise AssertionError("吸积盘外缘外温度应为 0")

    # 径向/切向单位向量正交且模为 1（偏离中心点）
    x, y = bp.CENTER[0] + 300, bp.CENTER[1] - 400
    ux, uy = bp.radial_unit(x, y)
    vx, vy = bp.tangential_unit(x, y)
    approx(math.hypot(ux, uy), 1.0, 1e-12)
    approx(ux * vx + uy * vy, 0.0, 1e-12)
    approx(bp.dist_to_bh(x, y), 500.0, 1e-9)

    return "区域判定/时间膨胀/ISCO 速度/阴影 alpha/盘温曲线 全部符合理论值"


# ═══════════════════════════════════════════════════════════════
#  2. 配置派生量与序列化往返
# ═══════════════════════════════════════════════════════════════
def check_config():
    from shikonghuaban.config import Config, get_config

    cfg = get_config()
    # 派生量必须恒等于 rs 的固定倍数，且不接受手填
    approx(cfg.bl_photon_sphere_r, cfg.bl_schwarzschild_r * 1.5)
    approx(cfg.bl_isco_r, cfg.bl_schwarzschild_r * 3.0)
    approx(cfg.bl_disk_outer_r, cfg.bl_schwarzschild_r * 10.0)
    approx(cfg.beat, 60.0 / cfg.bpm, 1e-12)

    # from_dict 只认已知字段；未知键忽略，派生量按新 rs 重算
    c2 = Config.from_dict({
        "bl_schwarzschild_r": 100.0,
        "bpm": 120,
        "unknown_key_should_be_ignored": 12345,
    })
    approx(c2.bl_schwarzschild_r, 100.0)
    approx(c2.bl_photon_sphere_r, 150.0)
    approx(c2.bl_isco_r, 300.0)
    approx(c2.bl_disk_outer_r, 1000.0)
    approx(c2.beat, 0.5, 1e-12)
    if hasattr(c2, "unknown_key_should_be_ignored"):
        raise AssertionError("from_dict 不应把未知键写成属性")

    # to_dict → from_dict 语义往返（派生量由 __post_init__ 重算，故一致）
    c3 = Config.from_dict(c2.to_dict())
    approx(c3.bl_isco_r, c2.bl_isco_r)
    approx(c3.beat, c2.beat, 1e-12)
    if c3.notes != c2.notes or c3.riff != c2.riff:
        raise AssertionError("to_dict/from_dict 往返后 notes/riff 不一致")

    # TOML 往返：写临时文件（项目外）→ 读回 → 派生量正确
    tmpdir = tempfile.mkdtemp(prefix="skhb_selfcheck_")
    toml_path = os.path.join(tmpdir, "cfg.toml")
    try:
        with open(toml_path, "w", encoding="utf-8") as f:
            f.write("[shikonghuaban]\nbl_schwarzschild_r = 250.0\nbpm = 90\nsr = 48000\n")
        c4 = Config.from_toml(toml_path)
        approx(c4.bl_schwarzschild_r, 250.0)
        approx(c4.bl_photon_sphere_r, 375.0)
        approx(c4.bl_isco_r, 750.0)
        approx(c4.bl_disk_outer_r, 2500.0)
        approx(c4.beat, 60.0 / 90.0, 1e-12)
        if c4.sr != 48000:
            raise AssertionError("TOML 的 sr 未被读入")
        if c4.width != 1920:
            raise AssertionError("未覆盖的字段应保持默认值 1920")
    finally:
        try:
            os.remove(toml_path)
            os.rmdir(tmpdir)
        except OSError:
            pass

    # 非法覆盖必须报错，而不是静默写入野属性（在副本上试，不污染全局单例）
    try:
        c2.override(nonexistent_field=1)
    except KeyError:
        pass
    else:
        raise AssertionError("override 未知字段应抛 KeyError")
    approx(c2.bl_isco_r, 300.0)  # 失败调用不得改动任何字段

    # replace() 后配置仍是合法对象（不可变式微调）
    c5 = Config.from_dict({"bl_schwarzschild_r": 90.0})
    approx(c5.bl_isco_r, 270.0)

    return "派生量恒等式 + dict/TOML 往返 + 非法键拒绝"


# ═══════════════════════════════════════════════════════════════
#  3. 共享状态（音频线程 ↔ 渲染线程 桥梁）
# ═══════════════════════════════════════════════════════════════
def check_shared_state():
    from shikonghuaban.config import NOTES
    from shikonghuaban.state import shared_state

    saved = (shared_state.volume, shared_state.beat, shared_state.section)
    try:
        # 写入 → 读取 可见（加锁访问不抛错，且值持久）
        with shared_state.lock:
            shared_state.volume = 0.75
            shared_state.beat = 42
            shared_state.section = 3
        if (shared_state.volume, shared_state.beat, shared_state.section) != (0.75, 42, 3):
            raise AssertionError("SharedState 写入后读回不一致")

        # 乐段编排结构：5 段，每段 (音符序列, 八度偏移)
        patterns = shared_state.patterns
        if len(patterns) != 5:
            raise AssertionError(f"patterns 应为 5 段，实际 {len(patterns)}")
        total = 0
        for seq, octave in patterns:
            if not isinstance(octave, int):
                raise AssertionError("段落八度偏移应为 int")
            for note in seq:
                total += 1
                if note is None:
                    continue  # 休止符
                if note not in NOTES:
                    raise AssertionError(f"乐段引用了未定义音符 {note!r}")
        if total == 0:
            raise AssertionError("乐段为空")

        # 首段是 riff（与 config.RIFF 同序）
        from shikonghuaban.config import RIFF
        if list(patterns[0][0]) != list(RIFF):
            raise AssertionError("首段应为 RIFF 音符序列")

        return f"音量/节拍写入读回一致；{len(patterns)} 段共 {total} 个音符引用全部有定义"
    finally:
        shared_state.volume, shared_state.beat, shared_state.section = saved


# ═══════════════════════════════════════════════════════════════
#  main
# ═══════════════════════════════════════════════════════════════
def main():
    print("时空画板 无头自检（不启动 pygame / 音频设备）")
    check("黑洞物理", check_blackhole_physics)
    check("配置派生与往返", check_config)
    check("共享状态", check_shared_state)

    if _FAILS:
        print(f"FAIL: {len(_FAILS)} 项检查未通过")
        for f in _FAILS:
            print(f"  - {f}")
        return 1

    print(
        "selfcheck ok: 黑洞物理（区域/时间膨胀/ISCO 速度/阴影 alpha）+ "
        "配置派生量与 dict/TOML 往返 + SharedState 写入读回"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
