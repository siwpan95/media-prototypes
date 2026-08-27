# -*- mode: python ; coding: utf-8 -*-
# shikonghuaban 安装包样板 spec（2026-08-25）
a = Analysis(
    ['G:/media/shikonghuaban/run.py'],
    pathex=['G:/media/shikonghuaban'],
    binaries=[],
    datas=[],
    hiddenimports=['sounddevice'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='shikonghuaban',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    contents_directory='.',
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='shikonghuaban')
