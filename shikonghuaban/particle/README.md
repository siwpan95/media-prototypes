# Particle System（独立粒子系统）

## 设计理念

1. **独立性**：不依赖任何项目，纯 Python + NumPy 实现
2. **可复制性**：复制整个目录到目标项目，微调即可使用
3. **简洁性**：只提供核心功能，不添加冗余特性

## 项目结构

```
particle/
├── core/
│   └── particle.py       # 核心粒子类（Particle, ParticleSystem, Emitter, ForceField）
├── renderers/
│   ├── pygame_renderer.py  # Pygame 渲染器（用于 pygame 项目）
│   └── pil_renderer.py     # PIL 渲染器（用于 PIL 项目）
├── examples/
│   └── fireworks.py       # 烟花效果示例
├── docs/
│   └── API.md            # API 文档（待创建）
└── README.md             # 本文件
```

## 核心类

### Particle（粒子）

单个粒子的数据结构：

```python
@dataclass
class Particle:
    x: float  # x 位置
    y: float  # y 位置
    vx: float  # x 速度
    vy: float  # y 速度
    life: float  # 剩余生命值 (0-1)
    max_life: float  # 最大生命值
    size: float  # 大小
    color: Tuple[int, int, int]  # RGB 颜色
    alpha: float = 1.0  # 透明度 (0-1)
```

### ParticleSystem（粒子系统管理器）

管理所有粒子、发射器和力场：

```python
ps = ParticleSystem(max_particles=1000)
ps.add_emitter(emitter)
ps.add_force_field(gravity)
ps.update(dt, audio_data)
ps.render(renderer)
```

### Emitter（发射器）

发射粒子：

```python
emitter = Emitter(
    x=width//2, y=height,
    rate=50.0,  # 发射速率（粒子/秒）
    spread=3.14,  # 扩散角度（弧度）
    speed=200.0,  # 发射速度
    life=2.0,  # 粒子生命值
    size=3.0,  # 粒子大小
    color=(255, 200, 50)  # 粒子颜色
)
```

### ForceField（力场）

模拟重力、风力、吸引力等：

```python
# 重力（向下）
gravity = ForceField(field_type='gravity', strength=100.0)

# 风力（向右）
wind = ForceField(field_type='wind', strength=50.0)

# 吸引力（指向某点）
attractor = ForceField(field_type='attraction', x=400, y=300, strength=200.0)
```

## 使用方法

### 1. 复制到目标项目

```bash
# 复制到 pywallpaper 项目（旧路径，pywallpaper 现已内置 particle.py 原语）
cp -r particle/ D:/allin/right/pywallpaper/particle/
```

### 2. 微调适配

根据目标项目的架构进行微调：

- **pywallpaper**：已集成 `particle.py` 原语，可以直接使用
- **draw**：已归档至 `G:media_archivedraw`（2026-08-21），不再作为集成目标

### 3. 使用示例

```python
from particle.core.particle import ParticleSystem, Emitter, ForceField
from particle.renderers.pygame_renderer import PygameRenderer

# 创建粒子系统
ps = ParticleSystem(max_particles=1000)

# 创建发射器
emitter = Emitter(x=400, y=300, rate=50.0, ...)
ps.add_emitter(emitter)

# 创建力场
gravity = ForceField(field_type='gravity', strength=100.0)
ps.add_force_field(gravity)

# 更新和渲染
ps.update(dt)
renderer = PygameRenderer(screen)
ps.render(renderer)
```

## 示例效果

### 烟花（Fireworks）

```bash
cd examples/
python fireworks.py
```

### 其他效果（待创建）

- 雨水（Rain）
- 雪花（Snow）
- 爆炸（Explosion）
- 魔法效果（Magic）

## 音频驱动

粒子系统支持音频驱动：

```python
# 更新时传入音频数据
audio_data = {
    'rms': 0.5,  # 音频 RMS 能量
    'beat': True,  # 是否检测到节拍
    'band_energy': [0.1, 0.2, 0.3]  # 频段能量
}
ps.update(dt, audio_data)
```

在 `Emitter.emit()` 中，可以根据 `audio_data` 调整发射速率：

```python
if audio_data:
    energy = audio_data.get('rms', 1.0)
    current_rate *= (1.0 + energy * 2.0)  # 根据音频能量调整发射速率
```

## 性能优化

### NumPy 向量化

将粒子数据存储在 NumPy 数组中，使用向量化计算：

```python
# TODO: 创建 ParticleSystemNumpy 类
class ParticleSystemNumpy:
    def __init__(self):
        self.positions = np.zeros((max_particles, 2))  # x, y
        self.velocities = np.zeros((max_particles, 2))  # vx, vy
        self.lives = np.zeros(max_particles)  # life
        # ...
```

### Numba JIT 编译

使用 Numba 编译粒子更新循环：

```python
from numba import jit

@jit(nopython=True)
def update_particles(positions, velocities, lives, dt):
    # ...
```

## 依赖

- **必需**：NumPy
- **可选**：Pygame（用于 `pygame_renderer.py`）、Pillow（用于 `pil_renderer.py`）

## 许可证

MIT License（可自由复制、修改、使用）

## 作者

- 全哥（独立开发者）
- AI 助手（WorkBuddy）

## 更新日志

- **2026-06-23**：初始版本，创建核心类和示例效果
