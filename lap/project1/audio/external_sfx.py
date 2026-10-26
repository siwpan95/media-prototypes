import pygame
import os
import sys


def _get_asset_path(relative_path):
    """获取资源路径，兼容开发环境和 PyInstaller 打包"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


class ExternalSFX:
    def __init__(self):
        pygame.mixer.init(frequency=44100, channels=2)
        self.base_path = _get_asset_path("assets/sfx")
        self.samples = {}
        self.load_samples()

    def _try_load(self, category, name):
        """尝试加载音频采样，先 .wav 再 .mp3"""
        for ext in (".wav", ".mp3"):
            path = os.path.join(self.base_path, category, f"{name}{ext}")
            if os.path.exists(path):
                return pygame.mixer.Sound(path)
        return None

    def load_samples(self):
        """加载所有外部采样"""
        categories = {
            "fan": ["idle_1", "low_2", "medium_3", "high_4"],
            "transient": ["startup", "shutdown", "click_on", "click_off"],
            "fault": ["wobble", "scrape", "bearing_fail"],
            "env": ["room_tone", "wind_noise"]
        }

        for category, files in categories.items():
            self.samples[category] = {}
            for name in files:
                sample = self._try_load(category, name)
                if sample:
                    self.samples[category][name] = sample

    def reload(self, base_path):
        """切换音效目录（用于 joke/normal 模式切换）"""
        if base_path is None:
            self.base_path = _get_asset_path("assets/sfx")
        else:
            self.base_path = _get_asset_path(base_path)
        self.samples = {}
        self.load_samples()

    def get_sample(self, category, name):
        """获取采样"""
        return self.samples.get(category, {}).get(name)

    def play_sample(self, category, name, volume=1.0):
        """播放采样"""
        sample = self.get_sample(category, name)
        if sample:
            sample.set_volume(volume)
            sample.play()
