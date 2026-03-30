#!/bin/bash
# 自动 Git 备份 - 每天凌晨 2:00 执行
cd /root/.openclaw/workspace

# Stage all changes
git add -A

# Check if there are changes
if git diff --cached --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M') 无变更，跳过"
    exit 0
fi

# Commit with timestamp
git commit -m "自动备份 $(date '+%Y-%m-%d %H:%M')" 2>/dev/null

# Push to Gitee (全部)
git push origin master 2>/dev/null
echo "$(date '+%Y-%m-%d %H:%M') Gitee 备份完成"

# Push to GitHub (排除飞书聊天备份 - 保护隐私)
# 先暂存 feishu-chat-backup 的状态
git stash push -q -- memory/feishu-chat-backup/ 2>/dev/null
git push github master 2>/dev/null
echo "$(date '+%Y-%m-%d %H:%M') GitHub 备份完成（不含飞书聊天）"
git stash pop -q 2>/dev/null
