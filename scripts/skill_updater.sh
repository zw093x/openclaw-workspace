#!/bin/bash
# 技能轮询更新脚本 v3
# 每次只检查一批技能（默认5个），循环覆盖全部
# 避免限速，降低负载

SKILLS_DIR="/root/.openclaw/workspace/skills"
LOG_FILE="/tmp/skill_out.txt"
STATE_FILE="/root/.openclaw/workspace/memory/skill-update-state.json"
BATCH_SIZE=5

# 确保状态文件存在
if [ ! -f "$STATE_FILE" ]; then
    echo '{"last_index": 0, "total_skills": 0, "last_run": ""}' > "$STATE_FILE"
fi

# 获取所有技能列表
SKILLS=()
for dir in "$SKILLS_DIR"/*/; do
    if [ -f "$dir/SKILL.md" ]; then
        SKILLS+=("$(basename "$dir")")
    fi
done
TOTAL=${#SKILLS[@]}

# 读取上次位置
LAST_INDEX=$(python3 -c "
import json
try:
    with open('$STATE_FILE') as f:
        d = json.load(f)
    print(d.get('last_index', 0))
except:
    print(0)
")

# 计算本轮要检查的技能
START=$LAST_INDEX
END=$((START + BATCH_SIZE))
if [ $END -ge $TOTAL ]; then
    END=$TOTAL
fi

echo "=== 技能轮询更新 $(date '+%Y-%m-%d %H:%M:%S') ===" > "$LOG_FILE"
echo "总技能: $TOTAL | 本轮检查: $START-$END (共$((END-START))个)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 逐个更新本轮技能
UPDATED=0
UP_TO_DATE=0
FAILED=0

for i in $(seq $START $((END-1))); do
    if [ $i -ge $TOTAL ]; then
        break
    fi
    skill="${SKILLS[$i]}"
    echo -n "[$((i+1))/$TOTAL] $skill: " >> "$LOG_FILE"
    
    result=$(npx clawhub update "$skill" --no-input --force 2>&1)
    
    if echo "$result" | grep -q "updated ->"; then
        echo "✅ 更新" >> "$LOG_FILE"
        UPDATED=$((UPDATED+1))
    elif echo "$result" | grep -q "already latest\|no changes\|up to date"; then
        echo "⏭ 已最新" >> "$LOG_FILE"
        UP_TO_DATE=$((UP_TO_DATE+1))
    elif echo "$result" | grep -q "Skill not found"; then
        echo "⏭ 本地技能(跳过)" >> "$LOG_FILE"
    elif echo "$result" | grep -q "Rate limit"; then
        echo "⚠️ 限速，暂停" >> "$LOG_FILE"
        sleep 5
    else
        echo "❌ 失败" >> "$LOG_FILE"
        FAILED=$((FAILED+1))
    fi
    
    # 间隔2秒避免限速
    sleep 2
done

# 更新位置（循环）
NEXT_INDEX=$((END))
if [ $NEXT_INDEX -ge $TOTAL ]; then
    NEXT_INDEX=0  # 回到开头，完成一轮
    echo "" >> "$LOG_FILE"
    echo "🔄 完成一轮全覆盖，下次从头开始" >> "$LOG_FILE"
fi

# 保存状态
python3 -c "
import json
state = {
    'last_index': $NEXT_INDEX,
    'total_skills': $TOTAL,
    'last_run': '$(date -Iseconds)',
    'last_batch': '$START-$END',
    'stats': {
        'updated': $UPDATED,
        'up_to_date': $UP_TO_DATE,
        'failed': $FAILED
    }
}
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
"

# 输出汇总
echo "" >> "$LOG_FILE"
echo "=== 汇总 ===" >> "$LOG_FILE"
echo "已更新: $UPDATED" >> "$LOG_FILE"
echo "已最新: $UP_TO_DATE" >> "$LOG_FILE"
echo "失败: $FAILED" >> "$LOG_FILE"
echo "下次位置: $NEXT_INDEX/$TOTAL" >> "$LOG_FILE"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

cat "$LOG_FILE"
