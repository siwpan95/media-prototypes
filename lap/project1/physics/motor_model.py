class MotorModel:
    def __init__(self):
        self.stall_torque = 1.2
        self.no_load_speed = 4000
        self.resistance = 1.5
        self.inductance = 0.01
        self.voltage = 12.0

    def torque_at(self, rpm):
        speed_ratio = rpm / self.no_load_speed
        return self.stall_torque * (1.0 - min(speed_ratio, 1.0))

    def current_draw(self, torque):
        return (torque / self.stall_torque) * 10.0

    def efficiency(self, rpm):
        if rpm <= 0:
            return 0.0
        torque = self.torque_at(rpm)
        power_out = torque * (rpm * 3.14159 / 30.0)
        power_in = self.voltage * self.current_draw(torque)
        return min(power_out / max(power_in, 1e-6), 1.0)