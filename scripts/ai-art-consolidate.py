#!/usr/bin/env python3
"""
AI Art 周整合汇总脚本
- 每周日执行
- 读取本周收集的资讯
- 生成摘要报告
- 推送给 P工（通过飞书）
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
KNOWLEDGE_FILE = MEMORY_DIR / "ai-art-research.md"
LOG_FILE = MEMORY_DIR / "ai-art-self-learn.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{ts}] {msg}")

def read_this_week_updates():
    """读取本周的更新内容"""
    try:
        content = KNOWLEDGE_FILE.read_text()
        # 找到最新的"学习更新"段落
        sections = content.split("## 学习更新")
        if len(sections) < 2:
            return []
        
        last_section = sections[-1].split("\n---")[0]
        items = []
        for part in last_section.split("### ["):
            if "级]" in part:
                level = part[:1]
                rest = part[3:].split("\n", 1)
                title = rest[0].strip()
                snippet = rest[1].split("来源:")[0].strip()[:200] if len(rest) > 1 else ""
                items.append({"level": level, "title": title, "snippet": snippet})
        return items
    except Exception as e:
        log(f"读取失败: {e}")
        return []

def generate_summary(updates):
    """生成汇总报告"""
    if not updates:
        return "本周无新资讯更新"
    
    # 统计来源等级
    levels = Counter([u["level"] for u in updates])
    
    report = f"""
## 📊 AI Art 本周资讯汇总

**更新时间**: {datetime.now().strftime('%Y-%m-%d')}
**收集数量**: {len(updates)} 条

### 来源分布
- A级: {levels.get('A', 0)} 条
- B级: {levels.get('B', 0)} 条

### 重点资讯

"""
    for i, u in enumerate(updates[:5], 1):
        report += f"{i}. **[{u['level']}级]** {u['title']}\n"
        if u['snippet']:
            report += f"   {u['snippet'][:100]}...\n"
    
    return report

def send_to_feishu(summary):
    """推送摘要到飞书"""
    try:
        # TODO: 调用飞书推送
        log("推送内容准备完成")
        return True
    except Exception as e:
        log(f"推送失败: {e}")
        return False

def main():
    log("=" * 50)
    log("AI Art 周整合汇总开始")
    
    updates = read_this_week_updates()
    log(f"本周收集到 {len(updates)} 条资讯")
    
    summary = generate_summary(updates)
    log("汇总报告:\n" + summary[:500])
    
    # 写入汇总文件
    weekly_file = MEMORY_DIR / f"ai-art-weekly-{datetime.now().strftime('%Y%m%d')}.md"
    weekly_file.write_text(summary)
    log(f"汇总已保存: {weekly_file.name}")
    
    log("AI Art 周整合汇总完成")
    log("=" * 50)

if __name__ == "__main__":
    main()
