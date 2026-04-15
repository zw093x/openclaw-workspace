#!/usr/bin/env python3
"""
AI Art 自主学习脚本 v3.0
- 优先抓取 A 级官方来源（arXiv/HuggingFace/官方博客）
- 补充高质量教程
- 过滤并标记来源等级
"""

import subprocess
import json
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SKILL_FILE = WORKSPACE / "skills/ai-art-master/SKILL.md"
KNOWLEDGE_FILE = MEMORY_DIR / "ai-art-research.md"
LOG_FILE = MEMORY_DIR / "ai-art-self-learn.log"
API_KEY = "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"

# ============================================
# A级来源（官方/权威，必须抓）
# ============================================
ARXIV_QUERIES = [
    "site:arxiv.org FLUX image generation 2026",
    "site:arxiv.org Stable Diffusion video generation 2026", 
    "site:arxiv.org AI video generation model 2026",
    "site:arxiv.org text-to-image diffusion model 2026",
]

HF_BLOG_QUERIES = [
    "site:huggingface.co FLUX model 2026",
    "site:huggingface.co stable diffusion tutorial",
    "site:huggingface.co AI image generation guide",
]

OFFICIAL_QUERIES = [
    "FLUX.1 official update 2026",
    "Stable Diffusion official announcement 2026",
    "Midjourney official news 2026",
    "ComfyUI official release 2026",
    "即梦 字节跳动 官方 2026",
    "Seedance 字节 官方 2026",
]

# ============================================
# B级来源（高质量教程/社区）
# ============================================
TUTORIAL_QUERIES = [
    "FLUX.1 tutorial workflow 2026",
    "Stable Diffusion XL best practices 2026",
    "AI video prompt engineering guide 2026",
    "ComfyUI FLUX workflow tutorial",
    "Midjourney V7 tips and tricks",
]

# B级来源过滤规则
TIER_B_PATTERNS = [
    "civitai.com", "reddit.com", "twitter.com", "x.com",
    "36kr.com", "机器之心", "量子位", "aigc", " zirconbook"
]

# 降低优先级（尽量排后）
TIER_C_PATTERNS = ["baidu.com", "sina.com", "weibo.com", "sohu.com", "bilibili.com"]

SEARCH_QUERIES = ARXIV_QUERIES + HF_BLOG_QUERIES + OFFICIAL_QUERIES + TUTORIAL_QUERIES

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def search_tavily(query, max_results=5):
    """通过 Tavily API 搜索"""
    try:
        import requests
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False
            },
            timeout=20
        )
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        log(f"搜索失败: {e}")
        return []

def classify_source(url):
    """分类来源等级"""
    url_lower = url.lower()
    
    # A级：官方/权威
    a_patterns = [
        "arxiv.org", "huggingface.co/blog", "stability.ai/blog",
        "blackforestlabs.ai", "openai.com/blog", "midjourney.com/blog",
        "runwayml.com/blog", "bytes.==.ai/blog", "jimeng.com"
    ]
    for p in a_patterns:
        if p in url_lower:
            return "A"
    
    # B级：高质量教程/社区
    for p in TIER_B_PATTERNS:
        if p in url_lower:
            return "B"
    
    # C级：降权
    for p in TIER_C_PATTERNS:
        if p in url_lower:
            return "C"
    
    return "B"  # 默认B

def extract_key_info(result):
    """提取关键信息"""
    return {
        "title": result.get("title", ""),
        "url": result.get("url", ""),
        "snippet": result.get("content", "")[:300],
        "source": classify_source(result.get("url", "")),
        "timestamp": datetime.now().strftime("%Y-%m-%d")
    }

def format_update(new_items):
    """格式化更新内容"""
    # A级放前面
    a_items = sorted([i for i in new_items if i["source"] == "A"], key=lambda x: -len(x["snippet"]))
    b_items = sorted([i for i in new_items if i["source"] == "B"], key=lambda x: -len(x["snippet"]))
    
    lines = [f"\n---\n\n## 学习更新 {datetime.now().strftime('%Y-%m-%d')}"]
    lines.append(f"\n| 等级 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| A级(官方) | {len(a_items)} |")
    lines.append(f"| B级(教程) | {len(b_items)} |")
    lines.append("")
    
    if a_items:
        lines.append("### 🏛️ A级来源（官方/权威）\n")
        for item in a_items:
            lines.append(f"**{item['title']}**")
            lines.append(f"来源: {item['url']}")
            lines.append(f"{item['snippet']}")
            lines.append("")
    
    if b_items:
        lines.append("### 📚 B级来源（教程/社区）\n")
        for item in b_items[:10]:  # 最多10条
            lines.append(f"**{item['title']}**")
            lines.append(f"来源: {item['url']}")
            lines.append(f"{item['snippet']}")
            lines.append("")
    
    return "\n".join(lines)

def update_knowledge(new_items):
    """更新知识库"""
    if not new_items:
        return False
    
    a_count = sum(1 for i in new_items if i["source"] == "A")
    b_count = sum(1 for i in new_items if i["source"] == "B")
    
    update_content = format_update(new_items)
    
    with open(KNOWLEDGE_FILE, "a") as f:
        f.write(update_content)
    
    return True, a_count, b_count

def main():
    log("=" * 50)
    log("AI Art 自主学习开始 (v3.0)")
    
    all_updates = []
    query_count = {"arxiv": 0, "official": 0, "tutorial": 0}
    
    for i, query in enumerate(SEARCH_QUERIES):
        if query.startswith("site:arxiv.org"):
            qtype = "arxiv"
        elif any(x in query for x in ["official", "即梦", "Seedance"]):
            qtype = "official"
        else:
            qtype = "tutorial"
        
        log(f"[{qtype}] {query[:60]}")
        results = search_tavily(query)
        
        for r in results:
            info = extract_key_info(r)
            if info["source"] in ["A", "B"]:
                all_updates.append(info)
                query_count[qtype] += 1
        
        import time
        time.sleep(0.5)  # 避免频率过高
    
    log(f"收集统计: A级官方={sum(1 for i in all_updates if i['source']=='A')}, B级教程={sum(1 for i in all_updates if i['source']=='B')}")
    
    # 更新知识库
    if all_updates:
        ok, a_cnt, b_cnt = update_knowledge(all_updates)
        if ok:
            log(f"知识库已更新: A级{a_cnt}条, B级{b_cnt}条")
        
        # 更新技能文件
        update_content = format_update(all_updates[:15])
        with open(SKILL_FILE, "a") as f:
            f.write(update_content)
        log("技能文件已更新")
    else:
        log("无更新")
    
    log("AI Art 自主学习完成")
    log("=" * 50)

if __name__ == "__main__":
    main()
