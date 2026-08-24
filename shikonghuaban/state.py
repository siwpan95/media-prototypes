"""
时空画板 — 共享状态

线程安全的数据桥梁，连接音频线程和渲染线程。
"""

import threading
from .config import RIFF, VERSE, CHORUS


class SharedState:
    """音频线程 ←→ 渲染线程 的数据桥梁"""

    def __init__(self):
        self.lock = threading.Lock()
        self.volume = 0.5
        self.beat = 0
        self.section = 0
        self.patterns = [
            (RIFF, -1),
            (VERSE, 0),
            (CHORUS, 0),
            (RIFF, 1),
            (CHORUS, 0),
        ]


# 全局单例
shared_state = SharedState()
