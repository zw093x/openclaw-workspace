#!/usr/bin/env python3
"""
检查 openclaw 是否升级，如有升级则重启 Gateway
通过比对 /root/.local/share/pnpm/openclaw 的 mtime 实现
"""
import os
import json
import subprocess
import time
from datetime import datetime

SHIM_PATH = "/root/.local/share/pnpm/openclaw"
STATE_FILE = "/root/.openclaw/workspace/memory/openclaw-upgrade-state.json"

def get_shim_mtime():
    try:
        return os.path.getmtime(SHIM_PATH)
    except:
        return None

def main():
    current_mtime = get_shim_mtime()
    if current_mtime is None:
        print("SHIM_NOT_FOUND")
        return

    # 读取上次记录
    last_mtime = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                last_mtime = json.load(f).get("shim_mtime")
        except:
            pass

    # 比对
    if last_mtime is None:
        # 首次记录
        with open(STATE_FILE, "w") as f:
            json.dump({"shim_mtime": current_mtime, "last_check": datetime.now().isoformat()}, f)
        print("INITIALIZED")
        return

    if current_mtime != last_mtime:
        # 检测到升级，执行 restart
        print(f"UPGRADE_DETECTED old={last_mtime} new={current_mtime}, restarting gateway...")
        with open(STATE_FILE, "w") as f:
            json.dump({"shim_mtime": current_mtime, "last_check": datetime.now().isoformat(), "last_upgrade": datetime.now().isoformat()}, f)
        try:
            # 重启 gateway
            r = subprocess.run(["systemctl", "--user", "restart", "openclaw-gateway"], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                print("RESTART_OK")
            else:
                print("RESTART_FAILED:", r.stderr[:100])
        except Exception as e:
            print("RESTART_ERROR:", str(e))
    else:
        print("UNCHANGED")

if __name__ == "__main__":
    main()
