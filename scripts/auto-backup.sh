#!/bin/bash
# 每日自动备份 - 凌晨2:00运行
cd /root/.openclaw/workspace

# 导出最新的Cron任务备份
openclaw cron list --json 2>/dev/null > memory/cron-backup.json 2>/dev/null

# Git提交
git add -A 2>/dev/null
git commit -m "auto-backup: $(date +%Y-%m-%d)" 2>/dev/null

# 如果有远程仓库，推送
git push 2>/dev/null

echo "$(date): backup completed" >> memory/backup-log.txt
