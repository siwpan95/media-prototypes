"""噪声序列化：.npy / .npz / .csv（仅用 numpy）。

``save_noise`` / ``load_noise`` 支持三种格式；csv 用 ``np.savetxt`` / ``np.loadtxt``，
零额外依赖。
"""
from __future__ import annotations

import numpy as np


def save_noise(x: np.ndarray, path: str, fmt: str = 'npz', metadata: dict | None = None) -> None:
    """保存噪声数组到磁盘。

    参数：
        x: 噪声数组（会被转换为 float64）
        path: 输出路径
        fmt: 'npy' | 'npz' | 'csv'
        metadata: 仅 npz 可附带（作为 ``meta_<key>`` 数组存入，加载时自动剥离前缀
                  还原为原始键名）；npy / csv 不支持 metadata，传入会抛 ValueError
    """
    x = np.asarray(x, dtype=np.float64)
    ext = fmt.lower()

    # 统一校验：仅 npz 支持 metadata，npy/csv 不支持（无法往返）
    if metadata is not None and ext != 'npz':
        raise ValueError(
            f"{fmt} 格式不支持 metadata（仅 npz 可附带，npy/csv 无法往返）；"
            f"如需保留元数据请使用 fmt='npz'"
        )

    if ext == 'npy':
        np.save(path, x)
    elif ext == 'npz':
        if metadata is None:
            np.savez(path, data=x)
        else:
            np.savez(path, data=x,
                     **{f'meta_{k}': np.asarray(v) for k, v in metadata.items()})
    elif ext == 'csv':
        np.savetxt(path, x, delimiter=',')
    else:
        raise ValueError(f"不支持的格式: {fmt}（可选 npy/npz/csv）")


def load_noise(path: str) -> tuple[np.ndarray, dict]:
    """从磁盘加载噪声数组，返回 ``(array, metadata)``。

    - .npy：返回 (array, {})
    - .npz：返回 (data, {非 data 的键: 值})；标量为 Python 原生类型
    - .csv：返回 (array, {})
    """
    if path.endswith('.npy'):
        return np.load(path), {}

    if path.endswith('.npz'):
        npz = np.load(path)
        x = npz['data']
        metadata = {}
        for k in npz.files:
            if k == 'data':
                continue
            # 剥离内部存储前缀 meta_，对外暴露用户原始键名
            user_key = k[len('meta_'):] if k.startswith('meta_') else k
            arr = npz[k]
            metadata[user_key] = arr.tolist() if arr.ndim == 0 else arr
        return x, metadata

    if path.endswith('.csv'):
        x = np.loadtxt(path, delimiter=',')
        return x, {}

    raise ValueError(f"无法识别的文件后缀: {path}（支持 .npy/.npz/.csv）")
