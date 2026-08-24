"""Windows桌面壁纸嵌入模块。

使用 Win32 API 将 pygame 窗口放置到 Windows 桌面图标**背后**，
实现真正的动态桌面壁纸效果，而非仅仅全屏覆盖。

工作原理：
  1. 获取 SDL2 窗口的原生 HWND
  2. 修改窗口扩展样式：隐藏任务栏图标、防止激活
  3. 将窗口钉在 Z 序最底层（HWND_BOTTOM）
  4. 可选：嵌入到 WorkerW 桌面窗口之下
  5. 在主循环中周期性重新钉住，防止被其他窗口推上来
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys
import time

# ── Win32 API 常量 ──────────────────────────────────────────────
HWND_BOTTOM: int = 1
HWND_NOTOPMOST: int = -2
HWND_TOP: int = 0

SWP_NOSIZE: int = 0x0001
SWP_NOMOVE: int = 0x0002
SWP_NOACTIVATE: int = 0x0010
SWP_SHOWWINDOW: int = 0x0040
SWP_NOZORDER: int = 0x0004
SWP_NOSENDCHANGING: int = 0x0400

GWL_EXSTYLE: int = -20
GWL_STYLE: int = -16

WS_EX_TOOLWINDOW: int = 0x00000080
WS_EX_NOACTIVATE: int = 0x08000000
WS_EX_APPWINDOW: int = 0x00040000
WS_EX_TRANSPARENT: int = 0x00000020

WS_CHILD: int = 0x40000000
WS_POPUP: int = 0x80000000

# 重新钉住间隔（秒）
_REPIN_INTERVAL: float = 0.5


def _is_windows() -> bool:
    return sys.platform == "win32"


def get_sdl_hwnd(pygame_surface) -> int:
    """从 pygame surface 获取原生 Windows HWND。"""
    if not _is_windows():
        return 0
    try:
        wm_info = pygame_surface.get_wm_info()
        return int(wm_info.get("window", 0))
    except Exception:
        return 0


def _find_workerw() -> int | None:
    """查找 WorkerW 桌面窗口（图标和壁纸之间的层）。"""
    user32 = ctypes.windll.user32

    # 1) 找到 Progman（程序管理器，桌面根窗口）
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        return None

    # 2) 发送 0x052C 消息，触发系统创建 WorkerW
    result = ctypes.c_void_p()
    user32.SendMessageTimeoutW(
        progman, 0x052C, 0, 0, 0x0002, 1000, ctypes.byref(result),
    )

    # 3) 枚举所有 WorkerW
    worker_hwnds: list[int] = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _enum(hwnd, _lparam):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        if buf.value == "WorkerW":
            worker_hwnds.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(_enum), 0)

    # 4) 找到那个包含 SHELLDLL_DefView 的 WorkerW（即桌面图标所在层）
    for hwnd in worker_hwnds:
        defview = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
        if defview:
            # 这是图标层的父窗口，我们的窗口应该放在它之前
            return hwnd

    return None


class DesktopWallpaper:
    """管理 pygame 窗口作为桌面壁纸的生命周期。"""

    def __init__(self, pygame_surface):
        self._hwnd: int = 0
        self._screen_width: int = 0
        self._screen_height: int = 0
        self._active: bool = False
        self._worker_hwnd: int | None = None
        self._last_repin: float = 0.0
        self._original_exstyle: int = 0
        self._original_style: int = 0

        if not _is_windows():
            return

        self._hwnd = get_sdl_hwnd(pygame_surface)
        if not self._hwnd:
            print("[Wallpaper] ⚠ 无法获取 SDL 窗口句柄")
            return

        # 获取屏幕尺寸
        self._screen_width = ctypes.windll.user32.GetSystemMetrics(0)   # SM_CXSCREEN
        self._screen_height = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN

    def activate(self) -> bool:
        """激活桌面壁纸模式。返回是否成功。"""
        if not self._hwnd:
            return False

        user32 = ctypes.windll.user32

        try:
            # 保存原始样式
            self._original_exstyle = user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
            self._original_style = user32.GetWindowLongW(self._hwnd, GWL_STYLE)

            # 修改扩展样式：隐藏任务栏、防激活
            new_exstyle = self._original_exstyle
            new_exstyle |= WS_EX_TOOLWINDOW   # 不在任务栏显示
            new_exstyle |= WS_EX_NOACTIVATE    # 不接受焦点
            new_exstyle &= ~WS_EX_APPWINDOW    # 不是应用窗口
            user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, new_exstyle)

            # 尝试嵌入 WorkerW（桌面图标背后）
            self._worker_hwnd = _find_workerw()
            if self._worker_hwnd:
                user32.SetParent(self._hwnd, self._worker_hwnd)
                print(f"[Wallpaper] ✅ 已嵌入桌面 WorkerW 层 ({self._worker_hwnd})")
            else:
                print("[Wallpaper] ℹ 未找到 WorkerW，使用 Z 序底层模式")

            # 将窗口移到最底层
            user32.SetWindowPos(
                self._hwnd,
                HWND_BOTTOM if not self._worker_hwnd else 0,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )

            # 如果不是嵌入模式，确保窗口盖满整个桌面
            if not self._worker_hwnd:
                user32.SetWindowPos(
                    self._hwnd, HWND_BOTTOM,
                    0, 0,
                    self._screen_width, self._screen_height,
                    SWP_NOACTIVATE,
                )

            self._active = True
            self._last_repin = time.monotonic()
            print(f"[Wallpaper] ✅ 桌面壁纸模式已激活 ({self._screen_width}x{self._screen_height})")
            return True

        except Exception as e:
            print(f"[Wallpaper] ❌ 激活失败: {e}")
            return False

    def deactivate(self) -> None:
        """停用壁纸模式，恢复窗口原始状态。"""
        if not self._hwnd or not self._active:
            return

        user32 = ctypes.windll.user32

        try:
            # 恢复原始样式
            user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, self._original_exstyle)
            user32.SetWindowLongW(self._hwnd, GWL_STYLE, self._original_style)

            # 如果之前嵌入了 WorkerW，恢复父窗口为桌面
            if self._worker_hwnd:
                user32.SetParent(self._hwnd, 0)

            self._active = False
            print("[Wallpaper] 壁纸模式已停用")

        except Exception as e:
            print(f"[Wallpaper] 停用失败: {e}")

    def repin(self) -> None:
        """周期性调用，确保窗口保持在最底层不被推上来。"""
        if not self._hwnd or not self._active:
            return

        now = time.monotonic()
        if now - self._last_repin < _REPIN_INTERVAL:
            return
        self._last_repin = now

        user32 = ctypes.windll.user32

        try:
            # 仅在非嵌入模式下需要重新钉住
            if not self._worker_hwnd:
                user32.SetWindowPos(
                    self._hwnd, HWND_BOTTOM,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOSENDCHANGING,
                )
        except Exception:
            pass  # 静默忽略周期性操作的错误

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def hwnd(self) -> int:
        return self._hwnd


# ── 便捷函数 ───────────────────────────────────────────────────

def create_wallpaper(pygame_surface) -> DesktopWallpaper:
    """创建桌面壁纸管理器实例。"""
    return DesktopWallpaper(pygame_surface)
