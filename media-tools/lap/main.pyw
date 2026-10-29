import tkinter as tk
from tkinter import ttk
import math

class FanSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("风扇模拟器")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # 风扇状态
        self.is_running = False
        self.speed = 5  # 初始速度 (1-10)
        self.angle = 0  # 当前旋转角度
        
        # 创建界面
        self.setup_ui()
        
        # 动画ID
        self.animation_id = None
    
    def setup_ui(self):
        # 标题
        title_label = tk.Label(
            self.root, 
            text="风扇模拟器", 
            font=("Arial", 20, "bold"),
            pady=10
        )
        title_label.pack()
        
        # 风扇画布
        self.canvas = tk.Canvas(
            self.root, 
            width=400, 
            height=400,
            bg="#f0f0f0",
            highlightthickness=2,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(pady=20)
        
        # 绘制风扇底座
        self.draw_fan_base()
        
        # 控制面板
        control_frame = tk.Frame(self.root, padx=20, pady=10)
        control_frame.pack(fill="x")
        
        # 开始/停止按钮
        self.toggle_btn = tk.Button(
            control_frame,
            text="开始",
            command=self.toggle_fan,
            font=("Arial", 14),
            bg="#4CAF50",
            fg="white",
            width=10,
            height=2
        )
        self.toggle_btn.grid(row=0, column=0, padx=10)
        
        # 风速控制标签
        speed_label = tk.Label(
            control_frame,
            text="风速调节:",
            font=("Arial", 12)
        )
        speed_label.grid(row=0, column=1, padx=(30, 10))
        
        # 风速滑块
        self.speed_scale = ttk.Scale(
            control_frame,
            from_=1,
            to=10,
            orient="horizontal",
            length=200,
            command=self.update_speed
        )
        self.speed_scale.set(self.speed)
        self.speed_scale.grid(row=0, column=2, padx=10)
        
        # 风速显示 - 修复：确保这个属性被正确创建
        self.speed_display = tk.Label(
            control_frame,
            text=f"速度: {self.speed}",
            font=("Arial", 12)
        )
        self.speed_display.grid(row=0, column=3, padx=10)
        
        # 状态显示
        self.status_label = tk.Label(
            self.root,
            text="状态: 停止",
            font=("Arial", 12),
            fg="red"
        )
        self.status_label.pack(pady=10)
        
        # 绘制初始风扇叶片
        self.draw_fan_blades()
    
    def draw_fan_base(self):
        """绘制风扇底座"""
        # 风扇中心圆
        self.canvas.create_oval(
            150, 150, 250, 250,
            fill="#333333",
            outline="#222222",
            width=2
        )
        
        # 风扇支架
        self.canvas.create_rectangle(
            195, 250, 205, 320,
            fill="#666666",
            outline="#555555"
        )
        
        # 底座
        self.canvas.create_oval(
            160, 310, 240, 350,
            fill="#888888",
            outline="#777777",
            width=2
        )
    
    def draw_fan_blades(self):
        """绘制风扇叶片"""
        # 清除之前的叶片
        self.canvas.delete("blade")
        
        center_x, center_y = 200, 200
        blade_length = 120
        blade_width = 40
        
        # 绘制三个叶片
        for i in range(3):
            angle_rad = math.radians(self.angle + i * 120)
            
            # 计算叶片端点坐标
            end_x = center_x + blade_length * math.cos(angle_rad)
            end_y = center_y + blade_length * math.sin(angle_rad)
            
            # 计算叶片宽度方向的两个点
            perp_angle = angle_rad + math.pi/2
            offset_x = (blade_width/2) * math.cos(perp_angle)
            offset_y = (blade_width/2) * math.sin(perp_angle)
            
            # 创建叶片多边形
            points = [
                center_x - offset_x, center_y - offset_y,
                center_x + offset_x, center_y + offset_y,
                end_x + offset_x, end_y + offset_x,
                end_x - offset_x, end_y - offset_y
            ]
            
            # 绘制叶片
            self.canvas.create_polygon(
                points,
                fill="#4a90e2",
                outline="#2171b5",
                width=1,
                tags="blade"
            )
    
    def toggle_fan(self):
        """切换风扇运行状态"""
        if self.is_running:
            self.stop_fan()
        else:
            self.start_fan()
    
    def start_fan(self):
        """启动风扇"""
        self.is_running = True
        self.toggle_btn.config(text="停止", bg="#f44336")
        self.status_label.config(text="状态: 运行中", fg="green")
        self.animate_fan()
    
    def stop_fan(self):
        """停止风扇"""
        self.is_running = False
        self.toggle_btn.config(text="开始", bg="#4CAF50")
        self.status_label.config(text="状态: 停止", fg="red")
        
        # 停止动画
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
    
    def update_speed(self, value):
        """更新风速"""
        self.speed = int(float(value))
        # 修复：确保 speed_display 存在后再更新
        if hasattr(self, 'speed_display'):
            self.speed_display.config(text=f"速度: {self.speed}")
    
    def animate_fan(self):
        """风扇动画"""
        if not self.is_running:
            return
        
        # 根据速度更新角度
        self.angle = (self.angle + self.speed) % 360
        
        # 重绘叶片
        self.draw_fan_blades()
        
        # 继续动画
        self.animation_id = self.root.after(50, self.animate_fan)

def main():
    root = tk.Tk()
    app = FanSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()