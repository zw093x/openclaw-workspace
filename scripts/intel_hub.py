#!/usr/bin/env python3
"""
统一智能层 — 将自学习进化系统接入所有子系统

连接关系:
  unified_heal.py ←→ learn_evolve.py ←→ error_evolution.py
       ↑                   ↑                    ↑
    cron任务             所有脚本              错误日志
       ↑                   ↑                    ↑
  自愈系统技能         自学习技能           错误进化引擎

用法:
  python3 scripts/intel_hub.py --sync      # 同步所有系统的学习数据
  python3 scripts/intel_hub.py --status    # 查看统一状态
  python3 scripts/intel_hub.py --feed      # 将所有错误导入学习系统
  python3 scripts/intel_hub.py --inform    # 将学习结果通知所有系统
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

WORKSPACE = Path("/root/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))

import error_evolution
import learn_evolve
import memory_evolve
import review_evolve

LEARN_DB = WORKSPACE / "memory" / "learn-db.json"
HEAL_LOG = WORKSPACE / "memory" / "heal-unified-log.jsonl"
HEAL_EVO = WORKSPACE / "memory" / "heal-evolution.json"
ERROR_KNOWLEDGE = WORKSPACE / "memory" / "error-knowledge.json"
ERROR_PATTERNS = WORKSPACE / "memory" / "error-patterns.json"
INTEL_STATE = WORKSPACE / "memory" / "intel-hub-state.json"
REVIEW_DB = WORKSPACE / "memory" / "review-db.json"

def load_json_safe(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default or {}

def save_json_safe(path, data):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_jsonl(path, max_lines=200):
    entries = []
    try:
        with open(path, "r") as f:
            for line in f.readlines()[-max_lines:]:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except:
                        pass
    except:
        pass
    return entries

# ===== 1. 错误进化 → 自学习 =====
def sync_errors_to_learn():
    """将错误进化引擎的记录导入自学习系统"""
    knowledge = load_json_safe(ERROR_KNOWLEDGE, {"errors": {}, "fixes": {}})
    db = learn_evolve.load_learn_db()
    imported = 0

    for fp, err_info in knowledge.get("errors", {}).items():
        if err_info.get("count", 0) >= 2:
            summary = f"{err_info.get('type','?')}错误: {err_info.get('sample_msg','')[:50]}"
            category = err_info.get("category", "unknown")
            existing = any(
                summary[:20] in l.get("summary", "")
                for l in db.get("lessons", {}).values()
            )
            if not existing:
                learn_evolve.record_lesson(
                    "error", category, summary,
                    f"来源:{err_info.get('sources',[])} 出现{err_info.get('count',0)}次",
                    priority="medium" if err_info.get("count", 0) < 3 else "high"
                )
                imported += 1

    return imported

# ===== 2. 自愈系统 → 自学习 =====
def sync_heal_to_learn():
    """将自愈系统的修复记录导入自学习系统"""
    heal_logs = load_jsonl(HEAL_LOG, 100)
    db = learn_evolve.load_learn_db()
    imported = 0

    for entry in heal_logs:
        pattern = entry.get("pattern", "")
        result = entry.get("result", "")
        root_cause = entry.get("root_cause", "")

        if result in ("failed", "error") and pattern:
            summary = f"自愈失败: {pattern} (根因:{root_cause})"
            existing = any(
                pattern in l.get("summary", "") and "自愈" in l.get("summary", "")
                for l in db.get("lessons", {}).values()
            )
            if not existing:
                learn_evolve.record_lesson(
                    "error", "self_heal", summary,
                    f"自愈系统修复{pattern}失败，根因:{root_cause}",
                    priority="high"
                )
                imported += 1

    return imported

# ===== 3. 自学习 → 自愈系统 =====
def inform_heal_from_learn():
    """将自学习的规则通知自愈系统"""
    db = learn_evolve.load_learn_db()
    heal_evo = load_json_safe(HEAL_EVO, {"root_causes": {}, "repair_scores": {}})
    applied = []

    # 将高频教训注入自愈系统的修复策略
    for lid, lesson in db.get("lessons", {}).items():
        if lesson.get("status") == "internalized":
            category = lesson.get("category", "")
            rule = db.get("rules", {}).get(lid, {}).get("rule", "")

            if rule and category in ("cron", "磁盘", "网络", "api", "gateway"):
                # 更新自愈系统的修复评分
                heal_evo.setdefault("learned_rules", {})[lid] = {
                    "rule": rule,
                    "category": category,
                    "source": "self_learn",
                    "applied_at": datetime.now().isoformat()
                }
                applied.append(lid)

    save_json_safe(HEAL_EVO, heal_evo)
    return applied

# ===== 4. 自学习 → 错误进化 =====
def inform_error_evo_from_learn():
    """将自学习的规则通知错误进化引擎"""
    db = learn_evolve.load_learn_db()
    patterns = load_json_safe(ERROR_PATTERNS, {"recommendations": []})
    applied = []

    for lid, lesson in db.get("lessons", {}).items():
        if lesson.get("status") in ("internalized", "promoted"):
            category = lesson.get("category", "")
            rule = db.get("rules", {}).get(lid, {}).get("rule", "")

            if rule:
                # 注入为内置修复方案
                existing_recs = patterns.get("recommendations", [])
                already = any(rule[:20] in r.get("message", "") for r in existing_recs)
                if not already:
                    existing_recs.append({
                        "type": "learned_rule",
                        "priority": lesson.get("priority", "medium"),
                        "message": f"[自学习] {rule}",
                        "action": "自动应用自学习规则",
                        "source": lid
                    })
                    patterns["recommendations"] = existing_recs
                    applied.append(lid)

    save_json_safe(ERROR_PATTERNS, patterns)
    return applied

# ===== 5. Cron错误 → 自学习 =====
def sync_cron_to_learn():
    """将cron任务错误导入自学习系统"""
    out, _ = subprocess.getstatusoutput("openclaw cron list --json 2>&1")
    try:
        data = json.loads(out)
        jobs = data.get("jobs", [])
    except:
        return 0

    db = learn_evolve.load_learn_db()
    imported = 0

    for job in jobs:
        state = job.get("state", {})
        errors = state.get("consecutiveErrors", 0)
        if errors >= 2:
            name = job.get("name", "?")
            last_err = state.get("lastError", "")[:100]
            summary = f"Cron'{name}'连续{errors}次错误"
            existing = any(
                name in l.get("summary", "") and "Cron" in l.get("summary", "")
                for l in db.get("lessons", {}).values()
            )
            if not existing:
                learn_evolve.record_lesson(
                    "error", "cron", summary,
                    f"任务:{name} 错误:{last_err}",
                    priority="high" if errors >= 3 else "medium"
                )
                imported += 1

    return imported

# ===== 全量同步 =====
def full_sync():
    """执行全量数据同步"""
    results = {}

    # 错误进化 → 自学习
    n1 = sync_errors_to_learn()
    results["错误→学习"] = n1

    # 自愈系统 → 自学习
    n2 = sync_heal_to_learn()
    results["自愈→学习"] = n2

    # Cron错误 → 自学习
    n3 = sync_cron_to_learn()
    results["Cron→学习"] = n3

    # 自学习 → 自愈系统
    n4 = inform_heal_from_learn()
    results["学习→自愈"] = len(n4)

    # 自学习 → 错误进化
    n5 = inform_error_evo_from_learn()
    results["学习→错误"] = len(n5)

    # 记忆系统 → 自学习（冲突检测）
    conflicts = memory_evolve.detect_conflicts()
    if conflicts:
        for c in conflicts:
            learn_evolve.record_lesson(
                "error", "记忆冲突",
                f"发现{c['topic']}矛盾: {', '.join(v[1] for v in c['values'])}",
                priority="high"
            )
        results["记忆→学习"] = len(conflicts)
    else:
        results["记忆→学习"] = 0

    # 复盘系统 → 自学习（失败决策）
    review_db = load_json_safe(REVIEW_DB, {"decisions": {}})
    for did, d in review_db.get("decisions", {}).items():
        if d.get("score") is not None and d["score"] < 0.4:
            summary = f"复盘低分: {d.get('topic','?')} - {d.get('decision','')[:40]}"
            existing = any(
                d.get("topic", "") in l.get("summary", "") and "复盘" in l.get("summary", "")
                for l in learn_evolve.load_learn_db().get("lessons", {}).values()
            )
            if not existing:
                learn_evolve.record_lesson(
                    "error", "复盘",
                    summary,
                    f"原因:{d.get('reason','')} 教训:{d.get('lesson','')}",
                    priority="high" if d["score"] < 0.3 else "medium"
                )
                results["复盘→学习"] = results.get("复盘→学习", 0) + 1

    # 更新状态
    save_json_safe(INTEL_STATE, {
        "last_sync": datetime.now().isoformat(),
        "sync_results": results
    })

    return results

def get_status():
    """获取统一状态"""
    db = learn_evolve.load_learn_db()
    knowledge = load_json_safe(ERROR_KNOWLEDGE, {"stats": {}})
    heal_evo = load_json_safe(HEAL_EVO, {})
    review = load_json_safe(REVIEW_DB, {"stats": {}})
    state = load_json_safe(INTEL_STATE, {})

    return {
        "self_learn": {
            "lessons": len(db.get("lessons", {})),
            "rules": len(db.get("rules", {})),
            "external": len(db.get("external_rules", [])),
            "cross_domain": sum(len(v) for v in db.get("cross_domain", {}).values()),
        },
        "error_evolution": {
            "total_errors": knowledge.get("stats", {}).get("total_errors", 0),
            "categories": len(knowledge.get("stats", {}).get("by_category", {})),
        },
        "self_heal": {
            "evolution_level": heal_evo.get("evolution_level", 1),
            "learned_rules": len(heal_evo.get("learned_rules", {})),
        },
        "review": {
            "decisions": review.get("stats", {}).get("total_decisions", 0),
            "predictions": review.get("stats", {}).get("total_predictions", 0),
            "avg_accuracy": review.get("stats", {}).get("avg_accuracy", 0),
            "avg_score": review.get("stats", {}).get("avg_decision_score", 0),
        },
        "last_sync": state.get("last_sync", "never"),
    }

# ===== CLI =====
if __name__ == "__main__":
    if "--sync" in sys.argv:
        print("🔄 执行全量同步...")
        results = full_sync()
        for k, v in results.items():
            icon = "✅" if v else "⬜"
            print(f"  {icon} {k}: {v}条")
        print("\n✅ 同步完成")

    elif "--status" in sys.argv:
        status = get_status()
        print("📊 统一智能层状态")
        print(f"  自学习: {status['self_learn']['lessons']}教训 / {status['self_learn']['rules']}规则")
        print(f"  错误进化: {status['error_evolution']['total_errors']}错误")
        print(f"  自愈系统: L{status['self_heal']['evolution_level']} / {status['self_heal']['learned_rules']}学习规则")
        print(f"  跨域迁移: {status['self_learn']['cross_domain']}条")
        print(f"  上次同步: {status['last_sync']}")

    elif "--feed" in sys.argv:
        print("📥 导入所有错误到学习系统...")
        n1 = sync_errors_to_learn()
        n2 = sync_heal_to_learn()
        n3 = sync_cron_to_learn()
        print(f"  错误进化: {n1} | 自愈系统: {n2} | Cron: {n3}")
        print(f"  总导入: {n1+n2+n3}条")

    elif "--inform" in sys.argv:
        print("📤 将学习结果通知所有系统...")
        n1 = inform_heal_from_learn()
        n2 = inform_error_evo_from_learn()
        print(f"  →自愈系统: {len(n1)}条 | →错误进化: {len(n2)}条")

    else:
        print(__doc__)


# ============================================================
# 方向C: 统一知识中枢 — 接收来自各系统的修复事件
# ============================================================
def receive_heal_event(event_type: str, data: dict):
    """
    方向C核心：统一知识中枢接收自愈系统事件
    事件类型:
      - fix_success: 修复成功 → 通知所有系统共享知识
      - fix_failed: 修复失败 → 导入学习系统找新解法
      - new_pattern: 发现新模式 → 广播到所有系统
    """
    db = learn_evolve.load_learn_db()
    event = {
        "timestamp": datetime.now().isoformat(),
        "source": "unified_heal",
        "type": event_type,
        "data": data
    }
    
    if event_type == "fix_success":
        # 修复成功 → 提炼为可复用知识
        pattern = data.get("pattern", "")
        job_name = data.get("job_id", "")[:8]
        fix_method = data.get("method", "unknown")
        learn_evolve.record_lesson(
            "success",
            f"自愈-{pattern}",
            f"{job_name}: {fix_method}",
            f"适用于{pattern}模式",
            priority="low"
        )
    
    elif event_type == "fix_failed":
        # 修复失败 → 通知所有系统寻找新解法
        pattern = data.get("pattern", "")
        symptom = data.get("symptom", "")
        learn_evolve.record_lesson(
            "error",
            f"自愈失败-{pattern}",
            symptom,
            "需要新解法，请分析其他可用工具",
            priority="high"
        )
    
    elif event_type == "new_pattern":
        # 新模式 → 广播到错误进化系统
        pattern_name = data.get("name", "")
        error_evolution.add_known_pattern(pattern_name, data)
    
    # 写入事件日志
    hub_events = WORKSPACE / "memory" / "intel-hub-events.jsonl"
    os.makedirs(WORKSPACE / "memory", exist_ok=True)
    with open(hub_events, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    # 更新intel hub状态
    state = load_json_safe(INTEL_STATE, {"last_sync": None, "sync_results": {}})
    state["last_heal_event"] = datetime.now().isoformat()
    save_json_safe(INTEL_STATE, state)


