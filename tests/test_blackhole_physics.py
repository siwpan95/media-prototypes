"""
Unit tests for the pure black-hole physics helpers in blackhole_physics.py.

These functions depend only on ``math`` + config constants, so they run
headlessly with no display or audio backend. Exact signatures / return values
were read from the source module.
"""

import math

from shikonghuaban import blackhole_physics as bh

# Mirror the config constants the module is built around so the expected
# region boundaries are explicit (kept in sync with config.py).
CENTER = (960, 540)
RS = 180.0          # BL_SCHWARZSCHILD_R
PHOTON = 270.0      # BL_PHOTON_SPHERE_R = 1.5 * RS
ISCO = 540.0        # BL_ISCO_R = 3 * RS
DISK_OUTER = 1800.0 # BL_DISK_OUTER_R = 10 * RS


# ── dist_to_bh ──

def test_dist_to_bh_at_center_is_zero():
    assert bh.dist_to_bh(CENTER[0], CENTER[1]) == 0.0


def test_dist_to_bh_axis_aligned_offsets():
    assert bh.dist_to_bh(CENTER[0] + 300, CENTER[1]) == 300.0
    assert bh.dist_to_bh(CENTER[0], CENTER[1] - 400) == 400.0


def test_dist_to_bh_diagonal_is_euclidean():
    r = bh.dist_to_bh(CENTER[0] + 3, CENTER[1] + 4)
    assert math.isclose(r, 5.0)


def test_dist_to_bh_negative_offset():
    r = bh.dist_to_bh(CENTER[0] - 3, CENTER[1] + 4)
    assert math.isclose(r, 5.0)


# ── shadow_alpha ──

def test_shadow_alpha_opaque_at_and_near_center():
    assert bh.shadow_alpha(0) == 255
    assert bh.shadow_alpha(RS * 0.5) == 255
    assert bh.shadow_alpha(RS * 0.95) == 255  # boundary of opaque band


def test_shadow_alpha_transparent_far_out():
    assert bh.shadow_alpha(DISK_OUTER) == 0
    assert bh.shadow_alpha(10_000) == 0


def test_shadow_alpha_outer_falloff_band():
    # PHOTON(270) < r <= falloff_r(324): fades 30 -> 0
    radii = [PHOTON + 6 * i for i in range(1, 10)]  # 276 .. 324
    alphas = [bh.shadow_alpha(r) for r in radii]
    assert alphas == sorted(alphas, reverse=True)
    assert alphas[0] <= 30 and alphas[-1] == 0


def test_shadow_alpha_inner_transition_decreasing():
    # 0.95*RS < r <= RS: strictly decreasing (255 -> ~178)
    radii = [RS * 0.95 + i for i in range(1, 10)]  # 171.1 .. 179.1
    alphas = [bh.shadow_alpha(r) for r in radii]
    assert alphas == sorted(alphas, reverse=True)
    assert all(170 <= a <= 255 for a in alphas)


def test_shadow_alpha_photon_sphere_band_decreasing():
    # RS < r <= PHOTON: strictly decreasing (180 -> 0)
    radii = [RS + 5 * i for i in range(1, 19)]  # 185 .. 270
    alphas = [bh.shadow_alpha(r) for r in radii]
    assert alphas == sorted(alphas, reverse=True)
    assert alphas[0] <= 180 and alphas[-1] == 0


def test_shadow_alpha_in_range_and_integer():
    for r in (0, 50, 171, 180, 200, 270, 300, 350, 500, 2000):
        a = bh.shadow_alpha(r)
        assert isinstance(a, int)
        assert 0 <= a <= 255


# ── region_of ──

def test_region_of_singularity():
    assert bh.region_of(0) == "singularity"
    assert bh.region_of(10) == "singularity"  # < 0.1 * RS


def test_region_of_inside_horizon():
    assert bh.region_of(100) == "inside_horizon"  # 0.1*RS <= r < RS
    assert bh.region_of(RS - 0.1) == "inside_horizon"


def test_region_of_photon_sphere():
    # Exactly RS falls into the photon_sphere band (boundary is exclusive).
    assert bh.region_of(RS) == "photon_sphere"
    assert bh.region_of(PHOTON - 0.1) == "photon_sphere"


def test_region_of_plunging():
    # Exactly PHOTON falls into plunging (ISCO-inner) band.
    assert bh.region_of(PHOTON) == "plunging"
    assert bh.region_of(ISCO - 0.1) == "plunging"


def test_region_of_disk():
    # Exactly ISCO falls into the disk band.
    assert bh.region_of(ISCO) == "disk"
    assert bh.region_of(DISK_OUTER - 0.1) == "disk"


def test_region_of_outer():
    # Exactly DISK_OUTER and beyond fall into the outer region.
    assert bh.region_of(DISK_OUTER) == "outer"
    assert bh.region_of(10_000) == "outer"
