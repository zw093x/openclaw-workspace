# HEARTBEAT.md - 主动监控任务

## 🔴 最高优先级：学习系统保障（每次心跳必检）

**确保深度学习系统正常运转，任何异常立即修复。**
- 检查深度学习 cron 任务（ID: 3273567b）是否 enabled 且正常执行
- 检查学习复盘报告 cron 任务（ID: 73d65bb2）是否 enabled
- 如任务失败 → 立即重新触发
- 如模型不可用 → 切换到可用模型后重试
- **此事项优先于一切其他监控**

## 黄金价格监控（每次心跳必检）

监控黄金（XAU/USD）和 PAXG（PAXGUSDT）实时价格：
- 通过 Swissquote API 获取黄金报价：`curl -s 'https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD'`
- 通过 CoinGecko 获取 PAXG 价格：`curl -s 'https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd,cny&include_24hr_change=true'`
- 获取 USD/CNY 汇率：`curl -s 'https://api.exchangerate-api.com/v4/latest/USD'`
- **触发预警条件：**
  - 单日涨跌幅 > ±2%（S1）→ 主动推送
  - 单日涨跌幅 > ±3%（S2）→ 紧急推送
  - 突破历史关键价位（如整数关口）→ 主动推送
- 状态文件：`memory/gold-price-state.json`

## ComfyUI 生态监控（每12小时检查一次）

**监控目标：** ComfyUI 架构变化 + 3D 节点生态 + AI 建模工作流
**检查频率：** 每12小时检查一次（通过状态文件记录上次检查时间）
**状态文件：** `memory/comfyui-monitor-state.json`（记录 lastCheck 时间戳，心跳时若距上次>=12小时则执行）
**触发条件：** 发现任何重大更新/新节点/工作流突破 → 立即主动推送

## OpenClaw 飞书插件动态监控（每日检查1次）

监控 OpenClaw 飞书官方插件更新动态：
- **检查方式：** 运行 `npx @larksuite/openclaw-lark info` 查看本地版本 vs 最新版本
- **触发推送条件：** 版本更新、新功能上线、破坏性更新、安全策略调整、重大 bug 修复
- **当前版本：** 2026.3.17
- **注意事项：** OpenClaw 3.22 存在不兼容变更，预计 3.24 修复完成

### 自动更新+自动学习流程
检测到新版本时，按以下流程自动执行：
1. **自动更新插件：** 运行 `npx -y @larksuite/openclaw-lark update`
2. **重新读取文档：** 获取飞书文档 `MFK7dDFLFoVlOGxWCv5cTXKmnMh` 最新内容
3. **学习变更内容：** 对比新旧版本差异
4. **主动推送通知：** 向用户汇报更新结果
5. **更新记忆文件：** 将版本信息和变更要点写入 `memory/`

---

## ℹ️ 已交由 Cron 处理的监控项（不在心跳中执行）

以下任务已移至 cron 定时任务，无需心跳重复检查：
- 股票技术面监控 → 盘中实时股票监控（cron，工作日15分钟一次）
- 股票减仓监控 → 盘中减仓监控（cron，工作日30分钟一次）
- 天气异常监控 → 每日天气穿衣饮食提醒（cron，每日08:00）
- AI模型状态 → AI模型价格监控周报（cron，每周一09:00）
- 船舶行业新闻 → 航运/船舶快讯（cron，每日每6小时）
- SpaceX上市新闻 → SpaceX上市新闻监控（cron，每日9/12/15/18/21点）
- 每日推送任务跟进 → cron 自动投递，无需心跳检查
