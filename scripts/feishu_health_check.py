#!/usr/bin/env python3
"""
飞书通道健康检测 + 自动重连
检测飞书WebSocket是否正常，异常时自动重启Gateway
"""
import subprocess
import json
import sys
from datetime import datetime

GATEWAY_PID_CMD = "ps aux | grep 'openclaw-gateway' | grep -v grep | awk '{print $2}'"
LOG_FILE = "/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
STATE_FILE = "/root/.openclaw/workspace/memory/feishu-health-state.json"

def get_gateway_pid():
    try:
        r = subprocess.run("ps aux | grep 'openclaw-gateway' | grep -v grep | awk '{print \$2}'",
                          shell=True, capture_output=True, text=True, timeout=5)
        pids = r.stdout.strip().split()
        return pids[0] if pids else None
    except:
        return None

def get_feishu_log_recent():
    """检查最近5分钟内飞书是否有收到消息的日志"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log = f"/tmp/openclaw/openclaw-{today}.log"
        r = subprocess.run(
            f"grep 'feishu.*DM from' {log} 2>/dev/null | tail -1",
            shell=True, capture_output=True, text=True, timeout=5
        )
        line = r.stdout.strip()
        if line:
            # 提取时间戳
            import re
            m = re.search(r'"time":"([^"]+)"', line)
            if m:
                t = datetime.fromisoformat(m.group(1).replace("+08:00", "+0800"))
                age = (datetime.now() - t.replace(tzinfo=None)).total_seconds()
                return age  # 秒数
        return None
    except:
        return None

def feishu_token_test():
    """测试飞书API token是否可用"""
    try:
        r = subprocess.run([
            "curl", "-s", "--max-time", "5",
            "-X", "POST",
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            "-H", "Content-Type: application/json",
            "-d", '{"app_id":"cli_a9489e1f4c78dbb6","app_secret":"mKeApaf2UE3CDN8wlh1IJcDSxcJlYlhD"}'
        ], capture_output=True, text=True, timeout=8)
        data = json.loads(r.stdout)
        return data.get("code") == 0
    except:
        return False

def restart_gateway():
    """重启Gateway"""
    try:
        # 停止当前Gateway
        pid = get_gateway_pid()
        if pid:
            subprocess.run(["kill", pid], timeout=5)
            import time; time.sleep(3)
        # 通过systemd重启
        subprocess.run(["systemctl", "--user", "restart", "openclaw-gateway"], timeout=15)
        return True
    except Exception as e:
        return False

def main():
    import os
    # 读取上次状态
    last_restart = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                last_restart = json.load(f).get("last_restart")
        except:
            pass

    # 1. Gateway进程是否存活
    pid = get_gateway_pid()
    if not pid:
        print("Gateway not running, restarting...")
        restart_gateway()
        with open(STATE_FILE, "w") as f:
            json.dump({"last_restart": datetime.now().isoformat(), "reason": "no_pid"}, f)
        print("Gateway restarted")
        sys.exit(0)

    # 2. 飞书token是否正常
    token_ok = feishu_token_test()
    if not token_ok:
        print("Feishu token invalid")
        # token无效不代表连接断，继续观察
        print("TOKEN_ERROR")

    # 3. 检查飞书最近是否收到消息
    last_msg_age = get_feishu_log_recent()
    
    # 如果最近5分钟没有收到飞书消息，可能是连接断了
    if last_msg_age is not None and last_msg_age > 300:
        # 检查距离上次重启是否已过30分钟（避免频繁重启）
        can_restart = True
        if last_restart:
            try:
                lr = datetime.fromisoformat(last_restart)
                if (datetime.now() - lr).total_seconds() < 1800:
                    can_restart = False
                    print(f"Last restart {last_restart}, too soon to restart again")
            except:
                pass
        
        if can_restart:
            print(f"No Feishu message for {int(last_msg_age)}s, restarting gateway...")
            restart_gateway()
            with open(STATE_FILE, "w") as f:
                json.dump({"last_restart": datetime.now().isoformat(), "reason": "feishu_silent"}, f)
            print("Gateway restarted due to Feishu silence")
        else:
            print(f"Feishu silent for {int(last_msg_age)}s, but restart throttled")
    else:
        print("Feishu channel healthy")
        print("HEALTHY")

if __name__ == "__main__":
    main()
