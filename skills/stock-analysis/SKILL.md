---
name: stock-analysis
description: "A-share stock technical analysis and portfolio tracking. Use for (1) analyzing individual stocks with MA/RSI/MACD/volume indicators (2) real-time quotes and intraday data (3) portfolio P&L and position tracking (4) unusual price/volume detection. Triggers on stocks, trading, 股票, 行情, 技术分析, 持仓, 涨跌. Supports Shanghai/Shenzhen A-shares."
license: MIT
metadata:
  author: pengyu
  version: "1.0"
  market: A-share (SSE/SZSE)
allowed-tools: Read Write
---

# Stock Analysis

## Quick Start

```bash
# Fetch real-time quote
python scripts/fetch_quote.py 600150

# Run technical analysis
python scripts/technical_analysis.py 600150 --period 60

# Portfolio summary
python scripts/fetch_quote.py 600150 600482
```

## Workflow

```
1. Fetch quote data → scripts/fetch_quote.py
2. Technical analysis → scripts/technical_analysis.py
3. Interpret results → references/indicator-guide.md
4. Portfolio impact → cross-reference with memory/stock-portfolio.md
```

## Output Format

### Single Stock Report
```
[Stock] 中国船舶 (600150)
价格: 38.50 | 涨跌: +1.23% | 成交额: 12.3亿
MA5: 37.80 ↑ | MA10: 37.20 ↑ | MA20: 36.50 ↑
均线状态: 多头排列
量比: 1.5 | 换手率: 2.3%
信号: 放量上涨（成交量/5日均量=1.5x）
```

### Portfolio Summary
```
[Portfolio] 持仓总览
中国船舶 600150: 4000股 × 38.50 = 154,000 (成本 152,784) 盈亏: +1,216 (+0.80%)
中国动力 600482: 3000股 × 34.20 = 102,600 (成本 103,167) 盈亏: -567 (-0.55%)
总资产: 256,600 | 总盈亏: +649 (+0.25%)
```

## Alert Conditions

| Level | Condition | Action |
|-------|-----------|--------|
| S1 | 涨跌幅 > ±3% | Push notification |
| S2 | 涨跌幅 > ±5% | Urgent push |
| S1 | 成交量 > 1.5x 5日均量 | Push notification |
| S1 | 站上/跌破 MA20 | Push notification |

## File References

- Indicator interpretation: [references/indicator-guide.md](references/indicator-guide.md)
- Portfolio format: [references/portfolio-format.md](references/portfolio-format.md)
