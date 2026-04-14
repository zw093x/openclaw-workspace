#!/usr/bin/env python3
"""
场景记忆系统 - Scene Memory v1.0
从对话历史中提取关键内容，自动写入对应场景
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

SCENE_DIR = Path("/root/.openclaw/workspace/skills/scene-memory/references")
INDEX_FILE = SCENE_DIR / "场景索引.md"

# 场景关键词映射
SCENE_KEYWORDS = {
    "01-数字环境与工作流": [
        "cron", "定时", "任务", "备份", "git", "openclaw", "服务器",
        "安装", "配置", "修复", "更新", "推送", "飞书", "docker",
        "skill", "插件", "腾讯云", "代理", "mihomo", "脚本"
    ],
    "02-投资管理与交易策略": [
        "股票", "持仓", "成本", "买入", "卖出", "建仓", "清仓",
        "止损", "涨跌", "股价", "大盘", "板块", "资金", "主力",
        "船舶", "动力", "三安", "视源", "600150", "600482",
        "大宗商品", "黄金", "白银", "甲醇", "持仓"
    ],
    "03-AI技术与产品研究": [
        "ai", "comfyui", "提示词", "即梦", "生图", "文生图",
        "3d", "建模", "模型师", "视频生成", "stable diffusion",
        "midjourney", "dall", "cuda", "gpu", "渲染"
    ],
    "04-宝宝健康成长": [
        "宝宝", "疫苗", "接种", "母乳", "产后", "月子", "儿",
        "喂养", "体重", "发育", "健康", "检查", "复查"
    ]
}

def get_topic_from_message(text: str) -> str:
    """根据消息内容判断所属场景"""
    text_lower = text.lower()
    scores = {}
    
    for scene, keywords in SCENE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores[scene] = score
    
    if not scores or max(scores.values()) == 0:
        return None
    
    return max(scores, key=scores.get)


def read_scene_file(scene_name: str) -> str:
    """读取场景文件内容"""
    scene_file = SCENE_DIR / f"{scene_name}.md"
    if scene_file.exists():
        with open(scene_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def update_scene(scene_name: str, new_content: str, source: str = "对话") -> bool:
    """向场景追加新内容"""
    scene_file = SCENE_DIR / f"{scene_name}.md"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## 新增记录 [{timestamp}]（来源: {source}）\n{new_content}\n"
    
    with open(scene_file, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    # 更新索引热度
    update_index(scene_name)
    
    return True


def update_index(scene_name: str, heat_increment: int = 1):
    """更新场景索引的热度"""
    if not INDEX_FILE.exists():
        return
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单热度更新：查找场景行，+1
    pattern = rf'(\| {re.escape(scene_name)} \|.*?\|\s*)(\d+)(\s*\|)'
    match = re.search(pattern, content)
    if match:
        current_heat = int(match.group(2))
        new_heat = current_heat + heat_increment
        new_line = match.group(1) + str(new_heat) + match.group(3)
        content = content[:match.start()] + new_line + content[match.end():]
        
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            f.write(content)


def list_scenes() -> dict:
    """列出所有场景"""
    scenes = {}
    for f in SCENE_DIR.glob("*.md"):
        if f.name == "场景索引.md":
            continue
        with open(f, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            scenes[f.stem] = first_line
    return scenes


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法: scene_memory.py <命令> [参数]")
        print("命令:")
        print("  list                      列出所有场景")
        print("  search <关键词>           搜索所有场景")
        print("  read <场景名>             读取场景内容")
        print("  append <场景名> <内容>    追加内容到场景")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        scenes = list_scenes()
        print("可用场景:")
        for name, desc in scenes.items():
            print(f"  {name}: {desc}")
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("请提供搜索关键词")
            sys.exit(1)
        keyword = sys.argv[2].lower()
        print(f"搜索关键词: {keyword}\n")
        for f in SCENE_DIR.glob("*.md"):
            if f.name == "场景索引.md":
                continue
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            if keyword in content.lower():
                print(f"命中: {f.stem}")
                # 找出包含关键词的行
                for line in content.split('\n'):
                    if keyword in line.lower():
                        print(f"  → {line.strip()[:80]}")
    
    elif cmd == "read":
        if len(sys.argv) < 3:
            print("请提供场景名")
            sys.exit(1)
        scene_name = sys.argv[2]
        if not scene_name.endswith('.md'):
            scene_name = scene_name + '.md'
        scene_file = SCENE_DIR / scene_name
        if scene_file.exists():
            with open(scene_file, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print(f"场景不存在: {scene_name}")
    
    elif cmd == "append":
        if len(sys.argv) < 4:
            print("请提供场景名和内容")
            sys.exit(1)
        scene_name = sys.argv[2]
        content = sys.argv[3]
        update_scene(scene_name, content)
        print(f"已追加到 {scene_name}")
    
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
