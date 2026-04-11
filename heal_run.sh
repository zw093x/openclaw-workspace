#!/bin/bash
cd /root/.openclaw/workspace
python3 scripts/intel_hub.py --sync
echo "===STEP1_DONE==="
python3 scripts/unified_heal.py --fix --report --evolve
echo "===STEP2_DONE==="
python3 scripts/learn_evolve.py --evolve
echo "===STEP3_DONE==="
python3 scripts/error_evolution.py --evolve
echo "===STEP4_DONE==="
