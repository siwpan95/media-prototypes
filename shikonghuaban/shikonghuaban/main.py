"""
时空画板 — 入口

24-Hour Spacetime Audio — 粒子增强版
基于 Penrose 几何的全屏音频可视化，集成 particle 粒子工具包。
"""

import logging
import sys
import pygame

from .audio_engine import AudioEngine
from .visual_engine import VisualEngine


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("fat.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _excepthook(exc_type, exc_value, exc_tb):
    logging.getLogger("main").exception(
        "未捕获异常", exc_info=(exc_type, exc_value, exc_tb)
    )
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    setup_logging()
    log = logging.getLogger("main")
    sys.excepthook = _excepthook

    print("启动 24 小时时空画板系统 — 粒子增强版...")
    print("=" * 50)
    print("控制说明:")
    print("  ESC   - 退出")
    print("  ↑ / ↓ - 调节音量")
    print("  SPACE - 切换显示模式")
    print("=" * 50)

    audio = AudioEngine()
    audio_ok = False
    try:
        audio.start()
        audio_ok = True
    except Exception as e:
        log.warning("音频引擎启动失败，进入纯视觉模式: %s", e)
        print("⚠ 音频不可用，已切换为纯视觉模式（无声音）。")

    try:
        visual = VisualEngine()
    except Exception:
        log.exception("可视化引擎初始化失败")
        print("❌ 可视化引擎初始化失败，程序退出。")
        if audio_ok:
            try:
                audio.stop()
            except Exception:
                pass
        pygame.quit()
        return

    try:
        visual.run()
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        if audio_ok:
            try:
                audio.stop()
            except Exception:
                pass
        pygame.quit()
        log.info("system closed")


if __name__ == "__main__":
    main()
