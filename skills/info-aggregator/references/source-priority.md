# 信息源优先级

## 可靠性分级

### Tier 1 - 官方/一手源
- 上交所/深交所官方公告
- 公司年报/季报
- 政府机构发布
- GitHub Release / 官方博客

### Tier 2 - 权威媒体
- 财联社、证券时报、第一财经
- Reuters、Bloomberg
- 知名行业媒体

### Tier 3 - 社区/分析
- 知乎专业回答
- Twitter/X 行业大V
- Reddit / Discord 社区
- B站/YouTube 技术博主

### Tier 4 - 仅供参考
- 自媒体标题党
- 无来源传闻
- 过期信息（>48h）

## 搜索工具优先级

| 场景 | 首选 | 备选 |
|------|------|------|
| 中文财经 | brave-search | multi-search-engine |
| 英文技术 | brave-search | tavily |
| 学术论文 | brave-search | browser |
| 中文综合 | multi-search-engine | searxng |

## 去重规则

1. 同一事件只保留最高可靠性来源
2. 相似内容合并为一条
3. 超过 48 小时的非重大新闻降级
4. 有明确数据的优先于纯观点
