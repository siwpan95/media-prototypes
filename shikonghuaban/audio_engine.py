"""
时空画板 — 音频引擎

在独立线程中通过 sounddevice 生成锯齿波音频，
按预编序列播放音符并将 RMS 音量写入共享状态。
"""

import logging
import numpy as np
import sounddevice as sd
from .config import SR, VOL, NOTES
from .state import shared_state


class AudioEngine:
    """锯齿波合成器，按预编序列播放"""

    def __init__(self):
        self.stream = None
        self.running = False
        self.phase = 0.0

    # ── 波形生成 ──

    @staticmethod
    def saw(t, f):
        return 2 * ((t * f) % 1.0) - 1

    @staticmethod
    def env(n):
        # att/rel 下限取 1，避免 n 较小时（如 n<5）取整为 0 导致
        # e[:0] / e[-0:] 切片形状不匹配而崩溃；生产 blocksize=1024 不受影响。
        att = max(1, int(0.01 * n))
        rel = max(1, int(0.2 * n))
        e = np.ones(n)
        e[:att] = np.linspace(0, 1, att)
        e[-rel:] = np.linspace(1, 0, rel)
        return e

    # ── 音符序列 ──

    def get_next_note(self):
        with shared_state.lock:
            pat, octv = shared_state.patterns[shared_state.section]
            idx = int(shared_state.beat) % len(pat)
            note = pat[idx]

            shared_state.beat += 0.5
            if shared_state.beat >= len(pat) * 2:
                shared_state.beat = 0
                shared_state.section = (
                    shared_state.section + 1
                ) % len(shared_state.patterns)

            return note, octv

    # ── sounddevice 回调（连续相位，避免爆音） ──

    def audio_callback(self, outdata, frames, time_info, status):
        if status:
            logging.getLogger("audio_engine").warning("audio callback status: %s", status)
        note, octv = self.get_next_note()
        if note is None:
            outdata[:] = np.zeros((frames, 1), dtype=np.float32)
            return
        f = NOTES[note] * (2 ** octv)
        n = np.arange(frames)
        phase = self.phase + 2.0 * np.pi * f * n / SR
        sig = 2.0 * ((phase / (2.0 * np.pi)) % 1.0) - 1.0   # 连续锯齿波
        self.phase += 2.0 * np.pi * f * frames / SR
        sig = sig * self.env(frames)
        rms = float(np.sqrt(np.mean(sig ** 2)))
        with shared_state.lock:
            shared_state.volume = min(rms * 5.0, 1.0)
        outdata[:] = (sig * VOL).reshape(-1, 1).astype(np.float32)

    # ── 生命周期 ──

    def start(self):
        self.running = True
        self.phase = 0.0
        self.stream = sd.OutputStream(
            samplerate=SR, channels=1, dtype='float32',
            callback=self.audio_callback,
            blocksize=1024, latency='low',
        )
        self.stream.start()
        print("音频引擎已启动")

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("音频引擎已停止")
