import pygame
import pygame_gui
import pygame_gui.core
import numpy as np
import sys
import os
import importlib.util
import inspect
from tkinter import Tk, filedialog

# ================== 配置参数 ==================
WIDTH, HEIGHT = 720, 520         # 窗口尺寸
CELL_SIZE = 2
GRID_W = 200
GRID_H = 200
PANEL_WIDTH = 200                # 侧边栏宽度
PREVIEW_W = WIDTH - PANEL_WIDTH
FPS = 60

# 颜色主题
BG_DARK = (30, 30, 40)
PANEL_BG = (45, 45, 60)
ACCENT_COLOR = (80, 140, 200)
TEXT_COLOR = (220, 220, 230)

# 反应扩散默认参数
Du = 0.16
Dv = 0.08
F  = 0.035
k  = 0.065
dt = 0.5
dx = CELL_SIZE

# ================== 初始化 pygame-ce ==================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cellular Automata - Formula Lab")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 18)
font_small = pygame.font.Font(None, 14)

# ================== 初始化 pygame_gui ==================
manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# ================== 侧边栏 UI 容器 ==================
sidebar_container = pygame_gui.core.UIContainer(
    relative_rect=pygame.Rect((PREVIEW_W, 0), (PANEL_WIDTH, HEIGHT)),
    manager=manager
)

# 标题
label_title = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((10, 10), (PANEL_WIDTH - 20, 35)),
    text="CONTROL PANEL",
    manager=manager,
    container=sidebar_container
)

# 公式显示
label_formula = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((10, 55), (PANEL_WIDTH - 20, 50)),
    text="Formula: Gray-Scott",
    manager=manager,
    container=sidebar_container
)

# 按钮组
btn_load = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((10, 115), (PANEL_WIDTH - 20, 36)),
    text="Load Formula",
    manager=manager,
    container=sidebar_container
)
btn_template = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((10, 160), (PANEL_WIDTH - 20, 36)),
    text="Generate Template",
    manager=manager,
    container=sidebar_container
)
btn_default = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((10, 205), (PANEL_WIDTH - 20, 36)),
    text="Restore Default",
    manager=manager,
    container=sidebar_container
)

# 参数显示
label_params_title = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((10, 260), (PANEL_WIDTH - 20, 25)),
    text="Parameters",
    manager=manager,
    container=sidebar_container
)
label_params = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((10, 285), (PANEL_WIDTH - 20, 80)),
    text=f"Du={Du}, Dv={Dv}\nF={F}, k={k}\ndt={dt}",
    manager=manager,
    container=sidebar_container
)

# 网格信息
label_grid_title = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((10, 385), (PANEL_WIDTH - 20, 25)),
    text="Grid Info",
    manager=manager,
    container=sidebar_container
)
label_grid = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((10, 410), (PANEL_WIDTH - 20, 50)),
    text=f"Size: {GRID_W} x {GRID_H}",
    manager=manager,
    container=sidebar_container
)

# 迭代计数器
iteration = 0

# ================== 默认公式（Gray‑Scott） ==================
def laplacian(grid, dx):
    return (np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
            np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) -
            4 * grid) / (dx**2)

def gray_scott_update(u, v, Du, Dv, F, k, dt, dx):
    Lu = laplacian(u, dx)
    Lv = laplacian(v, dx)
    uvv = u * v * v
    new_u = u + (Du * Lu - uvv + F * (1 - u)) * dt
    new_v = v + (Dv * Lv + uvv - (F + k) * v) * dt
    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)

current_update_func = gray_scott_update
current_formula_name = "Gray-Scott"
current_display_func = None      # 公式可选的自定义显示函数
current_init_func = None         # 公式可选的自定义初始化函数

# ================== 公式加载逻辑（增强版） ==================
def load_formula_from_file():
    global current_update_func, current_formula_name
    global current_display_func, current_init_func

    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="Select Python Formula File",
        filetypes=[("Python files", "*.py")]
    )
    root.destroy()
    if not file_path:
        return

    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        formula_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(formula_module)

        # 1. Must have update function
        if not hasattr(formula_module, 'update'):
            raise AttributeError("Formula file missing 'update' function")

        new_func = formula_module.update

        # 2. 判断是否支持无参调用（仅 u, v）
        sig = inspect.signature(new_func)
        params = list(sig.parameters.keys())
        if len(params) == 2:
            # 无参公式，包装成兼容函数
            def wrapper(u, v, Du, Dv, F, k, dt, dx):
                return new_func(u, v)
            current_update_func = wrapper
        else:
            current_update_func = new_func

        # 3. 获取公式名称
        if hasattr(formula_module, 'NAME'):
            current_formula_name = formula_module.NAME
        else:
            current_formula_name = os.path.basename(file_path)

        # 4. 获取可选显示函数
        if hasattr(formula_module, 'get_display'):
            current_display_func = formula_module.get_display
        else:
            current_display_func = None

        # 5. 获取可选初始化函数
        if hasattr(formula_module, 'init_state'):
            current_init_func = formula_module.init_state
        else:
            current_init_func = None

        label_formula.set_text(f"Formula: {current_formula_name}")
        print(f"Loaded formula: {current_formula_name}")

    except Exception as e:
        label_formula.set_text(f"Load Failed: {e}")
        print(f"Formula load error: {e}")

# ================== 网格初始化（支持钩子） ==================
def reset_grid():
    global u, v, iteration
    iteration = 0
    if current_init_func is not None:
        try:
            u, v = current_init_func(GRID_H, GRID_W)
            return
        except Exception as e:
            label_formula.set_text(f"Init Error: {e}")

    # 默认初始化：中心方形扰动
    u = np.ones((GRID_H, GRID_W))
    v = np.zeros((GRID_H, GRID_W))
    r = 10
    cx, cy = GRID_W // 2, GRID_H // 2
    v[cy-r:cy+r, cx-r:cx+r] = 1.0

# ================== 恢复默认公式 ==================
def restore_default_formula():
    global current_update_func, current_formula_name
    global current_display_func, current_init_func
    
    current_update_func = gray_scott_update
    current_formula_name = "Gray-Scott"
    current_display_func = None
    current_init_func = None
    
    reset_grid()
    label_formula.set_text(f"Formula: {current_formula_name}")
    print(f"Restored default formula: {current_formula_name}")

reset_grid()

# ================== 模板生成器 ==================
def generate_template():
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
    if not file_path:
        return

    template_content = '''# Custom Cellular Automata Formula
NAME = "My Model"   # Optional, displayed on the UI

def update(u, v, Du, Dv, F, k, dt, dx):
    """
    Called every frame, return new (u, v)
    Parameters:
        u, v : current state (2D numpy arrays)
        Du, Dv, F, k, dt, dx : predefined parameters (can be ignored)
    Notes:
        - Do not hardcode grid size, use u.shape
        - Return values will be clipped to [0, 1] (optional)
    """
    # Example: simple diffusion + reaction
    Lu = (np.roll(u, 1, 0) + np.roll(u, -1, 0) +
          np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4*u) / dx**2
    new_u = u + Du * Lu * dt
    new_v = v * 0.99  # slow decay
    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)

# Optional: custom display content (default displays v)
# def get_display(v):
#     return v * 0.5  # can return u, v, u*v, etc.

# Optional: custom initial state
# def init_state(H, W):
#     u = np.random.rand(H, W)
#     v = np.zeros((H, W))
#     v[H//2-5:H//2+5, W//2-5:W//2+5] = 1.0
#     return u, v
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    label_formula.set_text("Template Generated")
    print(f"Template saved to: {file_path}")

# ================== 主循环 ==================
running = True
error_msg = ""
iteration = 0

while running:
    time_delta = clock.tick(FPS) / 1000.0
    iteration += 1

    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == btn_load:
                load_formula_from_file()
                reset_grid()  # 加载新公式后自动重置
            elif event.ui_element == btn_template:
                generate_template()
            elif event.ui_element == btn_default:
                restore_default_formula()

    manager.update(time_delta)

    # --- 公式更新（安全沙箱） ---
    try:
        # 形状检查
        if u.shape != v.shape:
            raise ValueError(f"u/v shape mismatch: {u.shape} vs {v.shape}")

        new_u, new_v = current_update_func(u, v, Du, Dv, F, k, dt, dx)

        # 简单数值检查（防止 inf/nan）
        if not (np.isfinite(new_u).all() and np.isfinite(new_v).all()):
            raise ValueError("Formula output contains inf or nan")

        # 裁剪到 [0,1]（可根据公式决定是否启用，此处默认开启）
        u, v = np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)
        error_msg = ""
    except Exception as e:
        error_msg = f"Formula Error: {e}"
        label_formula.set_text(error_msg)
        # 保持当前 u,v 不变，继续显示

    # --- 绘制预览区域 ---
    if current_display_func is not None:
        try:
            display_array = current_display_func(v)
        except:
            display_array = v
    else:
        display_array = v

    display_array = (np.clip(display_array, 0, 1) * 255).astype(np.uint8)
    surface = pygame.surfarray.make_surface(
        np.stack([display_array]*3, axis=-1)
    )
    surface = pygame.transform.scale(surface, (PREVIEW_W, HEIGHT))
    screen.blit(surface, (0, 0))

    # --- 绘制侧边栏背景 ---
    panel_rect = pygame.Rect((PREVIEW_W, 0), (PANEL_WIDTH, HEIGHT))
    pygame.draw.rect(screen, PANEL_BG, panel_rect)
    pygame.draw.line(screen, ACCENT_COLOR, (PREVIEW_W, 0), (PREVIEW_W, HEIGHT), 2)

    # 绘制分隔线
    pygame.draw.line(screen, (70, 70, 90), (PREVIEW_W + 15, 108), (PREVIEW_W + PANEL_WIDTH - 15, 108), 1)
    pygame.draw.line(screen, (70, 70, 90), (PREVIEW_W + 15, 248), (PREVIEW_W + PANEL_WIDTH - 15, 248), 1)
    pygame.draw.line(screen, (70, 70, 90), (PREVIEW_W + 15, 380), (PREVIEW_W + PANEL_WIDTH - 15, 380), 1)

    # --- 绘制预览区域信息 ---
    # FPS
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, TEXT_COLOR)
    screen.blit(fps_text, (5, 5))
    
    # 迭代次数
    iter_text = font.render(f"Iter: {iteration}", True, TEXT_COLOR)
    screen.blit(iter_text, (5, 28))

    # 错误信息
    if error_msg:
        err_surf = font.render(error_msg, True, (255, 100, 100))
        screen.blit(err_surf, (5, 51))

    # --- 渲染 UI ---
    manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()