import math
import random

class FanPhysics:
    def __init__(self):
        self.moment_of_inertia = 0.1
        self.bearing_friction = 0.005
        self.max_temp = 80.0
        self.angular_velocity = 0.0
        self.target_velocity = 0.0
        self.temperature = 25.0
        self.wear_level = 0.0
        self.is_damaged = False
        self.damage_type = None

    def update(self, torque, dt=0.016):
        acceleration = torque / self.moment_of_inertia
        friction = -self.bearing_friction * abs(self.angular_velocity)
        self.angular_velocity += (acceleration + friction) * dt
        diff = self.target_velocity - self.angular_velocity
        self.angular_velocity += diff * 0.1 * dt
        
        heat = abs(torque * self.angular_velocity) * 0.001
        self.temperature += heat * dt
        self.temperature -= (self.temperature - 25.0) * 0.001 * dt
        
        wear_rate = abs(self.angular_velocity) * 0.00001
        self.wear_level += wear_rate * dt
        
        if self.wear_level > 0.8 and random.random() < 0.001:
            self.is_damaged = True
            self.damage_type = random.choice(["bearing", "blade", "motor"])
        
        return self.get_rpm()

    def get_rpm(self):
        return abs(self.angular_velocity * 60 / (2 * math.pi))