#!/usr/bin/env python3
"""
Cron 任务诊断与自动修复脚本 v2
用法: python3 scripts/cron_diagnose.py [--fix] [--report]

已知故障模式（7种）+ 自动修复方案：
1. channel_missing — 重新设置 delivery config
2. feishu_target — 检查飞书目标格式
3. message_failed — 触发重试
4. timeout — 增加 timeout
5. duplicate_delivery — 检查双触发 + 设置 --no-deliver
6. card_json_garbled — 去掉 JSON 卡片格式指令
7. agent_no_tool_call — 建议数据预注入
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
REGISTRY_FILE = WORKSPACE / "scripts" / "self_heal_registry.json"
LOG_FILE = WORKSPACE / "memory" / "cron-error-log.jsonl"
WRAPPER_SCRIPT = WORKSPACE / "scripts" / "cron_card_wrapper.py"

def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1

def get_jobs():
    out, code = run_cmd("openclaw cron list --json 2>&1")
    if code != 0:
        return []
    try:
        return json.loads(out).get("jobs", [])
    except:
        return []

def classify_error(error_msg):
    if not error_msg:
        return None
    patterns = {
        "channel_missing": "Channel is required when multiple channels are configured",
        "feishu_target": "Delivering to Feishu requires target",
        "message_failed": "Message failed",
        "timeout": "timed out",
        "sigterm": "SIGTERM",
    }
    for key, pattern in patterns.items():
        if pattern.lower() in error_msg.lower():
            return key
    return "unknown"

def fix_delivery(job_id, delivery):
    """修复投递配置"""
    channel = delivery.get("channel", "feishu")
    to = delivery.get("to", "")
    if not to:
        return False, "无目标地址"
    cmd = f'openclaw cron edit {job_id} --channel {channel} --to "{to}" --announce 2>&1'
    out, code = run_cmd(cmd)
    return code == 0, "配置已更新" if code == 0 else out[:100]

def trigger_retry(job_id):
    """触发重试"""
    out, code = run_cmd(f"openclaw cron run {job_id} 2>&1")
    return '"ok": true' in out, "已触发" if '"ok": true' in out else out[:100]

def diagnose_and_fix(jobs, do_fix=False):
    issues = []
    fixed = 0
    
    for job in jobs:
        state = job.get("state", {})
        errors = state.get("consecutiveErrors", 0)
        if errors == 0:
            continue
        
        name = job.get("name", "?")
        jid = job.get("id", "")
        last_error = state.get("lastError", "")
        error_type = classify_error(last_error)
        delivery = job.get("delivery", {})
        
        # Check for duplicate delivery
        is_card_wrapped = False
        try:
            out, _ = run_cmd("crontab -l 2>/dev/null | grep cron_card_wrapper")
            is_card_wrapped = jid[:8] in out
        except:
            pass
        
        if is_card_wrapped and delivery.get("mode") != "none":
            error_type = "duplicate_delivery"
            last_error = "任务由系统 crontab 卡片投递，但 OpenClaw 也启用了文本投递"
        
        issue = {
            "name": name,
            "id": jid,
            "errors": errors,
            "error_type": error_type,
            "last_error": last_error[:100],
            "fix": "",
            "severity": "high" if error_type in ("channel_missing", "feishu_target", "duplicate_delivery") else "medium",
        }
        
        # Auto-fix
        if do_fix:
            if error_type == "channel_missing" or error_type == "feishu_target":
                ok, msg = fix_delivery(jid, delivery)
                if ok:
                    trigger_retry(jid)
                    fixed += 1
                    issue["fix"] = "✅ 已修复"
                else:
                    issue["fix"] = f"❌ {msg}"
            elif error_type == "message_failed":
                ok, msg = trigger_retry(jid)
                if ok:
                    fixed += 1
                    issue["fix"] = "✅ 已触发重试"
                else:
                    issue["fix"] = f"❌ {msg}"
            elif error_type == "duplicate_delivery":
                out, code = run_cmd(f"openclaw cron edit {jid} --no-deliver 2>&1")
                if code == 0:
                    fixed += 1
                    issue["fix"] = "✅ 已禁用文本投递"
                else:
                    issue["fix"] = f"❌ 设置失败"
            elif error_type == "timeout":
                issue["fix"] = "⚠️ 需手动增加 timeout"
            else:
                issue["fix"] = "⚠️ 需人工排查"
        else:
            issue["fix"] = {
                "channel_missing": "openclaw cron edit <id> --channel feishu --to <target> --announce",
                "feishu_target": "检查 delivery.to 格式",
                "message_failed": "openclaw cron run <id> 触发重试",
                "timeout": "openclaw cron edit <id> --timeout-seconds 300",
                "duplicate_delivery": "openclaw cron edit <id> --no-deliver",
                "card_json_garbled": "去掉 prompt 中 JSON 卡片指令，用 cron_card_wrapper.py",
                "agent_no_tool_call": "数据预注入到 prompt 中",
            }.get(error_type, "需人工排查")
        
        issues.append(issue)
    
    return sorted(issues, key=lambda x: {"high": 0, "medium": 1}.get(x["severity"], 2)), fixed

def main():
    do_fix = "--fix" in sys.argv
    do_report = "--report" in sys.argv
    
    print("🔍 诊断 cron 任务...")
    jobs = get_jobs()
    if not jobs:
        print("❌ 无法获取任务列表")
        return
    
    issues, fixed = diagnose_and_fix(jobs, do_fix)
    
    if not issues:
        print("✅ 所有任务正常")
        return
    
    print(f"\n发现 {len(issues)} 个异常：\n")
    for i, issue in enumerate(issues, 1):
        icon = {"high": "🔴", "medium": "🟡"}.get(issue["severity"], "⚪")
        print(f"  {i}. {icon} {issue['name']}")
        print(f"     类型: {issue['error_type']} | 连续错误: {issue['errors']}")
        print(f"     修复: {issue['fix']}")
        print()
    
    if do_fix:
        print(f"✅ 已自动修复 {fixed} 个任务")
    
    # Log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "error_jobs": len(issues),
        "fixed": fixed,
        "issues": [{"name": i["name"], "type": i["error_type"]} for i in issues],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    print(f"📝 日志已记录")

if __name__ == "__main__":
    main()

# ========== 补充：鱼盆cron专项修复（network+config连锁）==========
def fix_fish_basin_network_chain():
    """
    鱼盆cron的network+config连锁根因分析：
    - 脚本本身运行正常（~2分钟完成，数据已写入文件）
    - 但 feishu_doc write 或 卡片推送 在网络抖动时失败
    - 导致 "Message failed" 但 lastDelivered=true（飞书内部重试成功）
    - self_heal 看到 error 状态 → 误判为脚本失败 → 错误修复方向
    
    修复策略：
    1. 检测 fish_basin cron 的 "Message failed" 错误
    2. 检查脚本是否实际完成（数据文件是否更新）
    3. 如果数据已更新 → 只重试飞书推送，不重跑脚本
    4. 如果数据未更新 → 增加timeout + 检查网络
    """
    import os
    from datetime import datetime
    
    FISH_DATA = "/root/.openclaw/workspace/memory/fish-basin-latest.json"
    result = {"action": "none", "reason": "", "fix": []}
    
    # 检查数据文件是否当天更新
    if os.path.exists(FISH_DATA):
        mtime = datetime.fromtimestamp(os.path.getmtime(FISH_DATA))
        now = datetime.now()
        is_today = mtime.date() == now.date()
        result["data_fresh"] = is_today
        result["data_mtime"] = mtime.isoformat()
    else:
        result["data_fresh"] = False
        result["data_mtime"] = None
    
    # 检查飞书连接
    import subprocess
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "5", "-o", "/dev/null", "-w", "%{http_code}",
             "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
             "-H", "Content-Type: application/json",
             "-d", '{"app_id":"cli_xxxx","app_secret":"xxxx"}'],
            capture_output=True, text=True, timeout=8
        )
        result["feishu_http"] = r.stdout.strip()
    except:
        result["feishu_http"] = "error"
    
    # 如果数据已更新但仍报错 → 问题在推送，不在脚本
    if result["data_fresh"]:
        result["action"] = "retry_push_only"
        result["reason"] = "数据已更新，问题在Feishu推送环节，不重跑脚本"
    else:
        result["action"] = "check_network"
        result["reason"] = "数据未更新，需检查网络+脚本问题"
    
    return result

if __name__ == "__main__":
    print("=== 鱼盆cron网络+配置连锁分析 ===")
    result = fix_fish_basin_network_chain()
    print(json.dumps(result, indent=2, ensure_ascii=False))
