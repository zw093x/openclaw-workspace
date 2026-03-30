#!/usr/bin/env python3
"""
Cron 任务卡片投递包装器
功能：触发 cron 任务 → 等待完成 → 获取内容 → 以卡片形式发送

用法：
  python3 scripts/cron_card_wrapper.py <job_id> <title> <color>

示例：
  python3 scripts/cron_card_wrapper.py 17468e27 "☀️ 每日早报" blue
  python3 scripts/cron_card_wrapper.py 8ec0edd5 "🌙 晚间复盘" orange
"""
import json
import subprocess
import sys
import time
import os
from datetime import datetime

SCRIPTS_DIR = "/root/.openclaw/workspace/scripts"
CARD_SENDER = os.path.join(SCRIPTS_DIR, "feishu_card_send.py")
WEATHER_PRELOAD = os.path.join(SCRIPTS_DIR, "weather_preload.py")


def run_cmd(cmd, timeout=30):
    """执行命令"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1


def trigger_cron(job_id):
    """触发 cron 任务"""
    out, code = run_cmd(f"openclaw cron run {job_id} 2>&1")
    if code == 0 and '"ok": true' in out:
        return True
    if "already-running" in out:
        return "running"
    return False


def wait_for_completion(job_id, max_wait=120):
    """等待任务完成并获取结果"""
    start = time.time()
    while time.time() - start < max_wait:
        out, code = run_cmd(f"openclaw cron runs --id {job_id} --limit 1 2>&1")
        if code != 0:
            time.sleep(5)
            continue
        
        try:
            data = json.loads(out)
            entries = data.get("entries", [])
            if not entries:
                time.sleep(5)
                continue
            
            latest = entries[0]
            status = latest.get("status", "")
            
            if status in ("ok", "error"):
                return latest
            
            # Still running
            time.sleep(5)
        except json.JSONDecodeError:
            time.sleep(5)
    
    return None


def send_as_card(title, content, color):
    """以卡片形式发送"""
    cmd = [
        "python3", CARD_SENDER,
        "--title", title,
        "--color", color,
        "--text", content
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.returncode == 0, r.stdout.strip()


def main():
    if len(sys.argv) < 4:
        print("Usage: cron_card_wrapper.py <job_id> <title> <color>")
        print("Example: cron_card_wrapper.py 17468e27 '☀️ 每日早报' blue")
        sys.exit(1)
    
    job_id = sys.argv[1]
    title = sys.argv[2]
    color = sys.argv[3]
    
    # 如果是天气相关任务，先预加载天气
    weather_jobs = ["17468e27", "e1a5659e", "e96cd217"]
    if any(job_id.startswith(j) for j in weather_jobs):
        print("🔄 预加载天气数据...")
        run_cmd(f"python3 {WEATHER_PRELOAD}", timeout=30)
    
    # 触发 cron 任务
    print(f"🔄 触发任务: {title}")
    result = trigger_cron(job_id)
    
    if result == "running":
        print("⏳ 任务正在运行，等待完成...")
    elif not result:
        print(f"❌ 触发失败")
        sys.exit(1)
    
    # 等待完成
    print("⏳ 等待任务完成...")
    run_result = wait_for_completion(job_id)
    
    if not run_result:
        print("❌ 任务超时")
        sys.exit(1)
    
    if run_result.get("status") == "error":
        error = run_result.get("error", "unknown")
        print(f"⚠️ 任务完成但有错误: {error}")
        # 即使有错误，也尝试发送已有内容
    
    summary = run_result.get("summary", "")
    if not summary:
        print("❌ 无内容可发送")
        sys.exit(1)
    
    # 以卡片形式发送
    print(f"📤 发送卡片: {title}")
    ok, msg = send_as_card(title, summary, color)
    
    if ok:
        print(f"✅ 卡片已发送: {title}")
    else:
        print(f"❌ 发送失败: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
