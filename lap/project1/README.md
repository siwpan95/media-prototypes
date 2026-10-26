# 工业级风扇仿真系统

基于 Python 的桌面级工业风扇物理仿真与可视化系统。

## 功能特性

- **物理仿真**：完整的风扇动力学模型（转动惯量、轴承摩擦、空气阻力）
- **电机模型**：直流电机扭矩曲线、电流计算、效率分析
- **气动计算**：推力、阻力扭矩、风噪增益
- **故障模拟**：随机故障触发（磨损累积 → 叶片/轴承/电机故障）
- **工业可视化**：3 叶片 Canvas 风扇动画，实时状态颜色映射
- **音频合成**：4 通道音频引擎 + 程序化故障音效 + DSP 效果器（多普勒/共振峰/变调）

## 运行方式

```bash
pip install -r requirements.txt
python main.py
```

## 项目结构

```
├── main.py              # 入口
├── engine.py            # 核心引擎（60FPS 主循环）
├── physics/             # 物理模拟
│   ├── fan_physics.py   #   风扇动力学
│   ├── aerodynamics.py  #   空气动力学
│   └── motor_model.py   #   电机模型
├── audio/               # 音频引擎
│   ├── audio_engine.py  #   四通道音频主控
│   ├── external_sfx.py  #   外部采样加载
│   ├── fault_audio.py   #   程序化故障音效
│   └── sfx_layer.py     #   DSP 效果器
├── ui/                  # 用户界面
│   └── ui_renderer.py   #   Canvas 渲染 + 控制面板
├── utils/               # 工具
│   ├── config.py        #   全局配置
│   └── math_utils.py    #   数学工具函数
└── assets/sfx/          # 音频资源
```

## 依赖

- Python 3.11+
- numpy
- scipy
- pygame-ce
- tkinter（Python 内置）
