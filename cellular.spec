# -*- mode: python ; coding: utf-8 -*-
# cellular_automaton 安装包样板 spec（2026-08-25，pywallpaper 样板同款）
a = Analysis(
    ['G:/media/cellular_automaton/main.py'],
    pathex=['G:/media/cellular_automaton'],
    binaries=[],
    datas=[
        ('G:/media/cellular_automaton/rules', 'rules'),
        ('G:/media/cellular_automaton/dinglieciweifont20250217-2.ttf', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # scipy 的 array_api_compat.common._helpers 顶层 import torch/cupy/dask/jax/ndonnx/sparse；
    # scipy.stats._fit/_survival 的字节码 import matplotlib（matplotlib.pyplot 又 import pandas），
    # 会把整个 ML/科学计算生态拖进依赖图；运行时均不加载，安全排除。
    excludes=['torch', 'cupy', 'dask', 'jax', 'ndonnx', 'sparse', 'sqlalchemy', 'matplotlib', 'pandas'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='cellular',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    contents_directory='.',
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='cellular')
