---
name: intl_news
description: "推送全球热门国际新闻。触发词：国际新闻、全球热点、今日要闻、world news、global news"
---

# 国际新闻推送技能

当用户询问国际新闻、全球热点、今日要闻时激活此技能。

## 使用工具

优先使用 Tavily 搜索获取最新新闻：

```bash
export TAVILY_API_KEY="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"
node ~/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "关键词" --topic news -n 5 --days 1
```

## 搜索策略

1. **多角度搜索**：分别搜索地缘政治、经济金融、科技、军事等方向
2. **关键词组合**：
   - `breaking world news today` — 综合热点
   - `global economy financial markets` — 经济金融
   - `geopolitics military conflict war` — 地缘军事
   - `AI technology innovation` — 科技创新
3. **去重合并**：多个搜索结果合并去重，按热度排序

## 输出格式

```
【🌍 国际热点速递】日期

🔴 1. 标题
简要描述（1-2句）
来源：媒体名

🟡 2. 标题
简要描述
来源：媒体名

...

---
整体趋势：一句话总结今日全球核心主线
```

- 热度分级：🔴 高热度 / 🟡 中热度 / 🟢 低热度
- 数量：Top 5-10 条
- 每条新闻 1-2 句话，简洁有力
- 末尾附整体趋势总结

## 注意事项

- 不分国界、不分种类，只看热度和影响力
- 如 Tavily 不可用，fallback 到 Google News RSS：
  ```bash
  curl -s 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en' | grep -oP '<title>(.*?)</title>' | head -10
  ```
