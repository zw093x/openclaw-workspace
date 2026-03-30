#!/bin/bash
# 自动备份 cron 任务 + 系统 crontab
BACKUP_DIR="/root/.openclaw/workspace/config"

# 导出 OpenClaw cron 任务
openclaw cron list --json > "$BACKUP_DIR/cron-jobs-export.json" 2>/dev/null

# 导出系统 crontab
crontab -l > "$BACKUP_DIR/system-crontab-backup.txt" 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M') 配置备份完成: cron=$(cat "$BACKUP_DIR/cron-jobs-export.json" | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("jobs",[])))')个任务"
