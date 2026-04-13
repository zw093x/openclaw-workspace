---
name: stock-intel
description: 股票信息采集与分析技能。当用户需要查询股票信息、收集市场数据、分析财务报告、评估信息可信度、或进行股票投资研究时触发。覆盖：信息来源分级体系、财务分析框架、研究流程规范。
---

# stock-intel — 股票信息采集与分析

## 信息来源分级（所有股票研究必须遵循）

| 等级 | 来源 | 用途 |
|------|------|------|
| A | 官方披露/年报/交易所 | 核心决策依据 |
| B | 权威媒体/券商研报 | 可用 |
| C | 行业媒体 | 辅助参考 |
| D | KOL/自媒体 | 谨慎采信 |

**执行规则：** 核心投资结论必须有A/B级来源支撑，C级以下信息不纳入核心判断。

## 股票自学体系

**启动时间：** 2026-03-26

**文件索引：**
- `memory/stock-knowledge.md` — 股票知识库
- `memory/analysis-accuracy.json` — 分析准确率追踪
- `memory/trade-journal.md` — 交易决策日志

**深度学习时间：** 每日01:30（4小时）

**学习内容：**
- 基本面分析（财务报表、行业周期、竞争格局）
- 技术面分析（趋势、均线、成交量）
- 消息面分析（政策、事件、情绪）

## 财报智能分析系统 L2

**文件：** `scripts/finance_judge.py` + `scripts/finance_evolve.py`

**分析维度（6维评分）：**

| 维度 | 评估内容 |
|------|----------|
| 成长性 | 营收/净利润增速 |
| 盈利能力 | 毛利率/净利率/ROE |
| ROE | 净资产收益率 |
| 稳健性 | 负债率/流动比 |
| 现金流 | 经营现金流/净利润比 |
| 存货 | 存货周转/积压风险 |

**数据源：**
- 主：同花顺（akshare）
- 备：通达信

**进化机制：** P工反馈 → 调整行业参数 → 60天股价验证

**使用方式：**
```bash
# 更新财报数据
python3 /root/.openclaw/workspace/scripts/finance_updater.py

# 分析评分
python3 /root/.openclaw/workspace/scripts/finance_judge.py
```

## 研究流程规范

1. **信息采集** → 按来源分级筛选
2. **交叉验证** → A/B源互相印证
3. **分析输出** → 结论标注来源等级
4. **决策记录** → 入库 `memory/trade-journal.md`
5. **准确率追踪** → 定期更新 `memory/analysis-accuracy.json`

## 持仓查询

如需查询当前持仓，请使用：`memory/stock-portfolio.md`

> 注意：本技能不含持仓数据，持仓信息存储于 `memory/stock-portfolio.md`
