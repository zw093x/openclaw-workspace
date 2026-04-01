## [LRN-20260325-001] correction

**Logged**: 2026-03-25T10:25:00+08:00
**Priority**: critical
**Status**: pending
**Area**: memory

### Summary
未主动记录用户股票持仓信息，导致每次需要重新询问

### Details
用户之前告知过持仓情况（中国船舶、中国动力），但未被记录到任何记忆文件中。当用户今天要求持仓分析时，无法提供完整信息，需要用户再次告知。

根本原因：之前采用"被动记录"策略，只在明确要求时才写文件。日常对话中的关键信息（持仓、偏好、决定等）被遗漏。

### Suggested Action
建立"主动记录"规则：
1. 财务操作 → 自动记录到 stock-portfolio.md
2. 重要决定 → 记录到当日日志
3. 个人信息 → 更新 USER.md
4. 规则：宁可多记，不可漏记
5. 每次会话结束前检查是否有新信息需要记录

### Metadata
- Source: user_feedback
- Related Files: memory/stock-portfolio.md, MEMORY.md, USER.md
- Tags: memory, portfolio, proactive
- See Also: -

---

## 2026-03-25: Google API 代理封锁规律

**category**: knowledge_gap  
**适用**: 服务器代理 + Google API

### 发现
- Google 对某些代理 IP 段（特别是数据中心 IP）做 TLS 级别封锁
- 特征：HTTP CONNECT 隧道可建立（200 OK），但 TLS 揩手失败（SSL_ERROR_SYSCALL）
- 跨所有节点（台湾/日本/新加坡）、所有协议（HTTP/SOCKS5/Python urllib）均失败
- `fonts.googleapis.com`（HTTP）可正常响应，说明封锁在 HTTPS/TLS 层

### 解决方案
- 通过 OpenRouter 中转访问 Google 模型（如 Gemini 2.5 Flash）
- OpenRouter 不受此限制，可正常通过代理访问

### 教训
- 遇到 TLS_ERROR_SYSCALL 时，先检查是否为目标域名的特殊封锁
- 不要在已被封锁的路径上浪费时间，优先寻找替代方案
- OpenRouter 作为 API 聚合器是可靠的中转选择

---

## 2026-03-25: Cloudflare 数据中心 IP 封锁

**category**: knowledge_gap  
**适用**: 代理订阅链接访问

### 发现
- Cloudflare 企业防火墙可直接封禁数据中心 IP
- 区别于 Cloudflare Challenge（验证码），这是硬拦截
- agent-browser（headless 浏览器）也无法绕过

### 解决方案
- 不依赖订阅链接，改为用户提供节点配置手动部署
- 或在本地浏览器获取订阅内容后粘贴到服务器


## 2026-03-26 | correction | 信息采集必须从一手源头获取
- P工要求：资讯类任务不能依赖二手/聚合信息源
- 必须直接从法新社、BBC、央视新闻、同花顺财经等头部新闻网获取
- 获取后从源头延展关联报道，确保信息的权威性和深度

## 2026-03-26 | correction | 角色定位：我是学习和分析的执行者
- 核心问题：不要把学习和分析的工作转嫁给用户
- 我是助手+秘书，应该自主学习、自主分析、给结论
- 推送标准：信息 + 分析 + 判断 + 建议，不是单纯搬运
- 不要反复请示框架性问题，直接执行

### 2026-03-26 - 回复风格纠正
- **category**: correction
- **问题**: 信息查询类操作时问"要我帮你查吗"，这是多余的一句话
- **正确做法**: 能查的先查了再说，直接给出具体数据，不让用户做无意义的判断
- **原则**: 专业秘书 = 主动执行 > 被动等待指令

## 2026-03-26 | correction | 模型切换是高风险操作
- 切换到 Gemini 2.5 Flash 时触发 billing error，导致约 2 小时全部 API 调用失败
- P工多次尝试沟通（滴滴、你好、你还活着吗）均无响应
- **教训**: 模型切换前必须先验证目标模型可用性，确认余额充足
- **教训**: 切换过程中保持当前模型可用，不要先切再验证
- **教训**: 系统可靠性是第一优先级，宁可不升级也不要搞挂

## 2026-03-26 | correction | 记住用户说过的话
- P工明确说过"OpenRouter已经充值成功"，我后续还在问"要不要充值"
- **问题**: 没有记住用户在本次会话中已经告知的信息
- **正确做法**: 用户说过的事实，立即记录并引用，不再重复询问
- **原则**: 用户说过的每句话都是事实，除非有矛盾需要澄清

## 2026-03-26 | best_practice | 推送不要信息过载
- P工反馈："当前看着太混乱了"
- 股票异动推送内容过多、格式复杂，反而降低了可读性
- **改进**: 单条推送聚焦1个核心结论，格式精简
- **改进**: 数据用列表呈现，重点加粗，不过度堆砌细节
- **改进**: 预警推送格式：结论 → 关键数据 → 建议，不超过10行

## 2026-03-26 | best_practice | 响应速度影响用户体验
- P工反馈："为什么这么慢"
- Gemini 模型推理时间明显长于 mimo-v2-pro，影响了实时交互体验
- **改进**: 对话场景优先使用响应快的模型，复杂推理任务再用大模型
- **改进**: 批量分析/报告生成用子代理，主对话保持轻量快速

### 2026-03-27: GitHub CLI PAT 登录流程
- **category**: best_practice
- **场景**: 用户需要在服务器上登录 GitHub
- **方法**: `echo "TOKEN" | gh auth login --with-token`（无需终端交互）
- **验证**: `gh auth status` 确认登录成功
- **注意**: Token 会存储在 `~/.config/gh/hosts.yml`
- **适用**: 无头服务器、SSH 环境、CI/CD

### 2026-03-27: OpenRouter 模型配置批量添加
- **category**: best_practice
- **场景**: 需要批量添加模型到 OpenClaw 配置
- **方法**: 读取 openclaw.json → Python 脚本去重追加 → 写回
- **关键**: 先用 set 去重，避免重复添加
- **脚本路径**: 可复用，下次直接调用

### 2026-03-27: Cron 任务降频解决 Session 争抢
- **category**: best_practice
- **问题**: 多个 every N cron 任务同时触发导致隔离 Session 超时
- **解决**: 将高频（≤2h）任务降到 6h+，错开触发时间
- **命令**: `openclaw cron edit <id> --every 6h`
- **教训**: 不要让多个 cron 任务在同一分钟触发

### 2026-03-27: 会话模型实时切换
- **category**: best_practice
- **场景**: 需要临时切换当前会话的模型（如免费→付费验证能力）
- **方法**: `session_status(model="openrouter/xxx")`
- **注意**: 仅影响当前会话，不影响全局默认模型
- **配合**: 修改 openclaw.json 的 models.default 影响全局

### 2026-03-27: 项目评估流程（AI Forge MCP 案例）
- **category**: best_practice
- **步骤**: gh repo view 看概要 → gh repo clone → 读 README/INSTALL/PIPELINE/CHANGELOG → 对比分析
- **关键**: 先确认是否开源（有无源码），闭源项目只看文档即可
- **输出**: 结构化对比表（与用户工作流的关联度、优劣势、建议）

## 提速实践（2026-03-31）

### category: best_practice

**问题**: 用户反映响应慢+无进度反馈

**解决方案**:
1. **先秒回再执行** — 复杂任务先发"收到，正在处理..."，结果出来后再发正式回复
2. **复杂任务用子代理** — 耗时>10s的任务用 sessions_spawn 交给子代理
3. **对话超长换会话** — 连续2小时+的对话主动建议开新会话，从 MEMORY.md 恢复
4. **Cron prompt精简** — 从300+token精简到100-150token，减少cron执行时间
5. **非紧急操作批量处理** — 攒到一起一次性执行，减少来回次数

**Cron Prompt精简统计**:
- 晚间复盘: 约400token → 150token
- 每日早报: 约300token → 120token
- AI综合日报: 约250token → 100token
- 盘前播报: 约200token → 80token
- CG科技日报: 约200token → 80token
- 收盘总结: 约250token → 100token

## 响应速度强制规则（2026-03-31 第二次确认）

### category: correction

**规则：收到任何需要执行的消息，必须先发"收到，正在处理..."，再执行。**
- 例外：纯文字回答（不需要跑脚本/查文件）可以秒答不发确认
- 例外：连续对话中直接回复（用户刚发消息等我回复）
- 强制：涉及脚本运行、文件读写、cron修改、数据查询 → 必须先发确认

**执行方式：使用 message(action=send) 先发确认，再做实际工作。**

### 2026-04-01 | correction | 交易决策前必须深度验证长期逻辑

**事件：** 上午建议动力减仓第一档（32.50卖500股），用户执行后发现长期逻辑是"一机难求"——结构性变化，不应该用周期股逻辑减仓。

**教训：**
1. 做减仓/止损建议前，先问用户的长期判断是什么
2. 不要默认套用通用减仓策略，需要深度验证行业逻辑
3. 用户的行业洞察可能比通用框架更有价值
4. 对"结构性变化"vs"周期反弹"要区分对待

**规则：** 涉及用户持仓的操作建议，必须先了解其长期投资逻辑，再做验证和补充，而不是先给建议。

---

### 2026-04-01 | knowledge_gap | 信息监控需要覆盖行业深度消息

**事件：** 用户提到"船用发动机订单爆满"的消息，但我之前没有主动监控这个方向。

**教训：**
- 股票监控不应只看价格和资金流，需要关注行业基本面变化
- 中国动力的核心变量是发动机供需关系，需要监控相关产业新闻
- 已将关键词加入 stock-knowledge.md

**行动：** 在盘中监控和每日资讯中增加行业深度消息的采集。

## [LRN-20260401-001] best_practice

**Logged**: 2026-04-01T16:36:00+08:00
**Priority**: critical
**Status**: implemented

**What happened**: 交易决策流程倒置 — 先卖出动力500股，事后才改为"长期持有"策略。

**Lesson**: 交易操作前必须先验证用户的长期逻辑，不套用通用减仓框架。用户对行业的深度洞察（一机难求、船周期）比通用策略更有价值。

**Action**: 写入 AGENTS.md 硬编码规则 — 交易决策前置5步流程，任何卖出/买入操作前必须先完成逻辑验证。

---

## [LRN-20260401-002] best_practice

**Logged**: 2026-04-01T16:36:00+08:00
**Priority**: high
**Status**: implemented

**What happened**: 信息搜索结果中混入未经验证的说法（"与中际旭创联合开发"等），后被纠正为"未见官方公告"。

**Lesson**: 投资分析中信息来源可靠性必须分级标注，不能将所有搜索结果等同对待。

**Action**: 写入 AGENTS.md 信息可靠性分级规则（A-E五级），核心投资结论必须有A/B级来源支撑。

---

## [LRN-20260401-003] correction

**Logged**: 2026-04-01T16:36:00+08:00
**Priority**: medium
**Status**: implemented

**What happened**: 泰禾智能题材股快进快出4.5小时亏损50元。无明确催化剂，买入时机不佳。

**Lesson**: 题材股建仓需要更严格的入场条件：明确催化剂+支撑位+止损位+热度判断。

**Action**: 写入 AGENTS.md 题材股建仓检查清单（6项条件全满足方可建仓）。

## [LRN-20260401-001] correction

**Logged**: 2026-04-01T22:20:20.154168
**Priority**: medium
**Status**: pending

### Summary
交易决策前必须深度验证长期逻辑

### Details
先卖动力500股才改长期持有，流程倒置

### Metadata
- Source: auto_record
- Tags: 交易, correction
---


## [LRN-20260401-002] correction

**Logged**: 2026-04-01T22:20:20.184791
**Priority**: medium
**Status**: pending

### Summary
投资信息必须标注来源等级

### Details
搜索结果混入未经验证说法

### Metadata
- Source: auto_record
- Tags: 信息, correction
---


## [LRN-20260401-003] error

**Logged**: 2026-04-01T22:20:20.215972
**Priority**: medium
**Status**: pending

### Summary
cron任务超时导致连续失败

### Details
技能更新批量执行超时

### Metadata
- Source: auto_record
- Tags: cron, error
---


## [LRN-20260401-004] best_practice

**Logged**: 2026-04-01T22:20:20.248539
**Priority**: medium
**Status**: pending

### Summary
单条推送聚焦1个结论不超过10行

### Details
信息过载降低可读性

### Metadata
- Source: auto_record
- Tags: 推送, best_practice
---


## [LRN-20260401-005] correction

**Logged**: 2026-04-01T22:20:20.278795
**Priority**: medium
**Status**: pending

### Summary
复杂任务先发确认再执行

### Details
不发确认用户不知道进度

### Metadata
- Source: auto_record
- Tags: 回复, correction
---


## [LRN-20260401-006] correction

**Logged**: 2026-04-01T23:09:15.175776
**Priority**: medium
**Status**: pending

### Summary
CG日报信息过载

### Details
单条消息太长用户看不完

### Metadata
- Source: auto_record
- Tags: 推送, correction
---


## [LRN-20260401-007] error

**Logged**: 2026-04-01T23:09:15.226334
**Priority**: medium
**Status**: pending

### Summary
磁盘使用率连续3天超90%

### Details
session文件堆积导致

### Metadata
- Source: auto_record
- Tags: 磁盘, error
---


## [LRN-20260401-008] best_practice

**Logged**: 2026-04-01T23:09:15.278002
**Priority**: medium
**Status**: pending

### Summary
复杂分析用子代理避免阻塞

### Details
用户等了20秒

### Metadata
- Source: auto_record
- Tags: 速度, best_practice
---


## [LRN-20260402-009] error

**Logged**: 2026-04-02T00:04:15.318288
**Priority**: high
**Status**: pending

### Summary
发现持仓矛盾: 500, 000, 4000, 1000, 500, 250, 3000, 250, 250, 000, 500, 500, 000, 500, 000, 500, 3000, 500, 500, 500

### Details
N/A

### Metadata
- Source: auto_record
- Tags: 记忆冲突, error
---


## [LRN-20260402-010] error

**Logged**: 2026-04-02T01:04:17.822754
**Priority**: high
**Status**: pending

### Summary
发现持仓矛盾: 500, 000, 4000, 1000, 500, 250, 3000, 250, 250, 000, 500, 500, 000, 500, 000, 500, 3000, 500, 500, 500

### Details
N/A

### Metadata
- Source: auto_record
- Tags: 记忆冲突, error
---


## [LRN-20260402-011] error

**Logged**: 2026-04-02T01:25:01.265661
**Priority**: high
**Status**: pending

### Summary
发现持仓矛盾: 500, 000, 4000, 1000, 500, 250, 3000, 250, 250, 000, 500, 500, 000, 500, 000, 500, 3000, 500, 3000, 500, 500

### Details
N/A

### Metadata
- Source: auto_record
- Tags: 记忆冲突, error
---


## [LRN-20260402-012] error

**Logged**: 2026-04-02T01:25:01.267018
**Priority**: medium
**Status**: pending

### Summary
复盘低分: 动力减仓 - 32.60卖出500股

### Details
原因:套用通用减仓框架 教训:减仓前应先验证用户长期逻辑

### Metadata
- Source: auto_record
- Tags: 复盘, error
---


## [LRN-20260402-013] error

**Logged**: 2026-04-02T01:25:01.268255
**Priority**: high
**Status**: pending

### Summary
复盘低分: 泰禾买入 - 21.10买入500股

### Details
原因:阳光新能源借壳题材 教训:题材股无催化剂不应建仓

### Metadata
- Source: auto_record
- Tags: 复盘, error
---

