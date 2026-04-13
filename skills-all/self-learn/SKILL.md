---
name: self-learn
description: 自学习进化系统 v2.0 — 11层全进化+统一智能层。当用户纠正错误、操作失败、发现知识过时、更好的方法时自动调用。L1自动记录 L2模式提取 L3规则验证 L4优先级进化 L5知识沉淀 L6跨域迁移 L7反馈闭环 L8衰减遗忘 L9外部学习 L10预测犯错 L11元学习。统一智能层连接自愈系统和错误进化引擎。
allowed-tools:
  - exec
  - read
  - write
metadata:
  version: "2.1"
  author: P
---

# 自学习进化系统 v2.1

11层全量进化 + 统一智能层。

## 快速使用

```bash
# 记录教训
python3 scripts/learn_evolve.py --record <type> <category> <summary>

# 场景检查（犯错前预警）
python3 scripts/learn_evolve.py --check "帮用户卖出股票"

# 执行全量进化
python3 scripts/learn_evolve.py --evolve

# 全量同步（连接所有系统）
python3 scripts/intel_hub.py --sync

# 查看统一状态
python3 scripts/intel_hub.py --status

# 完整报告
python3 scripts/learn_evolve.py --report
```

## 11层进化能力

| 层级 | 能力 | 说明 |
|------|------|------|
| L1 | 自动记录 | 报错/纠正自动写入 |
| L2 | 模式提取 | 提取通用规则 |
| L3 | 规则验证 | 追踪遵守/违反 |
| L4 | 优先级进化 | 频繁违反自动升级 |
| L5 | 知识沉淀 | critical规则→AGENTS.md |
| L6 | 跨域迁移 | 一条教训→所有相关领域 |
| L7 | 反馈闭环 | 有效内化/无效淘汰 |
| L8 | 衰减遗忘 | 14天标记→30天降级→90天归档 |
| L9 | 外部学习 | 导入行业最佳实践 |
| L10 | 预测犯错 | 场景匹配→犯错前弹出提醒 |
| L11 | 元学习 | 学习哪种学习方式最有效 |

## 统一智能层

```
unified_heal.py ←→ intel_hub.py ←→ error_evolution.py
     ↑                   ↑                ↑
  cron任务           所有脚本          错误日志
     ↑                   ↑                ↑
 自愈系统           自学习系统        错误进化引擎
```

## 数据文件

| 文件 | 用途 |
|------|------|
| `memory/learn-db.json` | 学习数据库 |
| `memory/learn-log.jsonl` | 学习日志 |
| `memory/learn-meta.json` | 元学习统计 |
| `memory/intel-hub-state.json` | 统一智能层状态 |
| `.learnings/LEARNINGS.md` | 兼容格式 |
