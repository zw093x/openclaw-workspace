#!/bin/bash
cd /root/.openclaw/workspace
echo "=== 1. intel_hub sync ==="
python3 scripts/intel_hub.py --sync
echo ""
echo "=== 2. unified_heal ==="
python3 scripts/unified_heal.py --fix --report --evolve
echo ""
echo "=== 3. learn_evolve ==="
python3 scripts/learn_evolve.py --evolve
echo ""
echo "=== 4. error_evolution ==="
python3 scripts/error_evolution.py --evolve
