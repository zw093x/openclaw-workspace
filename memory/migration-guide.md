# 系统迁移指南

*最后更新: 2026-03-26*
*用途: 服务器迁移或系统重建时的恢复指南*

## 一、Workspace 文件（核心）

以下文件是核心，必须完整迁移：

```
/root/.openclaw/workspace/
├── MEMORY.md              # 长期记忆（最重要）
├── SOUL.md                # 人格定义
├── USER.md                # 用户档案
├── IDENTITY.md            # 身份信息
├── AGENTS.md              # 工作规则
├── TOOLS.md               # 工具配置笔记
├── HEARTBEAT.md           # 心跳监控任务
├── memory/
│   ├── YYYY-MM-DD.md      # 每日记录
│   ├── stock-portfolio.md # 股票持仓
│   ├── stock-strategy-*.md # 减仓策略
│   ├── stock-knowledge.md # 股票知识库
│   ├── knowledge-shipping.md # 船舶行业知识库
│   ├── knowledge-ai.md    # AI行业知识库
│   ├── analysis-accuracy.md # 分析准确率追踪
│   ├── comfyui-*.md       # ComfyUI学习资料
│   ├── friend-account.md  # 朋友账户
│   ├── gold-price-state.json # 黄金价格状态
│   ├── comfyui-monitor-state.json # ComfyUI监控状态
│   ├── heartbeat-state.json # 心跳状态
│   ├── cron-backup.json   # Cron任务备份（本文件）
│   └── spacex-news.md     # SpaceX新闻
├── scripts/
│   ├── stock_realtime_monitor.py # 盘中实时监控脚本
│   ├── stock_analyzer.py  # 技术分析脚本
│   └── ...                # 其他脚本
└── .learnings/
    ├── LEARNINGS.md       # 学习记录
    └── ERRORS.md          # 错误记录
```

## 二、Cron定时任务重建

导入 `memory/cron-backup.json` 中的任务配置。

**关键任务清单（必须重建）：**

### 每日推送（按时间排序）
| 时间 | 任务名 | 类型 |
|------|--------|------|
| 07:00 | 每日健康小贴士 | isolated |
| 07:00 | 每日节气节日提醒 | isolated |
| 07:30 | 每日早报 | isolated |
| 08:00 | 每日天气穿衣饮食提醒 | isolated |
| 08:00 | CG行业资讯日报 | isolated |
| 08:00 | AI行业日报 | isolated |
| 08:30 | AI绘画日报 | isolated |
| 08:50 | A股大盘早评（工作日） | isolated |
| 08:55 | 每日股票开盘提醒 | isolated |
| 09:00 | 每日航运指数播报（工作日） | isolated |
| 09:00 | 科技资讯日报 | isolated |
| 09:00 | 船舶行业新闻监控（工作日，5次/天） | isolated |
| 10:00 | 每日开源项目推荐 | isolated |
| 12:00 | AI编程效率日报 | isolated |
| 15:10 | 每日股票收盘提醒（工作日） | isolated |
| 22:00 | 晚间复盘（含学习进度汇报） | isolated |

### 盘中监控（核心）
- **盘中实时股票监控**: cron 0,15,30,45 9-14 * * 1-5 @ Asia/Shanghai
- 运行脚本: `python3 /root/.openclaw/workspace/scripts/stock_realtime_monitor.py`

### 每周/每月
- 周六 09:00 周末生活指南
- 周日 10:00 综合周报
- 周一 09:00 AI模型价格监控
- 周三 10:00 宝宝成长健康提醒
- 每月1日 09:00 每月财务提醒

### 心跳监控（HEARTBEAT.md）
- 股票异动、天气异常、AI模型状态、船舶行业快讯、黄金价格、ComfyUI生态、SpaceX新闻、飞书插件动态

## 三、恢复步骤

1. **迁移workspace目录** — 整个 `/root/.openclaw/workspace/` 复制到新服务器
2. **安装OpenClaw** — 按官方文档安装
3. **配置飞书渠道** — 恢复飞书API配置
4. **重建Cron任务** — 参考 `memory/cron-backup.json` 逐个创建
5. **安装依赖** — `pip3 install` 监控脚本所需依赖
6. **配置代理** — 恢复 mihomo 配置（/etc/mihomo/）
7. **验证** — 运行 `openclaw status` 确认一切正常

## 四、信息源体系（31大类，250+源）

完整信息源列表见 MEMORY.md "信息采集原则" 章节。
涵盖：国际通讯社、财经、科技/AI/芯片/机器人、航运/船舶、军事、宏观经济、大宗商品、国际组织、政府机构、行业协会、智库、评级、央行、社交媒体、数据平台、政策文件、展会、宏观经济指标、并购/IPO、碳市场/ESG、航空航天、生物医药、稀土、3D打印、船级社、港口数据、外汇/债券、贸易救济、灾害监控、海上保险、离岸能源、研报券商。

## 五、股票自学体系

- 知识库: `memory/stock-knowledge.md`
- 行业知识库: `memory/knowledge-shipping.md`、`memory/knowledge-ai.md`
- 准确率追踪: `memory/analysis-accuracy.md`
- 8大学习模块: 基本面、技术面、行业研究、宏观、资金面、风险管理、行为金融、量化
- 每晚22:00汇报学习进度（融入晚间复盘）

---

*定期更新此文件。每次新增重要配置后同步更新。*
