#!/usr/bin/env python3
"""
Report formatter - converts raw information into standardized reports.

Usage:
    python format_report.py --type daily --topic ai-news --days 1
    python format_report.py --type custom --input results.json --template industry
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


TEMPLATES_DIR = Path(__file__).parent.parent / "assets"


def load_template(template_name: str) -> str:
    """Load a report template"""
    template_path = TEMPLATES_DIR / f"{template_name}-template.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return None


def generate_report_header(report_type: str, topic: str, days: int) -> str:
    """Generate report header"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    topic_names = {
        "ai-news": "AI 行业日报",
        "cg-news": "CG 行业资讯",
        "tech-news": "科技资讯日报",
        "stock-news": "股票资讯",
        "shipping-news": "航运行业资讯",
        "all": "综合周报",
    }
    
    title = topic_names.get(topic, f"{topic} 资讯")
    
    if report_type == "weekly":
        start = (datetime.now() - timedelta(days=days)).strftime("%m/%d")
        end = datetime.now().strftime("%m/%d")
        title = f"{title} ({start}-{end})"
    
    return f"# {title} ({date_str})\n\n> 数据整理自多源信息，按热度/重要性排序\n"


def format_items(items: list, max_items: int = 10) -> str:
    """Format a list of items with priority icons"""
    output = []
    
    priority_icons = {
        "hot": "🔥",
        "data": "📊",
        "insight": "💡",
        "update": "🆕",
        "warning": "⚠️",
        "normal": "📌",
    }
    
    for i, item in enumerate(items[:max_items]):
        icon = priority_icons.get(item.get("priority", "normal"), "📌")
        title = item.get("title", "Untitled")
        summary = item.get("summary", "")
        source = item.get("source", "")
        url = item.get("url", "")
        
        line = f"{icon} **{title}**"
        if summary:
            line += f"\n   {summary}"
        if url:
            line += f"\n   [来源]({url})"
        elif source:
            line += f"\n   来源: {source}"
        
        output.append(line)
    
    return "\n\n".join(output)


def format_section(title: str, items: list) -> str:
    """Format a section with items"""
    if not items:
        return ""
    return f"## {title}\n\n{format_items(items)}\n"


def generate_report(config: dict) -> str:
    """Generate a complete report from config"""
    parts = []
    
    # Header
    parts.append(generate_report_header(
        config.get("type", "daily"),
        config.get("topic", "general"),
        config.get("days", 1)
    ))
    
    # Summary
    if config.get("summary"):
        parts.append(f"> {config['summary']}\n")
    
    # Main sections
    sections = config.get("sections", [])
    for section in sections:
        content = format_section(section["title"], section.get("items", []))
        if content:
            parts.append(content)
    
    # Impact analysis
    if config.get("impact"):
        parts.append(f"## 影响分析\n\n{config['impact']}\n")
    
    # Footer
    sources = config.get("sources", [])
    source_str = ", ".join(sources) if sources else "多源"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts.append(f"---\n*来源: {source_str} | 生成时间: {timestamp}*")
    
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Report formatter")
    parser.add_argument("--type", default="daily", choices=["daily", "weekly", "industry", "briefing", "custom"])
    parser.add_argument("--topic", default="general", help="Report topic")
    parser.add_argument("--days", type=int, default=1, help="Coverage period in days")
    parser.add_argument("--input", help="Input JSON file with raw items")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--template", help="Template name to use")
    args = parser.parse_args()
    
    config = {
        "type": args.type,
        "topic": args.topic,
        "days": args.days,
    }
    
    # Load items from file if provided
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
            if isinstance(data, list):
                config["sections"] = [{"title": "资讯汇总", "items": data}]
            elif isinstance(data, dict):
                config.update(data)
    
    report = generate_report(config)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"[OK] Report saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
