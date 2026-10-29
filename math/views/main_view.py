"""视图层 - 主视图"""
import pygame
import numpy as np
from constants import BG_DARK, PREVIEW_W, HEIGHT


class MainView:
    """主视图 - 处理渲染"""

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.Font(None, 18)
        self.TEXT_COLOR = (220, 220, 230)
        self.ERROR_COLOR = (255, 100, 100)

    def render_grid(self, display_array: np.ndarray):
        """渲染网格预览"""
        display_array = (np.clip(display_array, 0, 1) * 255).astype(np.uint8)
        surface = pygame.surfarray.make_surface(
            np.stack([display_array] * 3, axis=-1)
        )
        surface = pygame.transform.scale(surface, (PREVIEW_W, HEIGHT))
        self.screen.blit(surface, (0, 0))

    def render_overlay(self, fps: float, iteration: int, error_msg: str = ""):
        """渲染叠加信息（FPS、迭代次数、错误）"""
        # FPS
        fps_text = self.font.render(f"FPS: {int(fps)}", True, self.TEXT_COLOR)
        self.screen.blit(fps_text, (5, 5))

        # 迭代次数
        iter_text = self.font.render(f"Iter: {iteration}", True, self.TEXT_COLOR)
        self.screen.blit(iter_text, (5, 28))

        # 错误信息
        if error_msg:
            err_surf = self.font.render(error_msg, True, self.ERROR_COLOR)
            self.screen.blit(err_surf, (5, 51))

    def clear(self):
        """清屏"""
        self.screen.fill(BG_DARK)
