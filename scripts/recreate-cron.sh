#!/bin/bash
cd /root/.openclaw/workspace

# Deep Learning cron task
timeout 10 openclaw cron create \
  --name "深度学习时段" \
  --schedule "0 1,2,3,4,5 * * *" \
  --timezone "Asia/Shanghai" \
  --session-target isolated \
  --wake-mode now \
  --delivery announce \
  --message "你是用户的专业股票学习系统。每晚01:30-05:30进行4小时深度学习。学习内容追加到memory/stock-knowledge.md，不推送飞书，只在summary输出复盘。分析标的：中国船舶(600150)、中国动力(600482)、泰禾智能(603656)。" \
  2>&1

echo "EXIT: $?"
