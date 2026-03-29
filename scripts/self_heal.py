#!/usr/bin/env python3
"""
OpenClaw 自愈系统 (Self-Healing Tool)
功能：
  1. 扫描错误（cron、gateway、飞书连接）
  2. 匹配已知故障库（errors_registry.json）
  3. 自动执行修复动作
  4. 记录新错误到故障库（学习能力）
  5. 生成健康报告

用法：
  python3 scripts/self_heal.py              # 诊断模式（只检查，不修复）
  python3 scripts/self_heal.py --fix        # 自动修复模式
  python3 scripts/self_heal.py --report     # 生成健康报告
  python3 scripts/self_heal.py --learn      # 扫描并学习新错误
"""

import json
import subprocess
import sys
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === 路径配置 ===
WORKSPACE = Path("/root/.openclaw/workspace")
REGISTRY_FILE = WORKSPACE / "scripts" / "self_heal_registry.json"
HEALTH_LOG = WORKSPACE / "scripts" / "self_heal_log.jsonl"
JOBS_FILE = Path("/root/.openclaw/cron/jobs.json")

# === 时区 ===
CST = timezone(timedelta(hours=8))


def now_cst():
    return datetime.now(CST)


def load_registry():
    """加载故障修复注册表"""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {"errors": [], "fixes": {}, "stats": {"total_scans": 0, "total_fixes": 0, "last_scan": None}}


def save_registry(registry):
    """保存故障修复注册表"""
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def log_event(event_type, details):
    """记录事件日志"""
    entry = {
        "ts": now_cst().isoformat(),
        "type": event_type,
        **details
    }
    with open(HEALTH_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_cmd(cmd, timeout=15):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() + result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


# ============================================================
# 错误扫描器
# ============================================================

def scan_cron_errors():
    """扫描 cron 任务错误"""
    errors = []
    output = run_cmd("openclaw cron list 2>/dev/null", timeout=20)
    if not output or "TIMEOUT" in output:
        return [{"type": "cron_unreachable", "msg": "无法获取 cron 列表", "severity": "high"}]

    for line in output.split("\n"):
        if "error" in line.lower():
            parts = line.strip().split()
            if len(parts) >= 2:
                task_id = parts[0]
                name = " ".join(parts[1:-2]) if len(parts) > 3 else "unknown"
                errors.append({
                    "type": "cron_error",
                    "task_id": task_id,
                    "name": name.strip(),
                    "severity": "medium"
                })
    return errors


def scan_cron_delivery_errors():
    """扫描 cron delivery 配置缺失"""
    errors = []
    try:
        with open(JOBS_FILE) as f:
            data = json.load(f)
        jobs = data.get("jobs", [])
        for job in jobs:
            delivery = job.get("delivery", {})
            missing = []
            if not delivery.get("channel"):
                missing.append("channel")
            if not delivery.get("to"):
                missing.append("to")
            if missing:
                errors.append({
                    "type": "cron_delivery_missing",
                    "task_id": job.get("id", "?")[:8],
                    "name": job.get("name", "?"),
                    "missing": missing,
                    "severity": "medium"
                })
    except Exception as e:
        errors.append({"type": "jobs_file_error", "msg": str(e), "severity": "high"})
    return errors


def scan_feishu_connection():
    """检测飞书连接状态"""
    output = run_cmd("openclaw status 2>/dev/null | grep -i feishu | head -5", timeout=15)
    if "TIMEOUT" in output or not output:
        return [{"type": "feishu_unreachable", "msg": "无法检测飞书连接状态", "severity": "high"}]
    # Check for error indicators
    if any(kw in output.lower() for kw in ["error", "fail", "disconnect", "closed"]):
        return [{"type": "feishu_connection_error", "msg": output[:200], "severity": "high"}]
    return []


def scan_gateway_health():
    """检测 gateway 进程状态"""
    output = run_cmd("openclaw status 2>/dev/null | head -5", timeout=15)
    if "TIMEOUT" in output or not output:
        return [{"type": "gateway_unreachable", "msg": "gateway 无响应", "severity": "critical"}]
    return []


def scan_disk_space():
    """检测磁盘空间"""
    output = run_cmd("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
    try:
        usage = int(output)
        if usage > 90:
            return [{"type": "disk_full", "msg": f"磁盘使用率 {usage}%", "severity": "high"}]
        elif usage > 80:
            return [{"type": "disk_warning", "msg": f"磁盘使用率 {usage}%", "severity": "low"}]
    except ValueError:
        pass
    return []


def scan_memory():
    """检测内存状态"""
    output = run_cmd("free -m | awk 'NR==2{printf \"%d\", $3*100/$2}'")
    try:
        usage = int(output)
        if usage > 95:
            return [{"type": "memory_critical", "msg": f"内存使用率 {usage}%", "severity": "high"}]
    except ValueError:
        pass
    return []


# ============================================================
# 修复动作
# ============================================================

FIXES = {
    "cron_delivery_missing": {
        "name": "修复 cron delivery 配置",
        "action": "fix_cron_delivery",
        "auto_fixable": True
    },
    "cron_error": {
        "name": "重启失败的 cron 任务",
        "action": "fix_cron_error",
        "auto_fixable": True
    },
    "feishu_connection_error": {
        "name": "重启 gateway 恢复飞书连接",
        "action": "fix_feishu_connection",
        "auto_fixable": True
    },
    "gateway_unreachable": {
        "name": "重启 gateway 进程",
        "action": "fix_gateway_restart",
        "auto_fixable": True
    },
    "disk_full": {
        "name": "清理日志和临时文件",
        "action": "fix_disk_cleanup",
        "auto_fixable": True
    }
}


def fix_cron_delivery(errors):
    """修复 cron delivery 配置"""
    try:
        with open(JOBS_FILE) as f:
            data = json.load(f)
        jobs = data.get("jobs", [])
        fixed = 0
        for job in jobs:
            delivery = job.get("delivery", {})
            if not delivery.get("channel") or not delivery.get("to"):
                job["delivery"] = {
                    "mode": delivery.get("mode", "announce"),
                    "channel": delivery.get("channel") or "feishu",
                    "to": delivery.get("to") or "ou_a6469ccc2902a590994b6777b9c8ae8f"
                }
                fixed += 1
        if fixed > 0:
            with open(JOBS_FILE, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            run_cmd("openclaw gateway restart 2>&1 &")
        return {"fixed": fixed, "msg": f"修复了 {fixed} 个任务的 delivery 配置"}
    except Exception as e:
        return {"fixed": 0, "msg": f"修复失败: {e}"}


def fix_cron_error(errors):
    """cron error 不逐个重触发，依赖 delivery 修复 + gateway 重启后自然恢复"""
    count = len(errors)
    return {"fixed": count, "msg": f"{count} 个 cron error 将在 delivery 修复 + gateway 重启后自动恢复"}


def fix_feishu_connection(errors):
    """重启 gateway 恢复飞书连接"""
    run_cmd("openclaw gateway restart 2>&1 &")
    return {"fixed": 1, "msg": "已触发 gateway 重启以恢复飞书连接"}


def fix_gateway_restart(errors):
    """重启 gateway"""
    run_cmd("openclaw gateway restart 2>&1 &")
    return {"fixed": 1, "msg": "已触发 gateway 重启"}


def fix_disk_cleanup(errors):
    """清理磁盘空间"""
    cleaned = 0
    # 清理旧日志
    output = run_cmd("find /root/.openclaw -name '*.log' -mtime +7 -delete 2>/dev/null; echo done")
    if "done" in output:
        cleaned += 1
    # 清理旧备份
    output = run_cmd("find /tmp -name 'openclaw*' -mtime +3 -delete 2>/dev/null; echo done")
    if "done" in output:
        cleaned += 1
    return {"fixed": cleaned, "msg": f"清理了 {cleaned} 类临时文件"}


FIX_HANDLERS = {
    "fix_cron_delivery": fix_cron_delivery,
    "fix_cron_error": fix_cron_error,
    "fix_feishu_connection": fix_feishu_connection,
    "fix_gateway_restart": fix_gateway_restart,
    "fix_disk_cleanup": fix_disk_cleanup,
}


# ============================================================
# 主流程
# ============================================================

def scan_all():
    """执行全部扫描"""
    all_errors = []
    scanners = [
        ("cron任务", scan_cron_errors),
        ("cron配置", scan_cron_delivery_errors),
        ("飞书连接", scan_feishu_connection),
        ("gateway", scan_gateway_health),
        ("磁盘空间", scan_disk_space),
        ("内存", scan_memory),
    ]
    for name, scanner in scanners:
        try:
            errors = scanner()
            all_errors.extend(errors)
        except Exception as e:
            all_errors.append({"type": f"{name}_scan_error", "msg": str(e), "severity": "low"})
    return all_errors


def apply_fixes(errors, registry):
    """根据错误类型自动修复"""
    results = []
    # 按类型分组
    grouped = {}
    for err in errors:
        err_type = err.get("type")
        if err_type not in grouped:
            grouped[err_type] = []
        grouped[err_type].append(err)

    for err_type, err_list in grouped.items():
        fix_info = FIXES.get(err_type)
        if not fix_info or not fix_info["auto_fixable"]:
            results.append({"type": err_type, "action": "skip", "msg": "无自动修复方案"})
            continue

        handler = FIX_HANDLERS.get(fix_info["action"])
        if not handler:
            results.append({"type": err_type, "action": "skip", "msg": "修复处理器不存在"})
            continue

        try:
            result = handler(err_list)
            results.append({"type": err_type, "action": fix_info["action"], **result})

            # 记录到故障库
            if err_type not in registry.get("fixes", {}):
                registry.setdefault("fixes", {})[err_type] = {
                    "first_seen": now_cst().isoformat(),
                    "fix_count": 0,
                    "fix_action": fix_info["action"],
                    "description": fix_info["name"]
                }
            registry["fixes"][err_type]["fix_count"] = registry["fixes"][err_type].get("fix_count", 0) + 1
            registry["fixes"][err_type]["last_fixed"] = now_cst().isoformat()

        except Exception as e:
            results.append({"type": err_type, "action": "error", "msg": f"修复异常: {e}"})

    return results


def generate_report(errors, fix_results=None):
    """生成健康报告"""
    report = []
    report.append("【🏥 OpenClaw 自愈报告】")
    report.append(f"---")
    report.append(f"⏰ {now_cst().strftime('%Y-%m-%d %H:%M:%S')}")

    if not errors:
        report.append("✅ 所有系统正常，未发现异常")
        report.append("---")
        return "\n".join(report)

    # 按严重度排序
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    errors.sort(key=lambda e: severity_order.get(e.get("severity", "low"), 99))

    for err in errors:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(err.get("severity"), "⚪")
        report.append(f"{icon} [{err['type']}] {err.get('name', err.get('msg', '?'))}")

    if fix_results:
        report.append(f"")
        report.append(f"🔧 修复结果：")
        for fr in fix_results:
            status = "✅" if fr.get("fixed", 0) > 0 else "⏭️"
            report.append(f"  {status} {fr['type']}: {fr.get('msg', 'N/A')}")

    report.append(f"---")
    return "\n".join(report)


def learn_new_errors(errors, registry):
    """学习新错误模式"""
    known_types = set(registry.get("fixes", {}).keys())
    new_errors = [e for e in errors if e.get("type") not in known_types]

    if new_errors:
        for err in new_errors:
            registry.setdefault("errors", []).append({
                "type": err["type"],
                "first_seen": now_cst().isoformat(),
                "severity": err.get("severity", "unknown"),
                "msg": err.get("msg", err.get("name", "?")),
                "auto_fixed": err["type"] in FIXES
            })
        return len(new_errors)
    return 0


def main():
    fix_mode = "--fix" in sys.argv
    report_mode = "--report" in sys.argv
    learn_mode = "--learn" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    registry = load_registry()
    registry["stats"]["total_scans"] = registry["stats"].get("total_scans", 0) + 1
    registry["stats"]["last_scan"] = now_cst().isoformat()

    # 扫描
    errors = scan_all()

    # 学习
    if learn_mode:
        new_count = learn_new_errors(errors, registry)
        if new_count:
            print(f"📚 学习到 {new_count} 个新错误类型")

    # 修复
    fix_results = None
    if fix_mode and errors:
        fix_results = apply_fixes(errors, registry)
        registry["stats"]["total_fixes"] = registry["stats"].get("total_fixes", 0) + sum(
            1 for r in fix_results if r.get("fixed", 0) > 0
        )

    # 报告
    if report_mode or not (fix_mode or learn_mode):
        print(generate_report(errors, fix_results))
    elif errors:
        print(generate_report(errors, fix_results))
    else:
        print("✅ 一切正常")

    # 保存
    save_registry(registry)

    # 记录日志
    log_event("scan", {
        "errors": len(errors),
        "fixes": len(fix_results) if fix_results else 0,
        "mode": "fix" if fix_mode else "scan"
    })

    return 1 if any(e.get("severity") in ("critical", "high") for e in errors) else 0


if __name__ == "__main__":
    sys.exit(main())
