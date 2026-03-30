#!/usr/bin/env python3
"""
OpenClaw 会话历史备份脚本
从 session store 提取完整的对话记录，按日期保存为可读的文本文件
只推送到 Gitee（不推送到 GitHub）
"""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
BACKUP_DIR = Path("/root/.openclaw/workspace/memory/feishu-chat-backup")
WORKSPACE = Path("/root/.openclaw/workspace")

def extract_messages(jsonl_path):
    """从 session JSONL 文件提取消息"""
    messages = []
    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                if entry.get("type") != "message":
                    continue
                
                msg = entry.get("message", {})
                role = msg.get("role", "unknown")
                content_blocks = msg.get("content", [])
                ts = entry.get("timestamp", "")
                
                # 提取文本内容
                text_parts = []
                for block in content_blocks:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "toolResult":
                            result = str(block.get("result", ""))[:500]
                            text_parts.append(f"[工具结果] {result}")
                    elif isinstance(block, str):
                        text_parts.append(block)
                
                text = "\n".join(text_parts).strip()
                if text:
                    messages.append({
                        "role": role,
                        "text": text[:2000],  # 限制长度
                        "timestamp": ts
                    })
    except Exception as e:
        print(f"  ⚠️ 读取失败: {e}")
    
    return messages

def format_chat_log(messages):
    """格式化为可读的聊天记录"""
    lines = []
    for msg in messages:
        ts = msg["timestamp"]
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                dt_local = dt.astimezone(timezone(timedelta(hours=8)))
                time_str = dt_local.strftime("%H:%M")
            except:
                time_str = "??:??"
        else:
            time_str = "??:??"
        
        role_label = "👤 用户" if msg["role"] == "user" else "🤖 小P"
        
        # 截取前 800 字符
        text = msg["text"][:800]
        if len(msg["text"]) > 800:
            text += "\n... (已截断)"
        
        lines.append(f"[{time_str}] {role_label}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines)

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    month_dir = BACKUP_DIR / datetime.now().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    
    # 找到主用户 session
    sessions_index = SESSIONS_DIR / "sessions.json"
    user_session_files = []
    
    # 扫描所有 session 文件（包括 .reset. 快照），找到有用户消息的
    for jsonl_file in SESSIONS_DIR.glob("*.jsonl*"):  # 匹配 .jsonl 和 .jsonl.reset.*
        if jsonl_file.name.endswith(".lock"):
            continue
        if ".deleted." in jsonl_file.name:
            continue
        
        size = jsonl_file.stat().st_size
        if size < 1000:  # 太小的跳过
            continue
        
        messages = extract_messages(jsonl_file)
        user_msgs = [m for m in messages if m["role"] == "user"]
        
        if len(user_msgs) >= 2:  # 至少有 2 条用户消息才备份
            user_session_files.append((jsonl_file, messages, len(user_msgs)))
    
    # 按用户消息数排序（最多的可能是主会话）
    user_session_files.sort(key=lambda x: x[2], reverse=True)
    
    total_backed = 0
    for jsonl_file, messages, user_count in user_session_files[:10]:  # 只备份前 10 个最大的
        # 获取最早消息的日期
        first_ts = messages[0].get("timestamp", "") if messages else ""
        if first_ts:
            try:
                first_date = datetime.fromisoformat(first_ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
            except:
                first_date = today
        else:
            first_date = today
        
        # 生成可读的聊天记录
        chat_log = format_chat_log(messages)
        
        # 保存到按日期组织的目录
        date_dir = month_dir / first_date
        date_dir.mkdir(exist_ok=True)
        
        short_id = jsonl_file.stem[:8]
        backup_file = date_dir / f"session-{short_id}.txt"
        
        header = f"=== Session: {jsonl_file.stem} ===\n"
        header += f"用户消息: {user_count} 条 | 总消息: {len(messages)} 条\n"
        header += f"最早: {first_ts} | 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header += "=" * 50 + "\n\n"
        
        with open(backup_file, 'w') as f:
            f.write(header + chat_log)
        
        total_backed += 1
    
    print(f"✅ 备份完成: {total_backed} 个会话 → {month_dir}")
    return total_backed

if __name__ == "__main__":
    count = main()
    
    # 推送到 Gitee（不推送到 GitHub）
    if count > 0:
        os.chdir(WORKSPACE)
        subprocess.run(["git", "add", "memory/feishu-chat-backup/"], capture_output=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:  # 有变更
            subprocess.run(["git", "commit", "-m", f"飞书对话备份 {datetime.now().strftime('%Y-%m-%d')}"], capture_output=True)
            subprocess.run(["git", "push", "origin", "master"], capture_output=True)  # 只推 Gitee
            print("✅ Gitee 推送完成")
        else:
            print("ℹ️ 无变更")
