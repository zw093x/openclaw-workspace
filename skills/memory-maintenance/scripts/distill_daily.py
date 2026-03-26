#!/usr/bin/env python3
"""
每日记忆提炼脚本
从 memory/YYYY-MM-DD.md 提取关键信息，对比 MEMORY.md 后合并。

用法:
    python distill_daily.py --date today
    python distill_daily.py --date 2026-03-25
    python distill_daily.py --dry-run  # 只分析不写入
"""

import argparse
import os
import re
from datetime import datetime, timedelta
from pathlib import Path


WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/root/.openclaw/workspace"))


def resolve_date(date_str: str) -> str:
    """解析日期字符串"""
    if date_str == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return date_str


def read_daily(date: str) -> str:
    """读取每日记录"""
    path = WORKSPACE / "memory" / f"{date}.md"
    if not path.exists():
        print(f"[Distill] 未找到: {path}")
        return None
    return path.read_text(encoding="utf-8")


def read_memory() -> str:
    """读取 MEMORY.md"""
    path = WORKSPACE / "MEMORY.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_valuable_entries(daily_content: str, date: str) -> list:
    """从每日记录中提取值得长期保留的信息"""
    valuable = []
    current_section = ""
    
    # 标记值得保留的关键词
    keep_patterns = [
        r"确认|决定|改为|更新|修改",  # 决策变更
        r"偏好|喜欢|不要|要求",        # 用户偏好
        r"持仓|成本|买入|卖出|操作",    # 财务操作
        r"进度|完成|里程碑|达成",       # 项目进展
        r"教训|错误|避免|注意",         # 学习经验
        r"重要|关键|必须|务必",         # 强调事项
    ]
    
    skip_patterns = [
        r"^#+\s*(天气|每日|例行|检查|状态)$",  # 常规检查标题
        r"HEARTBEAT_OK",
        r"已推送|已发送|已通知",
    ]
    
    lines = daily_content.split("\n")
    for line in lines:
        # 跟踪当前章节
        if line.startswith("#"):
            current_section = line.strip("# ").strip()
            continue
        
        # 跳过无价值内容
        if any(re.search(p, line) for p in skip_patterns):
            continue
        
        # 检查是否有保留价值
        if any(re.search(p, line) for p in keep_patterns):
            valuable.append({
                "date": date,
                "section": current_section,
                "content": line.strip(),
            })
    
    return valuable


def check_duplicate(content: str, memory: str) -> bool:
    """检查内容是否已存在于 MEMORY.md"""
    # 简单的关键词匹配
    key_phrases = re.findall(r'[\u4e00-\u9fff]{4,}|[A-Za-z_]{8,}', content)
    if not key_phrases:
        return False
    
    matches = sum(1 for phrase in key_phrases if phrase in memory)
    return matches >= len(key_phrases) * 0.6  # 60% 匹配率视为重复


def suggest_section(content: str) -> str:
    """根据内容建议放入 MEMORY.md 的哪个章节"""
    section_map = {
        "用户档案": ["姓名", "性别", "出生", "职业", "居住", "配偶"],
        "沟通偏好": ["风格", "要求", "偏好", "沟通"],
        "股票持仓": ["持仓", "股票", "成本", "买入", "卖出", "中国船舶", "中国动力"],
        "关注领域": ["关注", "领域", "优先"],
        "定时任务": ["任务", "定时", "推送", "提醒"],
        "重点待处理": ["待处理", "异常", "排查", "修复"],
    }
    
    for section, keywords in section_map.items():
        if any(kw in content for kw in keywords):
            return section
    
    return "重要事项"


def distill(date: str, dry_run: bool = False):
    """执行提炼"""
    print(f"[Distill] 处理日期: {date}")
    
    daily = read_daily(date)
    if not daily:
        return
    
    memory = read_memory()
    entries = extract_valuable_entries(daily, date)
    
    if not entries:
        print("[Distill] 无需提炼的内容")
        return
    
    new_items = []
    dup_items = []
    
    for entry in entries:
        if check_duplicate(entry["content"], memory):
            dup_items.append(entry)
        else:
            new_items.append(entry)
    
    print(f"[Distill] 提取 {len(entries)} 条，新增 {len(new_items)} 条，重复 {len(dup_items)} 条")
    
    if not new_items:
        print("[Distill] 无新内容需要写入")
        return
    
    # 生成待添加内容
    additions = []
    for item in new_items:
        section = suggest_section(item["content"])
        additions.append(f"### {section} ({item['date']})\n- {item['content']}")
    
    output = "\n\n".join(additions)
    
    if dry_run:
        print("\n[Distill] Dry run - 待添加内容:")
        print(output)
    else:
        # 追加到 MEMORY.md
        memory_path = WORKSPACE / "MEMORY.md"
        with open(memory_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n## 记忆提炼 ({date})\n\n{output}\n")
        print(f"[Distill] 已写入 {memory_path}")


def main():
    parser = argparse.ArgumentParser(description="每日记忆提炼")
    parser.add_argument("--date", default="today", help="日期 (YYYY-MM-DD / today / yesterday)")
    parser.add_argument("--dry-run", action="store_true", help="只分析不写入")
    args = parser.parse_args()
    
    date = resolve_date(args.date)
    distill(date, args.dry_run)


if __name__ == "__main__":
    main()
