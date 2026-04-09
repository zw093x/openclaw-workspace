# 系统全景概览
> 最后更新：2026-04-09 10:06

---

## 一、用户档案

| 项目 | 内容 |
|------|------|
| 姓名 | 彭煜 |
| 职业 | 模型师（广州天河猎德） |
| 配偶 | 广西梧州人，已生产 |
| 宝宝 | 2026-03-11 女宝，孕39周+2天足月，7.5斤 |
| 称呼 | P工 |

---

## 二、股票持仓

| 股票 | 代码 | 持仓 | 成本 | 策略 |
|------|------|------|------|------|
| 中国船舶 | 600150 | 3,000股 | 41.04 | 长期（2000核心+1000可操作） |
| 中国动力 | 600482 | 2,000股 | 35.079 | 长期（全固定不可动） |
| 三安光电 | 600703 | 500股 | 11.44 | 试探建仓 |
| 视源股份 | 002841 | 500股 | 33.80 | 朋友账户 |

---

## 三、服务器与系统

| 项目 | 详情 |
|------|------|
| 云服务器 | 腾讯云轻量 42.193.183.176 |
| 代理 | mihomo 127.0.0.1:7890（Trojan节点：沪→新加坡/日本） |
| Docker | v29.3.1，运行Open Terminal镜像 |
| Open Terminal | 端口8081，Key: `3SPH6J0J8nytZGU2pOphXgrjm2dkhd3y` |
| ttyd | 端口8082（admin/ttyd2026） |
| OpenClaw Gateway | http://127.0.0.1:18789，Token: `3d1438146f355d26c67c44516d809171ae180cedf85981d2` |
| 腾讯云CLI | v3.1.59.1（需配SecretId/Key） |

---

## 四、AI模型

| 模型 | 用途 | 状态 |
|------|------|------|
| blockrun/nemotron | Cron任务主力 | ✅ 免费 |
| minimax/MiniMax-M2.7 | 当前对话 | ✅ 默认 |
| openrouter/google/gemini-2.5-flash | 备选付费 | ⚠️ $0.15/M输入 |
| mimo-v2-pro (OpenRouter) | 已废弃 | ❌ 没钱了 |
| Gemini Key | Google直连 | ❌ 不可用 |

---

## 五、搜索/信息获取渠道

### 国际新闻 RSS（通过代理 127.0.0.1:7890）

| 媒体 | RSS地址 | 覆盖 |
|------|---------|------|
| BBC News | `https://feeds.bbci.co.uk/news/world/rss.xml` | 全球综合 |
| CNBC | `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114` | 财经/特朗普 |
| France 24 | `https://www.france24.com/en/rss` | 中东/政治 |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` | 中东/伊朗 |
| The Guardian | `https://www.theguardian.com/world/rss` | 欧洲深度 |
| NPR | `https://feeds.npr.org/1001/rss.xml` | 美国国内 |
| Deutsche Welle | `https://rss.dw.com/rdf/rss-en-all` | 欧洲视角 |

### 搜索工具

| 工具 | 说明 |
|------|------|
| web_search | DuckDuckGo通用搜索 |
| Tavily | AI优化搜索（skill） |
| SearXNG | 隐私搜索（skill） |

### 股票数据

| 源 | 说明 |
|------|------|
| mootdx（通达信） | A股主源，无需代理 |
| 腾讯行情 qt.gtimg.cn | A股备源，无需代理 |
| akshare（同花顺） | 财报/宏观，需代理 |

---

## 六、API/应用凭据

### OpenClaw

| 项目 | 值 |
|------|---|
| Gateway URL | http://127.0.0.1:18789 |
| Gateway Token | `3d1438146f355d26c67c44516d809171ae180cedf85981d2` |

### 飞书

| 项目 | 值 |
|------|---|
| App ID | `cli_a9489e1f4c78dbb6` |
| App Secret | `mKeApaf2UE3CDN8wlh1IJcDSxcJlYlhD` |

### AI平台

| 平台 | Key |
|------|-----|
| OpenRouter | `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`（余额$9.50）|
| mimo（小米） | `sk-c3ik1rbky5s8wejpwvjj3hufs7gh544ybxfxzts4jzb0cw19`（已无余额）|
| Gemini Key | `AIzaSyAT4rLWTjDh-2Y3zepE5MRXcNfCm8w0pIg` |

### 社交/账号

| 平台 | 凭据 |
|------|------|
| Google | `zw093x@gmail.com` / `0908093x.` |
| GitHub Token | `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` |
| Gitee Token | `cfefc79394c51645f6907ebe272749b5` |

### 仓库

| 仓库 | 地址 |
|------|------|
| Gitee | https://gitee.com/zw093x/openclaw-workspace |
| GitHub | https://github.com/zw093x/openclaw-workspace（写保护被拒）|

---

## 七、定时任务（65个cron）

| 任务 | 时间 | 状态 |
|------|------|------|
| ☀️ 每日早报 | 07:30 | 🔶需启用 |
| 🤖 AI综合日报 | 08:00 | 🔶需启用 |
| 🌍 全球热点新闻 | 08:00/20:00 | ✅ |
| 📊 A股盘前播报 | 08:50 (工作日) | ✅ |
| 🎨⚡ CG科技日报 | 12:30 | 🔶需启用 |
| 💰 大宗商品播报 | 每6h | ✅ |
| 📊 收盘总结 | 15:10 (工作日) | 🔶需启用 |
| 🚀 SpaceX追踪 | 9/15/21点 | 🔶需启用 |
| 🌙 晚间综合复盘 | 22:00 | 🔶需启用 |
| 深度学习时段 | 01:30 | 🔶需启用 |

> 今日修复：网关超时120s→300s，创建stock_premarket_report.py（腾讯行情直拉）

---

## 八、已安装技能（SkillHub）

| 技能 | 说明 |
|------|------|
| tavily-search | AI优化搜索 |
| searxng | 隐私搜索 |
| info-aggregator | 多源信息聚合 |
| intl-news | 国际新闻 |
| finance-report-analyzer | 财报分析 |
| tushare-finance | A股数据 |
| a-stock-analysis | A股行情分析 |
| agent-browser | 浏览器自动化 |
| summarize | URL/文件摘要 |
| x-api | X/Twitter发帖 |
| outlook-api | 邮件/日历 |

共约37个技能，详见 `~/.openclaw/workspace/skills/`

---

## 九、备份体系

| 目标 | 频率 | 状态 |
|------|------|------|
| Gitee | 每30分钟增量 | ✅ 正常 |
| GitHub | 每30分钟增量 | ❌ 写保护被拒 |
| cron/jobs.json | 已纳入Gitee | ✅ 今日加入 |

---

## 十、系统文件路径

| 类别 | 路径 |
|------|------|
| Cron配置 | `/root/.openclaw/cron/jobs.json` |
| 记忆文件 | `/root/.openclaw/workspace/memory/` |
| 脚本 | `/root/.openclaw/workspace/scripts/` |
| LCM数据库 | `/root/.openclaw/lcm.db` |
| 备份 | `/root/.openclaw/backups/` |
| OpenClaw配置 | `/root/.openclaw/openclaw.json` |

---

## 十一、未解决问题

| 问题 | 优先级 | 备注 |
|------|--------|------|
| GitHub写保护 | 🔴 高 | 需人工去GitHub设置解除 |
| 飞书 pairing失效 | 🔴 高 | 需重新配对 |
| 21个cron任务被禁用 | 🟡 中 | 正在逐一启用 |
| mootdx有时返回0 | 🟡 中 | 腾讯行情备源已加 |
| 盘中监控数据准确性 | 🟡 中 | 依赖真实脚本vs AI搜索 |

---

*此文件由系统自动生成，覆盖全量系统信息*
