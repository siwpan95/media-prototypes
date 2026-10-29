# Cellular Automata - Formula Lab

A cellular automata simulation tool with pluggable formula support.

## Structure

```
bofang/
├── main.py              # Application entry point
├── config.py            # Configuration settings
├── model/               # Data layer
│   ├── __init__.py
│   ├── grid.py          # Grid state management
│   └── formula_loader.py # Formula loading
├── view/                # Presentation layer
│   ├── __init__.py
│   ├── renderer.py      # Pygame rendering
│   └── ui.py            # UI components
├── controller/           # Business logic
│   ├── __init__.py
│   └── game_controller.py
└── resources/           # Formula files
    └── spiral.py
```

## Running

```bash
python main.py
```

## Building Executable

Using PyInstaller:

```bash
pyinstaller --onefile --windowed main.py
```

Or with spec file for better resource handling.

## Creating Custom Formulas

Create a `.py` file with an `update` function:

```python
NAME = "My Formula"

def update(u, v, Du, Dv, F, k, dt, dx):
    Lu = (np.roll(u, 1, 0) + np.roll(u, -1, 0) +
          np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4*u) / dx**2
    new_u = u + Du * Lu * dt
    new_v = v * 0.99
    return np.clip(new_u, 0, 1), np.clip(new_v, 0, 1)
```

Optional functions:
- `get_display(v)` - customize display
- `init_state(H, W)` - custom initial state
