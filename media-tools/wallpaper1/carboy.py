import os
import sys
import ctypes
import subprocess
import threading
import time
from pathlib import Path
from tkinter import Tk, Frame, Button, Label, filedialog, Listbox, Scrollbar, Entry, IntVar, Checkbutton, Canvas
from tkinter.ttk import Separator, Combobox
from PIL import Image, ImageTk, ImageSequence
import pystray
from pystray import MenuItem as item
import keyboard

# Windows API常量
class WindowsWallpaper:
    """Windows动态壁纸实现"""
    PROGMAN_HWND = 0x52C  # Progman窗口句柄
    
    @staticmethod
    def find_workerw():
        """查找WorkerW窗口"""
        workerw = None
        def enum_windows(hwnd, lParam):
            nonlocal workerw
            class_name = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetClassNameW(hwnd, class_name, 256)
            if class_name.value == "WorkerW":
                workerw = hwnd
                return False
            return True
        
        ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(enum_windows), 0)
        return workerw
    
    @staticmethod
    def set_dynamic_wallpaper(window_hwnd):
        """将窗口挂载到WorkerW"""
        try:
            # 查找WorkerW
            workerw = WindowsWallpaper.find_workerw()
            if workerw:
                # 设置父窗口
                ctypes.windll.user32.SetParent(window_hwnd, workerw)
                return True
            return False
        except Exception as e:
            print(f"Failed to set dynamic wallpaper: {e}")
            return False

class WallpaperRenderer:
    """壁纸渲染器基类"""
    def __init__(self, canvas):
        self.canvas = canvas
        self.is_running = False
        self.frame_delay = 33  # 约30fps
        
    def start(self):
        self.is_running = True
        self.render()
        
    def stop(self):
        self.is_running = False
        
    def render(self):
        pass

class StaticImageRenderer(WallpaperRenderer):
    """静态图片渲染器"""
    def __init__(self, canvas, image_path):
        super().__init__(canvas)
        self.image_path = image_path
        self.tk_image = None
        
    def render(self):
        if not self.is_running:
            return
            
        try:
            pil_img = Image.open(self.image_path)
            canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
            img_w, img_h = pil_img.size
            ratio = min(canvas_w / img_w, canvas_h / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))
            
            pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(pil_img)
            
            self.canvas.delete("all")
            x = (canvas_w - new_size[0]) // 2
            y = (canvas_h - new_size[1]) // 2
            self.canvas.create_image(x, y, anchor="nw", image=self.tk_image)
        except Exception as e:
            print(f"Render error: {e}")

class GIFRenderer(WallpaperRenderer):
    """GIF渲染器（优化版）"""
    def __init__(self, canvas, gif_path):
        super().__init__(canvas)
        self.gif_path = gif_path
        self.frames = []
        self.delays = []
        self.current_frame = 0
        
    def load_frames(self):
        """加载GIF帧"""
        try:
            gif = Image.open(self.gif_path)
            canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
            
            for frame in ImageSequence.Iterator(gif):
                img_w, img_h = frame.size
                ratio = min(canvas_w / img_w, canvas_h / img_h)
                new_size = (int(img_w * ratio), int(img_h * ratio))
                
                resized_frame = frame.resize(new_size, Image.Resampling.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(resized_frame))
                self.delays.append(frame.info.get('duration', 100))
        except Exception as e:
            print(f"GIF load error: {e}")
    
    def render(self):
        if not self.is_running or not self.frames:
            return
            
        # 显示当前帧
        self.canvas.delete("all")
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        frame_w = self.frames[self.current_frame].width()
        frame_h = self.frames[self.current_frame].height()
        
        x = (canvas_w - frame_w) // 2
        y = (canvas_h - frame_h) // 2
        self.canvas.create_image(x, y, anchor="nw", image=self.frames[self.current_frame])
        
        # 下一帧
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        delay = self.delays[self.current_frame] if self.delays else 100
        self.canvas.after(delay, self.render)

class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Wallpaper Manager")
        self.root.geometry("950x600")
        self.root.configure(bg="#f5f5f5")
        
        # 状态变量
        self.static_images = []
        self.gif_images = []
        self.current_renderer = None
        self.current_file = None
        self.auto_mode = False
        self.auto_interval = 30
        self.tray_icon = None
        self.system_type = "auto"
        self.dynamic_window = None  # 动态壁纸窗口
        
        # 初始化
        self.setup_ui()
        self.setup_tray()
        self.setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_ui(self):
        """创建UI"""
        # 顶部工具栏
        toolbar = Frame(self.root, bg="#ffffff", height=60)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        toolbar.pack_propagate(False)  # 来自 wallpaper5/playUI：固定工具栏高度
        
        Button(toolbar, text="📁 Folder", command=self.select_folder,
               bg="#4CAF50", fg="white", font=("", 10, "bold")).pack(side="left", padx=5, pady=10)
        
        Button(toolbar, text="🖼️ Static Image", command=self.select_static_image,
               bg="#2196F3", fg="white", font=("", 10, "bold")).pack(side="left", padx=5, pady=10)
        
        Button(toolbar, text="🎞️ GIF Animation", command=self.select_gif_image,
               bg="#FF9800", fg="white", font=("", 10, "bold")).pack(side="left", padx=5, pady=10)
        
        Button(toolbar, text="🎬 Dynamic Wallpaper", command=self.create_dynamic_wallpaper,
               bg="#9C27B0", fg="white", font=("", 10, "bold")).pack(side="left", padx=5, pady=10)
        
        # 系统选择
        system_frame = Frame(toolbar, bg="#ffffff")
        system_frame.pack(side="right", padx=10, pady=10)
        
        Label(system_frame, text="System:", bg="#ffffff").pack(side="left", padx=(0, 5))
        self.system_combo = Combobox(system_frame, values=["Auto Detect", "Windows", "macOS", "Linux"], 
                                     state="readonly", width=12)
        self.system_combo.set("Auto Detect")
        self.system_combo.pack(side="left")
        
        Separator(self.root, orient="horizontal").pack(fill="x", padx=10, pady=5)
        
        # 主内容区
        main_frame = Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧面板
        left_panel = Frame(main_frame, bg="#ffffff", width=280)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)  # 来自 wallpaper5/playUI：固定左栏宽度
        
        Label(left_panel, text="Wallpapers", bg="#ffffff", font=("", 12, "bold")).pack(pady=10)
        
        # 文件列表
        list_frame = Frame(left_panel, bg="#ffffff")
        list_frame.pack(fill="both", expand=True, padx=5)
        
        self.listbox = Listbox(list_frame, bg="#fafafa", borderwidth=0, highlightthickness=0,
                              selectbackground="#2196F3", font=("", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        scrollbar = Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # 控制面板
        control_panel = Frame(left_panel, bg="#ffffff")
        control_panel.pack(fill="x", pady=10, padx=5)
        
        self.auto_var = IntVar()
        Checkbutton(control_panel, text="Auto Switch", variable=self.auto_var,
                   bg="#ffffff", command=self.toggle_auto).pack(anchor="w")
        
        frame = Frame(control_panel, bg="#ffffff")
        frame.pack(fill="x", pady=5)
        
        Label(frame, text="Interval (sec):", bg="#ffffff").pack(side="left")
        self.interval_entry = Entry(frame, width=8)
        self.interval_entry.insert(0, "30")
        self.interval_entry.pack(side="left", padx=5)
        
        Button(control_panel, text="Set as Wallpaper", command=self.set_wallpaper,
               bg="#9C27B0", fg="white", font=("", 10, "bold")).pack(fill="x", pady=5)
        
        # 右侧预览区
        right_panel = Frame(main_frame, bg="#ffffff")
        right_panel.pack(side="right", fill="both", expand=True)
        
        Label(right_panel, text="Preview", bg="#ffffff", font=("", 12, "bold")).pack(pady=10)
        
        self.canvas = Canvas(right_panel, bg="#2b2b2b", width=650, height=400)
        self.canvas.pack(pady=10)
        
        # （已删除 FPS/Memory 指示器——从未更新的死代码，见 MERGE_PLAN.md 第 2 步）
        
        self.status = Label(right_panel, text="Select wallpaper to preview", bg="#ffffff", fg="#666")
        self.status.pack()
        
        # 底部状态栏
        status_bar = Frame(self.root, bg="#e0e0e0", height=25)
        status_bar.pack(fill="x", side="bottom")
        
        self.status_text = Label(status_bar, text="Ready", bg="#e0e0e0", fg="#333")
        self.status_text.pack(side="left", padx=10)
        
        Label(status_bar, text="Ctrl+Alt+N: Next | Esc: Stop", bg="#e0e0e0", fg="#666").pack(side="right", padx=10)
        
    def create_dynamic_wallpaper(self):
        """创建动态壁纸窗口（Windows专用）"""
        if sys.platform != "win32":
            self.update_status("Dynamic wallpaper only supported on Windows")
            return
            
        # 创建无边框全屏窗口
        self.dynamic_window = Tk()
        self.dynamic_window.attributes('-fullscreen', True)
        self.dynamic_window.attributes('-topmost', True)
        self.dynamic_window.overrideredirect(True)
        self.dynamic_window.configure(bg='black')
        
        # 挂载到WorkerW
        hwnd = int(self.dynamic_window.wm_frame(), 16)
        if WindowsWallpaper.set_dynamic_wallpaper(hwnd):
            self.update_status("Dynamic wallpaper window created")
            # 在这里可以添加视频播放器等
        else:
            self.update_status("Failed to mount dynamic wallpaper")
            self.dynamic_window.destroy()
    
    def select_static_image(self):
        """选择静态图片"""
        path = filedialog.askopenfilename(
            filetypes=[("Static Images", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if path:
            self.stop_current_renderer()
            self.static_images = [Path(path)]
            self.gif_images = []
            self.load_list()
            self.current_file = Path(path)
            self.start_static_renderer()
            
    def select_gif_image(self):
        """选择GIF动图"""
        path = filedialog.askopenfilename(
            filetypes=[("GIF Animations", "*.gif")]
        )
        if path:
            self.stop_current_renderer()
            self.gif_images = [Path(path)]
            self.static_images = []
            self.load_list()
            self.current_file = Path(path)
            self.start_gif_renderer()
            
    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.stop_current_renderer()
            self.static_images = sorted(
                p for p in Path(folder).iterdir() 
                if p.suffix.lower() in {".jpg", ".png", ".jpeg", ".bmp", ".webp"}
            )
            self.gif_images = sorted(
                p for p in Path(folder).iterdir()
                if p.suffix.lower() == ".gif"
            )
            self.load_list()
            self.current_file = None
            
    def load_list(self):
        """加载文件列表"""
        self.listbox.delete(0, "end")
        
        for img in self.static_images:
            self.listbox.insert("end", f"🖼️ {img.name}")
            
        for gif in self.gif_images:
            self.listbox.insert("end", f"🎞️ {gif.name}")
            
        if self.static_images or self.gif_images:
            self.listbox.selection_set(0)
            self.on_select(None)
            
    def on_select(self, event):
        """选择文件"""
        sel = self.listbox.curselection()
        if not sel:
            return
            
        index = sel[0]
        total_static = len(self.static_images)
        
        self.stop_current_renderer()
        
        if index < total_static:
            self.current_file = self.static_images[index]
            self.start_static_renderer()
        else:
            gif_index = index - total_static
            self.current_file = self.gif_images[gif_index]
            self.start_gif_renderer()
            
    def start_static_renderer(self):
        """启动静态图片渲染器"""
        if self.current_file:
            # 来自 wallpaper5/playUI：预览状态栏显示原图尺寸
            dims = ""
            try:
                with Image.open(self.current_file) as _img:
                    dims = f" ({_img.size[0]}x{_img.size[1]})"
            except Exception:
                pass
            self.current_renderer = StaticImageRenderer(self.canvas, self.current_file)
            self.current_renderer.start()
            self.status.config(text=f"🖼️ {self.current_file.name}{dims}")
            self.update_status(f"Loaded: {self.current_file.name}")
            
    def start_gif_renderer(self):
        """启动GIF渲染器"""
        if self.current_file:
            self.current_renderer = GIFRenderer(self.canvas, self.current_file)
            self.current_renderer.load_frames()
            self.current_renderer.start()
            # 来自 wallpaper5/playUI：预览状态栏显示帧数
            frames = len(self.current_renderer.frames)
            self.status.config(text=f"🎞️ {self.current_file.name} ({frames} frames)")
            self.update_status(f"GIF animation: {self.current_file.name}")
            
    def stop_current_renderer(self):
        """停止当前渲染器"""
        if self.current_renderer:
            self.current_renderer.stop()
            self.current_renderer = None
            
    def set_wallpaper(self):
        """设置壁纸"""
        if not self.current_file:
            return
            
        path = str(self.current_file.resolve())
        system_choice = self.system_combo.get()
        
        if system_choice == "Auto Detect":
            system = self.detect_system()
        else:
            system = system_choice
        
        try:
            if system == "Windows":
                # 如果是GIF，需要先转换为静态图片
                if self.current_file.suffix.lower() == ".gif":
                    # 提取第一帧作为静态壁纸
                    with Image.open(self.current_file) as img:
                        static_path = self.current_file.with_suffix('.png')
                        img.save(static_path, 'PNG')
                        path = str(static_path)
                
                ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
                
            elif system == "macOS":
                subprocess.run(["osascript", "-e", 
                               f'tell app "Finder" to set desktop picture to POSIX file "{path}"'])
            elif system == "Linux":
                subprocess.run(["gsettings", "set", 
                               "org.gnome.desktop.background", "picture-uri", f"file://{path}"])
            else:
                # 来自 wallpaper5/playUI：明确提示不支持的系统
                self.update_status(f"Unsupported system: {system}")
                return
            
            self.update_status(f"Wallpaper set: {self.current_file.name}")
            
        except Exception as e:
            self.update_status(f"Failed: {e}")
            
    def detect_system(self):
        """检测系统"""
        system = sys.platform.lower()
        if system == "win32":
            return "Windows"
        elif system == "darwin":
            return "macOS"
        elif system.startswith("linux"):
            return "Linux"
        return "Unknown"
        
    def toggle_auto(self):
        """切换自动模式"""
        self.auto_mode = bool(self.auto_var.get())
        if self.auto_mode:
            self.start_auto_switch()
            self.update_status(f"Auto mode ON ({self.auto_interval}s)")
        else:
            self.update_status("Auto mode OFF")
            
    def start_auto_switch(self):
        """开始自动切换"""
        if not self.auto_mode:
            return
            
        try:
            self.auto_interval = int(self.interval_entry.get() or 30)
        except:
            self.auto_interval = 30
            
        self.root.after(self.auto_interval * 1000, self.auto_switch)
        
    def auto_switch(self):
        """自动切换"""
        if not self.auto_mode:
            return
            
        self.next_wallpaper()
        self.root.after(self.auto_interval * 1000, self.auto_switch)
        
    def next_wallpaper(self):
        """下一张壁纸"""
        total_items = len(self.static_images) + len(self.gif_images)
        if total_items == 0:
            return
            
        current_selection = self.listbox.curselection()
        if current_selection:
            next_index = (current_selection[0] + 1) % total_items
        else:
            next_index = 0
            
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(next_index)
        self.listbox.see(next_index)
        self.on_select(None)
        self.set_wallpaper()
        
    def setup_tray(self):
        """设置系统托盘"""
        try:
            icon_image = Image.new('RGB', (64, 64), color='#4CAF50')
            
            menu = (
                item('Show', self.show_window),
                item('Next Wallpaper', self.next_wallpaper),
                item('Stop Rendering', self.stop_current_renderer),
                item('Exit', self.exit_app)
            )
            
            self.tray_icon = pystray.Icon("WallpaperManager", icon_image, "Wallpaper Manager", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            self.update_status(f"Tray init failed: {e}")
            
    def setup_hotkeys(self):
        """设置全局快捷键"""
        try:
            keyboard.add_hotkey('ctrl+alt+n', self.next_wallpaper)
            keyboard.add_hotkey('esc', self.stop_current_renderer)
            self.update_status("Global hotkeys registered")
        except Exception as e:
            self.update_status(f"Hotkey failed: {e}")
            
    def update_status(self, text):
        """更新状态"""
        if hasattr(self, 'status_text'):
            self.status_text.config(text=text)
            self.root.update_idletasks()
            
    def show_window(self):
        """显示窗口"""
        self.root.deiconify()
        self.root.lift()
        
    def on_close(self):
        """关闭窗口"""
        self.stop_current_renderer()
        self.root.withdraw()
        self.update_status("Running in system tray")
        
    def exit_app(self):
        """退出程序"""
        self.stop_current_renderer()
        if self.dynamic_window:
            self.dynamic_window.destroy()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        sys.exit(0)

if __name__ == "__main__":
    root = Tk()
    app = WallpaperApp(root)
    root.mainloop()