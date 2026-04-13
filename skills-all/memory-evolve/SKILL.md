---
name: memory-evolve
description: 记忆进化系统 v2.0 — 16层全进化。当记忆文件混乱、信息矛盾、知识过时、需要备份、需要关联、需要遗忘时自动调用。M1自动压缩 M2冲突检测 M3健康检查 M4智能关联 M5优先级排序 M6自动备份 M7语义聚类 M8去重合并 M9时序推理 M10上下文感知 M11预测需求 M12跨系统记忆 M13知识图谱 M14主动创建 M15记忆巩固 M16记忆模拟。
allowed-tools:
  - exec
  - read
  - write
metadata:
  version: "2.0"
  author: P
---

# 记忆进化系统 v2.0

16层记忆自进化。

## 快速使用

```bash
python3 scripts/memory_evolve.py --evolve      # 全量进化
python3 scripts/memory_evolve.py --report      # 报告
python3 scripts/memory_evolve.py --cluster     # M7: 语义聚类
python3 scripts/memory_evolve.py --graph       # M13: 知识图谱
python3 scripts/memory_evolve.py --predict     # M11: 预测需求
python3 scripts/memory_evolve.py --consolidate # M15: 记忆巩固
python3 scripts/memory_evolve.py --decay       # M16: 遗忘曲线
```

## 16层进化能力

| 层级 | 能力 |
|------|------|
| M1 | 自动压缩 — 旧日志压缩归档 |
| M2 | 冲突检测 — 矛盾信息发现 |
| M3 | 健康检查 — 过时/空/大文件评分 |
| M4 | 智能关联 — 实体/主题索引 |
| M5 | 优先级排序 — 核心/重要/一般/低 |
| M6 | 自动备份 — 关键文件快照 |
| M7 | 语义聚类 — 按含义分组 |
| M8 | 去重合并 — 相似记忆合并 |
| M9 | 时序推理 — 因果关系链 |
| M10 | 上下文感知 — 当前任务相关调取 |
| M11 | 预测需求 — 预判下一步需要的信息 |
| M12 | 跨系统记忆 — 所有子系统共享 |
| M13 | 知识图谱 — 实体关系可视化 |
| M14 | 主动创建 — 对话中自动创建记忆 |
| M15 | 记忆巩固 — 定期复习强化 |
| M16 | 记忆模拟 — 智能遗忘曲线 |

## 数据文件

| 文件 | 用途 |
|------|------|
| `memory/memory-index.json` | 实体/主题索引 |
| `memory/memory-health.json` | 健康评分 |
| `memory/memory-graph.json` | 知识图谱 |
| `memory/memory-clusters.json` | 语义聚类 |
| `memory/memory-decay.json` | 遗忘曲线 |
| `memory/backups/` | 备份快照 |
