## [ERR-20260325-001] 航运行业资讯 cron 任务超时

**Logged**: 2026-03-25T08:41:00+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
航运行业资讯定时任务连续 7 次执行超时

### Error
```
Error: cron: job execution timed out
```

### Context
- 任务每 2 小时执行一次，需要搜索和整理大量航运资讯
- 默认超时 120 秒不足以完成
- 连续 7 次失败（从 3/24 晚开始）

### Suggested Fix
超时从 120s 调整为 300s（已执行）

### Resolution
- **Resolved**: 2026-03-25T08:41:00+08:00
- **操作**: `openclaw cron edit 4f565b2e --timeout-seconds 300`
- **备注**: 如仍不够可进一步增大

---

## [ERR-20260326-001] Billing Error 连环故障（模型切换事故）

**Logged**: 2026-03-26T16:00:00+08:00
**Priority**: critical
**Status**: resolved
**Area**: config

### Summary
切换到 Gemini 2.5 Flash 时触发 billing error，导致约 2 小时（13:50-16:00）全部 API 调用失败

### Error
```
⚠️ API provider returned a billing error — your API key has run out of credits or has an insufficient balance.
```

### Context
- P工要求切换到 Gemini 2.5 Flash
- 执行 `openclaw config set` 切换默认模型
- 切换后立即触发 billing error（OpenRouter 账户状态异常）
- 影响范围：所有 cron 任务 + 用户对话，持续约 2 小时
- P工多次尝试沟通均失败（滴滴、你好、你还活着吗、切换模型、重启等）

### Root Cause
- 模型切换过程中，新模型（Gemini）的 API 调用被 OpenRouter 拒绝
- Gateway 配置已改但新模型不可用，旧模型也不再被使用
- OpenRouter 余额实际充足（$14.99），但账户状态/模型权限异常

### Resolution
- **Resolved**: 2026-03-26T16:03:00+08:00
- **操作**: 切换回 mimo/mimo-v2-pro 后恢复正常
- **教训**: 模型切换前必须先单独测试目标模型可用性

### Suggested Fix
1. 模型切换前先 curl 测试目标模型
2. 切换后立即发一条测试消息验证
3. 如失败，5秒内自动回滚到原模型
4. 考虑用模型 fallback 机制代替硬切换

---

## [ERR-20260326-002] 飞书 Pairing 失效（服务器迁移后）

**Logged**: 2026-03-26T20:34:00+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
服务器迁移后飞书用户授权丢失，需要重新 pairing

### Error
```
OpenClaw: access not configured. Your Feishu user id: ou_a6469ccc2902a590994b6777b9c8ae8f
Pairing code: RY7DS8BY
```

### Context
- 从旧服务器（159.75.77.36）迁移到新服务器（42.193.183.176）
- 配置文件迁移后，用户授权信息未包含在内
- P工手动执行 `openclaw pairing approve feishu RY7DS8BY` 后恢复

### Resolution
- **Resolved**: 2026-03-26T20:35:00+08:00
- **操作**: `openclaw pairing approve feishu RY7DS8BY`

### Suggested Fix
- 服务器迁移时需额外备份 `.openclaw/access.json` 或等效授权文件
- 迁移检查清单中增加"飞书 pairing"一项

---

## 2026-03-25: 股票记录严重失实

**错误**: 
1. 汇报"调仓盈利210元" — 实际整体浮亏约28,005元，调仓只是减少了损失
2. 完全遗漏了下午的调仓②（船舶减仓1000股+泰禾智能新建仓）
3. 把现金流差额（+210）等同于"盈利"，忽略了持仓成本远高于市价的事实

**根因**:
- 没有在汇报前读取 `stock-portfolio.md` 最新记录（该文件14:44已更新）
- 凭记忆中的早期数据汇报，导致信息过时
- 对"盈利"的理解错误：卖出价>买入价 ≠ 盈利，要看成本价

**教训**:
- 涉及财务数据，必须先查最新文件再汇报
- 不能把"现金流正向"说成"盈利"
- 复盘前要全面收集信息，不能只看对话记录

---

## 2026-03-25: 全天复盘质量差

**错误**:
- 全天复盘只覆盖了下午的代理部署，忽略了上午的投资操作和学习计划
- 被用户纠正后才补充完整

**根因**:
- 没有通读全天记忆文件就做总结
- 默认以最后对话内容为"今日主要工作"

**教训**:
- 做全天复盘前，必须先读取完整的 `memory/YYYY-MM-DD.md`
- 不要偷懒，每一条记录都要核实

