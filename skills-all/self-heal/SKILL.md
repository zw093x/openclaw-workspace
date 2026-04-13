---
name: self-heal
description: 自愈系统 v3.0 — 自进化式系统修复。当系统报错、cron任务失败、磁盘告警、服务异常时调用。5层进化：根因关联、模式发现、阈值自适应、预防性修复、策略优化。统一智能层连接自学习系统和错误进化引擎。
allowed-tools:
  - exec
  - read
  - write
metadata:
  version: "3.0"
  author: P
---

# 自愈系统 v3.0 — 自进化版

统一诊断、修复、进化学习。

## 快速使用

```bash
# 诊断
python3 scripts/unified_heal.py

# 诊断 + 修复
python3 scripts/unified_heal.py --fix

# 完整报告（含进化分析）
python3 scripts/unified_heal.py --fix --report

# 仅进化学习（不修复）
python3 scripts/unified_heal.py --evolve

# 全量同步（连接所有系统）
python3 scripts/intel_hub.py --sync
```

## 5层进化能力

| 层级 | 能力 | 说明 |
|------|------|------|
| L1 | 根因关联分析 | 症状→根因映射 |
| L2 | 模式自动发现 | 从日志发现新故障模式 |
| L3 | 阈值自适应 | 磁盘/Cron延迟动态调整 |
| L4 | 预防性修复 | 趋势预测，提前介入 |
| L5 | 策略优化 | 评估修复效果，选最优方案 |

## 统一智能层

自愈系统通过 `intel_hub.py` 连接：
- **自学习系统** (`learn_evolve.py`)：修复失败→记录教训
- **错误进化引擎** (`error_evolution.py`)：错误分类→根因→建议
- **Cron任务**：连续错误→自动导入学习

## 数据文件

| 文件 | 用途 |
|------|------|
| `config/heal_patterns.json` | 故障模式配置 |
| `memory/heal-unified-log.jsonl` | 修复日志 |
| `memory/heal-evolution.json` | 进化状态 |
| `memory/heal-thresholds.json` | 自适应阈值 |
| `memory/intel-hub-state.json` | 统一智能层状态 |
