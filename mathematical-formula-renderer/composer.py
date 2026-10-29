"""
可视化配方编辑器 —— 通过 GUI 交互式组合初始化/演化/颜色模板生成配方 JSON。

用法：
    独立模式:  python composer.py
    集成模式:  主渲染器中按 G 键打开
"""

import json
from pathlib import Path

import pygame

from templates import FORMULA_TEMPLATES
from recipes import generate_recipe_from_templates


class RecipeComposer:
    """可视化配方编辑器 —— 三列模板选择 + 实时预览 + 一键生成。

    ┌──────────────────────────────────────────────┐
    │  🧪 Recipe Composer                 [?] [X]  │
    ├──────────┬──────────┬──────────┬─────────────┤
    │ Init     │ Evol     │ Color    │  Preview    │
    │ ──────── │ ──────── │ ──────── │ ─────────── │
    │ ▶纯随机  │ Lenia…   │ 极光     │  init: ...  │
    │  稀疏随机│▶BZ反应…  │ 深海     │  evol: ...  │
    │  中心脉冲│ FHN…     │▶熔岩     │  col:  ...  │
    │  ...     │ ...      │ ...      │             │
    ├──────────┴──────────┴──────────┴─────────────┤
    │  Name: [__________________]  w:256  h:192    │
    │  [ ← 生成JSON ]    [ ▶ 生成并应用 ]          │
    └──────────────────────────────────────────────┘
    """

    PANEL_W = 160      # 每个模板列表面板宽度
    PREVIEW_W = 240    # 预览面板宽度
    SIDEBAR_W = 4      # 总面板区宽度
    ROW_H = 22
    HEADER_H = 30
    BOTTOM_H = 56

    COLORS = {
        'bg':        (22, 22, 28),
        'panel_bg':  (30, 30, 38),
        'header_bg': (36, 36, 46),
        'border':    (50, 50, 58),
        'text':      (200, 200, 215),
        'text_dim':  (120, 120, 140),
        'selected':  (45, 90, 160),
        'selected_border': (80, 140, 220),
        'btn':       (50, 100, 170),
        'btn_hover': (60, 120, 200),
        'btn_text':  (220, 220, 240),
        'input_bg':  (42, 42, 52),
        'input_border': (65, 65, 78),
        'input_active': (70, 120, 200),
        'preview_bg': (28, 28, 36),
        'code_text': (155, 210, 155),
        'error':     (255, 100, 100),
        'success':   (100, 220, 100),
        'slot_init': (220, 160, 60),
        'slot_evol': (100, 180, 220),
        'slot_col':  (180, 120, 220),
    }

    def __init__(self, screen, fonts, effects_dir):
        """
        Args:
            screen: Pygame display surface
            fonts: dict with 'title', 'normal', 'small' keys
            effects_dir: Path to effects/ directory
        """
        self.screen = screen
        self.win_w = screen.get_width()
        self.win_h = screen.get_height()
        self.font_title = fonts.get('title')
        self.font = fonts.get('normal')
        self.font_small = fonts.get('small')
        self.effects_dir = Path(effects_dir)

        # 模板数据
        self.init_templates = list(FORMULA_TEMPLATES['init'].items())
        self.evo_templates = list(FORMULA_TEMPLATES['evolution'].items())
        self.col_templates = list(FORMULA_TEMPLATES['color'].items())

        # 选择状态
        self.sel_init = 0
        self.sel_evo = 0
        self.sel_col = 0

        # 滚动
        self.scroll_init = 0
        self.scroll_evo = 0
        self.scroll_col = 0

        # 输入
        self.name_input = ""
        self.input_active = True
        self.grid_w = 256
        self.grid_h = 192

        # 结果
        self.generated_path = None
        self.generated_recipe = None
        self.status_msg = None
        self.status_timer = 0

        # 帮助提示
        self.show_help = False

        # 面板布局计算
        self._calc_layout()

    def _calc_layout(self):
        """计算面板位置"""
        gap = 4
        self.panels_x = {
            'init': gap,
            'evo':  gap + self.PANEL_W + gap,
            'col':  gap + (self.PANEL_W + gap) * 2,
        }
        self.preview_x = self.panels_x['col'] + self.PANEL_W + gap
        self.list_y = self.HEADER_H
        self.list_h = self.win_h - self.HEADER_H - self.BOTTOM_H
        self.visible_rows = self.list_h // self.ROW_H

        # 按钮区域
        self.bottom_y = self.win_h - self.BOTTOM_H
        btn_w = 130
        self.btn_gen_rect = pygame.Rect(
            self.preview_x + 10, self.bottom_y + 10, btn_w, 30)
        self.btn_apply_rect = pygame.Rect(
            self.btn_gen_rect.right + 15, self.bottom_y + 10, btn_w, 30)

        # 名称输入区域
        self.input_rect = pygame.Rect(
            self.preview_x + 10, self.bottom_y - 26, 130, 22)

    # ================================================================
    #  绘制
    # ================================================================
    def draw(self):
        """绘制整个编辑器"""
        # 半透明遮罩
        overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        self.screen.blit(overlay, (0, 0))

        # 标题栏
        self._draw_header()

        # 三个模板列
        self._draw_panel('init', '初始化', self.init_templates, self.sel_init,
                         self.scroll_init, self.panels_x['init'])
        self._draw_panel('evo', '演化规则', self.evo_templates, self.sel_evo,
                         self.scroll_evo, self.panels_x['evo'])
        self._draw_panel('col', '颜色映射', self.col_templates, self.sel_col,
                         self.scroll_col, self.panels_x['col'])

        # 预览区
        self._draw_preview()

        # 底部操作区
        self._draw_bottom()

        # 帮助
        if self.show_help:
            self._draw_help()

        # 状态消息
        if self.status_msg and self.status_timer > 0:
            self._draw_status()

    def _draw_header(self):
        """标题栏"""
        header = pygame.Rect(0, 0, self.win_w, self.HEADER_H)
        pygame.draw.rect(self.screen, self.COLORS['header_bg'], header)
        pygame.draw.line(self.screen, self.COLORS['border'],
                         (0, self.HEADER_H), (self.win_w, self.HEADER_H))

        title = self.font.render('🧪 Recipe Composer', True, self.COLORS['text'])
        self.screen.blit(title, (10, 6))

        # 帮助按钮
        help_txt = self.font_small.render('[?] 帮助', True, self.COLORS['text_dim'])
        hx = self.win_w - 100
        self.help_btn_rect = pygame.Rect(hx - 4, 4, help_txt.get_width() + 8, 22)
        pygame.draw.rect(self.screen, (50, 50, 60), self.help_btn_rect, border_radius=4)
        self.screen.blit(help_txt, (hx, 7))

        # 关闭按钮
        close_txt = self.font_small.render('✕ 关闭 [ESC]', True, (200, 100, 100))
        cx = self.win_w - close_txt.get_width() - 14
        self.close_btn_rect = pygame.Rect(cx - 4, 4, close_txt.get_width() + 8, 22)
        pygame.draw.rect(self.screen, (60, 30, 30), self.close_btn_rect, border_radius=4)
        self.screen.blit(close_txt, (cx, 7))

    def _draw_panel(self, cat, title, templates, sel_idx, scroll, px):
        """绘制单列模板面板"""
        # 面板背景
        panel_rect = pygame.Rect(px, self.HEADER_H, self.PANEL_W, self.list_h)
        pygame.draw.rect(self.screen, self.COLORS['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, self.COLORS['border'], panel_rect, 1)

        # 列标题
        self.screen.blit(
            self.font_small.render(title, True, self.COLORS['text_dim']),
            (px + 6, self.HEADER_H + 4))

        # 列表项
        for i in range(scroll, min(scroll + self.visible_rows, len(templates))):
            name, info = templates[i]
            y = self.HEADER_H + 22 + (i - scroll) * self.ROW_H
            row_rect = pygame.Rect(px + 2, y, self.PANEL_W - 4, self.ROW_H)

            if i == sel_idx:
                pygame.draw.rect(self.screen, self.COLORS['selected'], row_rect, border_radius=4)
                pygame.draw.rect(self.screen, self.COLORS['selected_border'],
                                 row_rect, 1, border_radius=4)
                color = (240, 240, 255)
            else:
                color = self.COLORS['text_dim']

            dn = name[:14] + '…' if len(name) > 15 else name
            txt = self.font_small.render(dn, True, color)
            self.screen.blit(txt, (px + 8, y + 3))

        # 滚动条
        if len(templates) > self.visible_rows:
            thumb_h = max(16, self.visible_rows * self.list_h // len(templates))
            thumb_y = self.HEADER_H + scroll * self.list_h // len(templates)
            sbx = px + self.PANEL_W - 7
            pygame.draw.rect(self.screen, (50, 50, 58),
                             (sbx, thumb_y, 4, thumb_h), border_radius=2)

    def _draw_preview(self):
        """预览面板 —— 显示选中模板的公式"""
        px = self.preview_x
        pw = self.win_w - px - 8

        # 背景
        prev_rect = pygame.Rect(px, self.HEADER_H, pw, self.list_h)
        pygame.draw.rect(self.screen, self.COLORS['preview_bg'], prev_rect)
        pygame.draw.rect(self.screen, self.COLORS['border'], prev_rect, 1)

        self.screen.blit(
            self.font_small.render('预览', True, self.COLORS['text_dim']),
            (px + 6, self.HEADER_H + 4))

        y = self.HEADER_H + 24
        lh = 17

        # 槽位标签
        slots = [
            ('INIT', self.init_templates, self.sel_init, self.COLORS['slot_init']),
            ('EVOL', self.evo_templates, self.sel_evo, self.COLORS['slot_evol']),
            ('COL',  self.col_templates, self.sel_col, self.COLORS['slot_col']),
        ]

        for label, temps, idx, clr in slots:
            if idx < len(temps):
                name, info = temps[idx]
                # 标签
                lbl = self.font_small.render(f'▎ {label}', True, clr)
                self.screen.blit(lbl, (px + 8, y))
                # 模板名
                nm = self.font_small.render(name[:20], True, self.COLORS['text'])
                self.screen.blit(nm, (px + 55, y))
                y += lh

                # 描述
                desc = info.get('description', '')[:32]
                if desc:
                    ds = self.font_small.render(desc, True, self.COLORS['text_dim'])
                    self.screen.blit(ds, (px + 12, y))
                    y += lh

                # 公式
                if 'expression' in info:
                    expr = info['expression']
                    self._draw_code_line(px + 8, y, pw - 16, expr)
                    y += lh

                if 'red' in info:
                    for ch in ['red', 'green', 'blue']:
                        line = f"  {ch[0].upper()}: {info[ch]}"
                        cs = self.font_small.render(line[:36], True, self.COLORS['code_text'])
                        self.screen.blit(cs, (px + 8, y))
                        y += lh
                y += 4

    def _draw_code_line(self, x, y, max_w, text):
        """分行绘制代码文本"""
        words = text.replace('(', '( ').replace(')', ' )').split()
        line = ""
        ly = y
        for w in words:
            test = line + (" " if line else "") + w
            if self.font_small.size(test)[0] > max_w - 16 and line:
                cs = self.font_small.render(line.strip(), True, self.COLORS['code_text'])
                self.screen.blit(cs, (x, ly))
                ly += 15
                line = w
            else:
                line = test
        if line:
            cs = self.font_small.render(line.strip(), True, self.COLORS['code_text'])
            self.screen.blit(cs, (x, ly))

    def _draw_bottom(self):
        """底部操作栏"""
        # 背景
        bottom = pygame.Rect(0, self.bottom_y, self.win_w, self.BOTTOM_H)
        pygame.draw.rect(self.screen, self.COLORS['header_bg'], bottom)
        pygame.draw.line(self.screen, self.COLORS['border'],
                         (0, self.bottom_y), (self.win_w, self.bottom_y))

        # 名称标签
        nlbl = self.font_small.render('名称:', True, self.COLORS['text_dim'])
        self.screen.blit(nlbl, (self.preview_x + 10, self.bottom_y + 7))
        # 名称输入框
        irect = pygame.Rect(self.preview_x + 48, self.bottom_y + 5, 130, 22)
        self.input_rect = irect
        border_c = self.COLORS['input_active'] if self.input_active else self.COLORS['input_border']
        pygame.draw.rect(self.screen, self.COLORS['input_bg'], irect, border_radius=4)
        pygame.draw.rect(self.screen, border_c, irect, 1, border_radius=4)
        cursor = '│' if self.input_active and (pygame.time.get_ticks() // 500) % 2 == 0 else ''
        disp = (self.name_input[:18] + cursor) if self.name_input else ('_' + cursor)
        nt = self.font_small.render(disp, True, self.COLORS['text'])
        self.screen.blit(nt, (irect.x + 6, irect.y + 3))

        # 网格尺寸
        sz_txt = self.font_small.render(f"w:{self.grid_w} h:{self.grid_h}", True, self.COLORS['text_dim'])
        self.screen.blit(sz_txt, (irect.right + 14, self.bottom_y + 8))

        # 生成按钮
        self._draw_button(self.btn_gen_rect, '📦 生成 JSON', self.COLORS['btn'])
        # 生成并应用
        self._draw_button(self.btn_apply_rect, '▶ 生成并应用', (40, 130, 50))

    def _draw_button(self, rect, text, color):
        """绘制按钮"""
        hover = rect.collidepoint(pygame.mouse.get_pos())
        c = self.COLORS['btn_hover'] if hover else color
        pygame.draw.rect(self.screen, c, rect, border_radius=5)
        pygame.draw.rect(self.screen, self.COLORS['border'], rect, 1, border_radius=5)
        txt = self.font_small.render(text, True, self.COLORS['btn_text'])
        self.screen.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2,
                               rect.y + (rect.h - txt.get_height()) // 2))

    def _draw_status(self):
        """状态消息"""
        color = self.COLORS['success'] if not isinstance(self.status_msg, tuple) \
                else self.status_msg[1]
        msg = self.status_msg if isinstance(self.status_msg, str) else self.status_msg[0]
        txt = self.font_small.render(msg, True, color)
        tw = txt.get_width()
        bar = pygame.Surface((tw + 16, 22), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 180))
        self.screen.blit(bar, (self.win_w // 2 - tw // 2 - 8, 10))
        self.screen.blit(txt, (self.win_w // 2 - tw // 2, 12))

    def _draw_help(self):
        """帮助覆盖"""
        ov = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.screen.blit(ov, (0, 0))

        lines = [
            ('操作说明', (255, 255, 200), self.font),
            ('', None, self.font),
            ('鼠标点击 → 选择模板', (200, 200, 200), self.font_small),
            ('鼠标滚轮 → 滚动列表', (200, 200, 200), self.font_small),
            ('Tab / Shift+Tab → 切换面板', (200, 200, 200), self.font_small),
            ('输入名称 → 配方名称', (200, 200, 200), self.font_small),
            ('Enter → 生成 JSON 文件', (200, 200, 200), self.font_small),
            ('Ctrl+Enter → 生成并立即应用', (200, 200, 200), self.font_small),
            ('ESC → 关闭编辑器', (200, 200, 200), self.font_small),
            ('', None, self.font),
            ('每个模板 = 初始化图案 + 演化规则 + 颜色方案', (160, 160, 180), self.font_small),
            ('组合后生成 JSON 配方文件到 effects/ 目录', (160, 160, 180), self.font_small),
        ]

        y = self.win_h // 2 - len(lines) * 12
        for text, color, font in lines:
            if text and color:
                t = font.render(text, True, color)
                self.screen.blit(t, (self.win_w // 2 - t.get_width() // 2, y))
            y += 24

    # ================================================================
    #  事件处理
    # ================================================================
    def handle_event(self, event):
        """处理事件。返回动作字符串或 None。"""
        action = None

        if event.type == pygame.KEYDOWN:
            action = self._handle_key(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            action = self._handle_click(event)

        return action

    def _handle_key(self, event):
        key = event.key
        mods = pygame.key.get_mods()

        if key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            else:
                return 'close'

        elif key == pygame.K_TAB:
            if mods & pygame.KMOD_SHIFT:
                self.input_active = not self.input_active
            else:
                self.input_active = not self.input_active

        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if mods & pygame.KMOD_CTRL:
                return 'generate_apply'
            else:
                return 'generate'

        elif self.input_active:
            if key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            elif key == pygame.K_v and mods & pygame.KMOD_CTRL:
                pass  # 暂不支持粘贴
            elif key < 128 and len(self.name_input) < 30:
                char = event.unicode
                if char and char.isprintable():
                    self.name_input += char

        return None

    def _handle_click(self, event):
        mx, my = event.pos

        # 关闭按钮
        if hasattr(self, 'close_btn_rect') and self.close_btn_rect.collidepoint(mx, my):
            if self.show_help:
                self.show_help = False
            else:
                return 'close'

        # 帮助按钮
        if hasattr(self, 'help_btn_rect') and self.help_btn_rect.collidepoint(mx, my):
            self.show_help = not self.show_help
            return None

        # 生成按钮
        if self.btn_gen_rect.collidepoint(mx, my):
            return 'generate'
        if self.btn_apply_rect.collidepoint(mx, my):
            return 'generate_apply'

        # 名称输入框
        if self.input_rect.collidepoint(mx, my):
            self.input_active = True
            return None

        # 面板点击
        for cat, temps, sel_attr, scroll_attr, px in [
            ('init', self.init_templates, 'sel_init', 'scroll_init', self.panels_x['init']),
            ('evo',  self.evo_templates, 'sel_evo', 'scroll_evo', self.panels_x['evo']),
            ('col',  self.col_templates, 'sel_col', 'scroll_col', self.panels_x['col']),
        ]:
            if px <= mx < px + self.PANEL_W and self.HEADER_H <= my < self.HEADER_H + self.list_h:
                scroll = getattr(self, scroll_attr)
                clicked = scroll + (my - self.HEADER_H - 22) // self.ROW_H
                if 0 <= clicked < len(temps):
                    setattr(self, sel_attr, clicked)
                    self.input_active = False
                return None

        # 点击空白区失焦
        self.input_active = False
        return None

    def handle_scroll(self, y_offset):
        """处理滚轮事件"""
        mx, _ = pygame.mouse.get_pos()

        for cat, temps, scroll_attr, px in [
            ('init', self.init_templates, 'scroll_init', self.panels_x['init']),
            ('evo',  self.evo_templates, 'scroll_evo', self.panels_x['evo']),
            ('col',  self.col_templates, 'scroll_col', self.panels_x['col']),
        ]:
            if px <= mx < px + self.PANEL_W:
                scroll = getattr(self, scroll_attr)
                max_scroll = max(0, len(temps) - self.visible_rows)
                new_scroll = max(0, min(max_scroll, scroll - y_offset))
                setattr(self, scroll_attr, new_scroll)
                break

    # ================================================================
    #  生成
    # ================================================================
    def generate(self, apply_now=False):
        """生成配方 JSON。apply_now=True 时返回 recipe dict 供立即应用。"""
        init_name, init_info = self.init_templates[self.sel_init]
        evo_name, _ = self.evo_templates[self.sel_evo]
        col_name, _ = self.col_templates[self.sel_col]

        default_name = f'{init_name} × {evo_name} × {col_name}'
        name = self.name_input.strip() or default_name

        try:
            recipe = generate_recipe_from_templates(
                init_name, evo_name, col_name, name=name,
                w=self.grid_w, h=self.grid_h)

            if apply_now:
                self.generated_recipe = recipe
                self.status_msg = f'已应用: {name}'
                self.status_timer = 120
                return recipe

            # 保存到文件
            safe = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            out = self.effects_dir / f'{safe}.json'
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(recipe, f, indent=2, ensure_ascii=False)
            self.generated_path = out
            self.status_msg = f'✓ 已保存: {out.name}'
            self.status_timer = 120
            return out

        except Exception as e:
            self.status_msg = (f'✗ 生成失败: {e}', self.COLORS['error'])
            self.status_timer = 180
            return None

    def update(self):
        """每帧更新（计时器等）"""
        if self.status_timer > 0:
            self.status_timer -= 1
            if self.status_timer <= 0:
                self.status_msg = None
