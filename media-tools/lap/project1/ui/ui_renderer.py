import tkinter as tk
from tkinter import ttk
import math
import time


class UIRenderer:
    def __init__(self, root, engine):
        self.root = root
        self.engine = engine
        self._blade_angle = 0.0   # 累积角度（避免混叠）
        self._last_time = time.time()
        self._power = 0
        self._wind = 5

        self.main = tk.Frame(root, bg="#1a1a1a")
        self.main.pack(fill="both", expand=True)

        # 左侧：风扇
        self.left = tk.Frame(self.main, bg="#1a1a1a")
        self.left.pack(side="left", padx=10, pady=10)

        self.canvas = tk.Canvas(
            self.left, width=400, height=400,
            bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack()

        self.status = tk.Label(
            self.left, text="状态: 待机",
            font=("Consolas", 12),
            fg="#00ff00", bg="#1a1a1a")
        self.status.pack(pady=5)

        # 右侧：控制 + 诊断
        self.right = tk.Frame(self.main, bg="#1a1a1a")
        self.right.pack(side="right", padx=10, pady=10, fill="y")

        self._build_controls()
        self._build_diagnostics()

    # ── 构建 UI ──────────────────────────────────────────────
    def _build_controls(self):
        f = tk.LabelFrame(
            self.right, text="控制面板",
            font=("Consolas", 10, "bold"),
            fg="#00ff00", bg="#2a2a2a")
        f.pack(fill="x", pady=(0, 5))

        # 功率
        tk.Label(f, text="功率 (0-10):",
                 fg="#cccccc", bg="#2a2a2a",
                 font=("Consolas", 9)).pack(anchor="w", padx=5)
        self.pow_scale = ttk.Scale(
            f, from_=0, to=10,
            command=lambda v: self.engine.set_power(float(v)))
        self.pow_scale.set(0)
        self.pow_scale.pack(fill="x", padx=5, pady=(0, 5))

        # 风速
        tk.Label(f, text="风速 (0-10):",
                 fg="#cccccc", bg="#2a2a2a",
                 font=("Consolas", 9)).pack(anchor="w", padx=5)
        self.wind_scale = ttk.Scale(
            f, from_=0, to=10,
            command=lambda v: self.engine.set_wind_speed(float(v)))
        self.wind_scale.set(5)
        self.wind_scale.pack(fill="x", padx=5, pady=(0, 5))

        # 恶搞模式
        self.joke_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            f, text="恶搞音效",
            variable=self.joke_var,
            command=self._on_joke,
            fg="#ff9900", bg="#2a2a2a",
            selectcolor="#1a1a1a",
            activeforeground="#ff9900",
            activebackground="#2a2a2a",
            font=("Consolas", 9)
        ).pack(anchor="w", padx=5, pady=(5, 5))

        # 启动/停止
        self.toggle_btn = tk.Button(
            f, text="启动",
            command=self.engine.toggle_power,
            font=("Consolas", 10),
            bg="#004400", fg="#00ff00", width=12)
        self.toggle_btn.pack(pady=(5, 3))

        # 紧急停止
        tk.Button(
            f, text="紧急停止",
            command=self.engine.emergency_stop,
            font=("Consolas", 10),
            bg="#440000", fg="#ff4444", width=12
        ).pack(pady=(0, 5))

    def _build_diagnostics(self):
        f = tk.LabelFrame(
            self.right, text="系统诊断",
            font=("Consolas", 10, "bold"),
            fg="#00ff00", bg="#2a2a2a")
        f.pack(fill="x", pady=5)

        self.rpm_var  = tk.StringVar(value="RPM: 0")
        self.temp_var = tk.StringVar(value="温度: 25.0 °C")
        self.wear_var = tk.StringVar(value="磨损: 0.0 %")
        self.eff_var  = tk.StringVar(value="效率: 100 %")
        self.wind_var = tk.StringVar(value="风速: 5")

        for var in (self.rpm_var, self.temp_var,
                     self.wear_var, self.eff_var, self.wind_var):
            tk.Label(f, textvariable=var,
                     fg="#dddddd", bg="#2a2a2a",
                     font=("Consolas", 9)).pack(anchor="w", padx=5, pady=1)

    # ── 回调 ──────────────────────────────────────────────
    def _on_joke(self):
        self.engine.toggle_joke_mode()

    # ── 公共接口 ──────────────────────────────────────────────
    def draw_initial_state(self):
        self._draw_base()
        self._draw_blades(0)

    def update_fan_blades(self, rpm):
        self._draw_blades(rpm)

    def update_status(self, text, power=None, wind=None):
        if power is not None:
            self._power = int(power)
        if wind is not None:
            self._wind = int(wind)

        cmap = {
            "启动中...":    "#ffff00",
            "运行中":       "#00ff00",
            "关闭中...":    "#ff9900",
            "已停止":       "#666666",
            "紧急停止":     "#ff0000",
            "故障":        "#ff0000",
            "恶搞模式 ON":  "#ff9900",
            "恶搞模式 OFF": "#00ff00",
        }
        color = cmap.get(text, "#ffffff")
        display = f"状态: {text} | 功率: {self._power}/10 | 风速: {self._wind}/10"
        self.status.config(text=display, fg=color)
        if "运行" in text:
            self.toggle_btn.config(text="停止", bg="#440000")
        else:
            self.toggle_btn.config(text="启动", bg="#004400")

    def update_diagnostics(self, rpm, temp, wear,
                            efficiency, wind_speed=5):
        self.rpm_var.set(f"RPM: {int(rpm)}")
        self.temp_var.set(f"温度: {temp:.1f} °C")
        self.wear_var.set(f"磨损: {wear*100:.1f} %")
        self.eff_var.set(f"效率: {efficiency*100:.0f} %")
        self.wind_var.set(f"风速: {int(wind_speed)}")

    # ── 绘图 ──────────────────────────────────────────────────
    def _draw_base(self):
        c = self.canvas
        c.delete("base")
        x, y = 200, 200
        c.create_oval(x-120, y-120, x+120, y+120,
                       outline="#444", width=3, tags="base")
        c.create_oval(x-20,  y-20,  x+20,  y+20,
                       fill="#666", outline="#888", tags="base")
        for i in range(3):
            a = math.radians(i * 120)
            ex = x + 80 * math.cos(a)
            ey = y + 80 * math.sin(a)
            c.create_line(x, y, ex, ey,
                           fill="#555", width=8, tags="base")

    def _draw_blades(self, rpm):
        c = self.canvas
        c.delete("blades")
        cx, cy = 200, 200
        # 基于时间增量累积角度，消除视觉混叠
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        # rpm → 度/秒: rpm / 60 * 360 = rpm * 6
        self._blade_angle += rpm * 6.0 * dt
        angle = self._blade_angle
        for i in range(3):
            ba = math.radians(angle + i * 120)
            pts = []
            for r in (30, 120):
                pts += [cx + r*math.cos(ba), cy + r*math.sin(ba)]
                perp = ba + math.pi/2
                off = 15 if r == 120 else 5
                pts += [cx + (r+off)*math.cos(perp),
                         cy + (r+off)*math.sin(perp)]
            col = "#4a90e2" if rpm > 100 else "#666666"
            c.create_polygon(pts, fill=col,
                              outline="#2171b5", tags="blades")
