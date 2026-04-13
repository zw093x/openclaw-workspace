---
name: review-evolve
description: 复盘进化系统 — 7层复盘自进化。当需要复盘决策、分析准确率、发现规律、优化策略、识别风险时自动调用。R1决策追踪 R2准确率分析 R3模式识别 R4策略优化 R5跨域学习 R6风险识别 R7元复盘。
allowed-tools:
  - exec
  - read
  - write
metadata:
  version: "1.0"
  author: P
---

# 复盘进化系统

7层复盘自进化，让决策越来越准。

## 快速使用

```bash
# 全量进化
python3 scripts/review_evolve.py --evolve

# 报告
python3 scripts/review_evolve.py --report

# 记录决策
python3 scripts/review_evolve.py --decide <topic> <decision> <reason>

# 记录结果
python3 scripts/review_evolve.py --outcome <id> <result> <score> [lesson]

# 每日/每周复盘模板
python3 scripts/review_evolve.py --daily
python3 scripts/review_evolve.py --weekly
```

## 7层进化能力

| 层级 | 能力 | 说明 |
|------|------|------|
| R1 | 决策追踪 | 每个决策→结果→教训全链路 |
| R2 | 准确率分析 | 预测vs实际，分主题统计 |
| R3 | 模式识别 | 发现成功/失败规律 |
| R4 | 策略优化 | 基于结果自动调整策略 |
| R5 | 跨域学习 | 一个领域的教训推广到其他领域 |
| R6 | 风险识别 | 未决决策/连续低分/未记录亏损 |
| R7 | 元复盘 | 复盘复盘系统本身 |

## 数据文件

| 文件 | 用途 |
|------|------|
| `memory/review-db.json` | 决策/预测/模式数据库 |
| `memory/review-log.jsonl` | 复盘日志 |
| `memory/analysis-accuracy.json` | 准确率统计 |
