import time
import math
from physics.fan_physics import FanPhysics
from physics.aerodynamics import Aerodynamics
from physics.motor_model import MotorModel
from audio.audio_engine import AudioEngine

class Engine:
    def __init__(self, root):
        self.root = root

        self.physics = FanPhysics()
        self.aero      = Aerodynamics()
        self.motor     = MotorModel()
        self.audio     = AudioEngine()

        from ui.ui_renderer import UIRenderer
        self.ui = UIRenderer(root, self)

        # 状态
        self.is_running  = False
        self.power       = 0.0
        self.wind_speed  = 5.0
        self.joke_mode   = False
        self.anim_id     = None

        self.audio.start()
        self.ui.draw_initial_state()

    # ── 电源控制 ──────────────────────────────────────────────
    def toggle_power(self):
        if self.is_running:
            self.shutdown()
        else:
            self.startup()

    def emergency_stop(self):
        self.is_running = False
        self.power = 0.0
        self.physics.target_velocity = 0.0
        self.audio.set_speed(0.0)
        self.audio.play_transient("shutdown")
        self.audio.play_transient("click_off")
        self.ui.update_status("紧急停止")

    def startup(self):
        self.is_running = True
        self.power = 0.1
        self.physics.target_velocity = 50.0
        self.audio.set_speed(0.1)
        self.audio.play_transient("startup")
        self.audio.play_transient("click_on")
        self.ui.update_status("启动中...")
        self.animate()

    def shutdown(self):
        self.is_running = False
        self.power = 0.0
        self.physics.target_velocity = 0.0
        self.audio.set_speed(0.0)
        self.audio.play_transient("shutdown")
        self.audio.play_transient("click_off")
        self.ui.update_status("关闭中...")

    # ── 参数设置 ──────────────────────────────────────────────
    def set_power(self, value):
        self.power = float(value)
        self.physics.target_velocity = float(value) * 50.0
        self.audio.set_speed(float(value))
        if hasattr(self, 'ui') and self.ui is not None:
            self.ui.update_status(f"功率: {int(value)}/10",
                                  power=int(value), wind=int(self.wind_speed))

    def set_wind_speed(self, value):
        self.wind_speed = float(value)
        self.audio.set_wind_speed(float(value))
        if hasattr(self, 'ui') and self.ui is not None:
            self.ui.update_status(f"风速: {int(value)}/10",
                                  power=int(self.power), wind=int(value))

    def toggle_joke_mode(self):
        self.joke_mode = self.audio.toggle_joke_mode()
        msg = "恶搞模式 ON" if self.joke_mode else "恶搞模式 OFF"
        if hasattr(self, 'ui') and self.ui is not None:
            self.ui.update_status(msg)

    # ── 主循环 ──────────────────────────────────────────────
    def animate(self):
        dt = 0.016
        rpm = self.physics.update(
            self.motor.torque_at(self.physics.get_rpm()), dt)

        self.ui.update_fan_blades(rpm)
        self.ui.update_diagnostics(
            rpm=rpm,
            temp=self.physics.temperature,
            wear=self.physics.wear_level,
            efficiency=self.motor.efficiency(rpm),
            wind_speed=self.wind_speed
        )

        if self.physics.is_damaged:
            self.audio.play_fault(self.physics.damage_type)
            self.ui.update_status("故障")

        if self.is_running or self.physics.get_rpm() > 1:
            self.anim_id = self.root.after(16, self.animate)
        else:
            self.audio.stop()
            self.ui.update_status("已停止")
