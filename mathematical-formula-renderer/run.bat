@echo off
chcp 65001 >nul
cd /d "%~dp0"
@REM 自发现 Python（不写死本机路径）：优先官方启动器 py，其次 PATH 里的 python
set "PYEXE="
where py >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE ( where python >nul 2>nul && set "PYEXE=python" )
if not defined PYEXE (
    echo [X] 找不到 Python。请安装 Python 3.x 并确保 py 或 python 在 PATH 中。
    pause
    exit /b 1
)
%PYEXE% main.py %*
pause
