# Cron 故障知识库 v2
*最后更新: 2026-03-30*

## 已知故障模式（9种）

| # | 故障类型 | 错误特征 | 根因 | 自动修复 | 预防措施 |
|---|---------|---------|------|---------|---------|
| 1 | channel_missing | `Channel is required when multiple channels...` | 双渠道配置后 cron channel 解析失败 | ✅ 重新设置 delivery | 新建任务必带 --channel |
| 2 | feishu_target | `Delivering to Feishu requires target...` | 飞书目标格式不对 | ✅ 重新设置 delivery | 统一用 open_id 格式 |
| 3 | message_failed | `⚠️ ✉️ Message failed` | 瞬态投递竞态 | ✅ 触发重试 | 检查 delivered 状态 |
| 4 | timeout | `cron: job execution timed out` | 任务耗时过长 | ⚠️ 增加 timeout | 搜索类≥300s，简单≥60s |
| 5 | sigterm | `SIGTERM` | 系统终止 | ⚠️ 检查资源 | 增加 timeout 或优化任务 |
| 6 | duplicate_delivery | 用户收到重复消息 | OpenClaw cron + 系统 crontab 同时触发 | ✅ 设置 --no-deliver | 卡片任务统一用系统 crontab |
| 7 | card_json_garbled | 显示原始 JSON | agent 输出 JSON 但文本投递 | ✅ 去掉 JSON 指令 | 用 cron_card_wrapper.py |
| 8 | agent_no_tool_call | 数据未获取/指令未执行 | mimo-v2-pro 在隔离会话不调用工具 | ⚠️ 数据预注入 | 用 weather_preload.py 预注入 |
| 9 | 流式卡片无内容 | `deliveryStatus=not-delivered` | agent 返回 NO_REPLY 但无实际投递 | ⚠️ 检查 agent 行为 | 确保 agent 实际发送了消息 |

## 卡片投递架构（当前方案）

```
┌─────────────────┐
│  系统 crontab    │  (定时触发)
│  07:25 天气预加载 │
│  07:35 早报投递   │
│  08:05 天气提醒   │
│  ...             │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ weather_preload  │     │ cron_card_wrapper │
│ 天气数据注入      │────▶│ 1.触发 cron 任务  │
└─────────────────┘     │ 2.等待完成       │
                        │ 3.获取内容       │
                        │ 4.调用飞书 API   │
                        └──────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ feishu_card_send │
                        │ 直接调用飞书 API  │
                        │ 发送卡片消息      │
                        └──────────────────┘
```

### 关键文件
- `scripts/weather_preload.py` — 天气数据预加载
- `scripts/cron_card_wrapper.py` — 卡片投递包装器
- `scripts/feishu_card_send.py` — 飞书 API 卡片发送
- `scripts/cron_diagnose.py` — 故障诊断+自动修复
- `scripts/update_fault_registry.py` — 故障知识库更新
- `scripts/self_heal_registry.json` — 自愈系统注册表

### 卡片投递任务（18个）
每日早报、天气穿衣、AI日报、CG资讯、AI绘画、科技资讯、A股早评、股票开盘、股票收盘、SpaceX监控、节气节日、健康小贴士、晚间复盘、股票复盘、ComfyUI学习、ComfyUI复盘、ComfyUI周总结、每周综合周报

### 系统 crontab 管理
```bash
crontab -l          # 查看
crontab -l | grep cron_card_wrapper  # 查看卡片任务
```

## 新建 cron 任务检查清单

1. [ ] 指定 `--channel feishu --to <open_id>`
2. [ ] 搜索类任务设置 `--timeout-seconds 300`
3. [ ] 如需卡片投递：添加到系统 crontab + 设置 `--no-deliver`
4. [ ] 如需天气数据：在 prompt 中说明引用预注入数据
5. [ ] 不要让 agent 输出 JSON 卡片格式
6. [ ] 测试手动触发：`openclaw cron run <id>`
7. [ ] 确认投递成功：`openclaw cron runs --id <id> --limit 1`
