import tkinter as tk
from engine import Engine
from utils.config import UI_CONFIG

def main():
    root = tk.Tk()
    root.title("工业级风扇仿真系统")

    w, h = UI_CONFIG["window_size"]
    root.geometry(f"{w}x{h}")
    root.configure(bg="#1a1a1a")
    root.resizable(False, False)

    app = Engine(root)

    def on_close():
        app.audio.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()