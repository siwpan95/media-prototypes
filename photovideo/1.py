import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import numpy as np
import cv2
import threading

# ==================== 绝对输出路径 ====================
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# π 前 200 位（足够任意幻灯片使用）
_PI_DIGITS = [int(c) for c in (
    "31415926535897932384626433832795028841971693993751058209749445"
    "92307816406286208998628034825342117067982148086513282306647093"
    "84460955058223172535940812848111745028410270193852110555964462"
    "2948954930381964428810975"
)]

def pi_duration(index: int) -> int:
    """第 index 张图的秒数 = π 的第 index 位（0 → 1秒）。"""
    d = _PI_DIGITS[index % len(_PI_DIGITS)]
    return max(1, d)

def ensure_output_dir():
    """确保输出目录存在（绝对路径 /output）"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except PermissionError:
        messagebox.showerror("权限错误", f"无法创建目录 {OUTPUT_DIR}，请以管理员权限运行或修改路径。")
        raise

class PhotoToVideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("照片拼接视频工具")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # 图片路径列表
        self.image_paths = []

        # ========== 顶部选择区 ==========
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        tk.Button(top_frame, text="选择照片", command=self.select_images, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="清空列表", command=self.clear_list, width=12).pack(side=tk.LEFT, padx=5)

        # ========== 图片列表及操作按钮 ==========
        list_frame = tk.Frame(root)
        list_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=20)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, width=70, height=12)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="↑ 上移", command=self.move_up).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="↓ 下移", command=self.move_down).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除选中", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

        # ========== 参数设置区 ==========
        param_frame = tk.Frame(root)
        param_frame.pack(pady=10)

        tk.Label(param_frame, text="帧率 (FPS):").grid(row=0, column=0, padx=5, sticky="e")
        self.fps_var = tk.IntVar(value=30)
        tk.Spinbox(param_frame, from_=1, to=60, textvariable=self.fps_var, width=5).grid(row=0, column=1, padx=5)

        tk.Label(param_frame, text="时长分配:").grid(row=0, column=2, padx=5, sticky="e")
        tk.Label(param_frame, text="π 律动", fg="#4CAF50").grid(row=0, column=3, padx=5, sticky="w")

        tk.Label(param_frame, text="输出文件名:").grid(row=1, column=0, padx=5, sticky="e")
        self.filename_var = tk.StringVar(value="output.mp4")
        tk.Entry(param_frame, textvariable=self.filename_var, width=20).grid(row=1, column=1, padx=5, columnspan=2)

        # ========== 进度条 ==========
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(pady=10)

        # ========== 生成按钮 ==========
        tk.Button(root, text="开始生成视频", command=self.start_generation, bg="#4CAF50", fg="white", height=2, width=20).pack(pady=10)

    # ==================== 功能函数 ====================
    def select_images(self):
        files = filedialog.askopenfilenames(
            title="选择照片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("所有文件", "*.*")]
        )
        if files:
            for f in files:
                if f not in self.image_paths:
                    self.image_paths.append(f)
                    self.listbox.insert(tk.END, os.path.basename(f))

    def clear_list(self):
        self.image_paths.clear()
        self.listbox.delete(0, tk.END)

    def move_up(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx == 0:
            return
        # 交换列表
        self.image_paths[idx], self.image_paths[idx-1] = self.image_paths[idx-1], self.image_paths[idx]
        # 更新 Listbox
        self.listbox.delete(idx)
        self.listbox.insert(idx-1, os.path.basename(self.image_paths[idx-1]))
        self.listbox.selection_set(idx-1)

    def move_down(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx == len(self.image_paths)-1:
            return
        self.image_paths[idx], self.image_paths[idx+1] = self.image_paths[idx+1], self.image_paths[idx]
        self.listbox.delete(idx)
        self.listbox.insert(idx+1, os.path.basename(self.image_paths[idx+1]))
        self.listbox.selection_set(idx+1)

    def delete_selected(self):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            del self.image_paths[idx]
            self.listbox.delete(idx)

    def start_generation(self):
        if not self.image_paths:
            messagebox.showwarning("无图片", "请先选择至少一张照片。")
            return

        output_filename = self.filename_var.get().strip()
        if not output_filename:
            messagebox.showwarning("文件名", "请输入输出文件名。")
            return
        if not output_filename.endswith(".mp4"):
            output_filename += ".mp4"

        output_path = os.path.join(OUTPUT_DIR, output_filename)

        if os.path.exists(output_path):
            if not messagebox.askyesno("文件已存在", f"文件 {output_path} 已存在，是否覆盖？"):
                return

        fps = self.fps_var.get()
        # 在子线程中生成视频，避免界面卡死
        threading.Thread(target=self.generate_video, args=(output_path, fps), daemon=True).start()

    def generate_video(self, output_path, fps):
        try:
            # 读取第一张图确定尺寸
            first_img = Image.open(self.image_paths[0]).convert("RGB")
            width, height = first_img.size
        except Exception as e:
            self.root.after(0, messagebox.showerror, "错误", f"无法读取图片 {self.image_paths[0]}:\n{e}")
            return

        # 定义编码器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            self.root.after(0, messagebox.showerror, "错误", "无法创建视频文件，请检查编解码器和路径权限。")
            return

        total = len(self.image_paths)
        self.progress["maximum"] = total
        self.progress["value"] = 0

        try:
            for idx, img_path in enumerate(self.image_paths):
                # 使用 PIL 统一尺寸并转为 OpenCV 格式
                pil_img = Image.open(img_path).convert("RGB").resize((width, height), Image.LANCZOS)
                frame = np.array(pil_img)
                # RGB -> BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frames = pi_duration(idx) * fps
                for _ in range(frames):
                    out.write(frame)

                # 更新进度条（在主线程）
                self.root.after(0, self.update_progress, idx + 1)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "错误", f"处理图片时出错:\n{e}")
        finally:
            out.release()
            self.root.after(0, self.generation_done, total)

    def update_progress(self, value):
        self.progress["value"] = value

    def generation_done(self, total):
        self.progress["value"] = total
        messagebox.showinfo("完成", f"视频已生成到 {OUTPUT_DIR} 目录。")

# ==================== 主程序 ====================
if __name__ == "__main__":
    ensure_output_dir()
    root = tk.Tk()
    app = PhotoToVideoApp(root)
    root.mainloop()