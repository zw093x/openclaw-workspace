---
name: session-logger
description: "记录所有会话事件到日志文件，便于审计和回溯"
metadata:
  openclaw:
    emoji: "📋"
    events: ["command:new", "command:reset", "command:stop", "agent:start", "agent:end"]
    requires:
      bins: ["node"]
---

# Session Logger Hook

记录所有会话事件到 `~/.openclaw/workspace/logs/session-events.log`。

## 功能

- 记录 `/new`、`/reset`、`/stop` 命令
- 记录 agent 启动和结束事件
- 包含时间戳、事件类型、会话 ID

## 日志格式

```
[2026-03-28 20:15:00] command:new | session:main | agent:main
[2026-03-28 20:20:00] agent:end | session:subagent:xxx | duration:25s
```
