"""pytest 配置：确保 G:/wave4 在 sys.path，并设置无头 Agg 后端。

放在测试收集之前执行，使 ``import wave4`` / ``import wave4_legacy`` 均可用，
且 matplotlib 在无头环境下使用 Agg 后端（避免绘图触发显示器依赖）。
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")  # 必须在 pyplot 导入前设置

# 将项目根目录（tests 的父目录）加入 sys.path，确保 `import wave4` 与
# `import wave4_legacy` 都能解析。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
