# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# 全部源码已收进 shikonghuaban/ 包，collect_submodules 覆盖主模块、
# particle_effects 以及 bundled 的 particle 工具包。
hiddenimports = collect_submodules('shikonghuaban')

a = Analysis(
    ['shikonghuaban/main.py'],
    pathex=[],
    binaries=[],
    datas=[('shikonghuaban/particle', 'shikonghuaban/particle')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='fat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
