"""wave4 原始单文件实现（v0.1 参考）。

保留为 QA 回归用的**原始数值参考**：4 种生成方法（basic/freq/iir/fractal）的
数值行为与新建的 ``wave4`` 包 1:1 一致。本文件底部的使用示例已用
``if __name__ == "__main__":`` 包裹，以便导入本模块做逐点比对时不会触发绘图。

如需与新建包做回归比对，可直接：
    import wave4_legacy as legacy
    g = legacy.BrownianNoiseGenerator('freq')
    x_old = g.generate(2000, fs=1000, f_min=1, f_max=100, seed=42)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 配置中文字体，解决中文乱码/缺失问题
matplotlib.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class BrownianNoiseGenerator:
    """
    布朗噪声生成器类，封装多种生成方法
    """

    def __init__(self, method='basic'):
        """
        初始化生成器

        参数：
        method: 生成方法
                'basic': 基本积分法
                'freq': 频域滤波法
                'iir': IIR滤波法
                'fractal': 分数阶噪声法
        """
        self.method = method
        self.rng = np.random.RandomState()

    def set_seed(self, seed):
        """设置随机种子"""
        self.rng.seed(seed)

    def generate(self, N, fs=1.0, intensity=1.0, **kwargs):
        """
        生成布朗噪声

        参数：
        N: 采样点数
        fs: 采样率
        intensity: 强度系数
        **kwargs: 方法特定的参数
        """
        if self.method == 'basic':
            return self._generate_basic(N, intensity, **kwargs)
        elif self.method == 'freq':
            return self._generate_freq(N, fs, intensity, **kwargs)
        elif self.method == 'iir':
            return self._generate_iir(N, intensity, **kwargs)
        elif self.method == 'fractal':
            return self._generate_fractal(N, fs, intensity, **kwargs)
        else:
            raise ValueError(f"未知方法: {self.method}")

    def _generate_basic(self, N, intensity, **kwargs):
        """基本积分法"""
        seed = kwargs.get('seed')
        if seed is not None:
            self.rng.seed(seed)

        white_noise = self.rng.randn(N)
        brownian_noise = np.cumsum(white_noise)
        brownian_noise = brownian_noise - np.mean(brownian_noise)
        brownian_noise = brownian_noise / np.std(brownian_noise) * intensity

        return brownian_noise

    def _generate_freq(self, N, fs, intensity, **kwargs):
        """频域滤波法"""
        seed = kwargs.get('seed')
        if seed is not None:
            self.rng.seed(seed)

        f_min = kwargs.get('f_min', None)
        f_max = kwargs.get('f_max', None)

        white_noise = self.rng.randn(N)
        noise_fft = np.fft.rfft(white_noise)
        freq = np.fft.rfftfreq(N, 1 / fs)

        with np.errstate(divide='ignore', invalid='ignore'):
            filter_response = 1.0 / np.where(freq > 0, freq, np.inf)
            filter_response[0] = filter_response[1]

        if f_min is not None:
            filter_response[freq < f_min] = 0
        if f_max is not None:
            filter_response[freq > f_max] = 0

        brown_fft = noise_fft * filter_response
        brownian_noise = np.fft.irfft(brown_fft, n=N)

        brownian_noise = brownian_noise - np.mean(brownian_noise)
        brownian_noise = brownian_noise / np.std(brownian_noise) * intensity

        return brownian_noise

    def _generate_iir(self, N, intensity, **kwargs):
        """IIR滤波法"""
        seed = kwargs.get('seed')
        if seed is not None:
            self.rng.seed(seed)

        alpha = kwargs.get('alpha', 0.99)

        white_noise = self.rng.randn(N)
        brownian_noise = np.zeros(N)
        brownian_noise[0] = white_noise[0]

        for i in range(1, N):
            brownian_noise[i] = alpha * brownian_noise[i - 1] + white_noise[i]

        brownian_noise = brownian_noise - np.mean(brownian_noise)
        brownian_noise = brownian_noise / np.std(brownian_noise) * intensity

        return brownian_noise

    def _generate_fractal(self, N, fs, intensity, **kwargs):
        """分数阶噪声法"""
        seed = kwargs.get('seed')
        if seed is not None:
            self.rng.seed(seed)

        beta = kwargs.get('beta', 2.0)

        white_noise = self.rng.randn(N)
        noise_fft = np.fft.rfft(white_noise)
        freq = np.fft.rfftfreq(N, 1 / fs)

        with np.errstate(divide='ignore', invalid='ignore'):
            filter_response = np.ones_like(freq)
            mask = freq > 0
            filter_response[mask] = 1.0 / (freq[mask] ** (beta / 2))
            filter_response[~mask] = filter_response[1]

        filtered_fft = noise_fft * filter_response
        fractal_noise = np.fft.irfft(filtered_fft, n=N)

        fractal_noise = fractal_noise - np.mean(fractal_noise)
        fractal_noise = fractal_noise / np.std(fractal_noise) * intensity

        return fractal_noise


if __name__ == "__main__":
    # 使用示例
    generator = BrownianNoiseGenerator(method='freq')

    # 生成不同参数的布朗噪声
    noise1 = generator.generate(10000, fs=1000, intensity=1.0,
                                f_min=1, f_max=100, seed=42)

    generator.method = 'fractal'
    noise2 = generator.generate(10000, fs=1000, intensity=1.0,
                                beta=2.5, seed=42)

    # 对比不同方法
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(noise1[:1000])
    plt.title('带限布朗噪声 (1-100Hz)')
    plt.xlabel('采样点')
    plt.ylabel('幅度')
    plt.grid(True, alpha=0.3)

    plt.subplot(2, 1, 2)
    plt.plot(noise2[:1000])
    plt.title('分数阶布朗噪声 (β=2.5)')
    plt.xlabel('采样点')
    plt.ylabel('幅度')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
