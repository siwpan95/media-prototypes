"""
E 配置外部化单元测试 (headless)。

验证：
  - 默认值正确（含 r_s 派生量）
  - 模块级常量与单例一致（向后兼容）
  - Config.from_dict 覆盖 + 派生量重算
  - load_config 写回单例并同步模块级常量（含复位）
"""

import pytest

import shikonghuaban.config as config
from shikonghuaban.config import Config, get_config, load_config


def test_defaults():
    c = get_config()
    assert c.width == 1920
    assert c.height == 1080
    assert c.bl_schwarzschild_r == 180.0
    # 派生量由 __post_init__ 计算
    assert c.bl_photon_sphere_r == 270.0   # 180 * 1.5
    assert c.bl_isco_r == 540.0            # 180 * 3.0
    assert c.bl_disk_outer_r == 1800.0     # 180 * 10.0
    assert c.beat == pytest.approx(60.0 / 118)


def test_module_constants_aliased_and_compatible():
    # 既有 from .config import WIDTH 的消费者看到的快照正确
    assert config.WIDTH == 1920
    assert config.HEIGHT == 1080
    assert config.CENTER == (960, 540)
    assert config.BL_PHOTON_SPHERE_R == 270.0
    assert config.NOTES["C5"] == 423.25 or config.NOTES["C5"] == 523.25


def test_from_dict_override_recomputes_derived():
    c = Config.from_dict({"width": 800, "bl_schwarzschild_r": 90.0})
    assert c.width == 800
    # 派生量随 r_s 变化重算
    assert c.bl_photon_sphere_r == 135.0   # 90 * 1.5
    assert c.bl_isco_r == 270.0            # 90 * 3.0
    assert c.bl_disk_outer_r == 900.0      # 90 * 10.0
    # 无关字段保留默认
    assert c.height == 1080
    assert c.bl_lens_strength == 2.0


def test_from_dict_ignores_unknown_keys():
    c = Config.from_dict({"width": 640, "totally_unknown": 999})
    assert c.width == 640
    assert not hasattr(c, "totally_unknown")


def test_load_config_updates_singleton_and_module_constants():
    try:
        load_config({"width": 800, "bl_schwarzschild_r": 90.0})
        # 单例与模块级常量同步
        assert get_config().width == 800
        assert config.WIDTH == 800
        assert config.CENTER == (400, 540)
        assert config.BL_PHOTON_SPHERE_R == 135.0
    finally:
        # 复位到干净默认
        load_config({})
        assert get_config().width == 1920
        assert config.WIDTH == 1920
        assert config.CENTER == (960, 540)


def test_from_toml(tmp_path):
    toml_path = tmp_path / "cfg.toml"
    toml_path.write_text(
        "[shikonghuaban]\nwidth = 1024\nbl_schwarzschild_r = 120.0\n",
        encoding="utf-8",
    )
    c = Config.from_toml(str(toml_path))
    assert c.width == 1024
    assert c.bl_schwarzschild_r == 120.0
    assert c.bl_photon_sphere_r == 180.0   # 120 * 1.5
