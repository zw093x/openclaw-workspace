#!/bin/bash
cd /root/.openclaw/workspace

echo "=== 1. 全量同步 ==="
python3 scripts/intel_hub.py --sync 2>&1
echo "EXIT: $?"

echo "=== 2. 统一自愈系统 ==="
python3 scripts/unified_heal.py --fix --report --evolve 2>&1
echo "EXIT: $?"

echo "=== 3. 自学习进化 ==="
python3 scripts/learn_evolve.py --evolve 2>&1
echo "EXIT: $?"

echo "=== 4. 错误进化 ==="
python3 scripts/error_evolution.py --evolve 2>&1
echo "EXIT: $?"
