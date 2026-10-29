import numpy as np
import pygame
from scipy import signal

class SFXLayer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def apply_doppler(self, audio_data, speed, prev_speed):
        """应用多普勒效应"""
        speed_diff = speed - prev_speed
        doppler_factor = 1.0 + speed_diff * 0.01
        
        # 重采样实现多普勒频移
        new_length = int(len(audio_data) / doppler_factor)
        indices = np.linspace(0, len(audio_data)-1, new_length)
        resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)
        
        return resampled
    
    def apply_formant_filter(self, audio_data, speed):
        """应用共振峰变化"""
        # 根据速度选择共振峰频率
        formant_freq = 400 + speed * 200
        
        # 设计带通滤波器
        nyquist = self.sample_rate / 2
        low = (formant_freq - 100) / nyquist
        high = (formant_freq + 100) / nyquist
        
        b, a = signal.butter(2, [low, high], 'band')
        filtered = signal.filtfilt(b, a, audio_data)
        
        return filtered
    
    def apply_pitch_shift(self, audio_data, pitch_factor):
        """音高变换"""
        # 简单重采样实现音高变换
        new_length = int(len(audio_data) / pitch_factor)
        indices = np.linspace(0, len(audio_data)-1, new_length)
        return np.interp(indices, np.arange(len(audio_data)), audio_data)