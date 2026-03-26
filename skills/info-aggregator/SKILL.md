---
name: info-aggregator
description: "Multi-source information aggregation and report generation. Use for (1) compiling daily briefings from multiple sources (2) industry news digests for AI, shipping, stocks, tech (3) standardized reports with consistent formatting (4) summarizing web search into structured output. Triggers on 新闻, 资讯, 日报, 汇总, 简报, 信息聚合. Supports Chinese and English sources."
license: MIT
metadata:
  author: pengyu
  version: "1.0"
  languages: zh-CN, en
allowed-tools: Read Write
---

# Info Aggregator

## Quick Start

```bash
# Generate a daily AI news digest
python scripts/format_report.py --type daily --topic ai-news --days 1

# Format raw search results into report
python scripts/format_report.py --type custom --input raw_results.json --template industry

# Generate weekly summary
python scripts/format_report.py --type weekly --topic all --days 7
```

## Report Types

| Type | Use Case | Schedule |
|------|----------|----------|
| `daily` | Single-topic daily digest | Daily push |
| `weekly` | Multi-topic weekly summary | Weekly |
| `industry` | Industry-specific deep dive | On demand |
| `briefing` | Multi-topic morning brief | Daily AM |

## Workflow

```
1. Define topic and sources → references/source-priority.md
2. Gather raw information → web search / API / scraping
3. Filter and rank → dedup + relevance scoring
4. Format output → scripts/format_report.py with template
5. Deliver → structured markdown for push channels
```

## Output Standard

Every report follows this structure:
```
# {标题}
> {一句话摘要，≤50字}

## 要点速览
- [🔥热点] item 1
- [📊数据] item 2
- [💡洞察] item 3

## 详细内容
### {子话题1}
内容 + 来源链接

### {子话题2}
内容 + 来源链接

## 影响分析
对用户关注领域的影响（股票/工作/生活）

---
*来源: {source_list} | 生成时间: {timestamp}*
```

## File References

- Report templates: [references/report-templates.md](references/report-templates.md)
- Source priority: [references/source-priority.md](references/source-priority.md)
- Daily template: [assets/daily-template.md](assets/daily-template.md)
