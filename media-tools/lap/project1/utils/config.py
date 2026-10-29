# 物理参数
PHYSICS_CONFIG = {
    "moment_of_inertia": 0.1,
    "drag_coefficient": 0.02,
    "bearing_friction": 0.005,
    "motor_torque": 0.5,
    "max_temperature": 80.0,
    "failure_threshold": 0.85
}

# 音频配置
AUDIO_CONFIG = {
    "sample_rate": 44100,
    "buffer_size": 256,
    "master_volume": 0.8,
    "doppler_intensity": 0.5,
    "formant_range": (300, 800)
}

# UI配置
UI_CONFIG = {
    "window_size": (900, 650),
    "canvas_size": (400, 400),
    "color_scheme": "industrial"
}