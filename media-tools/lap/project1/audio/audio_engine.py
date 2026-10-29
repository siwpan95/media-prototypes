import pygame
import numpy as np
import threading
import time
from .sfx_layer import SFXLayer
from .external_sfx import ExternalSFX

class AudioEngine:
    def __init__(self):
        pygame.mixer.init(frequency=44100, channels=4, buffer=256)
        self.external = ExternalSFX()
        self.sfx = SFXLayer()

        # 音频通道
        self.channels = {
            "motor": pygame.mixer.Channel(0),
            "wind":  pygame.mixer.Channel(1),
            "env":    pygame.mixer.Channel(2),
            "fault":  pygame.mixer.Channel(3)
        }

        # 状态
        self.speed = 0.0
        self.wind_speed = 5.0   # 0-10，默认 5
        self.joke_mode = False
        self.is_running = False
        self.stop_flag = False
        self.thread = None

    # ── 公共接口 ──────────────────────────────────────────────
    def start(self):
        self.is_running = True
        self.stop_flag = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self._play_env()

    def stop(self):
        self.is_running = False
        self.stop_flag = True
        for ch in self.channels.values():
            ch.stop()

    def set_speed(self, speed):
        self.speed = speed

    def set_wind_speed(self, ws):
        self.wind_speed = ws

    def toggle_joke_mode(self):
        """切换恶搞音效；返回切换后的状态"""
        self.joke_mode = not self.joke_mode
        if self.joke_mode:
            self.external.reload("assets/sfx_joke")
        else:
            self.external.reload(None)
        # 重新播放环境音（采样已换）
        self.channels["env"].stop()
        self._play_env()
        return self.joke_mode

    def play_transient(self, name):
        sample = self.external.get_sample("transient", name)
        if sample:
            sample.play()

    def play_fault(self, fault_type):
        mapping = {"bearing": "bearing_fail",
                   "blade":   "wobble",
                   "motor":   "scrape"}
        name = mapping.get(fault_type)
        if name:
            sample = self.external.get_sample("fault", name)
            if sample:
                self.channels["fault"].play(sample)

    # ── 内部方法 ──────────────────────────────────────────────
    def _play_env(self):
        sample = self.external.get_sample("env", "room_tone")
        if sample:
            self.channels["env"].play(sample, loops=-1)
            self.channels["env"].set_volume(0.3)

    def _loop(self):
        while not self.stop_flag:
            if self.is_running:
                self._update()
            time.sleep(0.05)

    def _update(self):
        sn = min(1.0, self.speed / 10.0)      # speed 归一化
        wn = min(1.0, self.wind_speed / 10.0) # wind  归一化

        # 电机声
        samp = self._choose_sample(sn)
        if samp:
            self.channels["motor"].play(samp, loops=-1)
            self.channels["motor"].set_volume(0.7 + sn * 0.3)

        # 风声（受风速滑块控制）
        wind = self.external.get_sample("env", "wind_noise")
        if wind:
            self.channels["wind"].play(wind, loops=-1)
            self.channels["wind"].set_volume(wn * 0.5)

    def _choose_sample(self, sn):
        if sn < 0.3:
            return self.external.get_sample("fan", "idle_1")
        elif sn < 0.6:
            return self.external.get_sample("fan", "low_2")
        elif sn < 0.9:
            return self.external.get_sample("fan", "medium_3")
        else:
            return self.external.get_sample("fan", "high_4")
