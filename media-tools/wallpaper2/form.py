import os
import sys
import ctypes
import subprocess
from pathlib import Path

def set_wallpaper(image_path):
    """设置桌面壁纸"""
    if not Path(image_path).exists():
        print(f"错误：文件 '{image_path}' 不存在")
        return False
    
    system = sys.platform.lower()
    
    try:
        if system == "win32":
            # Windows
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, image_path, 3
            )
            print("✓ Windows 壁纸已设置")
            
        elif system == "darwin":
            # macOS
            script = f'''
            tell application "Finder"
                set desktop picture to POSIX file "{image_path}"
            end tell
            '''
            subprocess.run(["osascript", "-e", script], check=True)
            print("✓ macOS 壁纸已设置")
            
        elif system.startswith("linux"):
            # Linux (支持 GNOME/KDE)
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            
            if "gnome" in desktop_env or "unity" in desktop_env:
                subprocess.run([
                    "gsettings", "set", "org.gnome.desktop.background",
                    "picture-uri", f"file://{image_path}"
                ], check=True)
                print("✓ GNOME 壁纸已设置")
                
            elif "kde" in desktop_env:
                # KDE Plasma
                subprocess.run([
                    "plasma-apply-wallpaperimage", image_path
                ], check=True)
                print("✓ KDE 壁纸已设置")
                
            else:
                # 通用方法（可能需要安装 feh）
                try:
                    subprocess.run(["feh", "--bg-fill", image_path], check=True)
                    print("✓ 使用 feh 设置壁纸")
                except FileNotFoundError:
                    print("⚠ 未找到 feh，请安装：sudo apt install feh")
                    return False
        else:
            print(f"❌ 不支持的操作系统：{system}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 设置壁纸失败：{e}")
        return False

def main():
    print("=== 纯 Python 壁纸设置工具 ===\n")
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("请输入图片路径（拖拽文件到此处）：").strip().strip('"\'')
    
    if not image_path:
        print("未提供图片路径")
        return
    
    # 转换为绝对路径
    abs_path = str(Path(image_path).resolve())
    set_wallpaper(abs_path)

if __name__ == "__main__":
    main()