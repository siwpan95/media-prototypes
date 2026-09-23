# -*- mode: python ; coding: utf-8 -*-
# shikonghuaban 安装包样板 spec（2026-08-25）
import os

# 2026-09-28 去本地化：源码路径改由 SPECPATH 推导
# （SPECPATH 为 PyInstaller 注入的全局变量 = 本 spec 文件所在目录 = 仓库根；
#   原 G:/media/shikonghuaban 已不存在）
_PKG_ROOT = SPECPATH

a = Analysis(
    [os.path.join(_PKG_ROOT, 'run.py')],
    pathex=[_PKG_ROOT],
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
