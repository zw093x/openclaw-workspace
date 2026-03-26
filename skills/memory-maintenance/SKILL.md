---
name: memory-maintenance
description: |
  记忆文件维护与整理技能。用于定期整理 agent 的长期记忆，从每日记录中提炼关键信息到 MEMORY.md。
  使用场景：(1) 定期记忆整理（每日/每周） (2) MEMORY.md 去重和更新 (3) 学习笔记从 .learnings/ 提升到长期记忆 (4) 记忆文件健康检查。
  触发词：整理记忆、更新 MEMORY、记忆维护、长期记忆、记忆回顾、distill memory。
license: MIT
metadata:
  author: pengyu
  version: "1.0"
allowed-tools: Read Write Exec
---

# 记忆维护技能

## 核心原则

记忆文件是 agent 的连续性基础。每次会话从零开始，靠文件恢复上下文。

**层级结构**：
```
MEMORY.md          ← 精炼的长期记忆（高层决策、偏好、状态）
memory/
├── YYYY-MM-DD.md  ← 每日原始日志
├── stock-portfolio.md  ← 持仓记录
├── *-state.json   ← 各种状态文件
└── ...
.learnings/        ← 错误和学习记录
├── ERRORS.md
├── LEARNINGS.md
└── FEATURE_REQUESTS.md
```

## 执行流程

### 流程一：每日记忆整理（心跳时或每日一次）

```bash
python scripts/distill_daily.py --date today
```

自动执行：
1. 读取 `memory/YYYY-MM-DD.md`（今日记录）
2. 提取值得长期保留的信息
3. 与 MEMORY.md 对比，去重后追加/更新
4. 标记已处理的条目

### 流程二：每周深度回顾

```bash
python scripts/weekly_review.py --week this
```

自动执行：
1. 扫描本周所有 `memory/YYYY-MM-DD.md`
2. 识别重复出现的模式和偏好变化
3. 清理 MEMORY.md 中过时的信息
4. 从 `.learnings/` 提取有价值的学习到 MEMORY.md
5. 生成回顾报告

### 流程三：记忆健康检查

```bash
python scripts/memory_health.py
```

检查项：
- MEMORY.md 是否超过 200 行（过长需要精简）
- 每日文件是否有缺失
- 状态文件 JSON 格式是否正确
- 有无孤立的、未被引用的文件

## MEMORY.md 写作规范

### 应该记录的
- 用户明确的偏好和指令
- 重要的决策和原因
- 持续关注的事项（股票、项目等）
- 学到的教训和最佳实践
- 关键状态（持仓、进度等）

### 不应该记录的
- 临时的对话上下文
- 已过时的信息（除非有追溯价值）
- 可以从其他文件推断的信息
- 纯技术性的操作记录

### 格式要求
- 使用结构化格式（表格、列表）
- 每条记录包含日期标记
- 长条目用折叠或链接到子文件
- 保持全局视角，不要陷入细节

## 文件引用

- 提炼脚本：[scripts/distill_daily.py](scripts/distill_daily.py)
- 周回顾脚本：[scripts/weekly_review.py](scripts/weekly_review.py)
- 健康检查：[scripts/memory_health.py](scripts/memory_health.py)
- 参考模板：[references/memory-template.md](references/memory-template.md)
