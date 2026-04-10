#!/bin/bash
cd /root/.openclaw/workspace
python3 ./scripts/intel_hub.py --sync
echo "---INTEL_DONE---"
python3 ./scripts/unified_heal.py --fix --report --evolve
echo "---HEAL_DONE---"
python3 ./scripts/learn_evolve.py --evolve
echo "---LEARN_DONE---"
python3 ./scripts/error_evolution.py --evolve
echo "---ERROR_DONE---"
