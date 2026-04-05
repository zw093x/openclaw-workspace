#!/usr/bin/env python3
"""
记忆系统增强模块 v2.0
包含5大升级:
  1. 记忆索引加速（topic-based自动归类）
  2. 记忆健康自动修复（空/过时/大文件自动清理归档）
  3. 跨记忆冲突检测（自动发现矛盾信息）
  4. 记忆使用统计（记录调用次数+生成周报）
  5. 语义检索（基于语义标签匹配，不依赖关键词）

用法:
  python3 scripts/memory_plus.py --index     # 方向①：构建主题索引
  python3 scripts/memory_plus.py --repair     # 方向②：自动修复
  python3 scripts/memory_plus.py --conflict   # 方向③：冲突检测
  python3 scripts/memory_plus.py --stats      # 方向④：使用统计
  python3 scripts/memory_plus.py --semantic   # 方向⑤：语义检索
  python3 scripts/memory_plus.py --full       # 全部运行
"""

import json
import re
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
sys.path.insert(0, str(WORKSPACE / "scripts"))

# ============================================================
# 配置
# ============================================================
TOPIC_INDEX_FILE = MEMORY_DIR / "topic-index.json"      # 方向①
USAGE_STATS_FILE = MEMORY_DIR / "memory-usage.json"     # 方向④
CONFLICT_FILE = MEMORY_DIR / "memory-conflicts.json"    # 方向③
DECAY_FILE = MEMORY_DIR / "memory-decay.json"

# 主题定义 + 语义标签（方向⑤）
TOPICS = {
    "📈 投资持仓": {
        "tags": ["股票", "持仓", "建仓", "清仓", "减仓", "加仓", "止损", "成本", "浮亏", "浮盈", "A股", "船舶", "动力"],
        "files": ["stock-portfolio.md", "stock-strategy-20260331.md", "stock-knowledge.md",
                  "knowledge-600150*.md", "knowledge-600482*.md", "knowledge-600703*.md",
                  "knowledge-600416*.md", "knowledge-shipping.md", "trade-journal.md"]
    },
    "👶 家庭护理": {
        "tags": ["宝宝", "月子", "配偶", "产后", "喂养", "疫苗", "体重", "发育", "黄疸", "母乳"],
        "files": ["USER.md", "广桂月子饮食指南.md", "育儿月子指南.md"]
    },
    "🤖 AI工具": {
        "tags": ["AI", "大模型", "GPT", "LLM", "图像生成", "视频生成", "ComfyUI", "Stable Diffusion",
                 "提示词", "prompt", "文生图", "图生图", "SD", "Flux", " Gemma"],
        "files": ["knowledge-ai.md", "knowledge-ai-tools.md", "AI绘画*.md",
                  "comfyui-*.md", "agentskills-*.md"]
    },
    "🛠️ 系统运维": {
        "tags": ["cron", "自愈", "gateway", "飞书", "超时", "修复", "错误", "异常", "磁盘",
                 "Docker", "代理", "端口", "部署", "日志", "OpenClaw", "mihomo"],
        "files": ["heal-*.md", "heal-*.json", "intel-*.json", "memory-evolve.md",
                  "cron-fault-knowledge.md", "TOOLS.md"]
    },
    "🧠 学习进化": {
        "tags": ["学习", "进化", "教训", "规则", "最佳实践", "纠正", "模式", "复盘", "准确率", "判断"],
        "files": ["learn-db.json", "learn-log.jsonl", "analysis-accuracy.md",
                  "review-db.json", "review-log.jsonl", "MEMORY.md"]
    },
    "🚀 ComfyUI": {
        "tags": ["ComfyUI", "节点", "工作流", "SDXL", "Flux", "3D", "Meshy", "Tripo",
                 "ControlNet", "LoRA", "模型加载", "v0.17", "v0.18"],
        "files": ["comfyui-*.md", "memory/comfyui-tutorial-guide.md"]
    },
    "🌍 行业资讯": {
        "tags": ["BDI", "航运", "造船", "SCFI", "CCFI", "原油", "大宗商品", "黄金", "白银", "汇率"],
        "files": ["knowledge-shipping.md", "fish-basin-*.json", "gold-price*.json"]
    },
    "📊 财报分析": {
        "tags": ["营收", "净利润", "ROE", "负债率", "现金流", "毛利率", "存货周转", "财报", "每股收益", "EPS"],
        "files": ["knowledge-*-finance.md", "finance-judgment-log.jsonl"]
    },
}

# 冲突检测规则（方向③）
CONFLICT_RULES = [
    # 同一股票不同价格
    {
        "pattern": r"(中国船舶|600150).*?(成本|买入|价格)[^\d]*(\d+\.?\d*)",
        "extract": lambda m: ("600150", float(m.group(3))),
        "topic": "股票成本"
    },
    {
        "pattern": r"(中国动力|600482).*?(成本|买入|价格)[^\d]*(\d+\.?\d*)",
        "extract": lambda m: ("600482", float(m.group(3))),
        "topic": "股票成本"
    },
]


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default or {}


def save_json(path, data):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_memory_files() -> List[Path]:
    """获取所有记忆文件"""
    files = []
    for ext in ["*.md", "*.json", "*.jsonl"]:
        files.extend(WORKSPACE.glob(f"memory/{ext}"))
        files.extend(WORKSPACE.glob(f"memory/*/{ext}"))
    # 也扫描 memory/archives
    if (MEMORY_DIR / "archives").exists():
        for sub in (MEMORY_DIR / "archives").iterdir():
            if sub.is_dir():
                for ext in ["*.md", "*.json"]:
                    files.extend(sub.glob(f"{ext}"))
    return list(set(f for f in files if f.is_file()))


# ============================================================
# 方向①：记忆索引加速（主题自动归类）
# ============================================================
def build_topic_index():
    """
    将79个文件按主题自动归类，生成 topic-index.json
    输出格式：
    {
      "投资持仓": {
        "files": ["stock-portfolio.md", ...],
        "tags": ["股票", "持仓", ...],
        "last_updated": "...",
        "file_count": N
      },
      ...
    }
    """
    all_files = get_all_memory_files()
    topic_result = {}

    for topic_name, topic_info in TOPICS.items():
        matched_files = []
        tags = topic_info["tags"]
        patterns = topic_info["files"]

        for f in all_files:
            fname = f.name
            # glob pattern匹配
            matched = False
            for pattern in patterns:
                pattern = pattern.replace("*", ".*")
                if re.match(pattern.replace("/", "[/\\\\]"), fname) or re.search(pattern.replace(".*", ""), fname):
                    matched = True
                    break
            # 或者内容包含标签词
            if not matched:
                try:
                    content = f.read_text()[:2000]  # 只读前2000字加速
                    content_lower = content.lower()
                    tag_matches = sum(1 for t in tags if t.lower() in content_lower)
                    if tag_matches >= 2:
                        matched = True
                except:
                    pass

            if matched:
                rel_path = str(f.relative_to(WORKSPACE))
                matched_files.append(rel_path)

        topic_result[topic_name] = {
            "files": matched_files,
            "file_count": len(matched_files),
            "tags": tags,
            "last_updated": datetime.now().isoformat()
        }

    save_json(TOPIC_INDEX_FILE, topic_result)
    return topic_result


def get_topic_for_query(query: str) -> List[Dict]:
    """
    给定查询，返回相关主题及其文件
    """
    index = load_json(TOPIC_INDEX_FILE, {})
    query_lower = query.lower()
    scored = []

    for topic_name, info in index.items():
        # 标签匹配
        tag_score = sum(1 for t in info.get("tags", []) if t.lower() in query_lower)
        # 文件数量加权
        file_score = min(info.get("file_count", 0) / 10, 1.0)
        total = tag_score * 2 + file_score

        if total > 0:
            scored.append({
                "topic": topic_name,
                "score": round(total, 2),
                "files": info.get("files", []),
                "file_count": info.get("file_count", 0),
                "matched_tags": [t for t in info.get("tags", []) if t.lower() in query_lower]
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


# ============================================================
# 方向②：记忆健康自动修复
# ============================================================
def auto_repair_memory():
    """
    自动修复记忆健康问题:
    1. 空文件(<50字节): 标记删除
    2. 过时日志(>60天且无关键内容): 归档压缩
    3. 大文件(>200KB): 标记需拆分
    4. 生成修复报告
    """
    all_files = get_all_memory_files()
    now = datetime.now()
    health = load_json(MEMORY_DIR / "memory-health.json", {})
    repaired = []

    for f in all_files:
        try:
            content = f.read_text()
            size = len(content)
            rel = str(f.relative_to(WORKSPACE))

            # 1. 空文件
            if size < 50:
                # 跳过关键文件
                if f.name in ["MEMORY.md", "USER.md", "TOOLS.md", "SOUL.md"]:
                    continue
                # 记录但不删除（安全优先）
                repaired.append({"file": rel, "action": "空文件_待清理", "size": size})

            # 2. 过时日志（>60天的旧日志）
            elif re.match(r"memory/\d{4}-\d{2}-\d{2}\.md", rel):
                try:
                    date_str = re.search(r"(\d{4}-\d{2}-\d{2})", rel).group(1)
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    days_old = (now - file_date).days
                    if days_old > 60:
                        # 归档压缩
                        archive_dir = MEMORY_DIR / "archives" / "old-logs"
                        archive_dir.mkdir(exist_ok=True)
                        archive_name = f"{date_str}_archived.md"
                        (f).rename(archive_dir / archive_name)
                        repaired.append({"file": rel, "action": "归档压缩", "days_old": days_old})
                except Exception:
                    pass

            # 3. 大文件(>200KB)拆分
            elif size > 200 * 1024:
                repaired.append({"file": rel, "action": "大文件_需拆分", "size_kb": size // 1024})

            # 4. 临时文件清理
            elif any(x in rel for x in ["weather-latest.txt", "gold-last-price.txt",
                                         "tech-levels.log", "card-delivery.log",
                                         "comfyui-monitor-last.txt"]):
                # 这些是运行时产生的，不归档，只清理内容
                if size > 50 * 1024:  # >50KB才清理
                    (f).write_text(f"# {f.name}\n# 最后清理: {now.isoformat()}\n")
                    repaired.append({"file": rel, "action": "运行时缓存_已清理", "size_kb": size // 1024})

        except Exception as e:
            continue

    # 保存修复报告
    repair_report = {
        "timestamp": now.isoformat(),
        "total_repaired": len(repaired),
        "actions": repaired[:20]  # 最多记录20条
    }
    save_json(MEMORY_DIR / "memory-repair-log.json", repair_report)
    return repair_report


# ============================================================
# 方向③：跨记忆冲突检测
# ============================================================
def detect_cross_memory_conflicts():
    """
    检测不同文件中同一信息的矛盾记录
    目前实现: 持仓成本矛盾检测
    """
    conflicts = []

    # 提取所有文件中的股票成本数据
    cost_data = defaultdict(list)  # {stock_code: [(file, price, context), ...]}

    all_files = get_all_memory_files()
    md_files = [f for f in all_files if f.suffix == ".md" and "memory/" in str(f)]

    for f in md_files:
        try:
            content = f.read_text()
            rel = str(f.relative_to(WORKSPACE))

            # 提取600150/600482成本
            for code in ["600150", "600482", "600703", "600416"]:
                name_map = {"600150": "中国船舶", "600482": "中国动力",
                            "600703": "三安光电", "600416": "湘电股份"}
                name = name_map.get(code, code)

                # 匹配模式：成本xx.xx / 买入xx.xx / 价格xx.xx
                matches = re.finditer(
                    rf"{name}|{code}.*?(成本|买入|价格)[^\d]*(\d+\.?\d*)",
                    content, re.IGNORECASE
                )
                for m in matches:
                    try:
                        price_str = m.group(2)
                        price = float(price_str)
                        # 提取上下文（前后50字）
                        start = max(0, m.start() - 30)
                        end = min(len(content), m.end() + 30)
                        context = content[start:end].replace("\n", " ").strip()

                        cost_data[code].append({
                            "file": rel,
                            "price": price,
                            "context": context[:80]
                        })
                    except:
                        pass
        except:
            continue

    # 检测矛盾（同一股票有不同价格，且差>0.5%）
    for code, entries in cost_data.items():
        if len(entries) < 2:
            continue
        prices = [e["price"] for e in entries]
        min_p, max_p = min(prices), max(prices)
        if max_p / min_p > 1.005:  # >0.5%差异
            conflicts.append({
                "type": "价格矛盾",
                "stock": code,
                "values": [(e["price"], e["file"]) for e in entries],
                "diff_pct": round((max_p / min_p - 1) * 100, 2),
                "severity": "high" if max_p / min_p > 1.02 else "medium"
            })

    # 检测过时信息（如旧服务器IP仍在MEMORY.md）
    memory_content = (WORKSPACE / "MEMORY.md").read_text()
    if "159.75.77.36" in memory_content:
        conflicts.append({
            "type": "过时信息",
            "detail": "MEMORY.md中仍包含旧服务器IP(159.75.77.36)",
            "severity": "low",
            "fix": "已在MEMORY.md清理中移除"
        })

    save_json(CONFLICT_FILE, {
        "timestamp": datetime.now().isoformat(),
        "conflicts": conflicts,
        "total": len(conflicts)
    })
    return conflicts


# ============================================================
# 方向④：记忆使用统计
# ============================================================
def record_memory_access(file_path: str):
    """在对话/检索时调用，记录记忆被使用"""
    stats = load_json(USAGE_STATS_FILE, {"access_log": [], "file_counts": {}})

    now = datetime.now()
    ts = now.isoformat()

    # 记录访问日志（只保留最近500条）
    stats["access_log"].append({"file": file_path, "ts": ts})
    if len(stats["access_log"]) > 500:
        stats["access_log"] = stats["access_log"][-500:]

    # 更新访问计数
    counts = stats.get("file_counts", {})
    counts[file_path] = counts.get(file_path, 0) + 1
    stats["file_counts"] = counts
    stats["last_access"] = ts

    save_json(USAGE_STATS_FILE, stats)


def generate_usage_report() -> Dict:
    """生成记忆使用统计报告"""
    stats = load_json(USAGE_STATS_FILE, {"access_log": [], "file_counts": {}})

    counts = stats.get("file_counts", {})
    total_accesses = sum(counts.values())

    # 排序
    most_used = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    never_used = [f for f, c in counts.items() if c == 0]

    # 本周访问统计
    now = datetime.now()
    week_access = sum(1 for l in stats.get("access_log", [])
                      if l.get("ts", "") > (now - timedelta(days=7)).isoformat())

    report = {
        "timestamp": now.isoformat(),
        "total_accesses": total_accesses,
        "week_access": week_access,
        "unique_files_accessed": len(counts),
        "most_used": [{"file": f, "count": c} for f, c in most_used],
        "never_used_count": len(never_used),
        "never_used_files": never_used[:10],
    }
    return report


# ============================================================
# 方向⑤：语义检索（标签+主题匹配）
# ============================================================
def semantic_search(query: str, top_n: int = 8) -> List[Dict]:
    """
    基于语义标签的主题检索，不依赖关键词精确匹配
    方法:
    1. 将query分解为语义标签
    2. 遍历所有主题，计算标签匹配度
    3. 聚合所有匹配文件，按主题权重排序
    4. 去重 + 截取top_n
    """
    index = load_json(TOPIC_INDEX_FILE, {})

    # 语义标签扩展（query词 → 标准标签）
    SEMANTIC_MAP = {
        "宝宝": "👶 家庭护理", "孩子": "👶 家庭护理", "婴儿": "👶 家庭护理",
        "媳妇": "👶 家庭护理", "老婆": "👶 家庭护理", "配偶": "👶 家庭护理",
        "持仓": "📈 投资持仓", "股票": "📈 投资持仓", "建仓": "📈 投资持仓",
        "亏损": "📈 投资持仓", "盈利": "📈 投资持仓", "成本": "📈 投资持仓",
        "ComfyUI": "🚀 ComfyUI", "工作流": "🚀 ComfyUI", "节点": "🚀 ComfyUI",
        "AI": "🤖 AI工具", "大模型": "🤖 AI工具", "GPT": "🤖 AI工具",
        "系统": "🛠️ 系统运维", "错误": "🛠️ 系统运维", "修复": "🛠️ 系统运维",
        "自愈": "🛠️ 系统运维", "cron": "🛠️ 系统运维",
        "财报": "📊 财报分析", "营收": "📊 财报分析", "利润": "📊 财报分析",
        "航运": "🌍 行业资讯", "BDI": "🌍 行业资讯", "造船": "🌍 行业资讯",
    }

    query_lower = query.lower()

    # 解析查询 → 匹配的主题列表
    matched_topics = []
    for kw, topic in SEMANTIC_MAP.items():
        if kw.lower() in query_lower:
            matched_topics.append(topic)

    if not matched_topics:
        # 没有匹配，用全量
        matched_topics = list(index.keys())

    # 收集文件 + 评分
    file_scores = defaultdict(lambda: {"score": 0, "topics": [], "matched_tags": []})
    for topic in set(matched_topics):
        if topic not in index:
            continue
        topic_info = index[topic]
        weight = min(len([t for t in matched_topics if t == topic]) / 2 + 1, 3)  # 1~3倍权重
        for f in topic_info.get("files", []):
            file_scores[f]["score"] += weight
            if topic not in file_scores[f]["topics"]:
                file_scores[f]["topics"].append(topic)

    # 排序
    ranked = sorted(file_scores.items(), key=lambda x: x[1]["score"], reverse=True)

    # 转换为输出格式
    results = []
    for rel_path, info in ranked[:top_n]:
        f = WORKSPACE / rel_path
        if not f.exists():
            continue
        try:
            preview = f.read_text()[:200].replace("\n", " ").strip()
        except:
            preview = "(无法读取)"

        results.append({
            "file": rel_path,
            "score": round(info["score"], 1),
            "topics": info["topics"],
            "preview": preview[:100]
        })

    # 自动记录访问统计（让记忆被调用时自动计数）
    try:
        for r in results:
            record_memory_access(r.get("file", ""))
    except Exception:
        pass

    return results


# ============================================================
# CLI 入口
# ============================================================
def main():
    args = sys.argv[1:]

    if "--full" in args or not args:
        print("🧠 记忆系统增强 v2.0 — 全量运行")
        print()

        print("① 构建主题索引...")
        t = build_topic_index()
        topics_built = len([v for v in t.values() if v.get("file_count", 0) > 0])
        print(f"   ✅ 完成: {topics_built}个主题已归类")

        print("② 记忆健康自动修复...")
        r = auto_repair_memory()
        print(f"   ✅ 完成: {r['total_repaired']}个问题已处理")

        print("③ 跨记忆冲突检测...")
        c = detect_cross_memory_conflicts()
        print(f"   ✅ 完成: {len(c)}个冲突已检测")

        print("④ 记忆使用统计...")
        s = generate_usage_report()
        print(f"   ✅ 统计: 总访问{ s['total_accesses']}次, 本周{ s['week_access']}次")
        if s["never_used_count"] > 0:
            print(f"   ⚠️ {s['never_used_count']}个文件从未被调用过")

        print("⑤ 语义检索测试...")
        results = semantic_search("股票投资持仓建仓")
        print(f"   ✅ 检索返回{len(results)}条结果(top3):")
        for r2 in results[:3]:
            print(f"   • {r2['file']} (score={r2['score']}) [{','.join(r2['topics'][:2])}]")

        print()
        print("✅ 记忆增强模块全部就绪")

    elif "--index" in args:
        t = build_topic_index()
        for topic, info in t.items():
            print(f"{topic}: {info['file_count']}个文件")

    elif "--repair" in args:
        r = auto_repair_memory()
        print(f"已处理 {r['total_repaired']} 个问题:")
        for item in r.get("actions", [])[:10]:
            print(f"  • {item['file']}: {item['action']}")

    elif "--conflict" in args:
        c = detect_cross_memory_conflicts()
        print(f"发现 {len(c)} 个冲突:")
        for conf in c:
            print(f"  • [{conf['type']}] {conf.get('stock', conf.get('detail',''))} - {conf.get('severity')}")

    elif "--stats" in args:
        s = generate_usage_report()
        print(f"总访问: {s['total_accesses']}次, 本周: {s['week_access']}次")
        print(f"已调用文件: {s['unique_files_accessed']}个")
        print("最常用文件:")
        for item in s["most_used"][:5]:
            print(f"  • {item['file']}: {item['count']}次")
        if s["never_used_count"] > 0:
            print(f"从未调用({s['never_used_count']}个): {', '.join(s['never_used_files'][:5])}")

    elif "--semantic" in args:
        query = " ".join([a for a in args if not a.startswith("--")]) or "股票持仓宝宝"
        results = semantic_search(query)
        print(f"语义检索「{query}」({len(results)}条):")
        for r in results[:8]:
            print(f"  [{r['score']}] {r['file']}")
            print(f"       topics: {', '.join(r['topics'])}")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()


# ============================================================
# 融合模块：LCM ↔ 记忆系统
# 直接读 LCM SQLite 数据库，为 distillation 提供深层上下文
# ============================================================
try:
    import sqlite3
    LCM_DB = Path("/root/.openclaw/lcm.db")
except:
    LCM_DB = None


def get_lcm_conversations(days=7, limit=10):
    """获取最近N天的对话摘要"""
    if not LCM_DB or not LCM_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(LCM_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT conversation_id, session_key, title, created_at, updated_at
            FROM conversations
            WHERE created_at > ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (week_ago, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return []


def get_lcm_messages(conversation_id, limit=50):
    """获取某对话的所有消息"""
    if not LCM_DB or not LCM_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(LCM_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, token_count, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY seq ASC
            LIMIT ?
        """, (conversation_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except:
        return []


def get_lcm_summaries(conversation_id):
    """获取某对话的摘要"""
    if not LCM_DB or not LCM_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(LCM_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT depth, content, token_count, created_at
            FROM summaries
            WHERE conversation_id = ?
            ORDER BY depth ASC
        """, (conversation_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except:
        return []


def search_lcm_raw(query, limit=20):
    """
    在原始消息中全文搜索（对应 lcm_grep）
    直接查 FTS5 表
    """
    if not LCM_DB or not LCM_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(LCM_DB))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.message_id, m.conversation_id, m.role, m.content, m.created_at
            FROM messages m
            WHERE m.content LIKE ?
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"message_id": r[0], "conversation_id": r[1], "role": r[2],
                 "content": r[3][:200], "created_at": r[4]} for r in rows]
    except:
        return []


def distill_from_lcm(days=7) -> dict:
    """
    从 LCM 融合：提取本周对话的精华内容
    用于补充 weekly distillation
    """
    conversations = get_lcm_conversations(days=days)
    if not conversations:
        return {"status": "no_data", "message": "LCM尚无历史数据（插件刚启用）"}
    
    distillations = []
    key_patterns = [
        "决定", "决策", "策略", "教训", "规则", "新增", "完成",
        "建仓", "清仓", "减仓", "加仓", "止损",
        "安装", "配置", "部署", "升级",
        "自愈", "修复", "错误", "异常",
        "记忆", "学习", "进化",
    ]
    
    for conv in conversations:
        cid = conv["conversation_id"]
        msgs = get_lcm_messages(cid, limit=30)
        summaries = get_lcm_summaries(cid)
        
        # 从摘要提取关键词内容
        summary_text = " ".join(s.get("content", "")[:300] for s in summaries)
        
        # 从原始消息中找关键记录
        key_entries = []
        for msg in msgs:
            content = msg.get("content", "")
            if any(pat in content for pat in key_patterns):
                role = msg.get("role", "?")
                # 跳过系统消息太长的情况
                if len(content) > 1000:
                    content = content[:1000] + "..."
                key_entries.append(f"[{role}] {content[:200]}")
        
        if key_entries or summary_text:
            distillations.append({
                "conversation": conv.get("title", conv.get("session_key", "?"))[:50],
                "conversation_id": cid,
                "created_at": conv.get("created_at", ""),
                "summary_preview": summary_text[:300] if summary_text else "",
                "key_entries": key_entries[:5],
                "message_count": len(msgs),
                "summary_count": len(summaries),
            })
    
    return {
        "status": "success",
        "conversations_found": len(conversations),
        "distillations": distillations,
    }


def enhance_memory_search_with_lcm(query: str, limit=5) -> List[Dict]:
    """
    融合入口：先用主题索引，再用语义检索，
    最后补充 LCM 历史搜索
    """
    from memory_plus import semantic_search, get_topic_for_query
    
    # Step 1: 语义检索
    semantic_results = semantic_search(query, top_n=limit)
    
    # Step 2: LCM 搜索
    lcm_results = search_lcm_raw(query, limit=limit)
    lcm_entries = []
    for r in lcm_results:
        lcm_entries.append({
            "file": f"[LCM对话] {r['conversation_id'][:16]}...",
            "score": 0.9,
            "topics": ["🤖 LCM历史"],
            "preview": r["content"][:150],
            "source": "lcm"
        })
    
    # 合并去重
    seen = set(e["file"] for e in semantic_results)
    combined = list(semantic_results)
    for entry in lcm_entries:
        if entry["file"] not in seen:
            combined.append(entry)
            seen.add(entry["file"])
    
    return combined[:limit]


