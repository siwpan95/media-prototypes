"""
P0 headless test bootstrap for 时空画板 / Space-Time Canvas.

This module is imported by pytest BEFORE any application module or test file,
so it must establish the headless environment first:

  1. Force SDL dummy video/audio drivers so pygame can import headlessly
     (no real display or PortAudio is needed for the pure-logic unit tests).
  2. Put the repo root on sys.path so the ``shikonghuaban`` package (which now
     holds ``config``, ``state``, ``audio_engine``, ``blackhole_physics`` …)
     is importable.
  3. Inject the bundled particle toolkit exactly like particle_effects.py does:
     add ``shikonghuaban/particle/`` to sys.path so ``core.particle`` resolves.
  4. Stub ``sounddevice`` (PortAudio is unavailable in CI/headless) so that
     audio_engine imports cleanly. The stub only needs to cover the API the
     module touches at import / static-method time.
  5. Import pygame once (guarded) to trigger the dummy backend init.
"""

import os
import sys
import types

# ── 1. Headless SDL drivers (must be set before any pygame import) ──
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# ── 2. sys.path wiring ──
# 只需保证仓库根在 sys.path，使 shikonghuaban 包可导入；
# particle 已是其子包，不再需要把 particle/ 单独塞进 sys.path。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ── 3. Stub sounddevice (no PortAudio in headless CI) ──
if "sounddevice" not in sys.modules:
    _fake_sd = types.ModuleType("sounddevice")

    class _OutputStream:
        """Minimal stand-in for sounddevice.OutputStream / RawOutputStream."""

        def __init__(self, *args, **kwargs):
            self.started = False

        def start(self):
            self.started = True

        def stop(self):
            self.started = False

        def close(self):
            self.started = False

    _fake_sd.OutputStream = _OutputStream
    _fake_sd.RawOutputStream = _OutputStream
    _fake_sd.InputStream = _OutputStream

    def _query_devices(*_args, **_kwargs):
        return {}

    _fake_sd.query_devices = _query_devices
    _fake_sd.query_hostapis = _query_devices
    _fake_sd.default = None

    sys.modules["sounddevice"] = _fake_sd

# ── 4. Trigger pygame dummy init once (guarded; pure tests don't need it) ──
try:
    import pygame  # noqa: E402

    if not pygame.display.get_init():
        pygame.display.init()
except Exception as exc:  # pragma: no cover - environment dependent
    print(f"[conftest] WARNING: pygame unavailable headless: {exc}")
