---
name: daily_briefing
description: "生成每日综合简报（天气+新闻+股票+提醒）。触发词：每日简报、今日简报、daily briefing、综合简报"
---

# 每日综合简报技能

当用户要求生成每日简报或综合报告时激活。

## 数据采集

### 1. 天气数据
```bash
# 广州天气
curl -s "https://wttr.in/Guangzhou?format=%C+%t+%h+%w" 2>/dev/null
# 佛山天气
curl -s "https://wttr.in/Foshan?format=%C+%t+%h+%w" 2>/dev/null
```

### 2. 股票数据
```bash
# 中国船舶 600150
curl -s "https://qt.gtimg.cn/q=sh600150" | iconv -f GBK -t UTF-8
# 中国动力 600482
curl -s "https://qt.gtimg.cn/q=sh600482" | iconv -f GBK -t UTF-8
```

### 3. 国际新闻
```bash
export TAVILY_API_KEY="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"
node ~/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "breaking world news today" --topic news -n 5 --days 1
```

### 4. 黄金/白银/甲醇
```bash
# 黄金
curl -s 'https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD'
# 白银
curl -s 'https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAG/USD'
# 甲醇
curl -s 'https://hq.sinajs.cn/list=nf_MA0' -H 'Referer: https://finance.sina.com.cn' | iconv -f GBK -t UTF-8
```

## 输出格式

```
【📋 每日综合简报】YYYY-MM-DD（星期X）

🌤️ 天气
- 广州：天气 + 温度 + 湿度
- 佛山：天气 + 温度 + 湿度
- 穿衣/饮食建议

📈 金融市场
- 黄金/白银/甲醇报价
- 持仓股票行情（如有交易日）

🌍 国际要闻（Top 3-5）
- 简要新闻摘要

📅 今日提醒
- 待办事项/定时任务/特殊日期
```

## 注意事项

- 周末不显示股票行情
- 月子期间需包含饮食建议
- 内容控制在 15 行以内
