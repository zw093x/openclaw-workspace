#!/bin/bash
# 飞书对话备份脚本
# 方案：将 memory/ 日记文件 + MEMORY.md 备份到独立目录
# 这些文件已经记录了所有重要对话内容，比原始聊天记录更有价值

BACKUP_DIR="/root/.openclaw/workspace/memory/feishu-chat-backup"
mkdir -p "$BACKUP_DIR/$(date +%Y-%m)"

TODAY=$(date +%Y-%m-%d)
MONTH_DIR="$BACKUP_DIR/$(date +%Y-%m)"

# 备份今天的日记（含对话精华）
if [ -f "/root/.openclaw/workspace/memory/$TODAY.md" ]; then
    cp "/root/.openclaw/workspace/memory/$TODAY.md" "$MONTH_DIR/memory-$TODAY.md"
fi

# 备份长期记忆
cp "/root/.openclaw/workspace/MEMORY.md" "$MONTH_DIR/MEMORY-$TODAY.md" 2>/dev/null

# 备份关键配置
cp "/root/.openclaw/workspace/USER.md" "$MONTH_DIR/USER-$TODAY.md" 2>/dev/null
cp "/root/.openclaw/workspace/SOUL.md" "$MONTH_DIR/SOUL-$TODAY.md" 2>/dev/null

# 备份持仓配置
cp "/root/.openclaw/workspace/config/holdings.json" "$MONTH_DIR/holdings-$TODAY.json" 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M') 对话备份完成 → $MONTH_DIR"

# 仅推送到 Gitee（不推送到 GitHub）
cd /root/.openclaw/workspace
git add memory/feishu-chat-backup/ 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "飞书对话备份 $TODAY" 2>/dev/null
    git push origin master 2>/dev/null  # 只推 Gitee
    echo "✅ Gitee 推送完成"
else
    echo "ℹ️ 无变更"
fi
