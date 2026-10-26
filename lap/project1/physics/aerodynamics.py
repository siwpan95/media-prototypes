import math

class Aerodynamics:
    def __init__(self):
        self.air_density = 1.225
        self.blade_area = 0.05
        self.lift_coeff = 0.8
        self.drag_coeff = 0.02

    def compute_thrust(self, rpm):
        v = rpm / 60.0
        return 0.5 * self.air_density * self.blade_area * self.lift_coeff * v ** 2

    def compute_drag_torque(self, rpm):
        omega = rpm * (2 * math.pi) / 60.0
        return self.drag_coeff * omega ** 2

    def wind_noise_gain(self, rpm):
        return min(rpm / 3000.0, 1.0)