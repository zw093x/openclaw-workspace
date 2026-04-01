#!/usr/bin/env python3
"""
自学习进化系统 v2.0 — 11层全进化

L1  自动记录    — 报错/纠正自动写入
L2  模式提取    — 从教训中提取通用规则
L3  规则验证    — 追踪规则是否被遵守
L4  优先级进化  — 频繁违反自动升级
L5  知识沉淀    — critical规则提升到 AGENTS.md
L6  跨域迁移    — 一条教训应用到所有领域
L7  反馈闭环    — 规则有效性追踪→有效则内化/无效则淘汰
L8  衰减遗忘    — 过时规则自动降级/归档
L9  外部学习    — 从社区/文档学习最佳实践
L10 预测犯错    — 识别场景→犯错前提醒
L11 元学习      — 学习哪种学习方式最有效

用法:
  python3 scripts/learn_evolve.py --record <type> <category> <summary> [details]
  python3 scripts/learn_evolve.py --check <context>   # L10: 场景检查
  python3 scripts/learn_evolve.py --migrate           # L6: 跨域迁移
  python3 scripts/learn_evolve.py --feedback          # L7: 反馈闭环
  python3 scripts/learn_evolve.py --decay             # L8: 衰减遗忘
  python3 scripts/learn_evolve.py --external          # L9: 外部学习
  python3 scripts/learn_evolve.py --meta              # L11: 元学习
  python3 scripts/learn_evolve.py --analyze           # L2: 模式分析
  python3 scripts/learn_evolve.py --apply             # L5: 提升规则
  python3 scripts/learn_evolve.py --report            # 完整报告
  python3 scripts/learn_evolve.py --track <id>        # L3: 追踪使用
"""

import json
import os
import sys
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
LEARNINGS_FILE = WORKSPACE / ".learnings" / "LEARNINGS.md"
LEARN_DB = WORKSPACE / "memory" / "learn-db.json"
LEARN_LOG = WORKSPACE / "memory" / "learn-log.jsonl"
META_LOG = WORKSPACE / "memory" / "learn-meta.json"
AGENTS_FILE = WORKSPACE / "AGENTS.md"

# ===== 工具函数 =====
def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default or {}

def save_json(path, data):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_log(entry):
    entry["ts"] = datetime.now().isoformat()
    os.makedirs(LEARN_LOG.parent, exist_ok=True)
    with open(LEARN_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_learn_db():
    return load_json(LEARN_DB, {
        "lessons": {},
        "rules": {},
        "stats": {"total_recorded": 0, "corrections": 0, "errors": 0, "feature_requests": 0},
        "effectiveness": {},
        "cross_domain": {},      # L6: 跨域映射
        "decay_state": {},       # L8: 衰减状态
        "external_rules": [],    # L9: 外部学习规则
        "predictions": [],       # L10: 预测记录
        "meta_stats": {}         # L11: 元学习统计
    })

def save_learn_db(db):
    save_json(LEARN_DB, db)

# ===== L1: 自动记录 =====
def record_lesson(lesson_type, category, summary, details="", priority="medium", files=None, domains=None):
    """自动记录教训（增强：支持跨域标签）"""
    db = load_learn_db()
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    seq = db["stats"]["total_recorded"] + 1
    lid = f"LRN-{date_str}-{seq:03d}"

    lesson = {
        "id": lid,
        "type": lesson_type,
        "category": category,
        "summary": summary,
        "details": details,
        "priority": priority,
        "files": files or [],
        "domains": domains or [category],  # L6: 关联的领域
        "created": now.isoformat(),
        "last_triggered": now.isoformat(),
        "applied_count": 0,
        "violated_count": 0,
        "status": "pending",
        "confidence": 0.5  # L7: 初始置信度
    }

    db["lessons"][lid] = lesson
    db["stats"]["total_recorded"] += 1
    if lesson_type in ("correction", "error", "feature_request"):
        db["stats"][lesson_type + "s" if not lesson_type.endswith("s") else lesson_type] = \
            db["stats"].get(lesson_type + "s" if not lesson_type.endswith("s") else lesson_type, 0) + 1

    rule = _extract_rule(lesson)
    if rule:
        db["rules"][lid] = rule

    save_learn_db(db)
    append_log({"action": "record", "id": lid, "type": lesson_type, "category": category, "summary": summary})
    _append_to_learnings_md(lesson)
    return lid

def _extract_rule(lesson):
    """从教训中提取可执行规则"""
    summary = lesson.get("summary", "").lower()
    category = lesson.get("category", "")

    rule_templates = {
        "correction": {
            "交易": "涉及用户持仓操作前，必须先了解长期逻辑，验证后再给建议",
            "回复": "复杂任务先发确认消息，再执行",
            "记录": "用户告知的事实立即记录到文件，不重复询问",
            "分析": "自主完成分析，不将学习任务转嫁给用户",
            "信息": "信息来源必须标注可靠性等级（A-E级），核心结论需A/B级来源",
            "模型": "模型切换前必须先验证目标模型可用性",
            "推送": "单条推送聚焦1个结论，不超过10行",
            "减仓": "任何减仓操作前必须了解用户长期逻辑",
            "卖出": "卖出操作前先验证用户判断，不套用通用框架",
            "买入": "题材股建仓必须满足6项检查清单",
        },
        "error": {
            "cron": "cron任务超时→检查是否需要增大timeout-seconds",
            "网络": "网络错误→检查代理配置或切换备用源",
            "磁盘": "磁盘告警→清理tmp/日志/session文件",
            "api": "API错误→检查配额或限速，等待后重试",
            "技能": "技能更新超时→使用批量脚本+轮询",
            "飞书": "飞书连接异常→检查channelSummary和gateway延迟",
        },
        "best_practice": {
            "推送": "单条推送聚焦1个结论，不超过10行",
            "速度": "耗时>10秒的任务用子代理，主对话保持轻量",
            "批量": "非紧急操作批量处理，减少来回次数",
        }
    }

    templates = rule_templates.get(lesson.get("type", ""), {})
    for keyword, rule in templates.items():
        if keyword in summary or keyword in category:
            return {
                "rule": rule,
                "source": lesson["id"],
                "keyword": keyword,
                "created": lesson["created"],
                "applied": 0
            }
    return None

def _append_to_learnings_md(lesson):
    os.makedirs(LEARNINGS_FILE.parent, exist_ok=True)
    entry = f"\n## [{lesson['id']}] {lesson['type']}\n\n**Logged**: {lesson['created']}\n**Priority**: {lesson['priority']}\n**Status**: {lesson['status']}\n\n### Summary\n{lesson['summary']}\n\n### Details\n{lesson['details'] or 'N/A'}\n\n### Metadata\n- Source: auto_record\n- Tags: {lesson['category']}, {lesson['type']}\n---\n\n"
    with open(LEARNINGS_FILE, "a") as f:
        f.write(entry)

# ===== L2: 模式提取 =====
def analyze_patterns():
    db = load_learn_db()
    lessons = db.get("lessons", {})
    patterns = {"by_category": defaultdict(list), "by_type": defaultdict(list), "recurring_themes": [], "hot_spots": []}

    for lid, lesson in lessons.items():
        patterns["by_category"][lesson.get("category", "unknown")].append(lid)
        patterns["by_type"][lesson.get("type", "unknown")].append(lid)

    for cat, ids in patterns["by_category"].items():
        if len(ids) >= 3:
            patterns["recurring_themes"].append({"theme": cat, "count": len(ids), "lesson_ids": ids})

    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent = {lid: l for lid, l in lessons.items() if l.get("created", "") >= week_ago}
    recent_cats = Counter(l.get("category", "") for l in recent.values())
    for cat, count in recent_cats.most_common(3):
        if count >= 2:
            patterns["hot_spots"].append({"category": cat, "recent_count": count, "total_count": len(patterns["by_category"].get(cat, []))})

    return patterns

# ===== L3: 规则验证 =====
def track_rule_usage(rule_id, applied=True):
    db = load_learn_db()
    effectiveness = db.get("effectiveness", {})
    if rule_id not in effectiveness:
        effectiveness[rule_id] = {"applied": 0, "violated": 0, "effective": 0}
    if applied:
        effectiveness[rule_id]["applied"] += 1
        effectiveness[rule_id]["effective"] += 1
    else:
        effectiveness[rule_id]["violated"] += 1
    db["effectiveness"] = effectiveness
    save_learn_db(db)

# ===== L4: 优先级进化 =====
def evolve_priorities():
    db = load_learn_db()
    lessons = db.get("lessons", {})
    changes = []
    for lid, lesson in lessons.items():
        priority = lesson.get("priority", "medium")
        violated = lesson.get("violated_count", 0)
        if violated >= 3 and priority == "medium":
            lesson["priority"] = "high"
            changes.append(f"{lid} → high")
        elif violated >= 5 and priority == "high":
            lesson["priority"] = "critical"
            changes.append(f"{lid} → critical")
    save_learn_db(db)
    return changes

# ===== L5: 知识沉淀 =====
def apply_to_rules():
    db = load_learn_db()
    lessons = db.get("lessons", {})
    rules = db.get("rules", {})
    promoted = []
    for lid, lesson in lessons.items():
        if lesson.get("priority") == "critical" and lesson.get("status") == "pending":
            rule_text = rules.get(lid, {}).get("rule", "")
            if rule_text:
                try:
                    agents_content = AGENTS_FILE.read_text()
                except:
                    agents_content = ""
                if lid not in agents_content and rule_text not in agents_content:
                    with open(AGENTS_FILE, "a") as f:
                        f.write(f"\n## {lesson['summary']}（{lid}）\n\n{rule_text}\n")
                    lesson["status"] = "promoted"
                    promoted.append({"id": lid, "summary": lesson["summary"]})
    save_learn_db(db)
    return promoted

# ===== L6: 跨域迁移 =====
def migrate_cross_domain():
    """将一条教训从源领域迁移到其他相关领域"""
    db = load_learn_db()
    lessons = db.get("lessons", {})
    cross_domain = db.get("cross_domain", {})

    # 领域关联映射
    domain_relations = {
        "交易": ["投资", "仓位", "建仓", "减仓"],
        "推送": ["日报", "播报", "通知", "提醒"],
        "回复": ["响应", "确认", "沟通"],
        "信息": ["搜索", "资讯", "新闻", "数据"],
        "cron": ["定时", "任务", "调度"],
        "磁盘": ["存储", "清理", "资源"],
    }

    migrations = []
    for lid, lesson in lessons.items():
        source_cat = lesson.get("category", "")
        rule_text = db.get("rules", {}).get(lid, {}).get("rule", "")

        if not rule_text:
            continue

        # 找到相关领域
        related = domain_relations.get(source_cat, [])
        existing_migrations = cross_domain.get(lid, [])

        for target in related:
            if target not in existing_migrations:
                # 检查目标领域是否已有类似规则
                target_has_rule = any(
                    target in l.get("category", "") or target in l.get("domains", [])
                    for l in lessons.values() if l["id"] != lid
                )

                if not target_has_rule:
                    cross_domain.setdefault(lid, []).append(target)
                    migrations.append({
                        "source": source_cat,
                        "target": target,
                        "rule": rule_text[:60],
                        "lesson_id": lid
                    })

    db["cross_domain"] = cross_domain
    save_learn_db(db)
    return migrations

# ===== L7: 反馈闭环 =====
def run_feedback_loop():
    """评估每条规则的有效性，自动内化或淘汰"""
    db = load_learn_db()
    lessons = db.get("lessons", {})
    effectiveness = db.get("effectiveness", {})
    changes = []

    for lid, lesson in lessons.items():
        stats = effectiveness.get(lid, {"applied": 0, "violated": 0})
        total = stats["applied"] + stats["violated"]

        if total < 3:
            continue  # 数据不足

        success_rate = stats["applied"] / total

        # 更新置信度
        lesson["confidence"] = round(success_rate, 2)

        if success_rate >= 0.9 and stats["applied"] >= 5:
            # 高效规则 → 内化（标记为已掌握）
            if lesson["status"] != "internalized":
                lesson["status"] = "internalized"
                changes.append(f"✅ {lid} 内化（成功率{success_rate:.0%}，{stats['applied']}次遵守）")

        elif success_rate < 0.3 and total >= 5:
            # 低效规则 → 淘汰
            if lesson["status"] != "deprecated":
                lesson["status"] = "deprecated"
                changes.append(f"❌ {lid} 淘汰（成功率{success_rate:.0%}，{stats['violated']}次违反）")

        elif success_rate < 0.5 and total >= 3:
            # 需优化 → 标记
            if lesson["status"] != "needs_review":
                lesson["status"] = "needs_review"
                changes.append(f"⚠️ {lid} 需优化（成功率{success_rate:.0%}）")

    save_learn_db(db)
    return changes

# ===== L8: 衰减遗忘 =====
def run_decay():
    """过时规则自动降级/归档"""
    db = load_learn_db()
    lessons = db.get("lessons", {})
    decay_state = db.get("decay_state", {})
    now = datetime.now()
    changes = []

    for lid, lesson in lessons.items():
        last_triggered = lesson.get("last_triggered", lesson.get("created", ""))
        if not last_triggered:
            continue

        try:
            last_dt = datetime.fromisoformat(last_triggered)
        except:
            continue

        days_inactive = (now - last_dt).days
        decay = decay_state.get(lid, {"level": 0, "last_check": now.isoformat()})

        if days_inactive >= 90 and lesson["status"] not in ("archived", "deprecated"):
            # 90天未触发 → 归档
            lesson["status"] = "archived"
            decay["level"] = 3
            changes.append(f"📦 {lid} 归档（{days_inactive}天未触发）")

        elif days_inactive >= 30 and lesson["priority"] not in ("low", "archived"):
            # 30天未触发 → 降级优先级
            old_priority = lesson["priority"]
            if old_priority == "critical":
                lesson["priority"] = "high"
            elif old_priority == "high":
                lesson["priority"] = "medium"
            elif old_priority == "medium":
                lesson["priority"] = "low"
            decay["level"] = 2
            changes.append(f"⬇️ {lid} 降级 {old_priority}→{lesson['priority']}（{days_inactive}天未触发）")

        elif days_inactive >= 14:
            # 14天未触发 → 标记待验证
            decay["level"] = 1
            # 不改变状态，仅标记

        decay["last_check"] = now.isoformat()
        decay_state[lid] = decay

    db["decay_state"] = decay_state
    save_learn_db(db)
    return changes

# ===== L9: 外部学习 =====
def learn_externally():
    """从内置知识库学习最佳实践"""
    db = load_learn_db()
    external = db.get("external_rules", [])

    # 内置最佳实践库（可扩展）
    best_practices = [
        {"domain": "系统运维", "rule": "定期清理日志，防止单文件超过100MB", "source": "ops_best_practice"},
        {"domain": "系统运维", "rule": "磁盘使用率超过85%时主动清理", "source": "ops_best_practice"},
        {"domain": "投资分析", "rule": "建仓前必须确认止损位，距离不超过5%", "source": "trading_best_practice"},
        {"domain": "投资分析", "rule": "题材股持仓不超过总仓位10%", "source": "trading_best_practice"},
        {"domain": "自动化", "rule": "定时任务失败3次应通知人工介入", "source": "automation_best_practice"},
        {"domain": "自动化", "rule": "批量操作之间加入间隔，避免被限速", "source": "automation_best_practice"},
        {"domain": "AI使用", "rule": "复杂推理用大模型，日常对话用快模型", "source": "ai_best_practice"},
        {"domain": "AI使用", "rule": "上下文超过2小时主动建议开新会话", "source": "ai_best_practice"},
        {"domain": "安全", "rule": "敏感信息不写入日志文件", "source": "security_best_practice"},
        {"domain": "安全", "rule": "外部操作前必须确认", "source": "security_best_practice"},
    ]

    imported = []
    existing_summaries = {l.get("summary", "") for l in db.get("lessons", {}).values()}
    existing_sources = {r.get("source", "") for r in external}

    for bp in best_practices:
        if bp["source"] not in existing_sources:
            # 检查是否已有类似规则
            if not any(bp["rule"][:20] in s for s in existing_summaries):
                external.append(bp)
                imported.append(bp)

    db["external_rules"] = external
    save_learn_db(db)
    return imported

# ===== L10: 预测犯错 =====
def check_context(context_text):
    """L10: 识别当前场景，匹配可能犯的错误"""
    db = load_learn_db()
    lessons = db.get("lessons", {})
    rules = db.get("rules", {})
    context_lower = context_text.lower()

    warnings = []

    for lid, lesson in lessons.items():
        if lesson.get("status") == "deprecated":
            continue

        # 关键词匹配
        keywords = [lesson.get("category", ""), lesson.get("summary", "")]
        matched = any(kw.lower() in context_lower for kw in keywords if kw)

        # 特殊场景匹配
        if not matched:
            scenario_patterns = {
                "交易决策": ["减仓", "卖出", "买入", "建仓", "清仓", "加仓"],
                "信息发布": ["推送", "播报", "日报", "通知"],
                "系统变更": ["修改", "切换", "更新", "重启", "部署"],
            }
            for scenario, triggers in scenario_patterns.items():
                if any(t in context_lower for t in triggers):
                    if scenario in lesson.get("category", "") or any(
                        t in lesson.get("summary", "").lower() for t in triggers
                    ):
                        matched = True
                        break

        if matched:
            rule_text = rules.get(lid, {}).get("rule", "")
            severity = lesson.get("priority", "medium")
            warnings.append({
                "lesson_id": lid,
                "rule": rule_text or lesson.get("summary", ""),
                "severity": severity,
                "confidence": lesson.get("confidence", 0.5),
                "category": lesson.get("category", "")
            })

    # 按严重性排序
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    warnings.sort(key=lambda x: severity_order.get(x["severity"], 4))

    return warnings

# ===== L11: 元学习 =====
def run_meta_learning():
    """学习哪种学习方式最有效"""
    db = load_learn_db()
    lessons = db.get("lessons", {})
    effectiveness = db.get("effectiveness", {})
    meta = db.get("meta_stats", {})

    # 按类型分析学习效果
    type_stats = defaultdict(lambda: {"count": 0, "promoted": 0, "internalized": 0, "deprecated": 0, "avg_confidence": 0})
    for lid, lesson in lessons.items():
        ltype = lesson.get("type", "unknown")
        stats = type_stats[ltype]
        stats["count"] += 1
        status = lesson.get("status", "pending")
        if status == "promoted":
            stats["promoted"] += 1
        elif status == "internalized":
            stats["internalized"] += 1
        elif status == "deprecated":
            stats["deprecated"] += 1
        stats["avg_confidence"] += lesson.get("confidence", 0.5)

    for ltype, stats in type_stats.items():
        if stats["count"] > 0:
            stats["avg_confidence"] = round(stats["avg_confidence"] / stats["count"], 2)
            success = stats["promoted"] + stats["internalized"]
            stats["success_rate"] = round(success / stats["count"], 2) if stats["count"] > 0 else 0

    # 按类别分析学习效果
    cat_effectiveness = defaultdict(lambda: {"learned": 0, "repeated": 0})
    for lid, lesson in lessons.items():
        cat = lesson.get("category", "")
        violated = lesson.get("violated_count", 0)
        cat_effectiveness[cat]["learned"] += 1
        if violated > 0:
            cat_effectiveness[cat]["repeated"] += violated

    # 找出学习效率最高的类型
    best_type = max(type_stats.items(), key=lambda x: x[1].get("success_rate", 0)) if type_stats else ("none", {})
    worst_cats = sorted(cat_effectiveness.items(), key=lambda x: x[1]["repeated"], reverse=True)[:3]

    meta["type_stats"] = dict(type_stats)
    meta["category_effectiveness"] = dict(cat_effectiveness)
    meta["best_learning_type"] = best_type[0] if best_type else "none"
    meta["hardest_categories"] = [c[0] for c in worst_cats if c[1]["repeated"] > 0]
    meta["last_run"] = datetime.now().isoformat()

    # 生成建议
    recommendations = []
    if best_type[0] != "none":
        recommendations.append(f"学习效率最高: {best_type[0]}类教训（成功率{best_type[1].get('success_rate',0):.0%}）")

    for cat, stats in worst_cats:
        if stats["repeated"] >= 3:
            recommendations.append(f"'{cat}'反复出错（{stats['repeated']}次），需要更严格的学习机制")

    meta["recommendations"] = recommendations
    db["meta_stats"] = meta
    save_learn_db(db)

    return meta

# ===== 完整报告 =====
def generate_report():
    db = load_learn_db()
    lessons = db.get("lessons", {})
    rules = db.get("rules", {})
    stats = db.get("stats", {})
    effectiveness = db.get("effectiveness", {})
    cross_domain = db.get("cross_domain", {})
    decay_state = db.get("decay_state", {})
    external = db.get("external_rules", [])
    meta = db.get("meta_stats", {})

    lines = ["📚 **自学习进化系统 v2.0 报告**", ""]

    # 基础统计
    lines.append(f"📝 教训: {stats.get('total_recorded', 0)} | 规则: {len(rules)} | 外部规则: {len(external)}")

    # 各层状态
    status_counts = Counter(l.get("status", "pending") for l in lessons.values())
    lines.append(f"📊 状态: 待处理{status_counts.get('pending',0)} | 已应用{status_counts.get('promoted',0)} | 已内化{status_counts.get('internalized',0)} | 已淘汰{status_counts.get('deprecated',0)} | 已归档{status_counts.get('archived',0)}")

    # 最近教训
    recent = sorted(lessons.values(), key=lambda x: x.get("created", ""), reverse=True)[:5]
    if recent:
        lines.append("")
        lines.append("📋 **最近教训**")
        for l in recent:
            icon = {"correction": "🔴", "error": "⚠️", "best_practice": "✅", "knowledge_gap": "❓"}.get(l.get("type"), "•")
            conf = l.get("confidence", 0.5)
            lines.append(f"  {icon} [{l.get('id','')}] {l.get('summary','')[:50]} (置信度{conf:.0%})")

    # L6 跨域迁移
    if cross_domain:
        lines.append("")
        lines.append(f"🔗 **跨域迁移: {sum(len(v) for v in cross_domain.values())}条**")
        for lid, targets in list(cross_domain.items())[:3]:
            lines.append(f"  • {lid} → {', '.join(targets)}")

    # L7 反馈闭环
    if effectiveness:
        lines.append("")
        lines.append("🔄 **规则有效性**")
        for rid, eff in list(effectiveness.items())[:3]:
            total = eff["applied"] + eff["violated"]
            rate = eff["applied"] / total if total > 0 else 0
            icon = "✅" if rate > 0.7 else "⚠️" if rate > 0.4 else "❌"
            lines.append(f"  {icon} {rid}: 遵守{eff['applied']}次 / 违反{eff['violated']}次 ({rate:.0%})")

    # L8 衰减状态
    archived = [lid for lid, l in lessons.items() if l.get("status") == "archived"]
    if archived:
        lines.append(f"📦 **已归档: {len(archived)}条**")

    # L9 外部规则
    if external:
        lines.append(f"🌐 **外部学习规则: {len(external)}条**")
        for r in external[:3]:
            lines.append(f"  • [{r.get('domain','')}] {r.get('rule','')[:50]}")

    # L11 元学习
    if meta.get("recommendations"):
        lines.append("")
        lines.append("🧠 **元学习建议**")
        for r in meta["recommendations"]:
            lines.append(f"  • {r}")

    # 进化等级
    level = 1
    if lessons: level = 2
    if rules: level = 3
    if effectiveness: level = 4
    if cross_domain: level = max(level, 6)
    if any(l.get("status") == "internalized" for l in lessons.values()): level = max(level, 7)
    if any(l.get("status") == "archived" for l in lessons.values()): level = max(level, 8)
    if external: level = max(level, 9)
    if meta: level = max(level, 11)

    lines.append("")
    lines.append(f"🧬 进化等级: L{level}")

    return "\n".join(lines)

# ===== CLI =====
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "--record":
        if len(args) >= 4:
            lid = record_lesson(args[1], args[2], args[3], args[4] if len(args) > 4 else "")
            print(f"✅ 已记录: {lid}")
        else:
            print("用法: --record <type> <category> <summary> [details]")

    elif cmd == "--check":
        if len(args) >= 2:
            context = " ".join(args[1:])
            warnings = check_context(context)
            if warnings:
                print(f"⚠️ 场景'{context}'匹配到 {len(warnings)} 条历史教训：")
                for w in warnings:
                    icon = {"critical": "🔴", "high": "🟡"}.get(w["severity"], "⚪")
                    print(f"  {icon} [{w['lesson_id']}] {w['rule'][:60]}")
            else:
                print("✅ 无匹配的历史教训")
        else:
            print("用法: --check <context_text>")

    elif cmd == "--migrate":
        migrations = migrate_cross_domain()
        if migrations:
            print(f"🔗 跨域迁移 {len(migrations)} 条：")
            for m in migrations:
                print(f"  • {m['source']}→{m['target']}: {m['rule'][:40]}")
        else:
            print("ℹ️ 暂无需要迁移的规则")

    elif cmd == "--feedback":
        changes = run_feedback_loop()
        if changes:
            print("🔄 反馈闭环结果：")
            for c in changes:
                print(f"  {c}")
        else:
            print("ℹ️ 数据不足，暂无变化")

    elif cmd == "--decay":
        changes = run_decay()
        if changes:
            print("⏳ 衰减遗忘结果：")
            for c in changes:
                print(f"  {c}")
        else:
            print("✅ 无过时规则")

    elif cmd == "--external":
        imported = learn_externally()
        if imported:
            print(f"🌐 导入 {len(imported)} 条外部规则：")
            for r in imported:
                print(f"  • [{r['domain']}] {r['rule'][:50]}")
        else:
            print("ℹ️ 外部规则已全部导入")

    elif cmd == "--meta":
        meta = run_meta_learning()
        print("🧠 元学习分析完成")
        if meta.get("recommendations"):
            for r in meta["recommendations"]:
                print(f"  • {r}")

    elif cmd == "--analyze":
        patterns = analyze_patterns()
        print(json.dumps(patterns, ensure_ascii=False, indent=2, default=str))

    elif cmd == "--apply":
        promoted = apply_to_rules()
        if promoted:
            print(f"✅ 提升 {len(promoted)} 条规则到 AGENTS.md")
            for p in promoted:
                print(f"  • {p['id']}: {p['summary']}")
        else:
            print("ℹ️ 无需要提升的规则")

    elif cmd == "--track":
        if len(args) >= 2:
            rule_id = args[1]
            violated = "--violated" in args
            track_rule_usage(rule_id, applied=not violated)
            print(f"✅ 已追踪: {rule_id} ({'违反' if violated else '遵守'})")
        else:
            print("用法: --track <rule_id> [--violated]")

    elif cmd == "--report":
        print(generate_report())

    elif cmd == "--evolve":
        # 执行全部进化
        print("🧬 执行全量进化...")
        migrations = migrate_cross_domain()
        print(f"  L6 跨域迁移: {len(migrations)}条")
        feedback = run_feedback_loop()
        print(f"  L7 反馈闭环: {len(feedback)}条变化")
        decay = run_decay()
        print(f"  L8 衰减遗忘: {len(decay)}条变化")
        imported = learn_externally()
        print(f"  L9 外部学习: {len(imported)}条导入")
        meta = run_meta_learning()
        print(f"  L11 元学习: 分析完成")
        promoted = apply_to_rules()
        print(f"  L5 知识沉淀: {len(promoted)}条提升")
        print(f"\n🧬 进化完成")

    else:
        print(__doc__)
