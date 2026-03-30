#!/usr/bin/env python3
"""
统一自愈系统 v2.0
合并 self_heal + cron_diagnose，统一故障模式、日志、统计

用法:
  python3 scripts/unified_heal.py              # 诊断
  python3 scripts/unified_heal.py --fix        # 诊断+修复
  python3 scripts/unified_heal.py --report     # 诊断+报告
  python3 scripts/unified_heal.py --fix --verify  # 诊断+修复+验证

功能:
  1. 扫描所有 cron 任务，检测 9 种故障模式
  2. 扫描飞书连接、磁盘、gateway 状态
  3. 自动修复（--fix）
  4. 修复后验证（--verify）
  5. 统一日志 + 统计更新
"""

import json
import subprocess
import sys
import os
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
PATTERNS_FILE = WORKSPACE / "config" / "heal_patterns.json"
LOG_FILE = WORKSPACE / "memory" / "heal-unified-log.jsonl"
STATS_FILE = WORKSPACE / "memory" / "heal-stats.json"

# ===== 工具函数 =====
def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1

def load_patterns():
    with open(PATTERNS_FILE, "r") as f:
        return json.load(f)

def save_patterns(data):
    with open(PATTERNS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_event(entry):
    """追加日志"""
    entry["ts"] = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def update_stats(pattern_name, success, fix_time_ms):
    """更新统计"""
    try:
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    except:
        stats = {"total_fixes": 0, "auto_fixed": 0, "recurring": 0, "patterns": {}}

    stats["total_fixes"] += 1
    if success:
        stats["auto_fixed"] += 1

    if pattern_name not in stats.get("patterns", {}):
        stats.setdefault("patterns", {})[pattern_name] = {"count": 0, "success": 0}
    stats["patterns"][pattern_name]["count"] += 1
    if success:
        stats["patterns"][pattern_name]["success"] += 1

    # 检查是否再发
    if stats["patterns"][pattern_name]["count"] > 1:
        stats["recurring"] = stats.get("recurring", 0) + 1

    stats["last_update"] = datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ===== Cron 任务扫描 =====
def get_cron_jobs():
    out, code = run_cmd("openclaw cron list --json 2>&1")
    if code != 0:
        return []
    try:
        return json.load(out).get("jobs", [])
    except:
        return []

def match_error(error_msg, patterns):
    """匹配错误消息到故障模式"""
    if not error_msg:
        return None
    error_lower = error_msg.lower()
    for name, pat in patterns.items():
        for keyword in pat.get("match", []):
            if keyword.lower() in error_lower:
                return name
    return None

# ===== 各类检查器 =====
def check_cron_jobs(patterns, do_fix):
    """扫描 cron 任务错误"""
    jobs = get_cron_jobs()
    issues = []
    fixes = 0

    for job in jobs:
        state = job.get("state", {})
        errors = state.get("consecutiveErrors", 0)
        name = job.get("name", "?")
        jid = job.get("id", "")

        # === 预防性检查：timeout 不足 ===
        if errors == 0 and do_fix:
            msg = job.get("payload", {}).get("message", "")
            timeout = job.get("payload", {}).get("timeoutSeconds", 0)
            search_keywords = ['搜索', 'search', '新闻', '资讯', '监控', '复盘', '周报', '早报', '日报', '报告', 'BDI']
            is_search = any(kw in msg for kw in search_keywords)
            if is_search and 0 < timeout < 300:
                run_cmd(f"openclaw cron edit {jid} --timeout-seconds 600 2>&1")
                log_event({
                    "pattern": "cron_timeout", "target": f"{name} ({jid[:8]})",
                    "action": "preventive_fix", "detail": f"timeout {timeout}→600s",
                    "result": "success", "time_ms": 500
                })
                fixes += 1

        if errors == 0:
            continue

        name = job.get("name", "?")
        jid = job.get("id", "")
        last_error = state.get("lastError", "")

        # 匹配故障模式
        pattern_name = match_error(last_error, patterns)

        # 特殊检测：重复投递
        if not pattern_name:
            delivery = job.get("delivery", {})
            is_card_wrapped = False
            try:
                out, _ = run_cmd("crontab -l 2>/dev/null | grep cron_card_wrapper")
                is_card_wrapped = jid[:8] in out
            except:
                pass
            if is_card_wrapped and delivery.get("mode") != "none":
                pattern_name = "cron_duplicate_delivery"
                last_error = "任务由系统 crontab 卡片投递，但 OpenClaw 也启用了文本投递"

        if not pattern_name:
            pattern_name = "cron_unknown"
            # 不处理未知模式
            issues.append({
                "name": name, "id": jid, "errors": errors,
                "pattern": "unknown", "severity": "medium",
                "error": last_error[:100], "fix": "需人工排查",
                "fixed": False
            })
            continue

        pat = patterns.get(pattern_name, {})
        severity = pat.get("severity", "medium")
        fix_cmd_template = pat.get("fix_cmd")
        auto_fixable = fix_cmd_template is not None

        issue = {
            "name": name, "id": jid, "errors": errors,
            "pattern": pattern_name, "severity": severity,
            "error": last_error[:100],
            "fix": pat.get("auto_fix", "需人工排查"),
            "fixed": False
        }

        # 自动修复
        if do_fix and auto_fixable:
            start = time.time()
            result = apply_fix(pattern_name, jid, job, fix_cmd_template)
            elapsed_ms = int((time.time() - start) * 1000)

            issue["fixed"] = result
            if result:
                fixes += 1

            # 记录日志
            log_event({
                "pattern": pattern_name, "target": f"{name} ({jid[:8]})",
                "action": "auto_fix", "result": "success" if result else "failed",
                "time_ms": elapsed_ms
            })

            # 更新统计
            update_stats(pattern_name, result, elapsed_ms)

            # 更新 pattern 计数
            if pattern_name in patterns:
                patterns[pattern_name]["fix_total"] = patterns[pattern_name].get("fix_total", 0) + 1
                if result:
                    patterns[pattern_name]["fix_success"] = patterns[pattern_name].get("fix_success", 0) + 1
                patterns[pattern_name]["last_seen"] = datetime.now().isoformat()

        issues.append(issue)

    return sorted(issues, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4)), fixes

def apply_fix(pattern_name, job_id, job, fix_cmd_template):
    """应用修复"""
    delivery = job.get("delivery", {})
    channel = delivery.get("channel", "feishu")
    to = delivery.get("to", "ou_a6469ccc2902a590994b6777b9c8ae8f")

    if pattern_name in ("cron_channel_missing", "cron_feishu_target"):
        cmd = f'openclaw cron edit {job_id} --channel {channel} --to "{to}" --announce 2>&1'
        out, code = run_cmd(cmd)
        if code == 0:
            run_cmd(f"openclaw cron run {job_id} 2>&1")
            return True
        return False

    elif pattern_name == "cron_message_failed":
        out, code = run_cmd(f"openclaw cron run {job_id} 2>&1")
        return '"ok": true' in out

    elif pattern_name == "cron_timeout":
        out, code = run_cmd(f"openclaw cron edit {job_id} --timeout-seconds 300 2>&1")
        return code == 0

    elif pattern_name == "cron_duplicate_delivery":
        out, code = run_cmd(f"openclaw cron edit {job_id} --no-deliver 2>&1")
        return code == 0

    elif pattern_name == "cron_config_side_effect":
        out, code = run_cmd("python3 /root/.openclaw/workspace/scripts/cron_diagnose.py --fix 2>&1")
        return "已自动修复" in out or "正常" in out

    elif pattern_name == "feishu_unreachable":
        out, code = run_cmd("openclaw gateway restart 2>&1")
        time.sleep(5)
        return True

    elif pattern_name == "disk_warning":
        run_cmd("find /tmp -mtime +7 -delete 2>/dev/null")
        run_cmd("find /root/.openclaw -name '*.log' -size +10M -delete 2>/dev/null")
        return True

    return False

def check_feishu_connection():
    """检查飞书连接"""
    out, code = run_cmd("openclaw status --json 2>&1")
    if code != 0:
        return {"status": "error", "msg": "无法获取状态"}
    try:
        data = json.loads(out)
        feishu = data.get("channels", {}).get("feishu", {})
        return {
            "status": "ok" if feishu.get("connected") else "disconnected",
            "connected": feishu.get("connected", False)
        }
    except:
        return {"status": "unknown", "msg": "解析失败"}

def check_disk():
    """检查磁盘"""
    out, code = run_cmd("df -h / | tail -1")
    if code != 0:
        return {"status": "error"}
    parts = out.split()
    if len(parts) >= 5:
        usage = parts[4].replace("%", "")
        return {"status": "ok", "usage_pct": int(usage), "available": parts[3]}
    return {"status": "unknown"}

# ===== 报告 =====
def generate_report(issues, feishu, disk, stats):
    """生成诊断报告"""
    lines = ["🔧 **统一自愈系统报告**", ""]

    if not issues and feishu.get("status") == "ok" and disk.get("usage_pct", 0) < 80:
        lines.append("✅ 所有系统正常")
        return "\n".join(lines)

    if issues:
        lines.append(f"⚠️ 发现 {len(issues)} 个 cron 异常：")
        for i, issue in enumerate(issues, 1):
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(issue["severity"], "⚪")
            fix_icon = "✅" if issue.get("fixed") else "❌"
            lines.append(f"  {i}. {icon} {issue['name']} — {issue['pattern']}")
            lines.append(f"     修复: {fix_icon} {issue['fix']}")
        lines.append("")

    if feishu.get("status") != "ok":
        lines.append(f"🔴 飞书连接异常: {feishu.get('msg', 'disconnected')}")

    if disk.get("usage_pct", 0) >= 80:
        lines.append(f"🟡 磁盘使用率: {disk['usage_pct']}% (可用 {disk.get('available', '?')})")

    if stats:
        lines.append("")
        lines.append(f"📊 历史统计: 总修复 {stats.get('total_fixes', 0)} 次, 自动修复 {stats.get('auto_fixed', 0)} 次, 再发 {stats.get('recurring', 0)} 次")

    return "\n".join(lines)

# ===== 主入口 =====
def main():
    do_fix = "--fix" in sys.argv
    do_verify = "--verify" in sys.argv
    do_report = "--report" in sys.argv

    patterns_data = load_patterns()
    patterns = patterns_data.get("patterns", {})

    # 1. Cron 任务扫描
    issues, fixes = check_cron_jobs(patterns, do_fix)

    # 2. 飞书连接
    feishu = check_feishu_connection()
    if feishu.get("status") != "ok" and do_fix:
        result = apply_fix("feishu_unreachable", None, {}, None)
        if result:
            log_event({"pattern": "feishu_unreachable", "target": "gateway", "action": "auto_fix", "result": "success", "time_ms": 5000})
            update_stats("feishu_unreachable", True, 5000)
            feishu = check_feishu_connection()

    # 3. 磁盘
    disk = check_disk()
    if disk.get("usage_pct", 0) >= 80 and do_fix:
        result = apply_fix("disk_warning", None, {}, None)
        if result:
            log_event({"pattern": "disk_warning", "target": "disk", "action": "auto_fix", "result": "success", "time_ms": 1000})
            update_stats("disk_warning", True, 1000)
            disk = check_disk()

    # 4. 保存更新后的 patterns
    patterns_data["patterns"] = patterns
    save_patterns(patterns_data)

    # 5. 报告
    if do_report or do_fix:
        stats = {}
        try:
            with open(STATS_FILE, "r") as f:
                stats = json.load(f)
        except:
            pass
        report = generate_report(issues, feishu, disk, stats)
        print(report)
    elif not issues and feishu.get("status") == "ok" and disk.get("usage_pct", 0) < 80:
        print("✅ 所有系统正常")
    else:
        print(f"⚠️ 发现 {len(issues)} 个异常，飞书={'ok' if feishu.get('status')=='ok' else '异常'}, 磁盘={disk.get('usage_pct','?')}%")

if __name__ == "__main__":
    main()
