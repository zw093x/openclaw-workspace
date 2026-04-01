#!/usr/bin/env python3
"""
全局错误进化引擎
任何脚本/任务的报错都可以接入此模块，自动学习→分析→优化

使用方式:
  from error_evolution import report_error, get_suggestions, run_evolution
  
  # 报告错误
  report_error("script_name", "error_type", "error message", context={...})
  
  # 获取修复建议
  suggestions = get_suggestions("error_type")
  
  # 执行进化学习
  run_evolution()
"""

import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

WORKSPACE = Path("/root/.openclaw/workspace")
ERROR_LOG = WORKSPACE / "memory" / "error-evolution-log.jsonl"
KNOWLEDGE_FILE = WORKSPACE / "memory" / "error-knowledge.json"
PATTERNS_FILE = WORKSPACE / "memory" / "error-patterns.json"

# ===== 错误分类体系 =====
ERROR_CATEGORIES = {
    "network": {
        "keywords": ["connection", "timeout", "refused", "unreachable", "dns", "ssl", "tls", "proxy"],
        "root_cause": "network_instability",
        "severity": "medium"
    },
    "permission": {
        "keywords": ["permission", "denied", "forbidden", "unauthorized", "access", "403", "401"],
        "root_cause": "permission_denied",
        "severity": "high"
    },
    "resource": {
        "keywords": ["disk", "memory", "space", "oom", "full", "quota", "limit"],
        "root_cause": "resource_exhaustion",
        "severity": "high"
    },
    "config": {
        "keywords": ["config", "missing", "not found", "invalid", "parse", "json", "yaml"],
        "root_cause": "config_error",
        "severity": "medium"
    },
    "dependency": {
        "keywords": ["module", "import", "package", "not installed", "version", "compatibility"],
        "root_cause": "dependency_missing",
        "severity": "medium"
    },
    "api": {
        "keywords": ["api", "rate limit", "429", "500", "502", "503", "504", "quota"],
        "root_cause": "api_failure",
        "severity": "medium"
    },
    "data": {
        "keywords": ["keyerror", "indexerror", "typeerror", "valueerror", "null", "none", "empty"],
        "root_cause": "data_issue",
        "severity": "low"
    },
    "cron": {
        "keywords": ["cron", "timeout", "schedule", "trigger", "stagger"],
        "root_cause": "cron_misconfiguration",
        "severity": "medium"
    },
    "gateway": {
        "keywords": ["gateway", "openclaw", "plugin", "channel", "feishu"],
        "root_cause": "gateway_issue",
        "severity": "high"
    }
}

def _load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default or {}

def _save_json(path, data):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _append_log(entry):
    os.makedirs(ERROR_LOG.parent, exist_ok=True)
    entry["ts"] = datetime.now().isoformat()
    with open(ERROR_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def _error_fingerprint(error_type, error_msg):
    """生成错误指纹（去重用）"""
    # 提取核心特征，忽略变化的部分
    clean = re.sub(r'\d+', 'N', error_msg.lower())
    clean = re.sub(r'[a-f0-9]{8,}', 'HEX', clean)
    clean = re.sub(r'/[\w/.]+', 'PATH', clean)
    key = f"{error_type}:{clean[:100]}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

def classify_error(error_msg):
    """自动分类错误"""
    if not error_msg:
        return "unknown", "unknown", "low"
    
    msg_lower = error_msg.lower()
    scores = {}
    
    for cat, info in ERROR_CATEGORIES.items():
        score = sum(1 for kw in info["keywords"] if kw in msg_lower)
        if score > 0:
            scores[cat] = score
    
    if scores:
        best_cat = max(scores, key=scores.get)
        info = ERROR_CATEGORIES[best_cat]
        return best_cat, info["root_cause"], info["severity"]
    
    return "unknown", "unknown", "low"

# ===== 核心API =====

def report_error(source, error_type, error_msg, context=None, fixed=False, fix_method=None):
    """
    报告错误（任何脚本调用此函数记录错误）
    
    Args:
        source: 来源（脚本名/cron任务名）
        error_type: 错误类型
        error_msg: 错误消息
        context: 附加上下文（dict）
        fixed: 是否已修复
        fix_method: 修复方法描述
    """
    # 自动分类
    category, root_cause, severity = classify_error(error_msg)
    
    # 生成指纹
    fingerprint = _error_fingerprint(error_type, error_msg)
    
    # 加载知识库
    knowledge = _load_json(KNOWLEDGE_FILE, {"errors": {}, "fixes": {}, "stats": {}})
    
    # 更新错误统计
    if fingerprint not in knowledge["errors"]:
        knowledge["errors"][fingerprint] = {
            "type": error_type,
            "category": category,
            "root_cause": root_cause,
            "severity": severity,
            "first_seen": datetime.now().isoformat(),
            "count": 0,
            "sources": [],
            "sample_msg": error_msg[:200]
        }
    
    err_info = knowledge["errors"][fingerprint]
    err_info["count"] += 1
    err_info["last_seen"] = datetime.now().isoformat()
    if source not in err_info["sources"]:
        err_info["sources"].append(source)
    
    # 记录修复方法
    if fixed and fix_method:
        if fingerprint not in knowledge["fixes"]:
            knowledge["fixes"][fingerprint] = []
        knowledge["fixes"][fingerprint].append({
            "method": fix_method,
            "ts": datetime.now().isoformat(),
            "source": source
        })
    
    # 更新统计
    knowledge["stats"]["total_errors"] = knowledge["stats"].get("total_errors", 0) + 1
    knowledge["stats"]["by_category"] = knowledge["stats"].get("by_category", {})
    knowledge["stats"]["by_category"][category] = knowledge["stats"]["by_category"].get(category, 0) + 1
    knowledge["stats"]["by_root_cause"] = knowledge["stats"].get("by_root_cause", {})
    knowledge["stats"]["by_root_cause"][root_cause] = knowledge["stats"]["by_root_cause"].get(root_cause, 0) + 1
    
    _save_json(KNOWLEDGE_FILE, knowledge)
    
    # 写入日志
    _append_log({
        "source": source,
        "type": error_type,
        "category": category,
        "root_cause": root_cause,
        "severity": severity,
        "fingerprint": fingerprint,
        "msg": error_msg[:300],
        "context": context or {},
        "fixed": fixed,
        "fix_method": fix_method
    })
    
    return {
        "fingerprint": fingerprint,
        "category": category,
        "root_cause": root_cause,
        "severity": severity,
        "is_known": err_info["count"] > 1
    }

def get_suggestions(error_type_or_msg):
    """
    获取修复建议（基于历史学习）
    
    Args:
        error_type_or_msg: 错误类型或错误消息
        
    Returns:
        list: 修复建议列表
    """
    knowledge = _load_json(KNOWLEDGE_FILE, {"errors": {}, "fixes": {}})
    
    # 尝试匹配
    suggestions = []
    
    # 1. 精确匹配
    for fp, err in knowledge.get("errors", {}).items():
        if err.get("type") == error_type_or_msg or err.get("sample_msg", "") in error_type_or_msg:
            fixes = knowledge.get("fixes", {}).get(fp, [])
            if fixes:
                # 按成功率排序
                for fix in fixes[-3:]:  # 最近3个有效修复
                    suggestions.append({
                        "method": fix["method"],
                        "source": fix["source"],
                        "used_at": fix["ts"],
                        "confidence": min(0.9, 0.5 + len(fixes) * 0.1)
                    })
    
    # 2. 分类匹配
    category, root_cause, _ = classify_error(error_type_or_msg)
    if category != "unknown":
        for fp, err in knowledge.get("errors", {}).items():
            if err.get("root_cause") == root_cause and fp not in [s.get("fingerprint") for s in suggestions]:
                fixes = knowledge.get("fixes", {}).get(fp, [])
                if fixes:
                    suggestions.append({
                        "method": fixes[-1]["method"],
                        "source": fixes[-1]["source"],
                        "used_at": fixes[-1]["ts"],
                        "confidence": 0.3,
                        "note": f"同类根治方案({root_cause})"
                    })
    
    # 3. 内置常见修复
    builtin = get_builtin_fixes(category, error_type_or_msg)
    suggestions.extend(builtin)
    
    return suggestions

def get_builtin_fixes(category, error_msg):
    """内置常见修复方案"""
    fixes = {
        "network": [
            {"method": "检查代理配置，重试请求", "confidence": 0.5},
            {"method": "检查目标服务是否可达 (ping/telnet)", "confidence": 0.4},
            {"method": "等待5秒后重试（可能临时网络波动）", "confidence": 0.3}
        ],
        "permission": [
            {"method": "检查文件/目录权限 (ls -la)", "confidence": 0.6},
            {"method": "使用 sudo 或切换用户", "confidence": 0.5},
            {"method": "检查 API Key/Token 是否有效", "confidence": 0.4}
        ],
        "resource": [
            {"method": "清理磁盘空间 (df -h 检查)", "confidence": 0.7},
            {"method": "清理临时文件 (find /tmp -mtime +7 -delete)", "confidence": 0.6},
            {"method": "检查内存使用 (free -h)", "confidence": 0.4}
        ],
        "config": [
            {"method": "检查配置文件是否存在且格式正确", "confidence": 0.6},
            {"method": "对比备份配置，还原已知正常的版本", "confidence": 0.5},
            {"method": "重新生成配置文件", "confidence": 0.3}
        ],
        "dependency": [
            {"method": "pip install 缺失的包", "confidence": 0.7},
            {"method": "检查虚拟环境是否激活", "confidence": 0.5},
            {"method": "检查版本兼容性", "confidence": 0.4}
        ],
        "api": [
            {"method": "检查API Key/配额", "confidence": 0.6},
            {"method": "等待限速冷却（1-5分钟）", "confidence": 0.5},
            {"method": "切换备用API源", "confidence": 0.4}
        ],
        "cron": [
            {"method": "增加 --timeout-seconds", "confidence": 0.6},
            {"method": "检查任务 prompt 是否正确", "confidence": 0.5},
            {"method": "手动触发测试: openclaw cron run <id>", "confidence": 0.4}
        ],
        "gateway": [
            {"method": "重启 gateway: openclaw gateway restart", "confidence": 0.7},
            {"method": "检查 gateway 日志: journalctl --user -u openclaw-gateway", "confidence": 0.5},
            {"method": "检查端口是否被占用", "confidence": 0.4}
        ]
    }
    return fixes.get(category, [{"method": "需人工排查", "confidence": 0.1}])

def get_root_cause_analysis():
    """获取根因分析报告"""
    knowledge = _load_json(KNOWLEDGE_FILE, {"errors": {}, "fixes": {}, "stats": {}})
    
    # 统计根因分布
    by_cause = knowledge.get("stats", {}).get("by_root_cause", {})
    by_category = knowledge.get("stats", {}).get("by_category", {})
    
    # 识别系统性问题（同一根因出现3+次）
    systemic = {k: v for k, v in by_cause.items() if v >= 3}
    
    # 识别高频错误
    errors = knowledge.get("errors", {})
    high_freq = {fp: info for fp, info in errors.items() if info.get("count", 0) >= 3}
    
    # 修复率统计
    total_fixes = sum(len(fixes) for fixes in knowledge.get("fixes", {}).values())
    total_errors = knowledge.get("stats", {}).get("total_errors", 0)
    fix_rate = total_fixes / total_errors if total_errors > 0 else 0
    
    return {
        "total_errors": total_errors,
        "total_fixes": total_fixes,
        "fix_rate": fix_rate,
        "systemic_issues": systemic,
        "high_frequency_errors": {fp: info["count"] for fp, info in high_freq.items()},
        "by_category": by_category,
        "by_root_cause": by_cause
    }

def discover_patterns():
    """从错误日志中发现模式"""
    patterns = []
    
    try:
        with open(ERROR_LOG, "r") as f:
            lines = f.readlines()[-200:]
    except:
        return patterns
    
    logs = []
    for line in lines:
        try:
            logs.append(json.loads(line.strip()))
        except:
            pass
    
    if len(logs) < 3:
        return patterns
    
    # 1. 时间模式（哪些时段错误集中）
    hour_errors = Counter()
    for log in logs:
        ts = log.get("ts", "")
        if ts:
            try:
                hour = datetime.fromisoformat(ts).hour
                hour_errors[hour] += 1
            except:
                pass
    
    peak = hour_errors.most_common(1)
    if peak and peak[0][1] >= 3:
        patterns.append({
            "type": "time_concentration",
            "detail": f"错误集中在{peak[0][0]}:00时段（{peak[0][1]}次）",
            "action": "在该时段前增加预防性检查"
        })
    
    # 2. 连锁故障（短时间内多个错误）
    for i in range(len(logs) - 2):
        t1 = logs[i].get("ts", "")
        t2 = logs[i+2].get("ts", "")
        if t1 and t2:
            try:
                dt1 = datetime.fromisoformat(t1)
                dt2 = datetime.fromisoformat(t2)
                if (dt2 - dt1).total_seconds() < 60:  # 1分钟内3个错误
                    cats = set(logs[j].get("category", "") for j in range(i, i+3))
                    if len(cats) >= 2:
                        patterns.append({
                            "type": "chain_failure",
                            "detail": f"连锁故障: {', '.join(cats)}",
                            "action": "可能存在共同根因，需关联分析"
                        })
                        break
            except:
                pass
    
    # 3. 修复失效模式（同一错误反复修复失败）
    knowledge = _load_json(KNOWLEDGE_FILE, {"errors": {}, "fixes": {}})
    for fp, info in knowledge.get("errors", {}).items():
        count = info.get("count", 0)
        fixes = knowledge.get("fixes", {}).get(fp, [])
        if count >= 3 and len(fixes) >= 2:
            # 检查是否用了不同方法
            methods = set(f["method"] for f in fixes)
            if len(methods) >= 2:
                patterns.append({
                    "type": "fix_ineffective",
                    "detail": f"错误{fp}反复出现({count}次)，已尝试{len(methods)}种方法",
                    "action": "需要根本性解决，而非临时修复"
                })
    
    return patterns

def run_evolution():
    """执行一次完整的进化学习"""
    results = {
        "ts": datetime.now().isoformat(),
        "root_cause_analysis": get_root_cause_analysis(),
        "discovered_patterns": discover_patterns(),
        "recommendations": []
    }
    
    # 生成建议
    rca = results["root_cause_analysis"]
    
    # 系统性问题建议
    for cause, count in rca.get("systemic_issues", {}).items():
        results["recommendations"].append({
            "type": "systemic_fix",
            "priority": "high",
            "message": f"根因'{cause}'已出现{count}次，需要系统级修复",
            "action": f"检查{cause}的底层原因并永久解决"
        })
    
    # 修复率建议
    if rca["fix_rate"] < 0.5 and rca["total_errors"] >= 5:
        results["recommendations"].append({
            "type": "fix_rate_low",
            "priority": "medium",
            "message": f"整体修复率仅{rca['fix_rate']:.0%}（{rca['total_fixes']}/{rca['total_errors']}）",
            "action": "审视修复策略，增加自动化修复能力"
        })
    
    # 模式发现建议
    for pattern in results["discovered_patterns"]:
        results["recommendations"].append({
            "type": "pattern_discovered",
            "priority": pattern.get("priority", "medium"),
            "message": pattern["detail"],
            "action": pattern["action"]
        })
    
    _save_json(PATTERNS_FILE, results)
    return results

# ===== 便捷包装 =====

def wrap_script_errors(script_name):
    """装饰器：自动捕获脚本错误并报告"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                report_error(
                    source=script_name,
                    error_type=type(e).__name__,
                    error_msg=str(e),
                    context={"args": str(args)[:200]}
                )
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # CLI 模式
    import sys
    
    if "--evolve" in sys.argv:
        results = run_evolution()
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif "--analyze" in sys.argv:
        rca = get_root_cause_analysis()
        print(json.dumps(rca, ensure_ascii=False, indent=2))
    elif "--suggest" in sys.argv and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        suggestions = get_suggestions(query)
        print(f"查询: {query}")
        print(f"建议:")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s['method']} (置信度:{s['confidence']:.0%})")
    else:
        print("用法:")
        print("  --evolve    执行进化学习")
        print("  --analyze   根因分析")
        print("  --suggest <error>  获取修复建议")
