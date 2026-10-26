import numpy as np
from PIL import Image

class Rasterizer:
    def __init__(self, w=800, h=600):
        self.w, self.h = w, h
        self.fb = np.zeros((h, w, 3), dtype=np.uint8)   # framebuffer
        self.zb = np.full((h, w), -np.inf)               # z-buffer

    def clear(self):
        self.fb[:] = 0
        self.zb[:] = -np.inf

    # ---------- 数学 ----------
    @staticmethod
    def perspective(fov, aspect, near, far):
        """透视投影矩阵 (FOV 单位弧度)"""
        f = 1 / np.tan(fov / 2)
        return np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), 2*far*near / (near - far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)

    @staticmethod
    def viewport(x, y, w, h, depth=255):
        """NDC(-1~1) → 屏幕坐标"""
        m = np.eye(4)
        m[0,0]=w/2; m[0,3]=x+w/2
        m[1,1]=h/2; m[1,3]=y+h/2
        m[2,2]=depth/2; m[2,3]=depth/2
        return m

    # ---------- 光栅化 ----------
    def draw_triangle(self, pts, colors):
        """
        pts: (3, 3)  三个顶点在屏幕空间 (x, y, z)
        colors: (3, 3)  每个顶点的 RGB
        """
        #  bounding box 裁剪
        min_x = max(int(np.floor(min(p[0] for p in pts))), 0)
        max_x = min(int(np.ceil(max(p[0] for p in pts))), self.w-1)
        min_y = max(int(np.floor(min(p[1] for p in pts))), 0)
        max_y = min(int(np.ceil(max(p[1] for p in pts))), self.h-1)

        v0, v1, v2 = pts
        for px in range(min_x, max_x+1):
            for py in range(min_y, max_y+1):
                # 重心坐标 (edge function)
                area = self._edge(v0, v1, v2)
                w0 = self._edge(v1, v2, (px, py, 0))
                w1 = self._edge(v2, v0, (px, py, 0))
                w2 = self._edge(v0, v1, (px, py, 0))
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                w0 /= area; w1 /= area; w2 /= area
                z = w0*v0[2] + w1*v1[2] + w2*v2[2]

                # Z-test
                if z > self.zb[py, px]:
                    self.zb[py, px] = z
                    # 颜色线性插值
                    c = w0*colors[0] + w1*colors[1] + w2*colors[2]
                    self.fb[py, px] = np.clip(c, 0, 255).astype(np.uint8)

    @staticmethod
    def _edge(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    def save(self, path):
        Image.fromarray(self.fb).save(path)


# ==================== demo ====================
if __name__ == "__main__":
    r = Rasterizer(800, 600)
    r.clear()

    # 三个顶点 (x, y, z)，z 越大越远（右手系，投影后翻转）
    verts = np.array([
        [-1, -1, 3],
        [ 1, -1, 4],
        [ 0,  1, 5],
    ], dtype=np.float32)

    colors = np.array([
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255],
    ], dtype=np.float32)

    # 透视投影 + viewport
    P = r.perspective(np.pi/3, 800/600, 0.1, 50)
    V = r.viewport(0, 0, 800, 600)
    pts = []
    for v in verts:
        clip = P @ np.array([v[0], v[1], v[2], 1])
        ndc = clip[:3] / clip[3]
        scr = V @ np.array([ndc[0], ndc[1], ndc[2], 1])
        pts.append(scr[:3])

    r.draw_triangle(pts, colors)
    r.save("triangle.png")
    print("输出 triangle.png")