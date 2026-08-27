"""io 序列化测试：随机数组在 .npy/.npz/.csv 三种格式上 round-trip，断言 np.allclose。"""
import os
import tempfile

import numpy as np
import pytest

from wave4.io.serialize import load_noise, save_noise


def test_roundtrip_all_formats():
    rng = np.random.RandomState(0)
    x = rng.randn(500).astype(np.float64)
    for fmt in ("npy", "npz", "csv"):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, f"x.{fmt}")
            save_noise(x, path, fmt=fmt)
            y, meta = load_noise(path)
            assert isinstance(meta, dict)
            assert np.allclose(x, y, atol=1e-8), f"fmt={fmt} round-trip 不一致"


def test_npz_metadata_roundtrip():
    x = np.arange(10, dtype=np.float64)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "m.npz")
        save_noise(x, path, fmt="npz", metadata={"H": 0.5, "method": "basic"})
        y, meta = load_noise(path)
        assert np.allclose(x, y)
        # load_noise 会剥离内部 meta_ 前缀，对外暴露原始键名
        assert meta.get("H") == 0.5
        assert meta.get("method") == "basic"


def test_csv_with_metadata_raises():
    """csv 不支持 metadata（表头会被 load 丢弃，无法往返），应抛 ValueError。"""
    x = np.arange(5, dtype=np.float64)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "m.csv")
        with pytest.raises(ValueError, match="csv"):
            save_noise(x, path, fmt="csv", metadata={"H": 0.5})


def test_npy_with_metadata_raises():
    """npy 同样不支持 metadata，应抛 ValueError。"""
    x = np.arange(5, dtype=np.float64)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "m.npy")
        with pytest.raises(ValueError):
            save_noise(x, path, fmt="npy", metadata={"H": 0.5})


def test_unsupported_format_raises():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.txt")
        with open(path, "w") as f:
            f.write("dummy")
        with pytest.raises(ValueError):
            load_noise(path)
