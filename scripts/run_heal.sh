#!/bin/bash
set -e
cd /root/.openclaw/workspace

echo "=== [1/4] intel_hub --sync ==="
python3 scripts/intel_hub.py --sync 2>&1 | tail -20

echo "=== [2/4] unified_heal --fix --report --evolve ==="
python3 scripts/unified_heal.py --fix --report --evolve 2>&1 | tail -40

echo "=== [3/4] learn_evolve --evolve ==="
python3 scripts/learn_evolve.py --evolve 2>&1 | tail -20

echo "=== [4/4] error_evolution --evolve ==="
python3 scripts/error_evolution.py --evolve 2>&1 | tail -20

echo "=== DONE ==="
