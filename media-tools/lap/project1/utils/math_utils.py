import math
import numpy as np

def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))

def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0.0, 1.0)

def exponential_decay(current, target, factor, dt):
    return target + (current - target) * math.exp(-factor * dt)

def rpm_to_rad_per_sec(rpm):
    return rpm * (2 * math.pi) / 60

def rad_per_sec_to_rpm(omega):
    return omega * 60 / (2 * math.pi)

def white_noise(length, scale=1.0):
    return np.random.randn(length) * scale