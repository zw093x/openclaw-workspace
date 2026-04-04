#!/usr/bin/env python3
"""
每日对话总结飞书文档更新脚本
每晚22:05执行，读取当日memory文件并更新飞书文档
文档ID: OB0odqEoioMeWZxDqFIcZE92nec
文档URL: https://feishu.cn/docx/OB0odqEoioMeWZxDqFIcZE92nec
"""

import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
DOC_ID = "OB0odqEoioMeWZxDqFIcZE92nec"
APP_ID = "cli_a9489e1f4c78dbb6"
APP_SECRET = "mKeApaf2UE3CDN8wlh1IJcDSxcJlYlhD"

def get_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read()).get("tenant_access_token", "")

def read_daily_memory():
    """读取今日memory文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = MEMORY_DIR / f"{today}.md"
    
    if not memory_file.exists():
        return None, f"今日文件不存在: {memory_file}"
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取当日关键内容（去除增量备份区块）
    sections = content.split("\n## ")
    
    key_sections = []
    for section in sections:
        if not section.strip():
            continue
        # 跳过增量备份区块
        if section.startswith("增量备份"):
            # 只取第一个时间条目（当日对话）
            match = re.search(r'\*\*(\d{2}:\d{2})\*\*.*?\*\*(.*?)\*\*', section)
            continue
        if section.startswith("盘中监控") or section.startswith("每日策略学习"):
            continue  # 跳过盘中快照和技术分析
        key_sections.append(section)
    
    return key_sections, None

def extract_summary_sections(memory_content):
    """从memory中提取每日总结的各板块"""
    lines = memory_content.split('\n')
    sections = {}
    current_section = "其他"
    current_lines = []
    
    for line in lines:
        if line.startswith('## '):
            if current_lines:
                sections[current_section] = '\n'.join(current_lines)
            current_section = line.replace('## ', '').strip()
            current_lines = []
        else:
            current_lines.append(line)
    
    if current_lines:
        sections[current_section] = '\n'.join(current_lines)
    
    return sections

def format_daily_summary():
    """生成当日摘要"""
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]
    
    memory_file = MEMORY_DIR / f"{today}.md"
    if not memory_file.exists():
        return None
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取关键部分
    sections = extract_summary_sections(content)
    
    # 过滤出核心内容
    important_sections = {}
    skip_keywords = ["增量备份", "盘中监控", "每日策略学习", "## 规则更新"]  # 规则更新保留
    
    for title, body in sections.items():
        skip = False
        for kw in skip_keywords:
            if kw in title:
                skip = True
                break
        if skip and title != "规则更新":
            continue
        if body.strip() and len(body.strip()) > 20:
            important_sections[title] = body
    
    # 构建格式化的摘要
    output = [f"## {today}（{weekday}）对话摘要\n"]
    
    # 核心板块
    key_topics = ["交易", "系统", "学习", "持仓", "策略", "变更", "决策", "配置"]
    for title, body in important_sections.items():
        for kw in key_topics:
            if kw in title:
                output.append(f"\n### {title}\n")
                # 取前500字
                output.append(body[:500])
                if len(body) > 500:
                    output.append("...\n")
                break
    
    # 如果没有特定匹配，输出全部
    if len(output) <= 2 and important_sections:
        for title, body in list(important_sections.items())[:5]:
            output.append(f"\n### {title}\n")
            output.append(body[:300] + ("..." if len(body) > 300 else ""))
    
    return ''.join(output)

def append_to_feishu_doc(token, content):
    """追加内容到飞书文档末尾"""
    if not content:
        return True  # 无内容算成功
    
    # 获取文档块列表
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_ID}/blocks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    
    block_ids = result.get("data", {}).get("items", [])
    last_block_id = block_ids[-1].get("block_id", "") if block_ids else None
    
    if not last_block_id:
        return False
    
    # 插入分隔线和日期标题
    insert_content = f"\n---\n\n## {datetime.now().strftime('%Y-%m-%d')}（{['周一','周二','周三','周四','周五','周六','周日'][datetime.now().weekday()]}）自动摘要\n\n{content}\n"
    
    # 使用paragraphs.create插入
    url2 = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_ID}/blocks/{last_block_id}/children"
    data = json.dumps({
        "children": [{
            "block_type": 2,  # Paragraph
            "text": {
                "elements": [{"text_run": {"content": insert_content}}],
                "style": {}
            }
        }]
    }).encode()
    req2 = urllib.request.Request(url2, data=data, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, method="POST")
    
    try:
        with urllib.request.urlopen(req2, timeout=15) as resp:
            return json.loads(resp.read()).get("code") == 0
    except Exception as e:
        print(f"追加文档失败: {e}")
        return False

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 读取当日memory
    memory_file = MEMORY_DIR / f"{today}.md"
    if not memory_file.exists():
        print(f"ℹ️ 今日memory文件不存在: {today}")
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取当日对话（排除旧日期和系统消息）
    lines = content.split('\n')
    new_lines = []
    skip_sections = ["增量备份 (2026-", "盘中监控", "每日策略学习"]
    
    in_skip = False
    for line in lines:
        skip = False
        for kw in skip_sections:
            if kw in line:
                skip = True
                break
        if skip:
            in_skip = True
            continue
        if line.startswith("## ") and not any(kw in line for kw in ["规则更新", "系统", "交易", "持仓", "策略", "决策"]):
            in_skip = False
        if not in_skip:
            new_lines.append(line)
    
    summary = '\n'.join(new_lines).strip()
    
    # 更新飞书文档（覆盖写入，用append追加模式）
    token = get_token()
    if not token:
        print("❌ 获取token失败")
        return
    
    # 直接全量更新文档内容
    success = append_to_feishu_doc(token, summary)
    
    if success:
        print(f"✅ 飞书文档已更新: {today}")
    else:
        print(f"❌ 飞书文档更新失败")

if __name__ == "__main__":
    main()
