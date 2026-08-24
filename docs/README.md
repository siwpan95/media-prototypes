# 文档地图（docs/）

本目录是「时空画板 / shikonghuaban」项目的文档中枢。按**角色**分层，避免报告堆叠、编号割裂。

## 治理类文档（audit/）
| 文件 | 角色 | 说明 |
|---|---|---|
| `audit/architecture-audit.md` | **债务基线**（来源） | 架构师 Archi 出具的架构债盘点（债 #1–#12）。本项目的治理来源与验收基准，内容保持原貌不动。 |
| `audit/remediation-report.md` | **治理报告**（结论） | 本项目（Senior Developer）的治理计划 + 执行结果 + 验证总览 + 遗留项。含「审计债 #1–#12 ↔ 治理项 A–I」映射表。 |

> 阅读顺序建议：先看 `remediation-report.md` §2 的映射表掌握全局，再按需回溯 `architecture-audit.md` 的债项细节。

## 项目说明文档（仓库根目录）
| 文件 | 角色 |
|---|---|
| `README.md` | 项目简介 / 运行 / 控制 / 配置 |
| `RUNBOOK.md` | 运维 / 事故处置手册（症状→原因→处置） |
| `CONTRIBUTING.md` | 参与开发指南 / 仓库布局 / 重构方向 |
| `pyproject.toml` / `fat.spec` | 打包与发行配置 |

## 当前项目状态
- ✅ **P0 / P1 债已清零**（审计 #1–#6、#8、#9、#11、#12 + 首批 A/B/C/D 全部落地）。
- ✅ 结构干净、可维护、可打包：`python -m shikonghuaban` 运行，`pyinstaller fat.spec` 重建 `fat.exe`。
- ⏸ **遗留（P2）**：`SharedState` 全局单例未做依赖注入（审计 #7）；持续 lint / 版本管理（git）为后续建议。
- 验证总览与逐项明细见 `audit/remediation-report.md` §3–§4。
