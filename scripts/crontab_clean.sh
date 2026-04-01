#!/bin/bash
# 统一 crontab 配置（精简版）
# 仅保留系统基础任务 + 天气预加载
# 卡片投递由 OpenClaw cron 原生处理，不再通过 crontab 触发

# === 系统基础任务 ===
*/5 * * * * flock -xn /tmp/stargate.lock -c '/usr/local/qcloud/stargate/admin/start.sh > /dev/null 2>&1 &'
55 1 * * * /bin/bash /root/.openclaw/workspace/scripts/auto-config-backup.sh >> /tmp/config-backup.log 2>&1
0 2 * * * /bin/bash /root/.openclaw/workspace/scripts/auto-git-backup.sh >> /tmp/git-backup.log 2>&1

# === 天气预加载（仅07:25一次，注入早报prompt供agent直接引用） ===
25 7 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/weather_preload.py >> /root/.openclaw/workspace/memory/weather-preload.log 2>&1

# === 技术指标自动计算（每日收盘后） ===
20 15 * * 1-5 /usr/bin/python3 /root/.openclaw/workspace/scripts/calc_tech_levels.py >> /root/.openclaw/workspace/memory/tech-levels.log 2>&1
30 9 * * 1-5 /usr/bin/python3 /root/.openclaw/workspace/scripts/calc_tech_levels.py >> /root/.openclaw/workspace/memory/tech-levels.log 2>&1

# === 飞书对话备份（每天23:50） ===
50 23 * * * /bin/bash /root/.openclaw/workspace/scripts/backup_feishu_chat.sh >> /tmp/feishu-backup.log 2>&1

# === OpenClaw Session 备份（每天23:55） ===
55 23 * * * python3 /root/.openclaw/workspace/scripts/backup_sessions.py >> /tmp/session-backup.log 2>&1

# === 每周日凌晨3:00清理旧 session 文件 ===
0 3 * * 0 /usr/bin/find /root/.openclaw/agents/main/sessions/ -name "*.deleted.*" -type f -mtime +3 -delete && /usr/bin/find /root/.openclaw/agents/main/sessions/ -name "*.reset.*" -type f -mtime +14 -delete >> /tmp/session-cleanup.log 2>&1
