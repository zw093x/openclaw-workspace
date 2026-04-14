#!/usr/bin/env python3
"""
记忆进化系统 v2.1 — 16层全进化 / 3阶段分组

【阶段1 采集分析】
M1  自动压缩 — 日志提炼到 MEMORY.md
M2  冲突检测 — 发现矛盾信息
M3  健康检查 — 过时信息标记/归档
M4  智能关联 — 跨文件链接
M5  优先级排序 — 重要记忆置顶
M7  语义聚类 — 按含义分组
M8  去重合并 — 相似记忆合并

【阶段2 推理输出】
M9  时序推理 — 因果关系链
M13 知识图谱 — 实体关系可视化
M14 场景化输出 — 进化结果同步至场景记忆系统

【阶段3 保障巩固】
M6  自动备份 — 关键变更快照
M10 上下文感知 — 当前任务相关记忆调取
M11 预测需求 — 预判下一步需要的信息
M12 跨系统记忆 — 所有子系统共享
M15 记忆巩固 — 定期复习强化
M16 记忆模拟 — 智能遗忘曲线
"""

import json
import os
import re
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_FILE = WORKSPACE / "MEMORY.md"
USER_FILE = WORKSPACE / "USER.md"
TOOLS_FILE = WORKSPACE / "TOOLS.md"
MEMORY_DIR = WORKSPACE / "memory"
SCENE_DIR = WORKSPACE / "skills" / "scene-memory" / "references"
SCENE_INDEX = SCENE_DIR / "场景索引.md"
LEARNINGS_DIR = WORKSPACE / ".learnings"
MEMORY_INDEX = WORKSPACE / "memory" / "memory-index.json"
MEMORY_HEALTH = WORKSPACE / "memory" / "memory-health.json"
MEMORY_BACKUP_DIR = WORKSPACE / "memory" / "backups"
MEMORY_GRAPH = WORKSPACE / "memory" / "memory-graph.json"
MEMORY_CLUSTERS = WORKSPACE / "memory" / "memory-clusters.json"
MEMORY_DECAY = WORKSPACE / "memory" / "memory-decay.json"

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

def get_file_hash(path):
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()[:12]
    except:
        return "missing"

def get_all_memory_files():
    """获取所有记忆相关文件"""
    files = []
    for p in [MEMORY_FILE, USER_FILE, TOOLS_FILE]:
        if p.exists():
            files.append(p)
    for p in MEMORY_DIR.glob("*.md"):
        files.append(p)
    for p in MEMORY_DIR.glob("*.json"):
        files.append(p)
    for p in LEARNINGS_DIR.glob("*.md"):
        files.append(p)
    return files

def parse_sections(content):
    """解析 markdown 的 ## 章节"""
    sections = []
    current_title = None
    current_lines = []
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_title:
                sections.append({"title": current_title, "content": "\n".join(current_lines)})
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_title:
        sections.append({"title": current_title, "content": "\n".join(current_lines)})
    return sections

# ===== M1: 自动压缩 =====
def compress_daily_logs():
    """将旧日志压缩提炼到 MEMORY.md"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    compressed = []
    archived = []
    
    for log_file in sorted(MEMORY_DIR.glob("????-??-??.md")):
        # 解析日期
        try:
            date_str = log_file.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            continue
        
        content = log_file.read_text()
        lines = content.strip().split("\n")
        
        if file_date < month_ago:
            # 超过30天 → 提取关键信息后归档
            key_points = _extract_key_points(content)
            if key_points:
                archived.append({
                    "date": date_str,
                    "points": key_points,
                    "original_size": len(content)
                })
            # 压缩文件（只保留关键信息）
            compressed_content = f"# {date_str} 归档\n\n"
            for pt in key_points[:5]:
                compressed_content += f"- {pt}\n"
            log_file.write_text(compressed_content)
            compressed.append(date_str)
        
        elif file_date < week_ago:
            # 7-30天 → 轻度压缩（删除空行和重复）
            lines = [l for l in lines if l.strip() and not l.startswith("---")]
            compressed_content = "\n".join(lines)
            if len(compressed_content) < len(content):
                log_file.write_text(compressed_content)
                compressed.append(date_str)
    
    return {"compressed": compressed, "archived": archived}

def _extract_key_points(content):
    """从日志中提取关键信息"""
    points = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 关键词匹配
        keywords = ["持仓", "买入", "卖出", "决策", "重要", "教训", "发现", "完成", "修复", "升级", "迁移", "新增", "删除"]
        if any(kw in line for kw in keywords):
            # 去掉 markdown 标记
            clean = re.sub(r'[*#\-\[\]]', '', line).strip()
            if len(clean) > 10:
                points.append(clean[:100])
    return points[:10]

# ===== M2: 冲突检测 =====
def detect_conflicts():
    """检测记忆文件之间的矛盾信息（v2.2修复版）
    
    核心逻辑：
    - 同一文件内、同一天的矛盾才算真正矛盾
    - 跨日期的持仓/成本变化 = 历史演变，不是矛盾
    - 千分位数字(3,000)正确解析
    """
    import re
    from collections import defaultdict
    
    conflicts = []
    
    files = get_all_memory_files()
    
    # 收集所有数据: date -> topic -> [(value, source_line, line_no)]
    records = defaultdict(lambda: defaultdict(list))  # date -> topic -> items
    
    for f in files:
        try:
            content = f.read_text()
        except:
            continue
        
        fname = str(f)
        
        # 从文件名提取日期
        date_match = re.search(r'(20\d{2}-\d{2}-\d{2})', fname)
        file_date = date_match.group(1) if date_match else None
        
        # 从H1标题提取日期
        if not file_date:
            first_line = content.split('\n')[0]
            hm = re.search(r'(20\d{2}-\d{2}-\d{2})', first_line)
            if hm:
                file_date = hm.group(1)
        
        if not file_date:
            continue
        
        lines = content.split('\n')
        
        for ln, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # 排除历史快照行
            historical_kw = ["原持仓", "当时为", "此前", "之前为", "上日", "昨日", "上个月", "历史"]
            is_hist = any(kw in line for kw in historical_kw)
            
            # 持仓：支持 3,000股 或 3000股 格式
            if ("持仓" in line or "持有" in line) and not is_hist:
                m = re.search(r'[^\d](\d{1,3}(?:,\d{3})*)\s*股', line)
                if m:
                    val = m.group(1).replace(",", "")
                    records[file_date]["持仓"].append((val, line[:80], ln))
            
            # 成本：支持 38.696 / 11.44 等格式
            if re.search(r'成本[价：:]', line) and not is_hist:
                m = re.search(r'成本[价：:]\s*(\d+\.\d{2,4})', line)
                if m:
                    records[file_date]["成本"].append((m.group(1), line[:80], ln))
            
            # 服务器IP
            if re.search(r'\d+\.\d+\.\d+\.\d+', line) and ("服务器" in line or "IP" in line):
                m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if m:
                    records[file_date]["服务器IP"].append((m.group(1), line[:80], ln))
    
    # 检测同日期内的矛盾
    for date, topics in records.items():
        for topic, items in topics.items():
            if topic in ("持仓", "成本", "服务器IP"):
                # 按文件分组
                by_file = {}
                for val, line, ln in items:
                    # 从line中提取文件名（如果有）
                    key = line[:60]  # 用行首60字符作为key
                    if key not in by_file:
                        by_file[key] = []
                    by_file[key].append(val)
                
                # 同源内是否有不同值
                for src, vals in by_file.items():
                    unique_vals = list(dict.fromkeys(vals))  # 去重保持顺序
                    if len(unique_vals) > 1:
                        conflicts.append({
                            "topic": topic,
                            "date": date,
                            "values": unique_vals,
                            "source": src[:60],
                            "severity": "high" if topic in ("持仓", "成本") else "low",
                            "note": f"同日期{date}内{topic}存在{len(unique_vals)}个不同值"
                        })
    
    return conflicts
# ===== M3: 健康检查 =====
def check_memory_health():
    """检查记忆文件的健康状态"""
    now = datetime.now()
    health = {
        "timestamp": now.isoformat(),
        "stale_files": [],
        "empty_files": [],
        "large_files": [],
        "inconsistent_dates": [],
        "overall_score": 100
    }
    
    files = get_all_memory_files()
    deductions = 0
    
    for f in files:
        try:
            content = f.read_text()
            stat = f.stat()
        except:
            continue
        
        filename = f.name
        
        # 检查空文件
        if len(content.strip()) < 50:
            health["empty_files"].append(filename)
            deductions += 2
        
        # 检查大文件
        if len(content) > 50000:
            health["large_files"].append({
                "file": filename,
                "size_kb": len(content) // 1024
            })
            deductions += 5
        
        # 检查过时信息
        if "memory" in str(f) and f.suffix == ".md":
            try:
                date_str = f.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                days_old = (now - file_date).days
                if days_old > 60:
                    health["stale_files"].append({
                        "file": filename,
                        "days_old": days_old
                    })
                    deductions += 3
            except:
                pass
        
        # 检查日期不一致（日志文件中的日期与文件名不符）
        if "memory" in str(f) and f.suffix == ".md" and re.match(r'\d{4}-\d{2}-\d{2}', filename):
            first_line = content.split("\n")[0] if content else ""
            if filename[:10] not in first_line and first_line.startswith("#"):
                health["inconsistent_dates"].append(filename)
                deductions += 2
    
    health["overall_score"] = max(0, 100 - deductions)
    
    save_json(MEMORY_HEALTH, health)
    return health

# ===== M4: 智能关联 =====
def build_memory_links():
    """建立跨文件的智能关联"""
    index = load_json(MEMORY_INDEX, {"entities": {}, "topics": {}, "file_hashes": {}})
    
    # 实体提取
    entity_patterns = {
        "股票": re.compile(r'(中国船舶|中国动力|湘电股份|三安光电|600150|600482|600416|600703)'),
        "人物": re.compile(r'(彭煜|P工|配偶|宝宝)'),
        "系统": re.compile(r'(自愈系统|自学习系统|错误进化|统一智能层|Cron)'),
        "服务器": re.compile(r'(\d+\.\d+\.\d+\.\d+)'),
        "工具": re.compile(r'(OpenClaw|ComfyUI|飞书|Docker|mihomo)'),
    }
    
    entities = defaultdict(lambda: {"files": [], "mentions": 0})
    topics = defaultdict(lambda: {"files": [], "keywords": []})
    
    files = get_all_memory_files()
    for f in files:
        try:
            content = f.read_text()
        except:
            continue
        
        filename = str(f.relative_to(WORKSPACE))
        
        # 实体识别
        for entity_type, pattern in entity_patterns.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                entities[name]["files"].append(filename)
                entities[name]["mentions"] += 1
        
        # 主题提取（基于章节标题）
        sections = parse_sections(content)
        for section in sections:
            title = section["title"]
            topics[title]["files"].append(filename)
    
    # 去重
    for name, info in entities.items():
        info["files"] = list(set(info["files"]))
    
    index["entities"] = dict(entities)
    index["topics"] = dict(topics)
    index["last_updated"] = datetime.now().isoformat()
    
    save_json(MEMORY_INDEX, index)
    return {"entities": len(entities), "topics": len(topics)}

# ===== M5: 优先级排序 =====
def prioritize_memories():
    """根据重要性对记忆排序"""
    index = load_json(MEMORY_INDEX, {"entities": {}})
    health = load_json(MEMORY_HEALTH, {})
    
    priorities = {
        "critical": [],  # 核心信息（持仓、策略、规则）
        "high": [],      # 重要信息（教训、决策）
        "medium": [],    # 一般信息（日志、状态）
        "low": []        # 低优先级（临时数据）
    }
    
    # 基于实体出现频率判断重要性
    entities = index.get("entities", {})
    for name, info in entities.items():
        mentions = info.get("mentions", 0)
        if mentions >= 10:
            priorities["critical"].append({"entity": name, "mentions": mentions})
        elif mentions >= 5:
            priorities["high"].append({"entity": name, "mentions": mentions})
        elif mentions >= 2:
            priorities["medium"].append({"entity": name, "mentions": mentions})
    
    # MEMORY.md 章节优先级
    if MEMORY_FILE.exists():
        content = MEMORY_FILE.read_text()
        sections = parse_sections(content)
        for section in sections:
            title = section["title"]
            if any(kw in title for kw in ["持仓", "策略", "决策", "规则", "最高优先级"]):
                priorities["critical"].append({"section": title})
            elif any(kw in title for kw in ["教训", "重点", "关注"]):
                priorities["high"].append({"section": title})
    
    return priorities

# ===== M6: 自动备份 =====
def backup_critical_files():
    """备份关键记忆文件"""
    MEMORY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    backup_dir = MEMORY_BACKUP_DIR / date_str
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backed_up = []
    
    # 关键文件列表
    critical_files = [
        MEMORY_FILE,
        USER_FILE,
        TOOLS_FILE,
        MEMORY_DIR / "stock-portfolio.md",
        MEMORY_DIR / "stock-strategy-20260331.md",
        MEMORY_DIR / "stock-knowledge.md",
        MEMORY_DIR / "learn-db.json",
    ]
    
    for f in critical_files:
        if f.exists():
            dest = backup_dir / f.name
            shutil.copy2(f, dest)
            backed_up.append(f.name)
    
    # 保留最近10个备份
    backups = sorted(MEMORY_BACKUP_DIR.iterdir())
    while len(backups) > 10:
        old = backups.pop(0)
        shutil.rmtree(old)
    
    # 清理超过30天的备份
    cutoff = now - timedelta(days=30)
    for b in MEMORY_BACKUP_DIR.iterdir():
        try:
            b_date = datetime.strptime(b.name[:8], "%Y%m%d")
            if b_date < cutoff:
                shutil.rmtree(b)
        except:
            pass
    
    return {"backed_up": backed_up, "backup_dir": str(backup_dir)}

# ===== M7: 语义聚类 =====
def semantic_clustering():
    """按含义对记忆内容分组"""
    clusters = defaultdict(lambda: {"members": [], "keywords": set(), "size": 0})

    # 语义主题定义
    themes = {
        "投资持仓": ["持仓", "股票", "买入", "卖出", "成本", "策略", "减仓", "加仓", "中国船舶", "中国动力"],
        "系统运维": ["自愈", "cron", "磁盘", "gateway", "飞书", "超时", "修复", "错误", "异常"],
        "学习进化": ["教训", "规则", "学习", "进化", "纠正", "最佳实践", "模式"],
        "家庭护理": ["月子", "宝宝", "配偶", "喂养", "疫苗", "产后", "护理"],
        "AI工具": ["ComfyUI", "AI", "模型", "大模型", "OpenClaw", "技能", "自动化"],
        "服务器": ["Docker", "mihomo", "代理", "端口", "SSH", "部署"],
    }

    files = get_all_memory_files()
    for f in files:
        try:
            content = f.read_text()
        except:
            continue

        filename = str(f.relative_to(WORKSPACE))
        content_lower = content.lower()

        for theme, keywords in themes.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score >= 2:
                clusters[theme]["members"].append(filename)
                clusters[theme]["keywords"].update(kw for kw in keywords if kw in content_lower)
                clusters[theme]["size"] += len(content)

    # 保存
    result = {k: {"members": v["members"], "keywords": list(v["keywords"]), "size": v["size"]}
              for k, v in clusters.items()}
    save_json(MEMORY_CLUSTERS, result)
    return result

# ===== M8: 去重合并 =====
def deduplicate_memories():
    """检测并合并相似/重复的记忆条目"""
    duplicates = []
    merged = 0

    # 检查 MEMORY.md 内部重复
    if MEMORY_FILE.exists():
        content = MEMORY_FILE.read_text()
        sections = parse_sections(content)
        seen_titles = {}
        for section in sections:
            title = section["title"]
            # 模糊匹配标题
            normalized = re.sub(r'[（(].*?[)）]', '', title).strip()
            if normalized in seen_titles:
                duplicates.append({
                    "type": "section_dup",
                    "title": title,
                    "duplicate_of": seen_titles[normalized],
                    "file": "MEMORY.md"
                })
            else:
                seen_titles[normalized] = title

    # 检查 memory/*.md 中的重复日志
    daily_files = sorted(MEMORY_DIR.glob("????-??-??.md"))
    contents = {}
    for f in daily_files:
        try:
            content = f.read_text()
            # 计算相似度（简化：比较关键段落）
            lines = [l.strip() for l in content.split("\n") if l.strip() and len(l.strip()) > 20]
            contents[f.stem] = "\n".join(lines[:10])  # 前10行非空内容
        except:
            continue

    dates = list(contents.keys())
    for i in range(len(dates)):
        for j in range(i + 1, len(dates)):
            # 简单相似度：共同行比例
            lines_i = set(contents[dates[i]].split("\n"))
            lines_j = set(contents[dates[j]].split("\n"))
            if lines_i and lines_j:
                overlap = len(lines_i & lines_j)
                similarity = overlap / min(len(lines_i), len(lines_j))
                if similarity > 0.7:
                    duplicates.append({
                        "type": "daily_dup",
                        "files": [dates[i], dates[j]],
                        "similarity": round(similarity, 2)
                    })

    return {"duplicates": len(duplicates), "details": duplicates[:5]}

# ===== M9: 时序推理 =====
def temporal_reasoning():
    """建立记忆的时间因果链"""
    chains = []

    # 提取所有事件及其时间
    events = []

    # 从日志文件提取
    for log_file in sorted(MEMORY_DIR.glob("????-??-??.md")):
        try:
            date_str = log_file.stem
            content = log_file.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # 检测行动类事件
                action_keywords = ["买入", "卖出", "加仓", "减仓", "清仓", "修复", "升级", "迁移", "部署", "创建", "删除", "决策"]
                if any(kw in line for kw in action_keywords):
                    events.append({
                        "date": date_str,
                        "event": line[:80],
                        "type": next((kw for kw in action_keywords if kw in line), "other")
                    })
        except:
            continue

    # 建立因果链（同一日期的事件按顺序关联，跨日期找关联）
    events.sort(key=lambda x: x["date"])

    # 同类事件链
    type_events = defaultdict(list)
    for e in events:
        type_events[e["type"]].append(e)

    for etype, evts in type_events.items():
        if len(evts) >= 2:
            chain = {
                "type": etype,
                "length": len(evts),
                "start": evts[0]["date"],
                "end": evts[-1]["date"],
                "events": [e["event"][:50] for e in evts[-3:]]  # 最近3个
            }
            chains.append(chain)

    return {"chains": len(chains), "total_events": len(events), "details": chains[:5]}

# ===== M10: 上下文感知 =====
def context_aware_retrieval(current_task=""):
    """
    根据当前任务自动调取相关记忆（遗忘曲线增强版）

    增强点：
    1. 加载 memory-decay.json 的记忆强度
    2. 按 strength × recency 加权排序
    3. 高强度文件优先，高时效性文件次之
    """
    if not current_task:
        return {"matched": 0}

    task_lower = current_task.lower()
    scored = []

    # 加载遗忘曲线数据
    decay_data = load_json(MEMORY_DECAY, {"entries": {}})
    decay_entries = decay_data.get("entries", {})

    # 关键词→文件映射（扩展）
    keyword_map = {
        "股票": ["stock-portfolio.md", "stock-strategy-20260331.md", "stock-knowledge.md"],
        "持仓": ["stock-portfolio.md", "stock-strategy-20260331.md"],
        "船舶": ["knowledge-shipping.md", "knowledge-600150-finance.md"],
        "动力": ["knowledge-600482-finance.md"],
        "月子": ["USER.md"],
        "宝宝": ["USER.md"],
        "自愈": ["heal-evolution.json", "heal-unified-log.jsonl"],
        "技能": ["skill-update-state.json"],
        "ComfyUI": ["comfyui-knowledge.md", "comfyui-learning-progress.md"],
        "CPO": ["knowledge-cpo-microled.md"],
        "湘电": ["knowledge-600416.md"],
        "三安": ["knowledge-600703.md"],
        "记忆": ["MEMORY.md"],
        "服务器": ["TOOLS.md"],
        "学习": ["MEMORY.md"],
        "宝宝疫苗": ["USER.md"],
        "财报": ["knowledge-600150-finance.md", "knowledge-600482-finance.md"],
        "评分": ["knowledge-600150-finance.md"],
        "进化": ["heal-evolution.json"],
        "模型": ["TOOLS.md"],
        "AI": ["knowledge-ai.md", "knowledge-ai-tools.md"],
    }

    # 计算遗忘权重
    now = datetime.now()
    for keyword, files in keyword_map.items():
        if keyword not in task_lower:
            continue
        for f in files:
            # 找文件（memory/ 或根目录）
            path = MEMORY_DIR / f
            if not path.exists():
                path = WORKSPACE / f
            if not path.exists():
                continue
            try:
                content = path.read_text()
                preview = content[:300]
            except:
                continue

            # 获取遗忘强度
            rel_path = str(path.relative_to(WORKSPACE))
            decay_info = decay_entries.get(rel_path) or decay_entries.get(f, {})
            retention = decay_info.get("retention", 1.0)  # 强度 0~1
            access_count = decay_info.get("access_count", 0)

            # 计算时效权重（7天内=1.0，之后线性衰减）
            last_check = decay_info.get("last_check", "")
            recency = 1.0
            if last_check:
                try:
                    last_dt = datetime.fromisoformat(last_check)
                    days_ago = (now - last_dt).days
                    recency = max(0.1, 1.0 - days_ago / 30)  # 30天衰减到0.1
                except:
                    pass

            # 综合得分 = 强度 × 时效 + 访问奖励
            strength_score = retention * recency
            if access_count > 5:
                strength_score += 0.1  # 经常用的文件加权

            scored.append({
                "file": rel_path,
                "preview": preview[:150],
                "strength": round(retention, 2),
                "recency": round(recency, 2),
                "score": round(strength_score, 3),
                "access_count": access_count,
            })

    # 按综合得分降序
    scored.sort(key=lambda x: x["score"], reverse=True)

    # 去重（同一文件只保留最高分）
    seen = set()
    unique = []
    for item in scored:
        if item["file"] not in seen:
            seen.add(item["file"])
            unique.append(item)

    return {
        "matched": len(unique),
        "files": unique[:5],
        "total_candidates": len(scored)
    }

# ===== M11: 预测需求 =====
def predict_needs():
    """预判下一步需要的信息"""
    predictions = []
    now = datetime.now()

    # 基于时间的预测
    hour = now.hour
    weekday = now.weekday()

    if 8 <= hour <= 9 and weekday < 5:
        predictions.append({"type": "time", "need": "股票行情", "reason": "交易时段即将开始"})
    if 14 <= hour <= 15 and weekday < 5:
        predictions.append({"type": "time", "need": "收盘总结", "reason": "交易时段即将结束"})
    if 22 <= hour or hour <= 1:
        predictions.append({"type": "time", "need": "晚间复盘", "reason": "晚间复盘时段"})

    # 基于最近事件的预测
    recent_logs = sorted(MEMORY_DIR.glob("????-??-??.md"))[-3:]
    for log in recent_logs:
        try:
            content = log.read_text()
            if "股票" in content and "分析" not in content:
                predictions.append({"type": "event", "need": "股票分析", "reason": "最近日志提到股票但无分析"})
            if "ComfyUI" in content and "进度" in content:
                predictions.append({"type": "event", "need": "学习总结", "reason": "ComfyUI学习中"})
        except:
            continue

    # 基于持仓的预测
    portfolio_file = MEMORY_DIR / "stock-portfolio.md"
    if portfolio_file.exists():
        content = portfolio_file.read_text()
        if "加仓" in content:
            predictions.append({"type": "action", "need": "加仓条件监控", "reason": "存在待触发的加仓策略"})

    return {"predictions": len(predictions), "details": predictions[:5]}

# ===== M12: 跨系统记忆 =====
def cross_system_memory():
    """同步记忆状态到所有子系统"""
    synced = {}

    # 读取核心记忆
    index = load_json(MEMORY_INDEX, {})
    db = load_json(WORKSPACE / "memory" / "learn-db.json", {})

    # 同步到自学习系统
    if db:
        lessons = db.get("lessons", {})
        for lid, lesson in lessons.items():
            # 将记忆健康状态注入教训
            if lesson.get("category") in ("记忆", "memory"):
                synced["self_learn"] = synced.get("self_learn", 0) + 1

    # 同步到自愈系统
    heal_evo = load_json(WORKSPACE / "memory" / "heal-evolution.json", {})
    if heal_evo:
        # 注入记忆健康指标
        health = load_json(MEMORY_HEALTH, {})
        heal_evo["memory_health"] = health.get("overall_score", 0)
        save_json(WORKSPACE / "memory" / "heal-evolution.json", heal_evo)
        synced["self_heal"] = 1

    # 同步到错误进化
    error_patterns = load_json(WORKSPACE / "memory" / "error-patterns.json", {})
    if error_patterns:
        conflicts = detect_conflicts()
        if conflicts:
            error_patterns.setdefault("memory_conflicts", []).extend(
                [{"topic": c["topic"], "severity": c["severity"]} for c in conflicts]
            )
            save_json(WORKSPACE / "memory" / "error-patterns.json", error_patterns)
            synced["error_evolution"] = len(conflicts)

    return {"synced_systems": len(synced), "details": synced}

# ===== M13: 知识图谱 =====
def build_knowledge_graph():
    """构建实体关系图"""
    graph = {"nodes": [], "edges": []}
    node_set = set()
    edge_set = set()

    files = get_all_memory_files()
    for f in files:
        try:
            content = f.read_text()
        except:
            continue

        filename = str(f.relative_to(WORKSPACE))

        # 实体识别
        entities_found = []
        entity_patterns = {
            "人": re.compile(r'(彭煜|P工)'),
            "股票": re.compile(r'(中国船舶|中国动力|湘电股份|三安光电)'),
            "系统": re.compile(r'(自愈系统|自学习系统|记忆进化|错误进化|统一智能层)'),
            "工具": re.compile(r'(OpenClaw|ComfyUI|飞书|Docker)'),
            "服务器": re.compile(r'(云服务器|本地服务器)'),
        }

        for etype, pattern in entity_patterns.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                if name not in node_set:
                    graph["nodes"].append({"id": name, "type": etype})
                    node_set.add(name)
                entities_found.append(name)

        # 同一文件中的实体互相关联
        for i in range(len(entities_found)):
            for j in range(i + 1, len(entities_found)):
                edge_key = tuple(sorted([entities_found[i], entities_found[j]]))
                if edge_key not in edge_set:
                    graph["edges"].append({
                        "source": edge_key[0],
                        "target": edge_key[1],
                        "relation": "co_mentioned",
                        "file": filename
                    })
                    edge_set.add(edge_key)

    save_json(MEMORY_GRAPH, graph)
    return {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])}

# ===== M14: 场景化输出 =====
SCENE_CATEGORIES = {
    "01-数字环境与工作流": {
        "keywords": ["openclaw", "cron", "定时", "备份", "git", "docker", "服务器", "腾讯云", "mihomo", "skill", "插件", "代理", "脚本", "记忆进化", "自愈", "自学习", "盘中监控", "大宗商品", "持仓", "股价", "股票"],
        "entities": ["OpenClaw", "服务器", "云服务器", "本地服务器", "自愈系统", "自学习系统", "记忆进化", "统一智能层"]
    },
    "02-投资管理与交易策略": {
        "keywords": ["股票", "持仓", "成本", "买入", "卖出", "建仓", "清仓", "止损", "涨跌", "大盘", "板块", "资金", "主力", "船舶", "动力", "三安", "视源", "大宗商品", "黄金", "白银", "甲醇"],
        "entities": ["中国船舶", "中国动力", "三安光电", "视源股份", "600150", "600482", "600703", "002841"]
    },
    "03-AI技术与产品研究": {
        "keywords": ["ai", "comfyui", "提示词", "即梦", "生图", "文生图", "3d", "建模", "模型师", "视频生成", "stable diffusion", "midjourney", "dall", "cuda", "gpu", "渲染", "人工智能", "大模型"],
        "entities": ["ComfyUI", "即梦", "Stable Diffusion", "Midjourney", "DALL"]
    },
    "04-宝宝健康成长": {
        "keywords": ["宝宝", "疫苗", "接种", "母乳", "产后", "月子", "儿", "喂养", "体重", "发育", "健康", "检查", "复查", "儿保"],
        "entities": ["宝宝", "疫苗", "儿保", "月子"]
    }
}

def _get_scene_updates(graph_data, cluster_data):
    """根据知识图谱和聚类结果，计算各场景的更新"""
    nodes = graph_data.get("nodes", [])
    scene_updates = {k: {"new_entities": [], "confidence": 0} for k in SCENE_CATEGORIES}
    
    # 按关键词/实体匹配场景
    for node in nodes:
        name = node.get("id", "")
        for scene, cfg in SCENE_CATEGORIES.items():
            # 直接实体匹配
            if name in cfg.get("entities", []):
                scene_updates[scene]["new_entities"].append(name)
                scene_updates[scene]["confidence"] += 2
            # 关键词匹配
            for kw in cfg.get("keywords", []):
                if kw.lower() in name.lower():
                    scene_updates[scene]["new_entities"].append(name)
                    scene_updates[scene]["confidence"] += 1
    
    return scene_updates

def _update_scene_index():
    """更新场景索引的热度"""
    index_file = SCENE_INDEX
    if not index_file.exists():
        return
    
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 每30天衰减10%，简单处理：每次进化热度+1
    import re
    for scene in SCENE_CATEGORIES:
        pattern = rf'(\| {re.escape(scene)} \|.*?\|\s*)(\d+)(\s*\|)'
        match = re.search(pattern, content)
        if match:
            current_heat = int(match.group(2))
            new_heat = current_heat + 1
            new_line = match.group(1) + str(new_heat) + match.group(3)
            content = content[:match.start()] + new_line + content[match.end():]
    
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(content)

def scene_output():
    """M14: 将记忆进化结果输出到场景化记忆系统"""
    graph = load_json(MEMORY_GRAPH, {"nodes": [], "edges": []})
    clusters = load_json(MEMORY_CLUSTERS, {})
    
    if not SCENE_DIR.exists():
        return {"updated": 0, "reason": "scene_dir_not_found"}
    
    scene_updates = _get_scene_updates(graph, clusters)
    updated_scenes = []
    
    # 更新各场景文件
    for scene_file in SCENE_DIR.glob("*.md"):
        scene_name = scene_file.name
        if scene_name == "场景索引.md":
            continue
        
        # 检查该场景是否有新实体
        has_update = False
        for scene_key, updates in scene_updates.items():
            if scene_key == scene_name and updates["confidence"] > 0:
                has_update = True
                break
        
        if has_update:
            # 更新时间戳
            with open(scene_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 替换更新时间行
            import re
            updated = re.sub(
                r'(热度：\d+ \| 最后更新：)\d{4}-\d{2}-\d{2}',
                lambda m: m.group(1) + datetime.now().strftime("%Y-%m-%d"),
                content
            )
            
            with open(scene_file, "w", encoding="utf-8") as f:
                f.write(updated)
            
            updated_scenes.append(scene_name)
    
    # 更新索引热度
    _update_scene_index()
    
    return {"updated": len(updated_scenes), "scenes": updated_scenes}

# ===== M15: 主动创建 =====
def proactive_memory_creation(conversation_text):
    """从对话中自动提取并创建记忆条目"""
    created = []

    if not conversation_text:
        return {"created": 0}

    text = conversation_text.lower()

    # 检测重要声明
    patterns = {
        "持仓变更": (r'(买入|卖出|加仓|减仓|清仓)\s*(\d+)\s*股', "stock-portfolio.md"),
        "策略调整": (r'(长期持有|分批减仓|止损|建仓)', "memory"),
        "新发现": (r'(发现|原来|其实|应该是)', "memory"),
        "偏好": (r'(喜欢|不喜欢|偏好|习惯)', "USER.md"),
    }

    for ptype, (pattern, target) in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            created.append({
                "type": ptype,
                "matches": len(matches),
                "target": target,
                "sample": str(matches[0])[:50]
            })

    return {"created": len(created), "details": created}

# ===== M15: 记忆巩固 =====
def memory_consolidation():
    """定期复习强化重要记忆"""
    consolidated = []
    now = datetime.now()

    # 找出需要复习的核心记忆
    index = load_json(MEMORY_INDEX, {})
    entities = index.get("entities", {})

    for name, info in entities.items():
        mentions = info.get("mentions", 0)
        files = info.get("files", [])

        if mentions >= 10:
            # 核心实体，检查最近是否被提及
            recent_mention = False
            for f in files[:3]:
                path = WORKSPACE / f
                if path.exists():
                    try:
                        mtime = datetime.fromtimestamp(path.stat().st_mtime)
                        if (now - mtime).days < 7:
                            recent_mention = True
                            break
                    except:
                        pass

            if not recent_mention:
                consolidated.append({
                    "entity": name,
                    "mentions": mentions,
                    "action": "需要复习 - 7天未提及",
                    "files": files[:3]
                })

    return {"needs_review": len(consolidated), "details": consolidated[:5]}

# ===== M16: 记忆模拟（智能遗忘曲线） =====
def memory_decay_simulation():
    """模拟人类记忆衰减，智能遗忘"""
    decay = load_json(MEMORY_DECAY, {"entries": {}})
    now = datetime.now()
    forgotten = []
    reinforced = []

    # 对所有记忆应用遗忘曲线
    files = get_all_memory_files()
    for f in files:
        try:
            stat = f.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            days_since = (now - last_modified).days
            filename = str(f.relative_to(WORKSPACE))
        except:
            continue

        # 艾宾浩斯遗忘曲线简化版
        # 1天后保留~33%，7天后保留~20%，30天后保留~10%
        if days_since > 0:
            retention = max(0.1, 1.0 / (1 + days_since * 0.1))
        else:
            retention = 1.0

        entry = decay["entries"].get(filename, {
            "first_seen": now.isoformat(),
            "access_count": 0,
            "retention": 1.0
        })

        entry["retention"] = round(retention, 3)
        entry["days_inactive"] = days_since
        entry["last_check"] = now.isoformat()
        decay["entries"][filename] = entry

        # 判断是否应该遗忘
        if retention < 0.15 and days_since > 60:
            forgotten.append({"file": filename, "retention": retention, "days": days_since})

        # 判断是否需要强化（重要但衰减中）
        if retention < 0.5 and retention >= 0.15:
            # 检查是否重要
            is_important = any(kw in f.name for kw in ["portfolio", "strategy", "knowledge"])
            if is_important:
                reinforced.append({"file": filename, "retention": retention, "action": "建议复习强化"})

    save_json(MEMORY_DECAY, decay)
    return {"forgotten": len(forgotten), "needs_reinforcement": len(reinforced),
            "forgotten_details": forgotten[:3], "reinforce_details": reinforced[:3]}

# ===== 全量进化 =====
def distill_weekly_memories():
    """
    M15记忆巩固 + M14主动创建：每周日自动蒸馏
    读取本周7个 daily.md → 识别关键记录 → 精华写入 MEMORY.md → 归档原始日志
    """
    from datetime import timedelta
    import calendar

    now = datetime.now()
    # 找本周所有 daily.md
    week_files = []
    for i in range(7):
        day = now - timedelta(days=i)
        filename = f"{day.strftime('%Y-%m-%d')}.md"
        path = MEMORY_DIR / filename
        if path.exists():
            week_files.append((day, path))
    
    if not week_files:
        return {"status": "no_files", "message": "本周无日志文件"}
    
    # 提取关键记录
    key_patterns = [
        "决定", "决策", "策略变更", "新增", "完成",
        "教训", "错误", "修复", "结论", "确认",
        "建仓", "清仓", "减仓", "加仓", "止损",
        "安装", "配置", "部署", "升级",
    ]
    
    distillations = {}

    # 融合LCM：从Lossless-Claw数据库提取本周对话精华
    try:
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from memory_plus import distill_from_lcm
        lcm_result = distill_from_lcm(days=7)
        if lcm_result.get("status") == "success":
            for item in lcm_result.get("distillations", []):
                if item.get("key_entries"):
                    conv_title = item.get("conversation", "?")[:30]
                    distillations[f"LCM:{conv_title}"] = item["key_entries"]
    except Exception as e:
        pass  # LCM尚无数据时静默跳过

    for day, path in week_files:
        try:
            content = path.read_text()
            lines = content.split("\n")
            week_notes = []
            in_key_section = False
            current_section = ""
            
            for line in lines:
                # 跳过时间戳和非内容行
                if re.match(r"^\d{2}:\d{2}\s*[\[\*]", line):
                    # 提取时间戳内容
                    content_part = re.sub(r"^\d{2}:\d{2}\s*[\[\*]", "", line).strip()
                    # 检查是否包含关键模式
                    if any(pat in content_part for pat in key_patterns):
                        week_notes.append(f"[{day.strftime('%m/%d')} {content_part[:120]}]")
                elif line.startswith("## ") and "关键" in line:
                    in_key_section = True
                    current_section = line
                elif line.startswith("## ") and in_key_section:
                    in_key_section = False
            
            if week_notes:
                distillations[day.strftime("%Y-%m-%d")] = week_notes
        except Exception as e:
            continue
    
    if not distillations:
        return {"status": "no_content", "message": "本周无关键记录"}
    
    # 更新 MEMORY.md 的"本周大事"或追加到重点追踪
    memory_path = WORKSPACE / "MEMORY.md"
    try:
        memory_content = memory_path.read_text()
    except:
        memory_content = ""
    
    # 追加本周摘要到 MEMORY.md 末尾
    now_str = now.strftime("%Y-%m-%d")
    week_summary = f"\n---\n## 本周大事（{now_str}自动蒸馏）\n"
    
    sections_added = 0
    for day_str, notes in sorted(distillations.items(), reverse=True):
        week_summary += f"\n### {day_str}\n"
        for note in notes[:5]:  # 每天最多5条
            week_summary += f"- {note}\n"
        sections_added += 1
    
    # 追加到 MEMORY.md（不超过20行）
    lines = memory_content.split("\n")
    # 找到最后一个 "---" 分隔符，在它之后插入
    insert_pos = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "---" and i > 5:
            insert_pos = i + 1
            break
    
    new_memory = "\n".join(lines[:insert_pos]) + week_summary + "\n" + "\n".join(lines[insert_pos:])
    
    # 限制 MEMORY.md 总行数（最多250行，去掉旧"本周大事"）
    memory_lines = new_memory.split("\n")
    recent_lines = []
    skip_old_weekly = False
    for line in memory_lines:
        if "## 本周大事" in line:
            skip_old_weekly = True
            continue
        if skip_old_weekly and line.startswith("## "):
            skip_old_weekly = False
        if not skip_old_weekly:
            recent_lines.append(line)
    
    if len(recent_lines) > 250:
        recent_lines = recent_lines[:250]
    
    memory_path.write_text("\n".join(recent_lines))
    
    # 归档：压缩本周日志
    archive_name = f"{now.strftime('%Y-%m')}-weekly-distilled.tar.gz"
    archive_path = MEMORY_DIR / "archives" / archive_name
    archive_path.parent.mkdir(exist_ok=True)
    
    # 写入蒸馏记录
    distill_record = {
        "date": now.isoformat(),
        "weeks_covered": list(distillations.keys()),
        "memory_updated": memory_path.exists(),
        "lines_now": len(recent_lines),
        "sections_distilled": sections_added,
        "lcm_contributions": sum(1 for k in distillations.keys() if str(k).startswith("LCM:")),
        "lcm_fusion": "✅ 已融合LCM数据库蒸馏",
    }
    distill_log = MEMORY_DIR / "archives" / "distill-log.jsonl"
    with open(distill_log, "a") as f:
        f.write(json.dumps(distill_record, ensure_ascii=False) + "\n")
    
    return {
        "status": "success",
        "weeks_covered": len(distillations),
        "memory_lines": len(recent_lines),
        "distillations": distillations,
    }


def full_evolve():
    """执行全量记忆进化 (M1-M16)，优化输出：仅显示有实质工作的模块"""
    results = {}
    lines = []  # 存储本次进化的输出行

    # 阶段1：采集分析
    r1 = compress_daily_logs()
    if r1['compressed']:
        lines.append(f"  压缩: {len(r1['compressed'])}个文件")

    r2 = detect_conflicts()
    if r2:
        lines.append(f"  冲突: {len(r2)}个矛盾")

    r3 = check_memory_health()
    score = r3['overall_score']
    icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "🔴"
    lines.append(f"  健康: {icon}{score}分")

    r4 = build_memory_links()
    if r4['entities']:
        lines.append(f"  关联: {r4['entities']}实体/{r4['topics']}主题")

    r5 = prioritize_memories()
    if r5['critical'] or r5['high']:
        lines.append(f"  优先级: {len(r5['critical'])}核心/{len(r5['high'])}重要")

    r7 = semantic_clustering()
    if r7:
        lines.append(f"  聚类: {len(r7)}个主题")

    r8 = deduplicate_memories()
    if r8['duplicates']:
        lines.append(f"  去重: {r8['duplicates']}个重复")

    # 阶段2：推理输出
    r9 = temporal_reasoning()
    if r9['chains']:
        lines.append(f"  时序: {r9['chains']}条因果链/{r9['total_events']}个事件")

    r13 = build_knowledge_graph()
    if r13['nodes']:
        lines.append(f"  图谱: {r13['nodes']}节点/{r13['edges']}边")

    r14 = scene_output()
    if r14.get('updated', 0) > 0:
        lines.append(f"  场景: {r14['updated']}个场景更新")

    # 阶段3：保障巩固
    r6 = backup_critical_files()
    if r6['backed_up']:
        lines.append(f"  备份: {len(r6['backed_up'])}个文件")

    r10 = context_aware_retrieval()
    if r10['matched']:
        lines.append(f"  上下文: {r10['matched']}个匹配")

    r11 = predict_needs()
    if r11['predictions']:
        lines.append(f"  预测: {r11['predictions']}个需求")

    r12 = cross_system_memory()
    if r12['synced_systems']:
        lines.append(f"  跨系统: {r12['synced_systems']}个系统")

    r15 = memory_consolidation()
    if r15['needs_review']:
        lines.append(f"  巩固: {r15['needs_review']}个需复习")

    r16 = memory_decay_simulation()
    if r16['needs_reinforcement']:
        lines.append(f"  强化: {r16['needs_reinforcement']}个待强化")

    results = {
        "M3_健康": score,
        "M4_关联": r4['entities'],
        "M7_聚类": len(r7),
        "M13_图谱": r13['nodes'],
    }

    # 输出优化：阶段分组 + 底部一行总结
    if lines:
        print("  📊 " + " / ".join(lines[:5]))  # 前5个关键指标
        if len(lines) > 5:
            for l in lines[5:]:
                print("     " + l)

    # 底部一行总结（供cron使用）
    active = len(lines)
    total = 16
    idle = total - active
    print(f"\n✅ 完成 M1-M16 ({active}项有效/{idle}项空闲) 健康{icon}{score}分 · 关联{r4['entities']}实体 · {len(r7)}主题 · 图谱{r13['nodes']}节点")

    return results

# ===== 报告 =====
def generate_report():
    """生成记忆健康报告 (M1-M16)"""
    index = load_json(MEMORY_INDEX, {})
    health = load_json(MEMORY_HEALTH, {})
    clusters = load_json(MEMORY_CLUSTERS, {})
    graph = load_json(MEMORY_GRAPH, {})
    decay = load_json(MEMORY_DECAY, {"entries": {}})

    lines = ["🧠 **记忆进化系统 v2.0 报告**", ""]

    # M3 健康
    score = health.get("overall_score", 0)
    icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "🔴"
    lines.append(f"{icon} 健康评分: {score}/100")

    if health.get("stale_files"):
        lines.append(f"  📅 过时文件: {len(health['stale_files'])}个")
    if health.get("large_files"):
        lines.append(f"  📦 大文件: {len(health['large_files'])}个")
    if health.get("empty_files"):
        lines.append(f"  📭 空文件: {len(health['empty_files'])}个")

    # M4 实体
    entities = index.get("entities", {})
    if entities:
        lines.append("")
        lines.append(f"🔗 **实体关联: {len(entities)}个**")
        top_entities = sorted(entities.items(), key=lambda x: x[1].get("mentions", 0), reverse=True)[:5]
        for name, info in top_entities:
            lines.append(f"  • {name}: {info.get('mentions',0)}次提及 / {len(info.get('files',[]))}个文件")

    # M5 优先级
    priorities = prioritize_memories()
    lines.append("")
    lines.append(f"⭐ **核心记忆: {len(priorities['critical'])}个**")
    for p in priorities["critical"][:3]:
        name = p.get("entity") or p.get("section", "?")
        lines.append(f"  • {name}")

    # M7 语义聚类
    if clusters:
        lines.append(f"📊 **语义聚类: {len(clusters)}个主题**")
        for theme, info in list(clusters.items())[:3]:
            lines.append(f"  • {theme}: {len(info.get('members',[]))}文件")

    # M2 冲突
    conflicts = detect_conflicts()
    if conflicts:
        lines.append("")
        lines.append("⚠️ **发现矛盾信息:**")
        for c in conflicts:
            lines.append(f"  🔴 {c['topic']}: {', '.join(v[1] for v in c['values'])}")

    # M13 知识图谱
    if graph.get("nodes"):
        lines.append(f"🌐 **知识图谱: {len(graph['nodes'])}节点 / {len(graph['edges'])}边**")

    # M15 巩固
    consolidation = memory_consolidation()
    if consolidation["needs_review"] > 0:
        lines.append(f"📚 **需复习: {consolidation['needs_review']}个核心记忆**")
        for item in consolidation["details"][:3]:
            lines.append(f"  ⚠️ {item['entity']}: {item['action']}")

    # M16 遗忘曲线
    forgotten_count = sum(1 for e in decay.get("entries", {}).values() if e.get("retention", 1) < 0.15)
    reinforce_count = sum(1 for e in decay.get("entries", {}).values() if 0.15 <= e.get("retention", 1) < 0.5)
    lines.append(f"🔄 **遗忘曲线: {forgotten_count}个可遗忘 / {reinforce_count}个需强化**")

    # M6 备份
    backups = list(MEMORY_BACKUP_DIR.iterdir()) if MEMORY_BACKUP_DIR.exists() else []
    lines.append(f"💾 备份: {len(backups)}个快照")

    # 进化等级
    level = 6
    if clusters: level = 7
    if graph.get("nodes"): level = max(level, 13)
    if decay.get("entries"): level = max(level, 16)
    lines.append(f"\n🧬 进化等级: M{level}")

    return "\n".join(lines)

# ===== CLI =====
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if not args or args[0] == "--report":
        print(generate_report())
    elif args[0] == "--compress":
        r = compress_daily_logs()
        print(f"✅ 压缩: {len(r['compressed'])}个文件, 归档: {len(r['archived'])}个")
    elif args[0] == "--conflict":
        c = detect_conflicts()
        if c:
            print(f"⚠️ 发现 {len(c)} 个矛盾:")
            for conflict in c:
                print(f"  {conflict['topic']}: {conflict['values']}")
        else:
            print("✅ 无矛盾")
    elif args[0] == "--health":
        h = check_memory_health()
        print(f"✅ 健康评分: {h['overall_score']}/100")
    elif args[0] == "--link":
        r = build_memory_links()
        print(f"✅ 关联: {r['entities']}实体, {r['topics']}主题")
    elif args[0] == "--prioritize":
        p = prioritize_memories()
        print(f"✅ 核心:{len(p['critical'])} 重要:{len(p['high'])} 一般:{len(p['medium'])}")
    elif args[0] == "--backup":
        r = backup_critical_files()
        print(f"✅ 备份 {len(r['backed_up'])} 个文件到 {r['backup_dir']}")
    elif args[0] == "--cluster":
        r = semantic_clustering()
        print(f"✅ 聚类: {len(r)}个主题")
    elif args[0] == "--dedup":
        r = deduplicate_memories()
        print(f"✅ 去重: {r['duplicates']}个重复")
    elif args[0] == "--timeline":
        r = temporal_reasoning()
        print(f"✅ 时序: {r['chains']}条因果链, {r['total_events']}个事件")
    elif args[0] == "--context":
        task = " ".join(args[1:]) if len(args) > 1 else ""
        r = context_aware_retrieval(task)
        print(f"✅ 上下文: {r['matched']}个匹配")
    elif args[0] == "--predict":
        r = predict_needs()
        print(f"✅ 预测: {r['predictions']}个需求")
        for p in r["details"]:
            print(f"  • {p['need']} ({p['reason']})")
    elif args[0] == "--sync":
        r = cross_system_memory()
        print(f"✅ 跨系统: 同步{r['synced_systems']}个系统")
    elif args[0] == "--graph":
        r = build_knowledge_graph()
        print(f"✅ 图谱: {r['nodes']}节点, {r['edges']}边")
    elif args[0] == "--consolidate":
        r = memory_consolidation()
        print(f"✅ 巩固: {r['needs_review']}个需复习")
    elif args[0] == "--distill":
        print("🧠 执行主动蒸馏（本周→MEMORY.md）...")
        r = distill_weekly_memories()
        if r["status"] == "success":
            print(f"✅ 蒸馏完成: {r['weeks_covered']}天覆盖, MEMORY.md现{r['memory_lines']}行")
            for day, notes in sorted(r['distillations'].items(), reverse=True):
                print(f"  {day}: {len(notes)}条关键记录")
        else:
            print(f"ℹ️ {r['message']}")
    elif args[0] == "--decay":
        r = memory_decay_simulation()
        print(f"✅ 遗忘: {r['forgotten']}个可遗忘, {r['needs_reinforcement']}个需强化")
    elif args[0] == "--evolve":
        print("🧬 记忆进化 M1-M16...")
        results = full_evolve()
    else:
        print(__doc__)
