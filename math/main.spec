# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# 入口脚本：由本 spec 所在目录推导（去本地化，原硬编码绝对路径已失效）
a = Analysis(
    [os.path.join(SPECPATH, 'main.py')],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(os.getcwd(), 'resources'), 'resources')],
    hiddenimports=['pygame', 'pygame_gui'],
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
    [],
    exclude_binaries=True,
    name='MathSimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_excludes=[],
    name='MathSimulator',
)
