"""视图层 - 侧边栏UI"""
import pygame
import pygame_gui
import pygame_gui.core


class SidebarView:
    """侧边栏视图"""

    def __init__(self, manager: pygame_gui.UIManager,
                 preview_w: int, panel_width: int, height: int):
        self.manager = manager
        self.preview_w = preview_w
        self.panel_width = panel_width
        self.height = height

        self.container = pygame_gui.core.UIContainer(
            relative_rect=pygame.Rect((preview_w, 0), (panel_width, height)),
            manager=manager
        )

        self._create_widgets()
        self._widgets = {}

    def _create_widgets(self):
        """创建所有UI组件"""
        pw = self.panel_width
        m = self.manager
        c = self.container

        # 标题
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (pw - 20, 35)),
            text="CONTROL PANEL",
            manager=m, container=c
        )

        # 公式显示
        self.formula_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 55), (pw - 20, 50)),
            text="Formula: Gray-Scott",
            manager=m, container=c
        )

        # 按钮组
        self.btn_load = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 115), (pw - 20, 36)),
            text="Load Formula",
            manager=m, container=c
        )

        self.btn_template = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 160), (pw - 20, 36)),
            text="Generate Template",
            manager=m, container=c
        )

        self.btn_default = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 205), (pw - 20, 36)),
            text="Restore Default",
            manager=m, container=c
        )

        # 参数显示
        self.params_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 260), (pw - 20, 25)),
            text="Parameters",
            manager=m, container=c
        )

        self.params_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 285), (pw - 20, 80)),
            text="Du=0.16, Dv=0.08\nF=0.035, k=0.065\ndt=0.5",
            manager=m, container=c
        )

        # 网格信息
        self.grid_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 385), (pw - 20, 25)),
            text="Grid Info",
            manager=m, container=c
        )

        self.grid_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 410), (pw - 20, 50)),
            text="Size: 200 x 200",
            manager=m, container=c
        )

    def update_formula_text(self, text: str):
        """更新公式名称显示"""
        self.formula_label.set_text(f"Formula: {text}")

    def update_params(self, Du: float, Dv: float, F: float, k: float, dt: float):
        """更新参数显示"""
        self.params_label.set_text(f"Du={Du}, Dv={Dv}\nF={F}, k={k}\ndt={dt}")

    def update_grid_info(self, width: int, height: int):
        """更新网格信息"""
        self.grid_label.set_text(f"Size: {width} x {height}")

    def show_error(self, message: str):
        """显示错误信息"""
        self.formula_label.set_text(f"Error: {message}")

    def show_message(self, message: str):
        """显示一般消息"""
        self.formula_label.set_text(message)

    def draw_background(self, screen):
        """绘制侧边栏背景"""
        from constants import PANEL_BG, ACCENT_COLOR

        panel_rect = pygame.Rect((self.preview_w, 0), (self.panel_width, self.height))
        pygame.draw.rect(screen, PANEL_BG, panel_rect)
        pygame.draw.line(screen, ACCENT_COLOR, (self.preview_w, 0), (self.preview_w, self.height), 2)

        # 分隔线
        pw = self.preview_w
        panel_w = self.panel_width
        h = self.height

        pygame.draw.line(screen, (70, 70, 90), (pw + 15, 108), (pw + panel_w - 15, 108), 1)
        pygame.draw.line(screen, (70, 70, 90), (pw + 15, 248), (pw + panel_w - 15, 248), 1)
        pygame.draw.line(screen, (70, 70, 90), (pw + 15, 380), (pw + panel_w - 15, 380), 1)

    def process_event(self, event):
        """处理UI事件"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_load:
                return 'load'
            elif event.ui_element == self.btn_template:
                return 'template'
            elif event.ui_element == self.btn_default:
                return 'default'
        return None
