"""
增强渲染器模块 —— Pygame 可视化、HUD、后处理特效、过渡动画、自动播放。
"""

import time as _time
from pathlib import Path

import numpy as np

import pygame
from pygame import gfxdraw

from engine import CARenderEngine
from recipes import load_effects_from_dir
from composer import RecipeComposer


# ================================================================
#  后处理特效器
# ================================================================
class PostProcess:
    """可组合的后处理特效链"""

    EFFECTS = ('none', 'bloom', 'edge', 'motion_trail', 'invert', 'vignette')

    @staticmethod
    def none(rgb, engine=None):
        return rgb

    @staticmethod
    def bloom(rgb, engine=None):
        """辉光效果：模糊版叠加到原图"""
        from scipy.ndimage import gaussian_filter
        blurred = np.zeros_like(rgb, dtype=np.float32)
        for c in range(3):
            blurred[:, :, c] = gaussian_filter(rgb[:, :, c].astype(np.float32), sigma=1.2)
        result = np.clip(rgb.astype(np.float32) + blurred * 0.4, 0, 255)
        return result.astype(np.uint8)

    @staticmethod
    def edge(rgb, engine=None):
        """边缘检测叠加（Sobel 近似）"""
        from scipy.ndimage import sobel
        v = rgb.astype(np.float32).mean(axis=2)
        edges = np.sqrt(sobel(v, axis=0) ** 2 + sobel(v, axis=1) ** 2)
        edges = np.clip(edges / edges.max() * 255, 0, 255).astype(np.uint8)
        # 将边缘与彩色叠加
        result = rgb.copy()
        edge_mask = edges > 30
        result[edge_mask] = np.clip(result[edge_mask].astype(np.int16) + 60, 0, 255).astype(np.uint8)
        return result

    @staticmethod
    def motion_trail(rgb, engine=None):
        """运动轨迹：叠加历史帧"""
        if not hasattr(PostProcess, '_trail_buffer'):
            PostProcess._trail_buffer = None
            PostProcess._trail_decay = 0.85

        buf = PostProcess._trail_buffer
        if buf is None or buf.shape != rgb.shape:
            buf = rgb.astype(np.float32)
        else:
            buf = buf * PostProcess._trail_decay + rgb.astype(np.float32) * (1 - PostProcess._trail_decay)
        PostProcess._trail_buffer = buf
        return np.clip(buf, 0, 255).astype(np.uint8)

    @staticmethod
    def invert(rgb, engine=None):
        """反色"""
        return 255 - rgb

    @staticmethod
    def vignette(rgb, engine=None):
        """暗角效果"""
        h, w = rgb.shape[:2]
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2)
        mask = np.clip(1.0 - dist * 0.7, 0.3, 1.0)
        result = (rgb.astype(np.float32) * mask[:, :, np.newaxis])
        return np.clip(result, 0, 255).astype(np.uint8)

    @staticmethod
    def reset_trail():
        PostProcess._trail_buffer = None

    @staticmethod
    def apply(effect_name, rgb, engine=None):
        func = getattr(PostProcess, effect_name, PostProcess.none)
        return func(rgb, engine)


# ================================================================
#  HUD 渲染器
# ================================================================
class HUD:
    """屏幕抬头显示：FPS、步数、统计、键盘提示、通知"""

    def __init__(self, font, font_small, win_w, win_h):
        self.font = font
        self.font_small = font_small
        self.win_w = win_w
        self.win_h = win_h
        self._help_visible = False
        self._fps_history = []

    def _avg_fps(self):
        if len(self._fps_history) > 30:
            self._fps_history = self._fps_history[-30:]
        return sum(self._fps_history) / max(len(self._fps_history), 1)

    def update_fps(self, fps):
        self._fps_history.append(fps)

    def draw(self, screen, engine, paused, auto_play, effect_name, scale, notify, error):
        """绘制 HUD 信息条"""
        BAR_H = 22
        # 顶部半透明条
        bar = pygame.Surface((self.win_w, BAR_H), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        screen.blit(bar, (0, 0))

        fps_val = self._avg_fps()
        name = engine.config.get('name', '?')
        stats = engine.get_grid_stats()
        cycle_info = ""
        if engine.cycle_steps > 0:
            cycle_info = f" | cycle:{engine.t}/{engine.cycle_steps}(#{engine._total_cycles})"

        status = f"{'||' if paused else '▶'} " if paused or auto_play else ""
        info = (f"{status}{name} | t:{engine.t} | "
                f"μ:{stats['mean']:.3f} σ:{stats['std']:.3f} "
                f"active:{stats['alive']:.1%}{cycle_info}")
        txt = self.font_small.render(info[:120], True, (200, 200, 220))
        screen.blit(txt, (6, 4))

        fps_txt = self.font_small.render(f"FPS:{fps_val:.0f}", True, (140, 220, 140))
        fx, _ = fps_txt.get_size()
        screen.blit(fps_txt, (self.win_w - fx - 8, 4))

        # 自动播放指示
        if auto_play:
            ap_txt = self.font_small.render("[AUTO]", True, (255, 200, 60))
            screen.blit(ap_txt, (self.win_w - fx - 100, 4))

        # 后处理指示
        if effect_name != 'none':
            ep_txt = self.font_small.render(f"FX:{effect_name}", True, (160, 160, 255))
            epx, _ = ep_txt.get_size()
            screen.blit(ep_txt, (self.win_w // 2 - epx // 2, 4))

        # 通知
        if notify:
            n_text, n_color = notify
            txt = self.font.render(n_text[:80], True, n_color)
            tw, th = txt.get_size()
            noverlay = pygame.Surface((tw + 12, th + 6), pygame.SRCALPHA)
            noverlay.fill((0, 0, 0, 180))
            screen.blit(noverlay, (6, BAR_H + 4))
            screen.blit(txt, (12, BAR_H + 7))

        # 错误
        if error:
            lines = error.split('\n')[:3]
            eh = 18 * len(lines) + 6
            bar = pygame.Surface((self.win_w, eh), pygame.SRCALPHA)
            bar.fill((80, 10, 10, 200))
            screen.blit(bar, (0, self.win_h - eh))
            for i, line in enumerate(lines):
                txt = self.font_small.render(line[:70], True, (255, 150, 150))
                screen.blit(txt, (6, self.win_h - eh + 3 + i * 18))

        # 帮助覆盖
        if self._help_visible:
            self._draw_help(screen)

    def toggle_help(self):
        self._help_visible = not self._help_visible

    def _draw_help(self, screen):
        overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        help_lines = [
            ("键盘快捷键", (255, 255, 200)),
            ("", None),
            ("ESC     退出", (200, 200, 200)),
            ("SPACE   暂停/继续", (200, 200, 200)),
            ("R       重新加载当前配方", (200, 200, 200)),
            ("C       手动重置网格", (200, 200, 200)),
            ("S       保存截图", (200, 200, 200)),
            ("H       显示/隐藏帮助", (200, 200, 200)),
            ("", None),
            ("← →    切换配方", (200, 200, 200)),
            ("↑ ↓    缩放 (1x~8x)", (200, 200, 200)),
            ("A       自动播放模式", (200, 200, 200)),
            ("F       循环后处理特效", (200, 200, 200)),
            ("T       运动轨迹开关", (200, 200, 200)),
            ("P       切换颜色预设", (200, 200, 200)),
        ]

        y = self.win_h // 2 - len(help_lines) * 10
        for line, color in help_lines:
            if line and color:
                txt = self.font_small.render(line, True, color)
                x = self.win_w // 2 - txt.get_width() // 2
                screen.blit(txt, (x, y))
            y += 22


# ================================================================
#  配方切换过渡动画
# ================================================================
class TransitionManager:
    """配方切换时的平滑过渡效果"""

    def __init__(self, duration_frames=30):
        self.active = False
        self.duration = duration_frames
        self.progress = 0
        self.old_frame = None  # 旧配方最后一帧的 Surface

    def start(self, old_surface):
        self.active = True
        self.progress = 0
        self.old_frame = old_surface.copy()

    def update(self):
        if self.active:
            self.progress += 1
            if self.progress >= self.duration:
                self.active = False
                self.old_frame = None

    def is_active(self):
        return self.active

    def apply(self, screen, new_surf, x, y):
        """在 screen 上绘制过渡效果"""
        if not self.active or self.old_frame is None:
            return

        t = self.progress / self.duration
        # 交叉淡入淡出
        alpha_old = int(255 * (1 - t))
        alpha_new = int(255 * t)

        old_copy = self.old_frame.copy()
        old_copy.set_alpha(alpha_old)
        new_copy = new_surf.copy()
        new_copy.set_alpha(alpha_new)

        screen.blit(old_copy, (x, y))
        screen.blit(new_copy, (x, y))


# ================================================================
#  颜色预设管理器
# ================================================================
class ColorPresets:
    """运行时颜色预设切换"""

    PRESETS = {
        'default': {'red': 'v', 'green': 'v', 'blue': 'v'},
        'fire': {'red': 'min(v*3, 1.0)', 'green': 'max(0, min((v-0.33)*3, 1.0))', 'blue': 'max(0, (v-0.66)*3)'},
        'ocean': {'red': 'v*0.1', 'green': 'v*0.6 + 0.2*sin(v*15)', 'blue': 'v*0.8 + 0.2'},
        'sunset': {'red': 'v*0.9 + (1-v)*0.05', 'green': 'v*0.3 + (1-v)*0.05', 'blue': 'v*0.1 + (1-v)*0.3'},
        'rainbow': {'red': '0.5+0.5*sin(v*12)', 'green': '0.5+0.5*sin(v*12+2.094)', 'blue': '0.5+0.5*sin(v*12+4.189)'},
        'neon': {'red': 'v*0.5 + 0.5*sin(v*25)', 'green': 'v*0.5 + 0.5*sin(v*25+2.094)', 'blue': 'v*0.8 + 0.2*sin(v*20)'},
        'ice': {'red': 'v*0.3', 'green': 'v*0.8', 'blue': '1.0 - v*0.4'},
        'invert': {'red': '1-v', 'green': '1-v', 'blue': '1-v'},
        'thermal': {'red': 'v', 'green': 'v*0.5', 'blue': '0.5 + 0.5*sin(v*10)'},
    }

    @classmethod
    def apply(cls, engine, preset_name):
        if preset_name not in cls.PRESETS:
            return False
        col = cls.PRESETS[preset_name]
        for channel in ['red', 'green', 'blue']:
            expr = col.get(channel, '0.0')
            engine.color_funcs[channel] = engine._compile(expr, ['v', 'x', 'y'])
        return True


# ================================================================
#  主渲染器
# ================================================================
class CARenderer:
    """增强 CA 渲染器 —— 封装整个可视化循环。

    特性：
    - HUD 信息条（FPS、步数、统计、通知）
    - 后处理特效链（辉光、边缘检测、运动轨迹、暗角、反色）
    - 配方切换淡入淡出过渡动画
    - 自动播放模式（定时切换配方）
    - 缩放控制 (1x ~ 8x)
    - 键盘快捷键 + 帮助覆盖
    - 颜色预设运行时切换
    - 截图保存
    """

    def __init__(self, effects_dir, preloaded_paths=None, preloaded_engine=None,
                 preloaded_idx=0):
        self.script_dir = Path(effects_dir).parent
        self.effects_dir = Path(effects_dir)

        # 加载配方（可使用预加载数据跳过文件扫描）
        if preloaded_paths is not None:
            self.recipe_paths = preloaded_paths
            self.current_idx = preloaded_idx
        else:
            self.recipe_paths = load_effects_from_dir(self.effects_dir)
            self.current_idx = 0
        if not self.recipe_paths:
            raise RuntimeError("effects/ 目录中没有找到任何 .json 配方")
        self.recipe_names = list(self.recipe_paths.keys())

        # 初始化引擎（可使用预加载引擎）
        if preloaded_engine is not None:
            self.engine = preloaded_engine
        else:
            self.engine = self._init_engine()

        # 侧边栏（需在 _setup_window 之前设置）
        self.SIDEBAR_W = 180
        self.sidebar_scroll = 0
        self.ROW_H = 20

        # 缩放级别
        self.scale_level = max(2, min(8, 800 // max(self.engine.w, self.engine.h)))

        # Pygame
        pygame.init()
        self._setup_window()
        self._setup_fonts()
        self._setup_render_surfaces()

        # 子系统
        self.hud = HUD(self.font, self.font_small, self.win_w, self.win_h)
        self.transition = TransitionManager(duration_frames=25)

        # 状态
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.auto_play = False
        self.auto_play_timer = 0
        self.auto_play_interval = 600   # 帧，约10秒
        self.current_effect = 'none'
        self.current_preset = 'default'

        # 通知/错误
        self.notify_msg = None   # (text, color)
        self.notify_timer = 0
        self.error_msg = None
        self.error_timer = 0

        # 配方编辑器
        self.composer = None
        self.composer_active = False

    def _init_engine(self):
        engine = None
        for try_idx in range(len(self.recipe_names)):
            name = self.recipe_names[try_idx]
            try:
                engine = CARenderEngine(self.recipe_paths[name])
                self.current_idx = try_idx
                break
            except Exception as e:
                print(f"[警告] 配方加载失败: {name}: {e}")
        if engine is None:
            raise RuntimeError("所有配方均加载失败")
        return engine

    def _setup_window(self):
        self.win_w = self.SIDEBAR_W + self.engine.w * self.scale_level
        self.win_h = self.engine.h * self.scale_level
        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        name = self.recipe_names[self.current_idx]
        pygame.display.set_caption(f"CA Render Engine — {name}")

    def _setup_fonts(self):
        font_path = self.script_dir / 'NotoSansSC-VF.ttf'
        if not font_path.exists():
            font_path = self.script_dir / 'simhei.ttf'
        if font_path.exists():
            self.font = pygame.font.Font(str(font_path), 13)
            self.font_small = pygame.font.Font(str(font_path), 11)
        else:
            self.font = pygame.font.Font(None, 13)
            self.font_small = pygame.font.Font(None, 11)

    def _setup_render_surfaces(self):
        self.display_surf = pygame.Surface((self.engine.w, self.engine.h))
        self.rgb_wh = np.zeros((self.engine.w, self.engine.h, 3), dtype=np.uint8)

    def _rebuild_window(self):
        """窗口尺寸变化后重建"""
        self.win_w = self.SIDEBAR_W + self.engine.w * self.scale_level
        self.win_h = self.engine.h * self.scale_level
        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        self.hud.win_w = self.win_w
        self.hud.win_h = self.win_h
        name = self.recipe_names[self.current_idx]
        pygame.display.set_caption(f"CA Render Engine — {name}")

    # ================================================================
    #  配方切换
    # ================================================================
    def switch_recipe(self, idx):
        if idx == self.current_idx:
            return

        # 保存旧帧用于过渡
        old_surf = self.display_surf.copy()
        self.transition.start(old_surf)

        self.current_idx = idx % len(self.recipe_names)
        name = self.recipe_names[self.current_idx]
        try:
            self.engine.load_config(self.recipe_paths[name])
            # 重新应用颜色预设
            if self.current_preset != 'default':
                ColorPresets.apply(self.engine, self.current_preset)
        except Exception as e:
            self.error_msg = f"配方加载失败: {name}\n{str(e)[:200]}"
            self.error_timer = 300
            return

        self._setup_render_surfaces()
        self._rebuild_window()
        self.sidebar_scroll = 0
        PostProcess.reset_trail()

    def reload_current(self):
        self.switch_recipe(self.current_idx)

    # ================================================================
    #  配方编辑器
    # ================================================================
    def _toggle_composer(self):
        """打开/关闭可视化配方编辑器"""
        if self.composer_active:
            self.composer_active = False
            self.composer = None
        else:
            fonts = {
                'title': self.font,
                'normal': self.font,
                'small': self.font_small,
            }
            self.composer = RecipeComposer(self.screen, fonts, self.effects_dir)
            self.composer_active = True

    def _handle_composer_action(self, action):
        """处理编辑器的动作"""
        if action == 'close':
            self.composer_active = False
            self.composer = None
        elif action == 'generate':
            result = self.composer.generate(apply_now=False)
            if result:
                # 重新扫描配方列表
                self.recipe_paths = load_effects_from_dir(self.effects_dir)
                self.recipe_names = list(self.recipe_paths.keys())
                self.notify(f'配方已生成: {result.name}', (100, 220, 100), duration=150)
        elif action == 'generate_apply':
            result = self.composer.generate(apply_now=True)
            if result:
                # 保存文件
                import json
                name = result.get('name', 'custom')
                safe = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                out = self.effects_dir / f'{safe}.json'
                with open(out, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                # 重新扫描并找到新配方
                self.recipe_paths = load_effects_from_dir(self.effects_dir)
                self.recipe_names = list(self.recipe_paths.keys())
                if name in self.recipe_names:
                    idx = self.recipe_names.index(name)
                    self.switch_recipe(idx)
                self.notify(f'已应用: {name}', (100, 220, 100), duration=150)
                self.composer_active = False
                self.composer = None

    # ================================================================
    #  通知
    # ================================================================
    def notify(self, text, color=(120, 255, 120), duration=90):
        self.notify_msg = (text, color)
        self.notify_timer = duration

    # ================================================================
    #  缩放
    # ================================================================
    def zoom_in(self):
        self.scale_level = min(8, self.scale_level + 1)
        self._rebuild_window()

    def zoom_out(self):
        self.scale_level = max(1, self.scale_level - 1)
        self._rebuild_window()

    # ================================================================
    #  手柄事件
    # ================================================================
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.composer_active:
                    self.composer_active = False
                    self.composer = None
                else:
                    self.running = False

            elif self.composer_active and self.composer is not None:
                # 配方编辑器模式 —— 委托事件
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in (4, 5):
                        self.composer.handle_scroll(1 if event.button == 4 else -1)
                    else:
                        action = self.composer.handle_event(event)
                        self._handle_composer_action(action)
                elif event.type == pygame.KEYDOWN:
                    action = self.composer.handle_event(event)
                    self._handle_composer_action(action)

            elif event.type == pygame.VIDEORESIZE:
                pass  # 简单忽略 resize，保持当前窗口

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):
                    self._handle_mouse_scroll(event)
                else:
                    self._handle_mouse(event)

            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard(event)

    def _handle_mouse(self, event):
        mx, my = event.pos
        sidebar_w = self.SIDEBAR_W

        if event.button == 1 and mx < sidebar_w:
            clicked = self.sidebar_scroll + my // self.ROW_H
            if 0 <= clicked < len(self.recipe_names) and clicked != self.current_idx:
                self.switch_recipe(clicked)

    def _handle_mouse_scroll(self, event):
        """滚轮事件"""
        if event.button == 4:
            self.sidebar_scroll = max(0, self.sidebar_scroll - 1)
        elif event.button == 5:
            visible_rows = self.win_h // self.ROW_H
            max_scroll = max(0, len(self.recipe_names) - visible_rows)
            self.sidebar_scroll = min(max_scroll, self.sidebar_scroll + 1)

    def _handle_keyboard(self, event):
        key = event.key

        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
            if not self.paused:
                self.auto_play = False
        elif key == pygame.K_h:
            self.hud.toggle_help()
        elif key == pygame.K_g:
            self._toggle_composer()
        elif key == pygame.K_r:
            self.reload_current()
            self.notify("已重新加载")
            self.error_msg = None
        elif key == pygame.K_c:
            self.engine.reset()
            PostProcess.reset_trail()
            self.notify("已重置网格")
        elif key == pygame.K_s:
            self._save_screenshot()
        elif key == pygame.K_a:
            self.auto_play = not self.auto_play
            self.paused = False
            msg = "自动播放 ON" if self.auto_play else "自动播放 OFF"
            self.notify(msg, (255, 200, 60))
        elif key == pygame.K_f:
            self._cycle_effect()
        elif key == pygame.K_t:
            if self.current_effect == 'motion_trail':
                self.current_effect = 'none'
                PostProcess.reset_trail()
                self.notify("轨迹 OFF")
            else:
                self.current_effect = 'motion_trail'
                self.notify("轨迹 ON", (160, 160, 255))
        elif key == pygame.K_p:
            self._cycle_preset()
        elif key == pygame.K_LEFT:
            self.switch_recipe(self.current_idx - 1)
        elif key == pygame.K_RIGHT:
            self.switch_recipe(self.current_idx + 1)
        elif key == pygame.K_UP:
            self.zoom_in()
            self.notify(f"缩放: {self.scale_level}x")
        elif key == pygame.K_DOWN:
            self.zoom_out()
            self.notify(f"缩放: {self.scale_level}x")

    def _cycle_effect(self):
        idx = PostProcess.EFFECTS.index(self.current_effect)
        idx = (idx + 1) % len(PostProcess.EFFECTS)
        self.current_effect = PostProcess.EFFECTS[idx]
        if self.current_effect != 'motion_trail':
            PostProcess.reset_trail()
        self.notify(f"特效: {self.current_effect}", (160, 160, 255))

    def _cycle_preset(self):
        presets = list(ColorPresets.PRESETS.keys())
        idx = presets.index(self.current_preset)
        idx = (idx + 1) % len(presets)
        self.current_preset = presets[idx]
        ColorPresets.apply(self.engine, self.current_preset)
        self.notify(f"颜色: {self.current_preset}", (180, 180, 255))

    def _save_screenshot(self):
        shot_dir = self.script_dir / 'screenshots'
        shot_dir.mkdir(exist_ok=True)
        fname = shot_dir / f"screenshot_{_time.strftime('%Y%m%d_%H%M%S')}.png"
        try:
            pygame.image.save(self.display_surf, str(fname))
            self.notify(f"已保存: {fname.name}")
        except Exception as e:
            self.notify(f"保存失败: {str(e)[:80]}", (255, 120, 120))

    # ================================================================
    #  侧边栏绘制
    # ================================================================
    def _draw_sidebar(self):
        sidebar_w = self.SIDEBAR_W
        visible_rows = self.win_h // self.ROW_H

        # 背景
        sidebar_rect = pygame.Rect(0, 0, sidebar_w, self.win_h)
        pygame.draw.rect(self.screen, (26, 26, 32), sidebar_rect)
        pygame.draw.line(self.screen, (50, 50, 55), (sidebar_w - 1, 0), (sidebar_w - 1, self.win_h))

        # 标题
        title = self.font_small.render("Recipes", True, (120, 120, 140))
        self.screen.blit(title, (8, 5))

        # 列表项
        for i in range(self.sidebar_scroll,
                       min(self.sidebar_scroll + visible_rows, len(self.recipe_names))):
            name = self.recipe_names[i]
            y = 22 + (i - self.sidebar_scroll) * self.ROW_H
            row_rect = pygame.Rect(2, y, sidebar_w - 4, self.ROW_H)

            if i == self.current_idx:
                if self.auto_play:
                    c = (160, 120, 30)
                else:
                    c = (45, 100, 180)
                pygame.draw.rect(self.screen, c, row_rect, border_radius=4)
                color = (240, 240, 255)
            else:
                color = (160, 160, 175)

            display_name = name if len(name) <= 13 else name[:12] + '\u2026'
            txt = self.font_small.render(display_name, True, color)
            self.screen.blit(txt, (8, y + 3))

        # 滚动条
        if len(self.recipe_names) > visible_rows:
            thumb_h = max(20, visible_rows * self.win_h // len(self.recipe_names))
            thumb_y = self.sidebar_scroll * self.win_h // len(self.recipe_names)
            pygame.draw.rect(self.screen, (70, 70, 80),
                             (sidebar_w - 6, thumb_y, 4, thumb_h), border_radius=2)

    # ================================================================
    #  循环进度条
    # ================================================================
    def _draw_cycle_bar(self, grid_w):
        if self.engine.cycle_steps <= 0:
            return
        progress = self.engine.t / self.engine.cycle_steps
        bar_w = grid_w - 16
        bar_h = 4
        bar_x = self.SIDEBAR_W + 8
        bar_y = self.win_h - 10
        pygame.draw.rect(self.screen, (30, 30, 38), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            r = int(80 + 175 * progress)
            g = int(160 - 100 * progress)
            b = int(220 - 140 * progress)
            pygame.draw.rect(self.screen, (r, g, b), (bar_x, bar_y, fill_w, bar_h), border_radius=2)
        cycle_text = f"cycle {self.engine.t}/{self.engine.cycle_steps}"
        txt = self.font_small.render(cycle_text, True, (140, 140, 160))
        self.screen.blit(txt, (bar_x, bar_y - 14))

    # ================================================================
    #  主循环
    # ================================================================
    def run(self):
        """启动主渲染循环"""
        while self.running:
            self._handle_events()

            # 更新定时器
            self._update_timers()

            # 配方编辑器激活时，暂停演化
            if self.composer_active and self.composer:
                if self.composer:
                    self.composer.update()
                self._render_frame()
                self.clock.tick(60)
                continue

            # 自动播放
            if self.auto_play and not self.paused:
                self.auto_play_timer += 1
                if self.auto_play_timer >= self.auto_play_interval:
                    self.auto_play_timer = 0
                    self.switch_recipe(self.current_idx + 1)

            # 过渡动画
            self.transition.update()

            # 演化
            if not self.paused:
                for _ in range(self.engine.steps_per_frame):
                    self.engine.step()
                if self.engine.t == 0 and self.engine._total_cycles > 0:
                    PostProcess.reset_trail()

            # 渲染
            self._render_frame()

            self.clock.tick(self.engine.fps)
            self.hud.update_fps(self.clock.get_fps())

        pygame.quit()

    def _update_timers(self):
        if self.notify_timer > 0:
            self.notify_timer -= 1
            if self.notify_timer <= 0:
                self.notify_msg = None
        if self.error_timer > 0:
            self.error_timer -= 1
            if self.error_timer <= 0:
                self.error_msg = None

    def _render_frame(self):
        # 1. 计算原始帧
        self.engine.fill_color_wh(self.rgb_wh)

        # 2. 后处理 (在 (w,h,3) 数组上)
        if self.current_effect != 'none':
            rgb_hw = self.rgb_wh.transpose(1, 0, 2).copy()
            processed = PostProcess.apply(self.current_effect, rgb_hw, self.engine)
            self.rgb_wh[:] = processed.transpose(1, 0, 2)

        # 3. Blit 到 surface
        pygame.surfarray.blit_array(self.display_surf, self.rgb_wh)

        # 4. 缩放
        grid_w = self.engine.w * self.scale_level
        grid_h = self.engine.h * self.scale_level
        big_surf = pygame.transform.scale(self.display_surf, (grid_w, grid_h))

        # 5. 清屏绘制
        self.screen.fill((18, 18, 22))

        # 6. 侧边栏
        self._draw_sidebar()

        # 7. CA 渲染区域
        sx = self.SIDEBAR_W
        if self.transition.is_active():
            self.transition.apply(self.screen, big_surf, sx, 0)
        else:
            self.screen.blit(big_surf, (sx, 0))

        # 8. 循环进度条
        self._draw_cycle_bar(grid_w)

        # 9. HUD
        notify = self.notify_msg if self.notify_timer > 0 else None
        error = self.error_msg if self.error_timer > 0 else None
        self.hud.draw(self.screen, self.engine, self.paused, self.auto_play,
                        self.current_effect, self.scale_level, notify, error)

        # 10. 配方编辑器（覆盖层）
        if self.composer_active and self.composer:
            self.composer.draw()

        pygame.display.flip()


# ================================================================
#  加载界面
# ================================================================
def _show_loading(effects_dir):
    """显示加载界面，扫描 JSON 配方并初始化引擎。
    返回 (recipe_paths, engine, current_idx) 或 None（失败时）。
    """
    effects_dir = Path(effects_dir)
    script_dir = effects_dir.parent

    # --- 初始化加载窗口 ---
    LOAD_W, LOAD_H = 480, 220
    screen = pygame.display.set_mode((LOAD_W, LOAD_H))
    pygame.display.set_caption("正在加载...")

    # 加载字体
    font_path = script_dir / 'NotoSansSC-VF.ttf'
    if not font_path.exists():
        font_path = script_dir / 'simhei.ttf'
    if font_path.exists():
        title_font = pygame.font.Font(str(font_path), 22)
        info_font = pygame.font.Font(str(font_path), 14)
        small_font = pygame.font.Font(str(font_path), 11)
    else:
        title_font = pygame.font.Font(None, 24)
        info_font = pygame.font.Font(None, 16)
        small_font = pygame.font.Font(None, 12)

    # --- 可变状态 ---
    progress = 0.0
    status_text = "正在初始化..."
    detail_text = ""
    phase = "scan"          # scan | engine | done
    error_msg = None

    def _draw_frame():
        """绘制单帧加载界面"""
        screen.fill((18, 18, 24))

        # 标题
        title = title_font.render("CA 渲染引擎", True, (210, 210, 230))
        tx = LOAD_W // 2 - title.get_width() // 2
        screen.blit(title, (tx, 22))

        # 状态文字 + 动态点
        dots = '.' * ((pygame.time.get_ticks() // 400) % 4)
        sf = info_font.render(status_text + dots, True, (160, 160, 185))
        screen.blit(sf, (LOAD_W // 2 - sf.get_width() // 2, 56))

        # 进度条背景
        bx, by, bw, bh = 44, 92, LOAD_W - 88, 20
        pygame.draw.rect(screen, (38, 38, 48), (bx, by, bw, bh), border_radius=5)

        # 进度条填充
        if progress > 0:
            fw = int(bw * progress)
            r = int(40 + 170 * progress)
            g = int(100 + 100 * progress)
            bc = int(190 + 45 * progress)
            pygame.draw.rect(screen, (r, g, bc), (bx, by, fw, bh), border_radius=5)

        # 百分比
        pct = small_font.render(f"{int(progress * 100)}%", True, (225, 225, 240))
        screen.blit(pct, (bx + bw // 2 - pct.get_width() // 2, by + 2))

        # 详情
        if detail_text:
            ds = small_font.render(detail_text[:52], True, (120, 120, 140))
            screen.blit(ds, (LOAD_W // 2 - ds.get_width() // 2, 126))

        # 阶段提示
        if phase == "scan":
            tip = small_font.render("正在扫描 effects/ 目录...", True, (80, 80, 100))
            screen.blit(tip, (LOAD_W // 2 - tip.get_width() // 2, 170))
        elif phase == "engine":
            tip = small_font.render("正在编译数学公式...", True, (80, 80, 100))
            screen.blit(tip, (LOAD_W // 2 - tip.get_width() // 2, 170))

        # 错误
        if error_msg:
            es = small_font.render(error_msg[:58], True, (255, 120, 120))
            screen.blit(es, (LOAD_W // 2 - es.get_width() // 2, 192))

        pygame.display.flip()

    # --- 阶段 1: 扫描 JSON 文件 ---
    def _progress_cb(current, total, filename):
        nonlocal progress, detail_text, status_text
        progress = 0.12 + (current / total) * 0.58  # 12% ~ 70%
        detail_text = filename
        status_text = f"加载配方文件 ({current}/{total})"
        _draw_frame()
        for _ in pygame.event.get():
            pass

    phase = "scan"
    status_text = "正在扫描配方目录"
    _draw_frame()
    pygame.time.wait(120)

    recipe_paths = {}
    try:
        recipe_paths = load_effects_from_dir(effects_dir, progress_callback=_progress_cb)
    except Exception as e:
        error_msg = f"扫描失败: {e}"
        status_text = "加载失败"
        progress = 0
        _draw_frame()
        pygame.time.wait(2500)
        return None

    if not recipe_paths:
        error_msg = "未找到任何 .json 配方文件"
        status_text = "加载失败"
        _draw_frame()
        pygame.time.wait(2500)
        return None

    # --- 阶段 2: 初始化引擎 ---
    phase = "engine"
    progress = 0.74
    recipe_names = list(recipe_paths.keys())
    engine = None
    current_idx = 0

    for try_idx, name in enumerate(recipe_names):
        status_text = f"编译配方: {name}"
        detail_text = ""
        _draw_frame()
        for _ in pygame.event.get():
            pass

        try:
            engine = CARenderEngine(recipe_paths[name])
            current_idx = try_idx
            progress = 0.82 + (try_idx + 1) / len(recipe_names) * 0.13
            break
        except Exception as e:
            error_msg = f"配方 [{name}] 编译失败"
            _draw_frame()
            pygame.time.wait(300)

    if engine is None:
        error_msg = "所有配方均加载失败"
        status_text = "初始化失败"
        progress = 0
        _draw_frame()
        pygame.time.wait(2500)
        return None

    # --- 完成 ---
    phase = "done"
    progress = 1.0
    status_text = "初始化完成"
    detail_text = f"已加载 {len(recipe_paths)} 个配方，即将启动..."
    error_msg = None
    _draw_frame()
    pygame.time.wait(500)

    return recipe_paths, engine, current_idx


# ================================================================
#  便捷入口
# ================================================================
def launch(effects_dir):
    """启动增强渲染器（带加载界面）"""
    pygame.init()

    loaded = _show_loading(effects_dir)
    if loaded is None:
        print("[错误] 加载失败，程序退出")
        pygame.quit()
        return

    recipe_paths, engine, idx = loaded
    renderer = CARenderer(effects_dir,
                          preloaded_paths=recipe_paths,
                          preloaded_engine=engine,
                          preloaded_idx=idx)
    renderer.run()


def _launch_composer_only(effects_dir):
    """独立模式：仅运行可视化配方编辑器（不启动 CA 引擎）。"""
    import sys
    effects_dir = Path(effects_dir)
    script_dir = effects_dir.parent

    pygame.init()
    screen = pygame.display.set_mode((800, 520))
    pygame.display.set_caption("Recipe Composer — CA Render Engine")

    # 字体
    font_path = script_dir / 'NotoSansSC-VF.ttf'
    if not font_path.exists():
        font_path = script_dir / 'simhei.ttf'
    if font_path.exists():
        title_font = pygame.font.Font(str(font_path), 16)
        normal_font = pygame.font.Font(str(font_path), 14)
        small_font = pygame.font.Font(str(font_path), 11)
    else:
        title_font = pygame.font.Font(None, 18)
        normal_font = pygame.font.Font(None, 15)
        small_font = pygame.font.Font(None, 12)

    fonts = {'title': title_font, 'normal': normal_font, 'small': small_font}
    composer = RecipeComposer(screen, fonts, effects_dir)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):
                    composer.handle_scroll(1 if event.button == 4 else -1)
                else:
                    action = composer.handle_event(event)
                    if action == 'close':
                        running = False
                    elif action == 'generate':
                        composer.generate(apply_now=False)
                    elif action == 'generate_apply':
                        composer.generate(apply_now=True)
            elif event.type == pygame.KEYDOWN:
                action = composer.handle_event(event)
                if action == 'close':
                    running = False
                elif action == 'generate':
                    composer.generate(apply_now=False)
                elif action == 'generate_apply':
                    composer.generate(apply_now=True)

        screen.fill((18, 18, 24))
        composer.draw()
        composer.update()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
