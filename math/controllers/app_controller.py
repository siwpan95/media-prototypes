"""控制器层 - 应用控制器"""
import numpy as np
import pygame
import pygame_gui
from tkinter import Tk, filedialog
from models import GridState, FormulaEngine
from views import MainView, SidebarView
from constants import *


class AppController:
    """应用控制器 - 协调 Model 和 View"""

    def __init__(self):
        # 初始化 pygame
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cellular Automata - Formula Lab")
        self.clock = pygame.time.Clock()

        # 初始化 Manager
        self.manager = pygame_gui.UIManager((WIDTH, HEIGHT))

        # 初始化 Model
        self.grid_state = GridState(GRID_W, GRID_H, CELL_SIZE)
        self.formula_engine = FormulaEngine()

        # 初始化 View
        self.main_view = MainView(self.screen, self.clock)
        self.sidebar_view = SidebarView(self.manager, PREVIEW_W, PANEL_WIDTH, HEIGHT)

        # 更新UI
        self._update_ui()

        # 状态
        self.running = True
        self.error_msg = ""

    def _update_ui(self):
        """更新UI显示"""
        self.sidebar_view.update_formula_text(self.formula_engine.formula_name)
        self.sidebar_view.update_params(Du, Dv, F, k, dt)
        self.sidebar_view.update_grid_info(GRID_W, GRID_H)

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            self.manager.process_events(event)

            action = self.sidebar_view.process_event(event)
            if action == 'load':
                self._on_load_formula()
            elif action == 'template':
                self._on_generate_template()
            elif action == 'default':
                self._on_restore_default()

    def _on_load_formula(self):
        """加载公式"""
        success = self.formula_engine.load_from_file()
        if success:
            self.sidebar_view.update_formula_text(self.formula_engine.formula_name)
            self._reset_simulation()
        else:
            self.sidebar_view.show_error("Load cancelled or failed")

    def _on_generate_template(self):
        """生成模板"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.asksaveasfilename(
            title="Save Formula Template",
            defaultextension=".py",
            filetypes=[("Python files", "*.py")],
            initialfile="my_formula.py"
        )
        root.destroy()

        if file_path:
            if self.formula_engine.generate_template(file_path):
                self.sidebar_view.show_message("Template Generated")
            else:
                self.sidebar_view.show_error("Failed to save template")

    def _on_restore_default(self):
        """恢复默认公式"""
        self.formula_engine.restore_default()
        self.sidebar_view.update_formula_text(self.formula_engine.formula_name)
        self._reset_simulation()

    def _reset_simulation(self):
        """重置模拟"""
        init_u, init_v = self.formula_engine.get_init_state(GRID_H, GRID_W)
        if init_u is not None and init_v is not None:
            self.grid_state.set_state(init_u, init_v)
        else:
            self.grid_state.reset()

    def update(self, time_delta: float):
        """更新模拟"""
        self.manager.update(time_delta)

        try:
            u, v = self.grid_state.u, self.grid_state.v
            new_u, new_v = self.formula_engine.execute_update(
                u, v, Du, Dv, F, k, dt, dx
            )

            if not (np.isfinite(new_u).all() and np.isfinite(new_v).all()):
                raise ValueError("Formula output contains inf or nan")

            self.grid_state.update(new_u, new_v)
            self.error_msg = ""

        except Exception as e:
            self.error_msg = f"Formula Error: {e}"
            self.sidebar_view.show_error(str(e))

    def render(self):
        """渲染画面"""
        self.main_view.clear()
        self.sidebar_view.draw_background(self.screen)

        # 获取显示数组
        display_array = self.formula_engine.get_display_array(self.grid_state.v)

        # 渲染网格
        self.main_view.render_grid(display_array)

        # 渲染叠加信息
        self.main_view.render_overlay(
            self.clock.get_fps(),
            self.grid_state.iteration,
            self.error_msg
        )

        # 渲染UI
        self.manager.draw_ui(self.screen)

        pygame.display.flip()

    def run(self):
        """主循环"""
        while self.running:
            time_delta = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            self.update(time_delta)
            self.render()

        pygame.quit()
