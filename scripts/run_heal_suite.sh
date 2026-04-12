#!/bin/bash
cd /root/.openclaw/workspace

echo "=== STEP 1: intel_hub --sync ==="
python3 scripts/intel_hub.py --sync 2>&1
echo "EXIT: $?"

echo ""
echo "=== STEP 2: unified_heal --fix --report --evolve ==="
python3 scripts/unified_heal.py --fix --report --evolve 2>&1
echo "EXIT: $?"

echo ""
echo "=== STEP 3: learn_evolve --evolve ==="
python3 scripts/learn_evolve.py --evolve 2>&1
echo "EXIT: $?"

echo ""
echo "=== STEP 4: error_evolution --evolve ==="
python3 scripts/error_evolution.py --evolve 2>&1
echo "EXIT: $?"
