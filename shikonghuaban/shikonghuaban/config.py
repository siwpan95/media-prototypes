"""
时空画板 — 全局配置

所有可调参数收敛到 :class:`Config` dataclass（单一真相）。模块级常量
(WIDTH/HEIGHT/CENTER/BL_* 等) 保留为向后兼容的快照，全仓既有的
``from .config import WIDTH`` 顶層导入无需改动。

外部化入口：
    - ``Config.from_dict({...})`` / ``Config.from_toml("cfg.toml")`` 覆盖生成新实例
    - ``load_config(source)`` 将覆盖写回全局单例 ``get_config()`` 并同步模块级常量
    - ``get_config()`` 返回全局单例
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


@dataclass
class Config:
    # ==================== 显示 ====================
    width: int = 1920
    height: int = 1080
    bg: Tuple[int, int, int] = (0, 0, 0)
    horizon: Tuple[int, int, int] = (80, 80, 100)
    singularity: Tuple[int, int, int] = (140, 35, 35)
    color: Tuple[int, int, int] = (180, 70, 70)

    # ==================== 黑洞物理常量 (屏幕坐标尺度) ====================
    # 史瓦西半径 (视界半径)，以屏幕像素为单位
    bl_schwarzschild_r: float = 180.0
    # 引力透镜缩放
    bl_lens_strength: float = 2.0
    # 多普勒束流强度
    bl_doppler_strength: float = 0.6
    # 派生量 (由 r_s 推出，禁止手动传参)
    bl_photon_sphere_r: float = field(init=False, default=0.0)   # = r_s * 1.5
    bl_isco_r: float = field(init=False, default=0.0)            # = r_s * 3.0
    bl_disk_outer_r: float = field(init=False, default=0.0)      # = r_s * 10.0

    # ==================== 音频 ====================
    sr: int = 44100
    bpm: int = 118
    vol: float = 0.12
    notes: Dict[str, float] = field(default_factory=lambda: {
        "C4": 261.63, "Eb": 311.13, "E": 329.63,
        "Gb": 369.99, "G": 392.00, "A": 440.00,
        "Bb": 466.16, "B": 493.88, "C5": 523.25,
    })
    riff: List = field(default_factory=lambda: ["C4", "Eb", "E", "Gb", "G", "A", "Bb", "C5"])
    verse: List = field(default_factory=lambda: ["A", "A", "A", "G", None, "E", "G", "G"])
    chorus: List = field(default_factory=lambda: ["C5", "C5", "C5", "B", "C5", "A", "G", "E"])

    def __post_init__(self):
        self._recompute_derived()

    # BEAT 是 BPM 的派生量（property，不占据 dataclass 字段）
    @property
    def beat(self) -> float:
        return 60.0 / self.bpm

    # —— 序列化 / 覆盖 ——
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Config":
        """只接受已知字段，忽略未知键，派生量交给 __post_init__ 重算。"""
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)

    @classmethod
    def from_toml(cls, path: str) -> "Config":
        if tomllib is None:
            raise RuntimeError("tomllib 不可用（需要 Python 3.11+）")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        # 容忍 [shikonghuaban] 小节或直接平铺
        section = data.get("shikonghuaban", data)
        return cls.from_dict(section)

    def override(self, **kwargs) -> None:
        """就地覆盖字段并重算派生量（用于运行时微调）。"""
        for k, v in kwargs.items():
            if k not in self.__dataclass_fields__:
                raise KeyError(f"未知配置项: {k}")
            setattr(self, k, v)
        self._recompute_derived()

    def _recompute_derived(self) -> None:
        self.bl_photon_sphere_r = self.bl_schwarzschild_r * 1.5
        self.bl_isco_r = self.bl_schwarzschild_r * 3.0
        self.bl_disk_outer_r = self.bl_schwarzschild_r * 10.0


# ==================== 全局单例 ====================
_config = Config()


def get_config() -> Config:
    """返回全局配置单例（外部化主入口）。"""
    return _config


def load_config(source=None):
    """将 dict / .toml 路径的覆盖写回全局单例并同步模块级常量。

    - ``source=None`` 原样返回单例（无操作）。
    - ``source=dict`` 用 ``Config.from_dict`` 生成覆盖实例。
    - ``source="x.toml"`` 用 ``Config.from_toml`` 加载。
    返回更新后的单例。
    """
    if source is None:
        return _config
    if isinstance(source, dict):
        cfg = Config.from_dict(source)
    elif isinstance(source, str):
        cfg = Config.from_toml(source)
    else:
        raise TypeError("source 必须是 dict 或 .toml 路径字符串")
    _config.__dict__.update(cfg.__dict__)
    _reexport()
    return _config


# ==================== 向后兼容：模块级常量快照 ====================
# 注意：这些是 import 时的静态绑定。已 ``from .config import WIDTH`` 的模块
# 不会热更新（Python 语义）；运行时热重载应改用 ``config.get_config().width``
# 或 ``config.WIDTH``（本模块属性，随 _reexport 同步）。
def _reexport() -> None:
    global WIDTH, HEIGHT, CENTER, BG, HORIZON, SINGULARITY, COLOR
    global BL_SCHWARZSCHILD_R, BL_PHOTON_SPHERE_R, BL_ISCO_R, BL_DISK_OUTER_R
    global BL_LENS_STRENGTH, BL_DOPPLER_STRENGTH
    global SR, BPM, BEAT, VOL, NOTES, RIFF, VERSE, CHORUS
    WIDTH = _config.width
    HEIGHT = _config.height
    CENTER = (WIDTH // 2, HEIGHT // 2)
    BG = _config.bg
    HORIZON = _config.horizon
    SINGULARITY = _config.singularity
    COLOR = _config.color
    BL_SCHWARZSCHILD_R = _config.bl_schwarzschild_r
    BL_PHOTON_SPHERE_R = _config.bl_photon_sphere_r
    BL_ISCO_R = _config.bl_isco_r
    BL_DISK_OUTER_R = _config.bl_disk_outer_r
    BL_LENS_STRENGTH = _config.bl_lens_strength
    BL_DOPPLER_STRENGTH = _config.bl_doppler_strength
    SR = _config.sr
    BPM = _config.bpm
    BEAT = _config.beat
    VOL = _config.vol
    NOTES = _config.notes
    RIFF = _config.riff
    VERSE = _config.verse
    CHORUS = _config.chorus


_reexport()
