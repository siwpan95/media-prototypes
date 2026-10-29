"""
时空画板 — 黑洞物理引擎

基于史瓦西度规 (Schwarzschild metric) 的黑洞物理计算：
  - 引力势 / 时间膨胀
  - 轨道速度 (开普勒 + 相对论修正)
  - 引力红移
  - 相对论多普勒因子
  - 光线偏折角 (引力透镜)
  - ISCO / 光子球 / 视界判定
"""

import math
from .config import (
    CENTER, BL_SCHWARZSCHILD_R, BL_PHOTON_SPHERE_R,
    BL_ISCO_R, BL_DISK_OUTER_R, BL_DOPPLER_STRENGTH
)

# ═══════════════════════════════════════════════════════════════
#  基本函数
# ═══════════════════════════════════════════════════════════════

def dist_to_bh(x: float, y: float) -> float:
    """计算点到黑洞中心的欧氏距离"""
    cx, cy = CENTER
    return math.hypot(x - cx, y - cy)


def angle_to_bh(x: float, y: float) -> float:
    """计算点相对于黑洞中心的角度 (弧度)"""
    cx, cy = CENTER
    return math.atan2(y - cy, x - cx)


def radial_unit(x: float, y: float) -> tuple:
    """从黑洞中心指向该点的单位径向向量"""
    r = dist_to_bh(x, y)
    if r < 0.001:
        return 1.0, 0.0
    cx, cy = CENTER
    return (x - cx) / r, (y - cy) / r


def tangential_unit(x: float, y: float) -> tuple:
    """逆时针切向单位向量"""
    ux, uy = radial_unit(x, y)
    return -uy, ux


def schwarzschild_r(r: float) -> float:
    """返回 r / r_s 的归一化值（方便度规计算）"""
    return max(r, BL_SCHWARZSCHILD_R * 0.01)  # 避免除零


# ═══════════════════════════════════════════════════════════════
#  引力效应
# ═══════════════════════════════════════════════════════════════

def gravitational_potential(r: float) -> float:
    """史瓦西引力势 (无量纲): Φ = -r_s / (2r)"""
    return -BL_SCHWARZSCHILD_R / (2.0 * max(r, 1.0))


def time_dilation(r: float) -> float:
    """
    引力时间膨胀因子: sqrt(1 - r_s / r)
    越靠近视界，时间越慢。r → r_s 时 → 0
    返回值 ∈ [0, 1]
    """
    if r <= BL_SCHWARZSCHILD_R:
        return 0.0
    return math.sqrt(1.0 - BL_SCHWARZSCHILD_R / r)


def gravitational_redshift(r: float) -> float:
    """
    引力红移因子: z_g = 1/sqrt(1 - r_s/r) - 1
    越靠近视界，红移越大
    """
    td = time_dilation(r)
    if td < 0.001:
        return 10.0  # 视界附近极大红移
    return 1.0 / td - 1.0


# ═══════════════════════════════════════════════════════════════
#  轨道力学
# ═══════════════════════════════════════════════════════════════

def newtonian_orbital_speed(r: float) -> float:
    """
    牛顿轨道速度: v = sqrt(GM / r)
    用 r_s = 2GM/c² 化简: v/c = sqrt(r_s / (2r))
    返还无量纲值
    """
    if r <= 0:
        return 0.0
    return math.sqrt(BL_SCHWARZSCHILD_R / (2.0 * r))


def relativistic_orbital_speed(r: float) -> float:
    """
    史瓦西度规下的圆轨道速度 (类时测地线):
    v² = (r_s / (2r)) / (1 - r_s / r)   →   v = sqrt(r_s / (2r - 2r_s))
    在 r = 3r_s (ISCO) 处 → v = sqrt(1/4) = 0.5c
    """
    if r <= BL_SCHWARZSCHILD_R:
        return 0.0
    denom = 2.0 * r - 2.0 * BL_SCHWARZSCHILD_R
    if denom <= 0:
        return 0.0
    return math.sqrt(BL_SCHWARZSCHILD_R / denom)


def orbital_period(r: float) -> float:
    """轨道周期 (无量纲): T = 2π * r / v"""
    v = relativistic_orbital_speed(r)
    if v < 0.001:
        return float('inf')
    return 2.0 * math.pi * r / v


def is_stable_orbit(r: float) -> bool:
    """判断给定半径是否 ≥ ISCO（史瓦西黑洞 r ≥ 3r_s 才有稳定圆轨道）"""
    return r >= BL_ISCO_R


# ═══════════════════════════════════════════════════════════════
#  相对论多普勒效应 + 束流
# ═══════════════════════════════════════════════════════════════

def relativistic_doppler(r: float, theta: float, v_frac: float = 0.8) -> float:
    """
    相对论多普勒因子（吸积盘束流效应）。

    参数:
        r:     到黑洞中心的距离
        theta: 观测角 — 粒子方向与视线方向的夹角。
                0 = 朝向观测者 (蓝移/增亮)
                π = 远离观测者 (红移/变暗)
        v_frac: 实际速度占轨道速度的比例 [0,1]
    
    返回:
        doppler_factor — 光强倍增因子。>1 表示更亮，<1 表示更暗。
    
    公式:  D = sqrt((1 - β²) / (1 - β cos θ)²)  ×  1 / (1 + z_g)
    
    史瓦西度规下的近似（包含引力红移和相对论多普勒）：
    I_obs / I_emit = (1 + z)^{-3}  其中 z 包含多普勒和引力红移
    """
    beta = newtonian_orbital_speed(r) * v_frac
    gamma = 1.0 / math.sqrt(max(1.0 - beta * beta, 0.01))
    
    # 多普勒因子
    cos_theta = math.cos(theta)
    doppler = 1.0 / (gamma * (1.0 - beta * cos_theta) + 0.001)
    
    # 叠加引力红移衰减
    z_g = gravitational_redshift(r)
    grav_dimming = 1.0 / ((1.0 + z_g) ** 2 + 0.01)
    
    return doppler * grav_dimming


# ═══════════════════════════════════════════════════════════════
#  区域判定
# ═══════════════════════════════════════════════════════════════

def region_of(r: float) -> str:
    """
    判定某半径处于黑洞的哪个区域：
        'singularity'  — 奇点 (r ≈ 0)
        'inside_horizon' — 视界内
        'photon_sphere' — 光子球区域
        'plunging' — 坠入区 (ISCO 以内)
        'disk' — 吸积盘区域
        'outer' — 远区
    """
    if r < BL_SCHWARZSCHILD_R * 0.1:
        return 'singularity'
    if r < BL_SCHWARZSCHILD_R:
        return 'inside_horizon'
    if r < BL_PHOTON_SPHERE_R:
        return 'photon_sphere'
    if r < BL_ISCO_R:
        return 'plunging'
    if r < BL_DISK_OUTER_R:
        return 'disk'
    return 'outer'


def accretion_temperature(r: float) -> float:
    """
    吸积盘温度曲线 (简化模型)
    标准薄盘: T ∝ r^{-3/4}
    返回归一化温度 [0, 1]
    """
    if r < BL_ISCO_R:
        return 0.0
    if r > BL_DISK_OUTER_R:
        return 0.0
    # T ∝ r^{-3/4}，在 ISCO 处最热
    t_inner = BL_ISCO_R ** -0.75
    t_outer = BL_DISK_OUTER_R ** -0.75
    t_raw = (r ** -0.75 - t_outer) / (t_inner - t_outer + 0.001)
    return max(0.0, min(1.0, t_raw))


# ═══════════════════════════════════════════════════════════════
#  黑洞阴影 (EHT 风格)
# ═══════════════════════════════════════════════════════════════

def shadow_alpha(r: float) -> int:
    """
    EHT 观测到的阴影特征：
    - 视界内：完全不透明 (alpha=255)
    - 视界 → 光子球：快速过渡
    - 光子球附近：半透明光环
    - 光子球外：逐渐透明
    
    返回 alpha [0, 255]
    """
    if r <= BL_SCHWARZSCHILD_R * 0.95:
        return 255
    if r <= BL_SCHWARZSCHILD_R:
        # 视界边缘微弱辉光（霍金辐射暗示）
        t = (r - BL_SCHWARZSCHILD_R * 0.95) / (BL_SCHWARZSCHILD_R * 0.05)
        return int(255 * (1.0 - t * 0.3))
    if r <= BL_PHOTON_SPHERE_R:
        # 光子球区域，过渡带
        t = (r - BL_SCHWARZSCHILD_R) / (BL_PHOTON_SPHERE_R - BL_SCHWARZSCHILD_R)
        return int(180 * (1.0 - t))
    # 光子球外渐变透明
    falloff_r = BL_PHOTON_SPHERE_R + BL_SCHWARZSCHILD_R * 0.3
    if r < falloff_r:
        return int(30 * (1.0 - (r - BL_PHOTON_SPHERE_R) / (falloff_r - BL_PHOTON_SPHERE_R)))
    return 0
