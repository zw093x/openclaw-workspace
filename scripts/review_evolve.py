#!/usr/bin/env python3
"""
复盘进化系统 v1.0 — 7层进化

R1 决策追踪    — 记录每个决策→结果→教训
R2 准确率分析  — 预测vs实际，自动统计
R3 模式识别    — 发现成功/失败规律
R4 策略优化    — 基于结果调整策略
R5 跨域学习    — 一个领域的教训应用到其他领域
R6 预测性复盘  — 提前识别风险
R7 元复盘      — 复盘复盘系统本身

用法:
  python3 scripts/review_evolve.py --decide <topic> <decision> <reason>  # R1: 记录决策
  python3 scripts/review_evolve.py --outcome <id> <result> <score>       # R1: 记录结果
  python3 scripts/review_evolve.py --accuracy                            # R2: 准确率分析
  python3 scripts/review_evolve.py --patterns                            # R3: 模式识别
  python3 scripts/review_evolve.py --optimize                            # R4: 策略优化
  python3 scripts/review_evolve.py --cross                               # R5: 跨域学习
  python3 scripts/review_evolve.py --risks                               # R6: 风险识别
  python3 scripts/review_evolve.py --meta                                # R7: 元复盘
  python3 scripts/review_evolve.py --evolve                              # 全量进化
  python3 scripts/review_evolve.py --report                              # 报告
  python3 scripts/review_evolve.py --daily                               # 每日复盘模板
  python3 scripts/review_evolve.py --weekly                              # 每周复盘模板
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
REVIEW_DB = WORKSPACE / "memory" / "review-db.json"
REVIEW_LOG = WORKSPACE / "memory" / "review-log.jsonl"
ACCURACY_FILE = WORKSPACE / "memory" / "analysis-accuracy.json"
TRADE_JOURNAL = WORKSPACE / "memory" / "trade-journal.md"
STOCK_PORTFOLIO = WORKSPACE / "memory" / "stock-portfolio.md"

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
    os.makedirs(REVIEW_LOG.parent, exist_ok=True)
    with open(REVIEW_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_review_db():
    return load_json(REVIEW_DB, {
        "decisions": {},       # id -> {topic, decision, reason, ts, outcome, score}
        "predictions": {},     # id -> {topic, prediction, confidence, ts, actual, accuracy}
        "patterns": {},        # 发现的规律
        "strategy_scores": {}, # 策略评分
        "cross_lessons": [],   # 跨域教训
        "risks": [],           # 识别的风险
        "stats": {
            "total_decisions": 0,
            "total_predictions": 0,
            "avg_accuracy": 0,
            "avg_decision_score": 0
        }
    })

def save_review_db(db):
    save_json(REVIEW_DB, db)

# ===== R1: 决策追踪 =====
def record_decision(topic, decision, reason=""):
    """记录一个决策"""
    db = load_review_db()
    now = datetime.now()
    did = f"DEC-{now.strftime('%Y%m%d')}-{db['stats']['total_decisions']+1:03d}"

    db["decisions"][did] = {
        "id": did,
        "topic": topic,
        "decision": decision,
        "reason": reason,
        "ts": now.isoformat(),
        "outcome": None,
        "score": None,
        "lesson": None
    }
    db["stats"]["total_decisions"] += 1
    save_review_db(db)
    append_log({"action": "decision", "id": did, "topic": topic, "decision": decision[:60]})
    return did

def record_outcome(decision_id, result, score=0.5, lesson=""):
    """记录决策结果"""
    db = load_review_db()
    d = db["decisions"].get(decision_id)
    if not d:
        return False

    d["outcome"] = result
    d["score"] = score  # 0-1，越高越好
    d["lesson"] = lesson

    # 更新平均分
    scored = [x for x in db["decisions"].values() if x.get("score") is not None]
    if scored:
        db["stats"]["avg_decision_score"] = round(sum(x["score"] for x in scored) / len(scored), 2)

    save_review_db(db)
    append_log({"action": "outcome", "id": decision_id, "score": score})
    return True

def record_prediction(topic, prediction, confidence=0.5):
    """记录一个预测"""
    db = load_review_db()
    now = datetime.now()
    pid = f"PRED-{now.strftime('%Y%m%d')}-{db['stats']['total_predictions']+1:03d}"

    db["predictions"][pid] = {
        "id": pid,
        "topic": topic,
        "prediction": prediction,
        "confidence": confidence,
        "ts": now.isoformat(),
        "actual": None,
        "accuracy": None
    }
    db["stats"]["total_predictions"] += 1
    save_review_db(db)
    return pid

def record_actual(prediction_id, actual_result, accuracy=0.5):
    """记录预测的实际结果"""
    db = load_review_db()
    p = db["predictions"].get(prediction_id)
    if not p:
        return False

    p["actual"] = actual_result
    p["accuracy"] = accuracy

    # 更新平均准确率
    verified = [x for x in db["predictions"].values() if x.get("accuracy") is not None]
    if verified:
        db["stats"]["avg_accuracy"] = round(sum(x["accuracy"] for x in verified) / len(verified), 2)

    save_review_db(db)
    return True

# ===== R2: 准确率分析 =====
def analyze_accuracy():
    """分析预测和决策的准确率"""
    db = load_review_db()
    predictions = db.get("predictions", {})
    decisions = db.get("decisions", {})

    # 预测准确率
    pred_verified = [p for p in predictions.values() if p.get("accuracy") is not None]
    pred_by_topic = defaultdict(list)
    for p in pred_verified:
        pred_by_topic[p["topic"]].append(p["accuracy"])

    topic_accuracy = {}
    for topic, scores in pred_by_topic.items():
        topic_accuracy[topic] = {
            "count": len(scores),
            "avg_accuracy": round(sum(scores) / len(scores), 2),
            "trend": "↗️" if len(scores) >= 2 and scores[-1] > scores[0] else "↘️" if len(scores) >= 2 and scores[-1] < scores[0] else "→"
        }

    # 决策质量
    dec_verified = [d for d in decisions.values() if d.get("score") is not None]
    dec_by_topic = defaultdict(list)
    for d in dec_verified:
        dec_by_topic[d["topic"]].append(d["score"])

    topic_quality = {}
    for topic, scores in dec_by_topic.items():
        topic_quality[topic] = {
            "count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "good": sum(1 for s in scores if s >= 0.7),
            "bad": sum(1 for s in scores if s < 0.4)
        }

    # 综合评分
    total_verified = len(pred_verified) + len(dec_verified)
    if total_verified > 0:
        total_score = (sum(p["accuracy"] for p in pred_verified) + sum(d["score"] for d in dec_verified)) / total_verified
    else:
        total_score = 0

    return {
        "prediction_accuracy": topic_accuracy,
        "decision_quality": topic_quality,
        "overall_score": round(total_score, 2),
        "total_verified": total_verified
    }

# ===== R3: 模式识别 =====
def recognize_patterns():
    """发现成功/失败的规律"""
    db = load_review_db()
    decisions = db.get("decisions", {})
    predictions = db.get("predictions", {})

    patterns = {"success": [], "failure": [], "neutral": []}

    # 分析决策模式
    for did, d in decisions.items():
        if d.get("score") is None:
            continue

        decision = d.get("decision", "").lower()
        reason = d.get("reason", "").lower()
        score = d["score"]

        if score >= 0.7:
            # 成功模式
            if "验证" in reason or "分析" in reason:
                patterns["success"].append({
                    "type": "decision",
                    "pattern": "先验证后决策",
                    "example": d["decision"][:50],
                    "score": score
                })
            if "长期" in reason or "结构性" in reason:
                patterns["success"].append({
                    "type": "decision",
                    "pattern": "基于长期逻辑",
                    "example": d["decision"][:50],
                    "score": score
                })

        elif score < 0.4:
            # 失败模式
            if "追" in decision or "追高" in reason:
                patterns["failure"].append({
                    "type": "decision",
                    "pattern": "追高/追涨",
                    "example": d["decision"][:50],
                    "score": score
                })
            if "没验证" in reason or "直接" in reason:
                patterns["failure"].append({
                    "type": "decision",
                    "pattern": "未验证就执行",
                    "example": d["decision"][:50],
                    "score": score
                })

    # 保存到数据库
    db["patterns"] = {
        "success_patterns": patterns["success"][:5],
        "failure_patterns": patterns["failure"][:5],
        "last_updated": datetime.now().isoformat()
    }
    save_review_db(db)

    return {
        "success": len(patterns["success"]),
        "failure": len(patterns["failure"]),
        "details": patterns
    }

# ===== R4: 策略优化 =====
def optimize_strategies():
    """基于复盘结果优化策略"""
    db = load_review_db()
    decisions = db.get("decisions", {})
    patterns = db.get("patterns", {})

    optimizations = []

    # 找出低分决策的主题
    low_score_topics = defaultdict(list)
    for did, d in decisions.items():
        if d.get("score") is not None and d["score"] < 0.5:
            low_score_topics[d["topic"]].append(d)

    for topic, decs in low_score_topics.items():
        if len(decs) >= 2:
            # 同一主题多次低分，需要优化
            common_issues = []
            for d in decs:
                reason = d.get("reason", "")
                if "没验证" in reason or "直接" in reason:
                    common_issues.append("缺乏验证")
                if "追" in d.get("decision", ""):
                    common_issues.append("追高")

            if common_issues:
                optimizations.append({
                    "topic": topic,
                    "issue": Counter(common_issues).most_common(1)[0][0],
                    "occurrences": len(decs),
                    "suggestion": f"在'{topic}'决策前增加验证步骤"
                })

    # 保存
    db["strategy_scores"] = {o["topic"]: o for o in optimizations}
    save_review_db(db)

    return optimizations

# ===== R5: 跨域学习 =====
def cross_domain_learning():
    """将一个领域的教训应用到其他领域"""
    db = load_review_db()
    decisions = db.get("decisions", {})
    patterns = db.get("patterns", {})

    cross_lessons = []

    # 成功模式跨域推广
    for p in patterns.get("success_patterns", []):
        pattern = p["pattern"]
        source = p.get("example", "")

        # 检查其他领域是否也可以用
        domains = set(d.get("topic", "") for d in decisions.values())
        for domain in domains:
            if domain and domain not in source:
                # 检查该领域是否有失败记录
                domain_failures = [
                    d for d in decisions.values()
                    if d.get("topic") == domain and d.get("score", 1) < 0.5
                ]
                if domain_failures:
                    cross_lessons.append({
                        "pattern": pattern,
                        "source_example": source[:50],
                        "target_domain": domain,
                        "reason": f"{domain}存在失败记录，可应用成功模式"
                    })

    # 失败模式跨域警告
    for p in patterns.get("failure_patterns", []):
        pattern = p["pattern"]
        cross_lessons.append({
            "pattern": f"⚠️ 避免: {pattern}",
            "source_example": p.get("example", "")[:50],
            "target_domain": "所有领域",
            "reason": "失败模式需全局警惕"
        })

    db["cross_lessons"] = cross_lessons[:10]
    save_review_db(db)

    return cross_lessons

# ===== R6: 风险识别 =====
def identify_risks():
    """基于复盘数据识别当前风险"""
    db = load_review_db()
    decisions = db.get("decisions", {})
    risks = []
    now = datetime.now()

    # 1. 未出结果的决策（悬而未决）
    pending = [d for d in decisions.values() if d.get("outcome") is None]
    for d in pending:
        try:
            created = datetime.fromisoformat(d["ts"])
            days_open = (now - created).days
            if days_open > 3:
                risks.append({
                    "type": "pending_decision",
                    "severity": "medium",
                    "message": f"决策'{d['topic']}'已{days_open}天未出结果",
                    "action": "跟进结果并记录"
                })
        except:
            pass

    # 2. 连续低分主题
    recent_decisions = sorted(
        [d for d in decisions.values() if d.get("score") is not None],
        key=lambda x: x.get("ts", ""),
        reverse=True
    )[:10]

    topic_scores = defaultdict(list)
    for d in recent_decisions:
        topic_scores[d["topic"]].append(d["score"])

    for topic, scores in topic_scores.items():
        if len(scores) >= 2 and all(s < 0.5 for s in scores[:2]):
            risks.append({
                "type": "declining_topic",
                "severity": "high",
                "message": f"'{topic}'连续{len(scores[:2])}次低分",
                "action": f"暂停'{topic}'新决策，先复盘根因"
            })

    # 3. 从交易日志检测风险
    if TRADE_JOURNAL.exists():
        content = TRADE_JOURNAL.read_text()
        if "亏损" in content and "教训" not in content:
            risks.append({
                "type": "unrecorded_loss",
                "severity": "medium",
                "message": "交易日志存在亏损记录但缺少教训总结",
                "action": "补充教训到交易日志"
            })

    db["risks"] = risks
    save_review_db(db)

    return risks

# ===== R7: 元复盘 =====
def meta_review():
    """复盘复盘系统本身"""
    db = load_review_db()
    stats = db.get("stats", {})

    meta = {
        "review_health": {},
        "suggestions": []
    }

    # 复盘覆盖率
    total_decisions = stats.get("total_decisions", 0)
    verified = len([d for d in db.get("decisions", {}).values() if d.get("outcome") is not None])
    coverage = verified / total_decisions if total_decisions > 0 else 0

    meta["review_health"]["decision_coverage"] = round(coverage, 2)
    meta["review_health"]["total_decisions"] = total_decisions
    meta["review_health"]["verified_decisions"] = verified

    # 建议
    if coverage < 0.5 and total_decisions >= 3:
        meta["suggestions"].append(f"决策复盘覆盖率仅{coverage:.0%}，需加强结果追踪")

    if stats.get("avg_accuracy", 0) < 0.5 and stats.get("total_predictions", 0) >= 3:
        meta["suggestions"].append(f"预测准确率{stats['avg_accuracy']:.0%}偏低，需改进分析方法")

    # 复盘频率
    if REVIEW_LOG.exists():
        try:
            lines = REVIEW_LOG.read_text().strip().split("\n")
            recent = [l for l in lines if l and datetime.fromisoformat(json.loads(l).get("ts", "")).date() >= (datetime.now() - timedelta(days=7)).date()]
            meta["review_health"]["weekly_reviews"] = len(recent)
            if len(recent) < 3:
                meta["suggestions"].append("本周复盘次数不足3次，建议增加复盘频率")
        except:
            pass

    return meta

# ===== 模板生成 =====
def generate_daily_template():
    """生成每日复盘模板"""
    now = datetime.now()
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]

    template = f"""# 每日复盘 — {now.strftime('%Y-%m-%d')} {weekday}

## 今日大事
-

## 持仓复盘
| 股票 | 今日涨跌 | 原因 | 操作 |
|------|---------|------|------|
| 中国船舶 | | | |
| 中国动力 | | | |

## 决策记录
- 决策:
- 原因:
- 结果:

## 学习进度
-

## 明日计划
-

## 教训总结
-
"""
    return template

def generate_weekly_template():
    """生成每周复盘模板"""
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())

    template = f"""# 每周复盘 — {week_start.strftime('%m/%d')}~{now.strftime('%m/%d')}

## 本周总结
### 股票表现
| 股票 | 周初 | 周末 | 周涨跌 | 操作 |
|------|------|------|--------|------|
| 中国船舶 | | | | |
| 中国动力 | | | | |

### 准确率统计
- 预测准确率: {load_review_db().get('stats',{}).get('avg_accuracy',0):.0%}
- 决策质量: {load_review_db().get('stats',{}).get('avg_decision_score',0):.0%}

### 成功决策
-

### 失败决策
-

### 教训
-

## 下周展望
### 关注点
-

### 风险点
-

### 学习目标
-
"""
    return template

# ===== 全量进化 =====
def full_evolve():
    """执行全量复盘进化"""
    results = {}

    print("  R1 决策追踪...", end=" ")
    db = load_review_db()
    results["R1_决策"] = f"{db['stats']['total_decisions']}个"
    print(f"✅ {results['R1_决策']}")

    print("  R2 准确率分析...", end=" ")
    r2 = analyze_accuracy()
    results["R2_准确率"] = f"{r2['overall_score']:.0%}"
    print(f"✅ {results['R2_准确率']}")

    print("  R3 模式识别...", end=" ")
    r3 = recognize_patterns()
    results["R3_模式"] = f"成功{r3['success']}个/失败{r3['failure']}个"
    print(f"✅ {results['R3_模式']}")

    print("  R4 策略优化...", end=" ")
    r4 = optimize_strategies()
    results["R4_优化"] = f"{len(r4)}个建议"
    print(f"✅ {results['R4_优化']}")

    print("  R5 跨域学习...", end=" ")
    r5 = cross_domain_learning()
    results["R5_跨域"] = f"{len(r5)}条"
    print(f"✅ {results['R5_跨域']}")

    print("  R6 风险识别...", end=" ")
    r6 = identify_risks()
    results["R6_风险"] = f"{len(r6)}个"
    print(f"✅ {results['R6_风险']}")

    print("  R7 元复盘...", end=" ")
    r7 = meta_review()
    results["R7_元复盘"] = f"{len(r7['suggestions'])}条建议"
    print(f"✅ {results['R7_元复盘']}")

    return results

# ===== 报告 =====
def generate_report():
    db = load_review_db()
    stats = db.get("stats", {})
    accuracy = analyze_accuracy()
    patterns = db.get("patterns", {})
    risks = identify_risks()
    meta = meta_review()

    lines = ["📊 **复盘进化系统报告**", ""]

    # 总览
    lines.append(f"📝 决策: {stats.get('total_decisions',0)}个 | 预测: {stats.get('total_predictions',0)}个")
    lines.append(f"📈 平均准确率: {stats.get('avg_accuracy',0):.0%} | 决策质量: {stats.get('avg_decision_score',0):.0%}")

    # 分主题准确率
    topic_acc = accuracy.get("prediction_accuracy", {})
    if topic_acc:
        lines.append("")
        lines.append("📊 **分主题准确率**")
        for topic, info in topic_acc.items():
            lines.append(f"  • {topic}: {info['avg_accuracy']:.0%} ({info['count']}次) {info['trend']}")

    # 成功/失败模式
    if patterns.get("success_patterns"):
        lines.append("")
        lines.append("✅ **成功模式**")
        for p in patterns["success_patterns"][:3]:
            lines.append(f"  • {p['pattern']}: {p['example'][:40]}")

    if patterns.get("failure_patterns"):
        lines.append("")
        lines.append("❌ **失败模式**")
        for p in patterns["failure_patterns"][:3]:
            lines.append(f"  • {p['pattern']}: {p['example'][:40]}")

    # 跨域教训
    cross = db.get("cross_lessons", [])
    if cross:
        lines.append("")
        lines.append(f"🔗 **跨域教训: {len(cross)}条**")
        for c in cross[:3]:
            lines.append(f"  • {c['pattern']} → {c['target_domain']}")

    # 风险
    if risks:
        lines.append("")
        lines.append("⚠️ **当前风险**")
        for r in risks:
            icon = "🔴" if r["severity"] == "high" else "🟡"
            lines.append(f"  {icon} {r['message']}")

    # 元复盘建议
    if meta.get("suggestions"):
        lines.append("")
        lines.append("💡 **改进建议**")
        for s in meta["suggestions"]:
            lines.append(f"  • {s}")

    return "\n".join(lines)

# ===== CLI =====
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "--report":
        print(generate_report())

    elif args[0] == "--decide" and len(args) >= 4:
        topic, decision = args[1], args[2]
        reason = args[3] if len(args) > 3 else ""
        did = record_decision(topic, decision, reason)
        print(f"✅ 决策已记录: {did}")

    elif args[0] == "--outcome" and len(args) >= 4:
        did, result = args[1], args[2]
        score = float(args[3]) if len(args) > 3 else 0.5
        lesson = args[4] if len(args) > 4 else ""
        ok = record_outcome(did, result, score, lesson)
        print(f"✅ 结果已记录" if ok else "❌ 决策ID不存在")

    elif args[0] == "--accuracy":
        r = analyze_accuracy()
        print(f"✅ 综合准确率: {r['overall_score']:.0%} ({r['total_verified']}个已验证)")
        for topic, info in r["prediction_accuracy"].items():
            print(f"  • {topic}: {info['avg_accuracy']:.0%} {info['trend']}")

    elif args[0] == "--patterns":
        r = recognize_patterns()
        print(f"✅ 成功模式: {r['success']}个, 失败模式: {r['failure']}个")
        for p in r["details"]["success"][:3]:
            print(f"  ✅ {p['pattern']}: {p['example'][:40]}")
        for p in r["details"]["failure"][:3]:
            print(f"  ❌ {p['pattern']}: {p['example'][:40]}")

    elif args[0] == "--optimize":
        r = optimize_strategies()
        print(f"✅ {len(r)}个策略优化建议")
        for o in r:
            print(f"  • {o['topic']}: {o['suggestion']}")

    elif args[0] == "--cross":
        r = cross_domain_learning()
        print(f"✅ {len(r)}条跨域教训")
        for c in r[:5]:
            print(f"  • {c['pattern']} → {c['target_domain']}")

    elif args[0] == "--risks":
        r = identify_risks()
        print(f"✅ {len(r)}个风险")
        for risk in r:
            icon = "🔴" if risk["severity"] == "high" else "🟡"
            print(f"  {icon} {risk['message']}")

    elif args[0] == "--meta":
        r = meta_review()
        print(f"✅ 元复盘完成")
        for s in r.get("suggestions", []):
            print(f"  💡 {s}")

    elif args[0] == "--daily":
        print(generate_daily_template())

    elif args[0] == "--weekly":
        print(generate_weekly_template())

    elif args[0] == "--evolve":
        print("🧬 执行全量复盘进化 (R1-R7)...")
        results = full_evolve()
        print(f"\n✅ 进化完成")

    elif args[0] == "--predict" and len(args) >= 3:
        topic = args[1]
        prediction = " ".join(args[2:])
        pid = record_prediction(topic, prediction)
        print(f"✅ 预测已记录: {pid}")

    elif args[0] == "--actual" and len(args) >= 4:
        pid, actual = args[1], args[2]
        accuracy = float(args[3]) if len(args) > 3 else 0.5
        ok = record_actual(pid, actual, accuracy)
        print(f"✅ 实际结果已记录" if ok else "❌ 预测ID不存在")

    else:
        print(__doc__)
