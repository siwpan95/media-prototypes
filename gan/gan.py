import numpy as np
import cv2
import sys
import argparse

# ========================= 参数设置 =========================
SIZE = 64                # 帧尺寸 (SIZE x SIZE)
FPS = 30                 # 目标帧率（用于 waitKey 延时控制）
LAPL_KERNEL = np.array([[0.05, 0.2, 0.05],
                        [0.2, -1.0, 0.2],
                        [0.05, 0.2, 0.05]], dtype=np.float32)

# ========================= 1. 马尔科夫链 (Markov Chain) =========================
states = ['mode0', 'mode1', 'mode2']
trans_mat = np.array([[0.8, 0.1, 0.1],
                      [0.2, 0.7, 0.1],
                      [0.3, 0.2, 0.5]])
state = 0   # 初始状态

# ========================= 2. 元胞自动机 (Cellular Automaton - Gray-Scott 模型) =========================
u = np.ones((SIZE, SIZE), dtype=np.float32)
v = np.zeros((SIZE, SIZE), dtype=np.float32)
rng = np.random.RandomState(42)
v[28:36, 28:36] = 0.5
u[28:36, 28:36] = 0.5
ru_base, rv_base = 0.04, 0.06
Du, Dv = 0.16, 0.08

# ========================= 3. 卷积神经网络 (CNN) =========================
cnn_kernel = np.random.randn(3, 3).astype(np.float32) * 0.1

# ========================= 4. 循环神经网络 (RNN) =========================
RNN_HIDDEN = 512
rnn_h = np.zeros(RNN_HIDDEN)
rnn_Wh = np.random.randn(RNN_HIDDEN, RNN_HIDDEN).astype(np.float32) * 0.01
rnn_Wx = np.random.randn(RNN_HIDDEN, SIZE*SIZE*3).astype(np.float32) * 0.01
rnn_Wy = np.random.randn(SIZE*SIZE*3, RNN_HIDDEN).astype(np.float32) * 0.01

# ========================= 5. 图神经网络 (GNN) =========================
# 构建 8x8 网格图的邻接矩阵
adj = np.zeros((64, 64), dtype=np.float32)
for i in range(8):
    for j in range(8):
        idx = i*8 + j
        adj[idx, idx] = 1.0
        if i > 0: adj[idx, (i-1)*8+j] = 1.0
        if i < 7: adj[idx, (i+1)*8+j] = 1.0
        if j > 0: adj[idx, i*8+j-1] = 1.0
        if j < 7: adj[idx, i*8+j+1] = 1.0
W_gnn = np.random.randn(3, 3).astype(np.float32) * 0.1

# ========================= 6. 强化学习 (RL) =========================
n_actions_rl = 3   # 动作：增加/不变/减少噪声
n_states_rl = 5    # 亮度离散化状态数
Q_rl = np.zeros((n_states_rl, n_actions_rl), dtype=np.float32)

# ========================= 7. 生成对抗网络 (GAN) =========================
G_W1 = np.random.randn(10, 128).astype(np.float32) * 0.1
G_b1 = np.zeros(128, dtype=np.float32)
G_W2 = np.random.randn(128, SIZE*SIZE*3).astype(np.float32) * 0.1
G_b2 = np.zeros(SIZE*SIZE*3, dtype=np.float32)

def generate_G(z):
    h = z @ G_W1 + G_b1
    h = np.maximum(0, h)               # ReLU
    out = h @ G_W2 + G_b2
    out = 1.0 / (1.0 + np.exp(-out))   # sigmoid
    return out.reshape(SIZE, SIZE, 3)

# ========================= 8. Transformer (自注意力) =========================
Wq = np.random.randn(12, 8).astype(np.float32) * 0.1
Wk = np.random.randn(12, 8).astype(np.float32) * 0.1
Wv = np.random.randn(12, 8).astype(np.float32) * 0.1
Wo = np.random.randn(8, 12).astype(np.float32) * 0.1

# ========================= 9. 变分自编码器 (VAE) =========================
vae_enc_W1 = np.random.randn(SIZE*SIZE*3, 256).astype(np.float32) * 0.01
vae_enc_b1 = np.zeros(256, dtype=np.float32)
vae_enc_W_mean = np.random.randn(256, 32).astype(np.float32) * 0.01
vae_enc_W_logvar = np.random.randn(256, 32).astype(np.float32) * 0.01
vae_dec_W1 = np.random.randn(32, 256).astype(np.float32) * 0.01
vae_dec_b1 = np.zeros(256, dtype=np.float32)
vae_dec_W2 = np.random.randn(256, SIZE*SIZE*3).astype(np.float32) * 0.01

# ========================= 10. 多智能体强化学习 (MARL) =========================
pos1 = np.array([32.0, 32.0])
pos2 = np.array([32.0, 32.0])
Q_agent1 = np.zeros(9, dtype=np.float32)   # 3x3 动作空间
Q_agent2 = np.zeros(9, dtype=np.float32)

# ========================= 视频写入初始化 =========================
def init_video_writer(output_path, fps):
    """初始化视频写入器"""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (SIZE, SIZE))
    if not out.isOpened():
        print("错误：无法打开视频写入器，请确认已安装 opencv-python")
        sys.exit(1)
    return out

# ========================= 主循环 =========================
def process_frame():
    """处理一帧，返回帧数据"""
    global state, u, v, cnn_kernel, rnn_h, pos1, pos2, Q_agent1, Q_agent2, Q_rl
    
    # --- 马尔科夫链状态转移 ---
    state = np.random.choice(3, p=trans_mat[state])
    mode = state

    # --- 元胞自动机迭代 (5次) ---
    for _ in range(5):
        Lu = cv2.filter2D(u, -1, LAPL_KERNEL)
        Lv = cv2.filter2D(v, -1, LAPL_KERNEL)
        if mode == 0:
            ru, rv = ru_base, rv_base
        elif mode == 1:
            ru, rv = ru_base*1.2, rv_base*0.8
        else:
            ru, rv = ru_base*0.8, rv_base*1.2
        du = ru * (1 - u) - u * v * v + Du * Lu
        dv = -rv * v + u * v * v + Dv * Lv
        u += du
        v += dv
        u = np.clip(u, 0, 1)
        v = np.clip(v, 0, 1)

    # 以 v 浓度作为基础灰度纹理，转为三通道
    frame = (v * 255).astype(np.float32)
    frame = np.stack([frame]*3, axis=-1)   # shape: (SIZE, SIZE, 3)

    # --- 卷积神经网络 (CNN) 处理 ---
    cnn_out = cv2.filter2D(frame, -1, cnn_kernel)
    frame += cnn_out * 0.1
    # 核缓慢变化，模拟 CNN 权重在线微调
    cnn_kernel += np.random.randn(3, 3).astype(np.float32) * 0.001

    # --- 循环神经网络 (RNN) 处理 ---
    x_flat = frame.flatten().astype(np.float32)
    rnn_h = np.tanh(rnn_Wh @ rnn_h + rnn_Wx @ x_flat)
    y_rnn = rnn_Wy @ rnn_h
    frame += y_rnn.reshape(SIZE, SIZE, 3) * 0.05

    # --- 图神经网络 (GNN) 处理 ---
    small_frame = cv2.resize(frame, (8, 8))  # 下采样至 8x8
    node_features = small_frame.reshape(64, 3).astype(np.float32)  # 64 个节点，特征维度 3
    H_new = np.maximum(0, adj @ node_features @ W_gnn)   # 图卷积 + ReLU
    up = H_new.reshape(8, 8, 3)
    up = cv2.resize(up, (SIZE, SIZE), interpolation=cv2.INTER_NEAREST)
    frame += up * 0.1

    # --- 强化学习 (RL) 调节噪声幅度 ---
    brightness = np.mean(frame)
    s_rl = min(4, int(brightness // 51))
    epsilon = 0.1
    if np.random.rand() < epsilon:
        a_rl = np.random.randint(n_actions_rl)
    else:
        a_rl = np.argmax(Q_rl[s_rl])
    noise_amp = (a_rl - 1) * 0.02 * 255
    frame += np.random.randn(*frame.shape) * noise_amp
    # 计算奖励：像素强度熵 (鼓励高熵)
    hist = cv2.calcHist([frame.astype(np.uint8)], [0], None, [16], [0, 256])
    hist = hist / hist.sum()
    entropy = -np.sum(hist * np.log2(hist + 1e-7))
    reward_rl = entropy
    s_next_rl = min(4, int(np.mean(frame) // 51))
    # Q-learning 更新
    Q_rl[s_rl, a_rl] += 0.1 * (reward_rl + 0.9 * np.max(Q_rl[s_next_rl]) - Q_rl[s_rl, a_rl])

    # --- 生成对抗网络 (GAN) 生成纹理并优化潜在向量 ---
    z_gan = np.random.randn(10).astype(np.float32)
    # 目标区域：中央 8x8 区域，优化 z 使生成图像逼近该区域
    target_patch = frame[30:38, 30:38, :] / 255.0
    for _ in range(3):   # 数值梯度下降 3 步
        gen_img = generate_G(z_gan)
        loss = np.mean((gen_img[30:38, 30:38, :] - target_patch) ** 2)
        grad = np.zeros(10, dtype=np.float32)
        eps_fd = 1e-4
        for i in range(10):
            z_plus = z_gan.copy()
            z_plus[i] += eps_fd
            gen_plus = generate_G(z_plus)
            loss_plus = np.mean((gen_plus[30:38, 30:38, :] - target_patch) ** 2)
            grad[i] = (loss_plus - loss) / eps_fd
        z_gan -= 0.01 * grad
    gan_frame = generate_G(z_gan) * 255
    frame += gan_frame * 0.1

    # --- Transformer (自注意力) 处理 ---
    small = cv2.resize(frame, (8, 8)).astype(np.float32)  # 下采样 8x8
    # 分成 4x4 个 patch，每个 patch 2x2, 通道 3 => 12 维
    patches = small.reshape(4, 2, 4, 2, 3).transpose(0, 2, 1, 3, 4).reshape(16, 12)
    Q = patches @ Wq
    K = patches @ Wk
    V = patches @ Wv
    scores = Q @ K.T / np.sqrt(8.0)
    attn_weights = np.exp(scores) / np.sum(np.exp(scores), axis=1, keepdims=True)
    out_patches = attn_weights @ V   # (16, 8)
    recon_patches = out_patches @ Wo  # (16, 12)
    # 重塑回 8x8x3
    recon = recon_patches.reshape(4, 4, 2, 2, 3).transpose(0, 2, 1, 3, 4).reshape(8, 8, 3)
    recon_up = cv2.resize(recon, (SIZE, SIZE))
    frame += recon_up * 0.1

    # --- 变分自编码器 (VAE) 重构 ---
    x_vae = frame.flatten() / 255.0
    h_enc = np.maximum(0, x_vae @ vae_enc_W1 + vae_enc_b1)
    mean = h_enc @ vae_enc_W_mean
    logvar = h_enc @ vae_enc_W_logvar
    eps_vae = np.random.randn(32).astype(np.float32) * 0.1
    z_vae = mean + np.exp(0.5 * logvar) * eps_vae
    h_dec = np.maximum(0, z_vae @ vae_dec_W1 + vae_dec_b1)
    recon_flat = 1.0 / (1.0 + np.exp(-(h_dec @ vae_dec_W2)))   # sigmoid
    frame += recon_flat.reshape(SIZE, SIZE, 3) * 255 * 0.05

    # --- 多智能体强化学习 (MARL) 竞争绘图 ---
    # 动作选择 (epsilon-greedy)
    eps_marl = 0.1
    if np.random.rand() < eps_marl:
        a1 = np.random.randint(9)
    else:
        a1 = np.argmax(Q_agent1)
    if np.random.rand() < eps_marl:
        a2 = np.random.randint(9)
    else:
        a2 = np.argmax(Q_agent2)

    # 动作解码：0~8 对应 3x3 位移
    dx1 = (a1 % 3) - 1
    dy1 = (a1 // 3) - 1
    dx2 = (a2 % 3) - 1
    dy2 = (a2 // 3) - 1
    new_pos1 = np.clip(pos1 + [dy1, dx1], 0, SIZE-1)
    new_pos2 = np.clip(pos2 + [dy2, dx2], 0, SIZE-1)

    # 生成各自的覆盖区域 (3x3 方块)
    mask1 = np.zeros((SIZE, SIZE), dtype=bool)
    mask2 = np.zeros((SIZE, SIZE), dtype=bool)
    x1, y1 = int(new_pos1[1]), int(new_pos1[0])
    x2, y2 = int(new_pos2[1]), int(new_pos2[0])
    x1_min, x1_max = max(0, x1-1), min(SIZE, x1+2)
    y1_min, y1_max = max(0, y1-1), min(SIZE, y1+2)
    x2_min, x2_max = max(0, x2-1), min(SIZE, x2+2)
    y2_min, y2_max = max(0, y2-1), min(SIZE, y2+2)
    mask1[y1_min:y1_max, x1_min:x1_max] = True
    mask2[y2_min:y2_max, x2_min:x2_max] = True

    # 奖励设计：独占区域全奖，重叠区域半奖 (竞争)
    only1 = np.sum(mask1 & ~mask2)
    only2 = np.sum(mask2 & ~mask1)
    both = np.sum(mask1 & mask2)
    reward1 = only1 + 0.5 * both
    reward2 = only2 + 0.5 * both

    # 更新 Q 值 (简单增量平均)
    Q_agent1[a1] += 0.1 * (reward1 - Q_agent1[a1])
    Q_agent2[a2] += 0.1 * (reward2 - Q_agent2[a2])

    # 在画面上绘制
    frame[y1_min:y1_max, x1_min:x1_max, :] = [0, 0, 255]   # 智能体1 红色
    frame[y2_min:y2_max, x2_min:x2_max, :] = [0, 255, 0]   # 智能体2 绿色

    pos1 = new_pos1
    pos2 = new_pos2

    # --- 裁剪并返回 ---
    frame = np.clip(frame, 0, 255).astype(np.uint8)
    return frame

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='多AI技术随机视频生成器')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出视频文件路径（如不指定则启动实时预览）')
    parser.add_argument('--frames', '-f', type=int, default=150,
                        help='输出视频的总帧数（默认150）')
    parser.add_argument('--fps', type=int, default=FPS,
                        help=f'输出视频的帧率（默认{FPS}）')
    args = parser.parse_args()
    
    if args.output:
        # 视频输出模式
        out = init_video_writer(args.output, args.fps)
        
        print(f"正在生成视频：{args.output}")
        print(f"总帧数：{args.frames}，帧率：{args.fps}")
        
        for t in range(args.frames):
            frame = process_frame()
            out.write(frame)
            if (t + 1) % 30 == 0:
                print(f"进度：{t + 1}/{args.frames} 帧")
        
        out.release()
        print(f"视频已生成：{args.output}")
    else:
        # 实时预览模式
        cv2.namedWindow('Random Video (ESC to exit)', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Random Video (ESC to exit)', SIZE*4, SIZE*4)  # 放大显示
        
        print("实时预览已启动。按 ESC 键退出。")
        
        frame_count = 0
        while True:
            frame = process_frame()
            cv2.imshow('Random Video (ESC to exit)', frame)
            
            # 按 ESC (27) 退出
            key = cv2.waitKey(int(1000 / FPS)) & 0xFF
            if key == 27:
                break
            
            frame_count += 1
        
        cv2.destroyAllWindows()
        print(f"预览结束，共显示 {frame_count} 帧。")
