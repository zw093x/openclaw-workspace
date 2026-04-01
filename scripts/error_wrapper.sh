#!/bin/bash
# 通用错误捕获包装器
# 任何命令都可以通过此脚本执行，错误自动报告给进化引擎
#
# 用法: bash scripts/error_wrapper.sh <source_name> <command...>
# 示例: bash scripts/error_wrapper.sh finance_updater python3 scripts/finance_updater.py

SOURCE="${1:-unknown}"
shift
CMD="$*"

# 执行命令并捕获输出
OUTPUT=$(eval "$CMD" 2>&1)
EXIT_CODE=$?

# 如果有错误，报告给进化引擎
if [ $EXIT_CODE -ne 0 ]; then
    ERROR_MSG=$(echo "$OUTPUT" | tail -5 | tr '\n' ' ' | head -c 500)
    python3 /root/.openclaw/workspace/scripts/error_evolution.py --report \
        --source "$SOURCE" \
        --type "execution_error" \
        --msg "$ERROR_MSG" 2>/dev/null
    
    # 同时写入统一日志
    echo "{\"ts\":\"$(date -Iseconds)\",\"source\":\"$SOURCE\",\"cmd\":\"${CMD:0:100}\",\"exit_code\":$EXIT_CODE,\"error\":\"${ERROR_MSG:0:200}\"}" \
        >> /root/.openclaw/workspace/memory/error-wrapper-log.jsonl
fi

# 输出原始结果
echo "$OUTPUT"
exit $EXIT_CODE
