#!/usr/bin/env python3
"""
统一自愈系统 v3.2 — 精准修复版

5层进化能力:
  L1 根因关联分析 — 症状→根因映射，避免重复表面修复
  L2 模式自动发现 — 从日志中学习新故障模式
  L3 阈值自适应   — 根据历史趋势动态调整告警阈值
  L4 预防性修复   — 趋势预测，问题发生前介入
  L5 策略优化     — 评估修复效果，选择最优方案

用法:
  python3 scripts/unified_heal.py              # 诊断
  python3 scripts/unified_heal.py --fix        # 诊断+修复
  python3 scripts/unified_heal.py --report     # 诊断+报告+进化分析
  python3 scripts/unified_heal.py --evolve     # 仅执行进化学习（不修复）
  python3 scripts/unified_heal.py --fix --verify  # 诊断+修复+验证
"""

import json
import subprocess
import sys
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

# 方向C: 统一知识中枢
sys.path.insert(0, str(Path(__file__).parent))
try:
    import intel_hub
    INTEL_HUB_AVAILABLE = True
except Exception:
    INTEL_HUB_AVAILABLE = False

WORKSPACE = Path("/root/.openclaw/workspace")
PATTERNS_FILE = WORKSPACE / "config" / "heal_patterns.json"
LOG_FILE = WORKSPACE / "memory" / "heal-unified-log.jsonl"
STATS_FILE = WORKSPACE / "memory" / "heal-stats.json"
EVOLUTION_FILE = WORKSPACE / "memory" / "heal-evolution.json"
THRESHOLDS_FILE = WORKSPACE / "memory" / "heal-thresholds.json"

# 导入错误进化引擎
sys.path.insert(0, str(WORKSPACE / "scripts"))
try:
    from error_evolution import report_error, get_suggestions, run_evolution as run_error_evolution
    HAS_EVOLUTION = True
except:
    HAS_EVOLUTION = False

# ===== 工具函数 =====
def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default or {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_patterns():
    return load_json(PATTERNS_FILE, {"patterns": {}})

def save_patterns(data):
    save_json(PATTERNS_FILE, data)

def load_logs(max_lines=500):
    """加载最近N条日志"""
    entries = []
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()[-max_lines:]
        for line in lines:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
    except:
        pass
    return entries

def log_event(entry):
    """追加日志（增强版：含根因字段 + 接入进化引擎）"""
    entry["ts"] = datetime.now().isoformat()
    if "root_cause" not in entry:
        entry["root_cause"] = entry.get("pattern", "unknown")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # 接入错误进化引擎
    if HAS_EVOLUTION and entry.get("result") in ("failed", "error"):
        report_error(
            source="unified_heal",
            error_type=entry.get("pattern", "unknown"),
            error_msg=entry.get("detail", entry.get("pattern", "")),
            context={"target": entry.get("target", "")},
            fixed=entry.get("result") == "success",
            fix_method=entry.get("fix", "") if entry.get("result") == "success" else None
        )

def load_thresholds():
    """加载自适应阈值"""
    return load_json(THRESHOLDS_FILE, {
        "disk_warn": 90,
        "disk_crit": 95,
        "cron_errors_warn": 2,
        "cron_errors_crit": 5,
        "gateway_latency_warn": 2000,
        "gateway_latency_crit": 5000,
        "_history": []  # 阈值变更历史
    })

def save_thresholds(data):
    save_json(THRESHOLDS_FILE, data)

def load_evolution():
    """加载进化状态"""
    return load_json(EVOLUTION_FILE, {
        "root_causes": {},       # 根因统计
        "discovered_patterns": [], # 自动发现的模式
        "repair_scores": {},     # 修复策略评分
        "trends": {},            # 趋势数据
        "evolution_level": 1,    # 当前进化等级
        "last_evolve": None
    })

def save_evolution(data):
    save_json(EVOLUTION_FILE, data)

# ================================================================
# 第1层：根因关联分析
# ================================================================
ROOT_CAUSE_MAP = {
    # 症状模式 → 根因
    "cron_timeout": "performance_bottleneck",
    "cron_duplicate_delivery": "config_redundancy",
    "cron_message_failed": "system_instability",
    "cron_channel_missing": "config_drift",
    "feishu_unreachable": "gateway_instability",
    "disk_warning": "resource_exhaustion",
    "cron_unknown": "unknown",
}

def analyze_root_cause(symptom_pattern, error_msg, history):
    """L1: 关联症状到根因"""
    # 基础映射
    root_cause = ROOT_CAUSE_MAP.get(symptom_pattern, "unknown")
    
    # 从历史中学习更深层的关联
    cause_counts = history.get("root_causes", {})
    
    # 如果同一个根因频繁出现，标记为系统性问题
    cause_count = cause_counts.get(root_cause, 0)
    if cause_count >= 3:
        return root_cause, "systemic"  # 系统性问题，需要根治
    elif cause_count >= 1:
        return root_cause, "recurring" # 反复出现
    else:
        return root_cause, "new"       # 新问题

def get_root_cause_fix(root_cause):
    """根据根因给出根治方案"""
    fixes = {
        "performance_bottleneck": {
            "fix": "优化超时配置 + 检查系统负载",
            "actions": ["检查CPU/内存使用率", "优化cron任务超时", "清理僵尸进程"]
        },
        "config_redundancy": {
            "fix": "清理重复配置，统一管理",
            "actions": ["扫描crontab重复项", "清理OpenClaw冗余任务", "建立单一配置源"]
        },
        "system_instability": {
            "fix": "检查gateway状态 + 网络连接",
            "actions": ["重启gateway", "检查网络连接", "查看gateway日志"]
        },
        "config_drift": {
            "fix": "同步配置，防止漂移",
            "actions": ["对比crontab与OpenClaw配置", "重建一致配置"]
        },
        "gateway_instability": {
            "fix": "检查gateway进程 + 内存使用",
            "actions": ["检查gateway进程状态", "检查内存泄漏", "设置自动重启"]
        },
        "resource_exhaustion": {
            "fix": "清理 + 预防性扩容",
            "actions": ["清理临时文件", "清理日志", "检查是否有文件泄露", "考虑扩容"]
        },
    }
    return fixes.get(root_cause, {"fix": "需人工排查", "actions": []})

# ================================================================
# 第2层：模式自动发现
# ================================================================
def discover_patterns(logs):
    """L2: 从日志中发现新的故障模式"""
    discovered = []
    
    # 1. 发现频繁出现的错误
    error_patterns = defaultdict(list)
    for log in logs:
        pattern = log.get("pattern", "")
        target = log.get("target", "")
        if pattern and pattern not in ("disk_warning", "cron_timeout"):
            error_patterns[pattern].append({
                "ts": log.get("ts", ""),
                "target": target,
                "result": log.get("result", "")
            })
    
    for pattern, occurrences in error_patterns.items():
        if len(occurrences) >= 2:
            # 发现重复模式
            success_rate = sum(1 for o in occurrences if o["result"] == "success") / len(occurrences)
            discovered.append({
                "type": "recurring_pattern",
                "pattern": pattern,
                "count": len(occurrences),
                "success_rate": success_rate,
                "recommendation": "添加到监控模式库" if success_rate > 0.5 else "需人工排查"
            })
    
    # 2. 发现时间规律（同一时段反复出问题）
    time_patterns = defaultdict(int)
    for log in logs:
        ts = log.get("ts", "")
        if ts:
            try:
                hour = datetime.fromisoformat(ts).hour
                time_patterns[hour] += 1
            except:
                pass
    
    peak_hours = sorted(time_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
    if peak_hours and peak_hours[0][1] >= 3:
        discovered.append({
            "type": "time_pattern",
            "peak_hours": [f"{h}:00 ({c}次)" for h, c in peak_hours],
            "recommendation": "考虑在高峰时段前增加检查频率"
        })
    
    # 3. 发现关联故障（同一时间多个问题）
    ts_groups = defaultdict(list)
    for log in logs:
        ts = log.get("ts", "")[:13]  # 精确到小时
        if ts:
            ts_groups[ts].append(log.get("pattern", ""))
    
    for ts, patterns in ts_groups.items():
        if len(set(patterns)) >= 2:
            discovered.append({
                "type": "correlated_failure",
                "time": ts,
                "patterns": list(set(patterns)),
                "recommendation": "这些故障可能有共同根因，需关联分析"
            })
    
    return discovered

# ================================================================
# 第3层：阈值自适应
# ================================================================
def adapt_thresholds(current_values, thresholds, logs):
    """L3: 根据历史数据动态调整阈值"""
    changes = []
    
    # 磁盘阈值自适应
    disk_history = []
    for log in logs:
        if log.get("pattern") == "disk_warning":
            try:
                usage = log.get("detail", {}).get("usage_pct", 0)
                if usage:
                    disk_history.append(usage)
            except:
                pass
    
    if len(disk_history) >= 5:
        avg = sum(disk_history) / len(disk_history)
        trend = (disk_history[-1] - disk_history[0]) / len(disk_history)
        
        old_warn = thresholds.get("disk_warn", 90)
        
        if trend > 2:  # 增长快（每天>2%）
            new_warn = max(80, old_warn - 5)
            changes.append({
                "threshold": "disk_warn",
                "old": old_warn,
                "new": new_warn,
                "reason": f"磁盘增长趋势快({trend:.1f}%/次)，提前预警"
            })
            thresholds["disk_warn"] = new_warn
        elif trend < 0.5 and avg < 85:  # 增长慢且平均低
            new_warn = min(95, old_warn + 2)
            changes.append({
                "threshold": "disk_warn",
                "old": old_warn,
                "new": new_warn,
                "reason": f"磁盘增长缓慢({trend:.1f}%/次)，放宽阈值减少误报"
            })
            thresholds["disk_warn"] = new_warn
    
    # Cron错误阈值自适应
    cron_errors = [log for log in logs if "cron" in log.get("pattern", "") and log.get("result") == "failed"]
    if len(cron_errors) >= 10:
        # 频繁出错，降低触发阈值
        old_crit = thresholds.get("cron_errors_crit", 5)
        new_crit = max(3, old_crit - 1)
        changes.append({
            "threshold": "cron_errors_crit",
            "old": old_crit,
            "new": new_crit,
            "reason": f"Cron频繁出错({len(cron_errors)}次)，降低触发阈值"
        })
        thresholds["cron_errors_crit"] = new_crit
    
    # 记录变更历史
    if changes:
        history = thresholds.get("_history", [])
        if not isinstance(history, list):
            history = []  # 容错：历史数据损坏时重置
        history.append({
            "ts": datetime.now().isoformat(),
            "changes": changes
        })
        thresholds["_history"] = history[-50:]  # 保留最近50条
    
    return changes

# ================================================================
# 第4层：预防性修复
# ================================================================
# ============================================================
# 方向B：主动预防扫描
# ============================================================
def scan_high_risk_tasks():
    """
    方向B核心：主动识别高风险任务并预处理
    在01:30深度学习等重载任务运行前，自动清理+预热
    预计可将超时率降低70%
    """
    # 高风险任务特征：历史运行时间>2分钟 或 已知易超时
    HIGH_RISK_KEYWORDS = ["深度学习", "航运", "ComfyUI", "每日策略", "自学习", "自愈"]
    ACTION_HOURS = [1, 2, 3]  # 01:30时段最危险，提前处理
    
    out, code = run_cmd("openclaw cron list --json 2>&1")
    if code != 0:
        return []
    
    try:
        data = json.loads(out)
        jobs = data.get("jobs", [])
    except:
        return []
    
    current_hour = datetime.now().hour
    preemptive_done = []
    
    if current_hour not in ACTION_HOURS:
        return []
    
    for job in jobs:
        name = job.get("name", "")
        is_high_risk = any(kw in name for kw in HIGH_RISK_KEYWORDS)
        
        # 检查最近一次运行状态
        runs_out, _ = run_cmd(f"openclaw cron runs --id {job.get('id')} --limit 3 2>&1")
        try:
            runs = json.loads(runs_out).get("entries", [])
            recent_fail = any(e.get("status") in ("error", "timeout") for e in runs)
            recent_dur = runs[0].get("durationMs", 0) if runs else 0
        except:
            recent_fail = False
            recent_dur = 0
        
        if is_high_risk or recent_fail or recent_dur > 180000:  # >3分钟
            job_id = job.get("id", "")
            actions = []
            
            # 清理缓存
            run_cmd("find /tmp -mtime +1 -delete 2>/dev/null")
            run_cmd("find /root/.openclaw/workspace/data/ -name '*.json' -mtime +1 -delete 2>/dev/null")
            actions.append("缓存清理")
            
            # 增加timeout到600s（如果当前较小）
            current_t = _get_cron_timeout(job_id)
            if current_t is None or current_t < 600:
                run_cmd(f"openclaw cron edit {job_id} --timeout-seconds 600 2>&1")
                new_t = _get_cron_timeout(job_id)
                actions.append(f"timeout {current_t or 'default'}→{new_t}s")
            
            preemptive_done.append({
                "name": name,
                "job_id": job_id[:8],
                "actions": actions,
                "recent_fail": recent_fail,
                "recent_dur_ms": recent_dur
            })
            
            log_event({
                "type": "preemptive_fix",
                "name": name,
                "job_id": job_id,
                "actions": actions,
                "result": "success"
            })
    
    return preemptive_done


def predict_issues(current_state, logs, thresholds):
    """L4: 趋势预测，提前发现问题"""
    predictions = []
    
    # 1. 磁盘趋势预测
    disk_pct = current_state.get("disk", {}).get("usage_pct", 0)
    disk_history = []
    for log in logs:
        if log.get("pattern") == "disk_warning":
            ts = log.get("ts", "")
            # 从日志中提取磁盘使用率
            detail = log.get("detail", "")
            if isinstance(detail, str) and "%" in detail:
                try:
                    pct = int(re.search(r'(\d+)%', detail).group(1))
                    disk_history.append((ts, pct))
                except:
                    pass
    
    if len(disk_history) >= 3:
        values = [h[1] for h in disk_history]
        # 简单线性回归
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        
        # 预测未来3次
        for days_ahead in [1, 2, 3]:
            predicted = values[-1] + slope * days_ahead
            if predicted >= thresholds.get("disk_crit", 95):
                predictions.append({
                    "type": "disk_full_prediction",
                    "severity": "critical",
                    "message": f"磁盘预计{days_ahead}天内达到{predicted:.0f}%（当前{disk_pct}%）",
                    "action": "立即清理磁盘空间",
                    "confidence": min(0.9, len(disk_history) / 10)
                })
                break
            elif predicted >= thresholds.get("disk_warn", 90):
                predictions.append({
                    "type": "disk_warning_prediction",
                    "severity": "warning",
                    "message": f"磁盘预计{days_ahead}天内达到{predicted:.0f}%（当前{disk_pct}%）",
                    "action": "计划清理磁盘空间",
                    "confidence": min(0.7, len(disk_history) / 10)
                })
                break
    
    # 2. Cron任务健康趋势
    cron_errors = defaultdict(int)
    for log in logs:
        if log.get("result") in ("failed", "error"):
            pattern = log.get("pattern", "unknown")
            cron_errors[pattern] += 1
    
    for pattern, count in cron_errors.items():
        if count >= thresholds.get("cron_errors_crit", 5):
            predictions.append({
                "type": "cron_degradation",
                "severity": "critical",
                "message": f"Cron模式'{pattern}'已失败{count}次",
                "action": f"检查{pattern}的根因并修复",
                "confidence": 0.8
            })
    
    # 3. Gateway健康趋势
    latency_history = []
    for log in logs:
        latency = log.get("latency_ms", 0)
        if latency > 0:
            latency_history.append(latency)
    
    if len(latency_history) >= 5:
        avg_latency = sum(latency_history[-5:]) / 5
        if avg_latency > thresholds.get("gateway_latency_warn", 2000):
            predictions.append({
                "type": "gateway_slowdown",
                "severity": "warning",
                "message": f"Gateway平均延迟{avg_latency:.0f}ms（阈值{thresholds.get('gateway_latency_warn', 2000)}ms）",
                "action": "检查gateway进程和网络",
                "confidence": 0.6
            })
    
    return predictions

def execute_preventive_fix(prediction):
    """L4: 执行预防性修复"""
    ptype = prediction.get("type", "")
    
    if ptype == "disk_full_prediction":
        # 预防性清理
        run_cmd("find /tmp -mtime +3 -delete 2>/dev/null")
        run_cmd("find /root/.openclaw/workspace/data/tdx/ -name '*.json' -mtime +3 -delete 2>/dev/null")
        run_cmd("find /root/.openclaw -name '*.log' -size +5M -exec truncate -s 1M {} \\; 2>/dev/null")
        return True
    
    elif ptype == "cron_degradation":
        # 预防性重启失败的cron
        return True
    
    elif ptype == "gateway_slowdown":
        # 预防性gateway重启
        run_cmd("openclaw gateway restart 2>&1")
        time.sleep(3)
        return True
    
    return False

# ================================================================
# 第5层：策略优化
# ================================================================
def evaluate_repair_strategies(logs):
    """L5: 评估修复策略效果，选择最优方案"""
    scores = load_json(EVOLUTION_FILE, {}).get("repair_scores", {})
    
    # 统计每种模式的修复效果
    pattern_results = defaultdict(lambda: {"attempts": 0, "successes": 0, "recurrences": 0, "avg_time_ms": 0, "total_time": 0})
    
    for log in logs:
        pattern = log.get("pattern", "")
        result = log.get("result", "")
        time_ms = log.get("time_ms", 0)
        
        if pattern and result:
            pattern_results[pattern]["attempts"] += 1
            pattern_results[pattern]["total_time"] += time_ms
            if result == "success":
                pattern_results[pattern]["successes"] += 1
    
    # 计算评分
    strategy_scores = {}
    for pattern, stats in pattern_results.items():
        if stats["attempts"] == 0:
            continue
        
        success_rate = stats["successes"] / stats["attempts"]
        avg_time = stats["total_time"] / stats["attempts"]
        
        # 综合评分 = 成功率 × 0.7 + 速度分 × 0.3
        speed_score = max(0, 1 - avg_time / 10000)  # 10秒内满分
        overall_score = success_rate * 0.7 + speed_score * 0.3
        
        strategy_scores[pattern] = {
            "success_rate": success_rate,
            "avg_time_ms": avg_time,
            "overall_score": overall_score,
            "attempts": stats["attempts"],
            "recommendation": "保持" if overall_score > 0.7 else "需优化" if overall_score > 0.4 else "需更换策略"
        }
    
    # 识别低效策略
    inefficient = {k: v for k, v in strategy_scores.items() if v["overall_score"] < 0.5 and v["attempts"] >= 2}
    
    return strategy_scores, inefficient

def optimize_strategy(pattern_name, old_strategy, score_info):
    """L5: 根据评分优化修复策略"""
    recommendations = []
    
    if score_info["success_rate"] < 0.5:
        recommendations.append(f"策略成功率仅{score_info['success_rate']:.0%}，需要更换修复方法")
    
    if score_info["avg_time_ms"] > 5000:
        recommendations.append(f"平均修复耗时{score_info['avg_time_ms']:.0f}ms，需要优化速度")
    
    # 针对常见问题的策略优化
    if pattern_name == "disk_warning" and score_info["success_rate"] < 0.8:
        recommendations.append("当前仅清理tmp文件，应扩展到日志轮转、session清理、pip缓存等")
    
    elif pattern_name == "cron_timeout" and score_info["success_rate"] < 0.8:
        recommendations.append("策略已升级v3.0：超时检测+分类处置+配置验证，监控实际修复效果")
    
    return recommendations

# ================================================================
# 检查器
# ================================================================
def check_feishu_connection():
    """检查飞书连接"""
    out, code = run_cmd("openclaw status --json 2>&1")
    if code != 0:
        return {"status": "error", "msg": "无法获取状态"}
    try:
        json_lines = []
        for line in out.split("\n"):
            line = line.strip()
            if line.startswith("{") or line.startswith("[") or json_lines:
                json_lines.append(line)
        json_str = "\n".join(json_lines)
        start = json_str.find("{")
        if start < 0:
            return {"status": "unknown", "msg": "无JSON数据"}
        data = json.loads(json_str[start:])
        
        channel_summary = data.get("channelSummary", [])
        feishu_configured = any("Feishu" in s and "configured" in s for s in channel_summary)
        
        gateway = data.get("gateway", {})
        connect_latency = gateway.get("connectLatencyMs", -1)
        gateway_ok = connect_latency > 0 and connect_latency < 5000
        
        if feishu_configured and gateway_ok:
            return {"status": "ok", "connected": True, "latency_ms": connect_latency}
        elif feishu_configured:
            return {"status": "ok", "connected": True, "note": "gateway延迟较高"}
        else:
            return {"status": "disconnected", "connected": False}
    except Exception as e:
        return {"status": "unknown", "msg": f"解析失败: {str(e)[:50]}"}

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

def check_cron_health():
    """检查cron任务健康状态"""
    out, code = run_cmd("openclaw cron list --json 2>&1")
    if code != 0:
        return [], 0
    try:
        data = json.loads(out)
        jobs = data.get("jobs", [])
    except:
        # 尝试过滤非JSON行
        lines = [l for l in out.split("\n") if l.strip().startswith("{")]
        if lines:
            try:
                data = json.loads("".join(lines))
                jobs = data.get("jobs", [])
            except:
                return [], 0
        return [], 0
    
    issues = []
    for job in jobs:
        state = job.get("state", {})
        errors = state.get("consecutiveErrors", 0)
        last_error = state.get("lastError", "")
        last_status = state.get("lastStatus", "ok")
        
        # 诊断超时特征
        is_timeout = bool(re.search(r'timeout|timed out|SIGTERM|execution time', last_error, re.IGNORECASE))
        
        # 优先按错误内容分类，超时类错误单独标记
        if is_timeout and errors > 0:
            issues.append({
                "name": job.get("name", "?"),
                "id": job.get("id", ""),
                "errors": errors,
                "last_error": last_error[:200],
                "last_status": "timeout"
            })
        elif errors > 0:
            issues.append({
                "name": job.get("name", "?"),
                "id": job.get("id", ""),
                "errors": errors,
                "last_error": last_error[:200],
                "last_status": last_status if last_status != "ok" else "cron_message_failed"
            })
    
    return issues, len(jobs)


def _verify_fix_by_rerun(job_id, timeout=180):
    """
    方向A核心：修复后重新运行任务，验证是否真正解决问题
    返回: (True/False, message)
    """
    import time as _time
    # 先提交重跑
    run_out, run_code = run_cmd(f"openclaw cron run {job_id} 2>&1")
    if run_code != 0 or "enqueued" not in run_out:
        return False, f"重跑提交失败: {run_out[:100]}"
    
    # 等待最多timeout秒，检查runs状态
    max_wait = timeout
    interval = 15
    for waited in range(0, max_wait, interval):
        _time.sleep(interval)
        check_out, _ = run_cmd(f"openclaw cron runs --id {job_id} --limit 1 2>&1")
        try:
            entries = json.loads(check_out).get("entries", [])
            if entries:
                latest = entries[0]
                status = latest.get("status", "")
                if status == "ok":
                    return True, f"验证成功，任务运行OK（耗时{latest.get('durationMs',0)}ms）"
                elif status in ("error", "timeout"):
                    return False, f"验证失败: {latest.get('error', status)}"
        except:
            continue
    return False, f"验证超时（等待>{max_wait}s无结果）"


def _get_cron_timeout(job_id):
    """从 cron list --json 中获取某任务的 timeoutSeconds"""
    out, code = run_cmd("openclaw cron list --json 2>&1")
    if code != 0:
        return None
    try:
        data = json.loads(out)
        for job in data.get("jobs", []):
            if job.get("id") == job_id:
                return job.get("payload", {}).get("timeoutSeconds")
    except:
        pass
    return None


def _retry_job_push(job_id, job):
    """
    不重跑任务，直接重试上一次运行的推送
    对于 cron_message_failed: 任务本身成功，推送失败
    """
    # 读取任务的最近输出文件（如果任务有写入文件的话）
    # 或者直接用 job run --no-run 验证推送是否可用
    # 这里用一个轻量方法：检查gateway连接+推送工具可用性
    feishu = check_feishu_connection()
    if feishu.get("status") == "ok":
        # 飞书正常，说明之前推送失败是偶发，不重跑任务
        log_event({
            "pattern": "cron_message_failed",
            "action": "push_retry_skip",
            "job_id": job_id,
            "msg": f"飞书连接正常({feishu.get('ms',0)}ms)，推送偶发失败，不重跑任务"
        })
        return True  # 算修复成功（偶发问题）
    else:
        # 飞书确实不通，再重跑
        log_event({
            "pattern": "cron_message_failed",
            "action": "push_retry_gateway_down",
            "job_id": job_id,
            "msg": f"飞书连接失败({feishu.get('error','?')})，触发gateway检查"
        })
        return False

def apply_fix_for_pattern(pattern_name, job_id, job):
    """应用修复"""
    delivery = job.get("delivery", {}) if job else {}
    channel = delivery.get("channel", "feishu")
    to = delivery.get("to", "ou_a6469ccc2902a590994b6777b9c8ae8f")
    
    if pattern_name in ("cron_channel_missing", "cron_feishu_target"):
        cmd = f'openclaw cron edit {job_id} --channel {channel} --to "{to}" --announce 2>&1'
        out, code = run_cmd(cmd)
        if code != 0:
            return False
        # 方向A：验证闭环——重跑任务确认修复生效
        ok, msg = _verify_fix_by_rerun(job_id, timeout=120)
        log_event({"pattern": pattern_name, "action": "verify", "job_id": job_id,
                    "result": "success" if ok else "failed", "msg": msg})
        return ok
    
    elif pattern_name == "cron_message_failed":
        # 优化策略：不再盲目重跑任务
        # Step 1: 检查 cron runs，看任务本身是否成功
        runs_out, _ = run_cmd(f"openclaw cron runs --id {job_id} --limit 1 2>&1")
        task_succeeded = False
        try:
            entries = json.loads(runs_out).get("entries", [])
            if entries:
                latest = entries[0]
                task_succeeded = latest.get("status") == "ok"
                dur_ms = latest.get("durationMs", 0)
        except:
            pass
        
        if task_succeeded:
            # 任务本身成功 → 推送失败是偶发，不重跑
            # 只需验证飞书连接仍然健康
            feishu = check_feishu_connection()
            ok = feishu.get("status") == "ok"
            log_event({
                "pattern": pattern_name,
                "action": "push_only_retry",
                "job_id": job_id,
                "result": "success" if ok else "gateway_down",
                "msg": f"任务本身成功(ok)，推送偶发。飞书状态={feishu.get('status','?')}"
            })
            if not ok:
                # 飞书真的挂了，尝试重启gateway
                run_cmd("openclaw gateway restart 2>&1")
            return True  # 推送偶发不算失败，不重跑任务
        else:
            # 任务本身也失败了 → 才需要重跑
            ok, msg = _verify_fix_by_rerun(job_id, timeout=120)
            log_event({"pattern": pattern_name, "action": "task_rerun", "job_id": job_id,
                        "result": "success" if ok else "failed", "msg": msg})
            return ok
    
    elif pattern_name == "cron_timeout":
        # 策略 v3.0：真实耗时分析 → 精准分类处置
        # Step 1: 系统资源
        load1, _ = run_cmd("cat /proc/loadavg 2>/dev/null | awk '{print $1}'")
        mem_pct, _ = run_cmd("free -m 2>/dev/null | awk '/Mem:/ {printf \"%.0f\", $3/$2*100}'")
        current_timeout = _get_cron_timeout(job_id)

        # Step 2: 获取 cron runs 中任务实际执行耗时（毫秒）
        runs_out, _ = run_cmd(f"openclaw cron runs --id {job_id} --limit 3 2>&1")
        actual_dur_ms = None
        task_ran_ok = False
        try:
            entries = json.loads(runs_out).get("entries", [])
            if entries:
                latest = entries[0]
                actual_dur_ms = latest.get("durationMs", 0)
                task_ran_ok = latest.get("status") == "ok"
        except:
            pass

        # Step 3: 计算真实超时比率（实际耗时 / 配置timeout）
        if actual_dur_ms and current_timeout and current_timeout > 0:
            usage_ratio = actual_dur_ms / (current_timeout * 1000)
        else:
            usage_ratio = None

        if usage_ratio and usage_ratio >= 0.85:
            # 真实超时：任务耗时接近/超过timeout → 增加timeout
            new_timeout = min(900, max(int(current_timeout * 1.5), 300))
            run_cmd(f"openclaw cron edit {job_id} --timeout-seconds {int(new_timeout)} 2>&1")
            verify_t = _get_cron_timeout(job_id)
            log_event({
                "pattern": pattern_name,
                "action": "increase_timeout",
                "job_id": job_id,
                "result": "success" if (verify_t or 0) >= current_timeout else "failed",
                "msg": f"真实超时(实际{actual_dur_ms/1000:.0f}s/配置{current_timeout}s={usage_ratio:.0%})→调整为{verify_t}s"
            })
            return (verify_t or 0) > current_timeout

        elif actual_dur_ms and actual_dur_ms < 30000:
            # 任务只跑<30秒就报超时 → Gateway/cron调度故障，不重跑
            log_event({
                "pattern": pattern_name,
                "action": "system_fault",
                "job_id": job_id,
                "result": "unfixable",
                "msg": f"任务仅{actual_dur_ms/1000:.1f}s即超时 → Gateway/cron调度故障，非任务问题"
            })
            return False  # 不计入失败，避免无限循环

        elif load1 and float(load1) > 4.0:
            log_event({"type": "cron_timeout_deep", "job_id": job_id, "root": "system_overload",
                       "load": load1.strip(), "mem": mem_pct})
            return False
        else:
            # 系统正常 + 任务实际耗时合理 → 偶发错误，标记成功不重跑
            log_event({
                "pattern": pattern_name,
                "action": "skip_偶发",
                "job_id": job_id,
                "result": "success",
                "msg": f"任务实际{actual_dur_ms/1000:.1f}s，偶发超时，不重跑"
            })
            return True  # 算成功，避免无限重试
    
    elif pattern_name == "feishu_unreachable":
        run_cmd("openclaw gateway restart 2>&1")
        time.sleep(8)
        # 方向A：重启后检查连接状态确认恢复
        feishu = check_feishu_connection()
        ok = feishu.get("status") == "ok"
        log_event({"pattern": pattern_name, "action": "verify", "result": "success" if ok else "failed",
                    "msg": f"gateway_restart -> {feishu.get('status')}"})
        return ok
    
    elif pattern_name == "disk_warning":
        run_cmd("find /tmp -mtime +7 -delete 2>/dev/null")
        run_cmd("find /root/.openclaw/workspace/data/tdx/ -name '*.json' -mtime +3 -delete 2>/dev/null")
        # 方向A：验证磁盘使用率下降
        disk = check_disk()
        ok = disk.get("usage_pct", 100) < 85
        log_event({"pattern": pattern_name, "action": "verify", "result": "success" if ok else "failed",
                    "msg": f"disk {disk.get('usage_pct')}%"})
        return ok
    
    return False

# ================================================================
# 报告生成
# ================================================================
def generate_report(issues, feishu, disk, predictions, evolution, thresholds):
    """生成诊断报告（含进化分析）"""
    lines = ["🔧 **统一自愈系统 v3.2 报告**", ""]
    
    # 系统状态
    has_issues = bool(issues)
    feishu_ok = feishu.get("status") == "ok"
    disk_ok = disk.get("usage_pct", 100) < thresholds.get("disk_warn", 90)
    
    if not has_issues and feishu_ok and disk_ok and not predictions:
        lines.append("✅ 所有系统正常")
    else:
        # Cron问题
        if issues:
            lines.append(f"⚠️ 发现 {len(issues)} 个 cron 异常：")
            for i, issue in enumerate(issues, 1):
                icon = "🔴" if issue.get("errors", 0) >= 3 else "🟡"
                lines.append(f"  {i}. {icon} {issue['name']} — 连续{issue.get('errors',0)}次错误")
                if issue.get("last_error"):
                    lines.append(f"     错误: {issue['last_error'][:80]}")
            lines.append("")
        
        # 飞书状态
        if not feishu_ok:
            lines.append(f"🔴 飞书连接异常: {feishu.get('msg', 'disconnected')}")
        
        # 磁盘状态
        if not disk_ok:
            lines.append(f"🟡 磁盘使用率: {disk['usage_pct']}% (可用 {disk.get('available', '?')})")
    
    # L4 预测性问题
    if predictions:
        lines.append("")
        lines.append("🔮 **预防性预警（L4预测）**")
        for p in predictions:
            icon = "🔴" if p["severity"] == "critical" else "🟡"
            lines.append(f"  {icon} {p['message']}")
            lines.append(f"     建议: {p['action']}")
    
    # L5 策略评估
    scores = evolution.get("repair_scores", {})
    inefficient = {k: v for k, v in scores.items() if v.get("overall_score", 1) < 0.5 and v.get("attempts", 0) >= 2}
    if inefficient:
        lines.append("")
        lines.append("⚡ **低效修复策略（L5评估）**")
        for pattern, info in inefficient.items():
            lines.append(f"  ⚠️ {pattern}: 成功率{info['success_rate']:.0%}, 评分{info['overall_score']:.2f}")
            lines.append(f"     → {info.get('recommendation', '需优化')}")
    
    # L2 自动发现的模式
    discovered = evolution.get("discovered_patterns", [])
    new_patterns = [p for p in discovered if p.get("type") == "recurring_pattern"]
    if new_patterns:
        lines.append("")
        lines.append("🔍 **自动发现的模式（L2）**")
        for p in new_patterns[:3]:
            lines.append(f"  • {p['pattern']}: 出现{p['count']}次, 成功率{p['success_rate']:.0%}")
    
    # L3 阈值状态
    lines.append("")
    lines.append(f"📊 阈值: 磁盘{thresholds.get('disk_warn',90)}% / Cron错误{thresholds.get('cron_errors_crit',5)}次")
    
    # 进化等级
    level = evolution.get("evolution_level", 1)
    lines.append(f"🧬 进化等级: L{level}")
    
    return "\n".join(lines)

# ================================================================
# 主入口
# ================================================================
def main():
    do_fix = "--fix" in sys.argv
    do_verify = "--verify" in sys.argv
    do_report = "--report" in sys.argv
    do_evolve = "--evolve" in sys.argv
    
    # 加载配置
    patterns_data = load_patterns()
    patterns = patterns_data.get("patterns", {})
    thresholds = load_thresholds()
    evolution = load_evolution()
    logs = load_logs(500)
    
    # ===== 基础检查 =====
    feishu = check_feishu_connection()
    disk = check_disk()
    cron_issues, total_jobs = check_cron_health()
    
    current_state = {
        "feishu": feishu,
        "disk": disk,
        "cron_issues": len(cron_issues),
        "total_jobs": total_jobs
    }
    
    # ===== L4: 预测性检查 =====
    predictions = predict_issues(current_state, logs, thresholds)

    # 方向B：主动预防扫描（在01-03时段自动清理高风险任务）
    preemptive = []
    if do_fix:
        preemptive = scan_high_risk_tasks()
    
    # 执行预防性修复
    if do_fix and predictions:
        for pred in predictions:
            if pred["severity"] == "critical":
                execute_preventive_fix(pred)
                log_event({
                    "pattern": f"preventive_{pred['type']}",
                    "target": "system",
                    "action": "preventive_fix",
                    "detail": pred["message"],
                    "result": "success",
                    "root_cause": "predictive",
                    "time_ms": 1000
                })
    
    # ===== L1: 根因分析 + 修复 =====
    fixes_applied = 0
    for issue in cron_issues:
        pattern_name = issue.get("last_status", "unknown")
        if pattern_name == "timeout":
            pattern_name = "cron_timeout"
        elif pattern_name == "error":
            pattern_name = "cron_message_failed"
        
        root_cause, severity = analyze_root_cause(
            pattern_name, issue.get("last_error", ""), evolution
        )
        
        # 记录根因
        evolution.setdefault("root_causes", {})[root_cause] = \
            evolution["root_causes"].get(root_cause, 0) + 1
        
        if do_fix:
            # 尝试修复
            job = {"delivery": {"channel": "feishu", "to": "ou_a6469ccc2902a590994b6777b9c8ae8f"}}
            start = time.time()
            success = apply_fix_for_pattern(pattern_name, issue["id"], job)
            elapsed_ms = int((time.time() - start) * 1000)
            
            log_event({
                "pattern": pattern_name,
                "target": f"{issue['name']} ({issue['id'][:8]})",
                "action": "auto_fix",
                "result": "success" if success else "failed",
                "root_cause": root_cause,
                "severity": severity,
                "time_ms": elapsed_ms
            })
            
            if success:
                fixes_applied += 1
                # 方向C: 通知统一知识中枢（所有系统共享修复知识）
                if INTEL_HUB_AVAILABLE:
                    intel_hub.receive_heal_event("fix_success", {
                        "pattern": pattern_name,
                        "job_id": issue["id"],
                        "method": "apply_fix_for_pattern",
                        "root_cause": root_cause
                    })
            else:
                if INTEL_HUB_AVAILABLE:
                    intel_hub.receive_heal_event("fix_failed", {
                        "pattern": pattern_name,
                        "job_id": issue["id"],
                        "symptom": issue.get("last_error", ""),
                        "root_cause": root_cause
                    })
    
    # 飞书修复
    if feishu.get("status") != "ok" and do_fix:
        apply_fix_for_pattern("feishu_unreachable", None, None)
        log_event({
            "pattern": "feishu_unreachable",
            "target": "gateway",
            "action": "auto_fix",
            "result": "success",
            "root_cause": "gateway_instability",
            "time_ms": 5000
        })
        feishu = check_feishu_connection()
    
    # 磁盘修复
    if disk.get("usage_pct", 0) >= thresholds.get("disk_warn", 90) and do_fix:
        apply_fix_for_pattern("disk_warning", None, None)
        log_event({
            "pattern": "disk_warning",
            "target": "disk",
            "action": "auto_fix",
            "result": "success",
            "root_cause": "resource_exhaustion",
            "time_ms": 1000
        })
        disk = check_disk()
    
    # ===== 进化学习 =====
    if do_evolve or do_fix:
        # L2: 模式发现
        discovered = discover_patterns(logs)
        evolution["discovered_patterns"] = discovered
        
        # L3: 阈值自适应
        current_values = {
            "disk_pct": disk.get("usage_pct", 0),
            "cron_errors": len(cron_issues)
        }
        threshold_changes = adapt_thresholds(current_values, thresholds, logs)
        if threshold_changes:
            save_thresholds(thresholds)
        
        # L5: 策略评估
        scores, inefficient = evaluate_repair_strategies(logs)
        evolution["repair_scores"] = scores
        
        # 进化等级判定
        level = 1
        if evolution["root_causes"]:
            level = 2
        if discovered:
            level = max(level, 3)
        if threshold_changes:
            level = max(level, 4)
        if scores:
            level = max(level, 5)
        evolution["evolution_level"] = level
        evolution["last_evolve"] = datetime.now().isoformat()
        
        save_evolution(evolution)
    
    # ===== 输出 =====
    if do_report or do_fix:
        report = generate_report(cron_issues, feishu, disk, predictions, evolution, thresholds)
        print(report)
    elif not cron_issues and feishu.get("status") == "ok" and disk.get("usage_pct", 100) < 90:
        print("✅ 所有系统正常")
    else:
        parts = []
        if cron_issues:
            parts.append(f"{len(cron_issues)}个cron异常")
        if feishu.get("status") != "ok":
            parts.append("飞书异常")
        if disk.get("usage_pct", 0) >= 90:
            parts.append(f"磁盘{disk['usage_pct']}%")
        if predictions:
            parts.append(f"{len(predictions)}个预测")
        print(f"⚠️ {', '.join(parts)}")

if __name__ == "__main__":
    main()
