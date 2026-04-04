#!/usr/bin/env python3
"""
增量 Memory 备份脚本
每次执行时检查自上次备份以来的新对话内容，自动追加到 memory/YYYY-MM-DD.md
配合 AGENTS.md 的"立即写入Memory"规则使用
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
STATE_FILE = MEMORY_DIR / "memory_backup_state.json"

# 关键话题关键词（命中则写入Memory）
KEY_TOPICS = [
    # 交易相关
    "买", "卖", "加仓", "减仓", "建仓", "清仓", "止损", "持仓",
    "买入", "卖出", "成交", "操作", "交易", "仓位", "换股",
    # 策略/决策
    "策略", "逻辑", "分析", "看法", "判断", "决策",
    # 系统配置
    "备份", "cron", "定时", "任务", "推送", "渠道",
    "安装", "卸载", "修复", "配置", "设置", "更新",
    # 重要信息
    "账号", "密码", "密钥", "API", "记住", "注册",
    # 学习/能力
    "学习", "了解", "追踪", "跟踪", "研究", "教程", "掌握",
    # AI绘画/视频类
    "AI绘画", "AI视频", "AI生图", "AI生成", "提示词", "咒语",
    "ComfyUI", "MJ", "Midjourney", "SD", "Stable Diffusion",
    "DALL", "即梦", "可灵", "生图", "文生图", "图生视频",
    "概念设计", "角色建模", "3D建模", "3D节点",
    # 记忆/知识管理类
    "记忆", "知识库", "总结", "记录", "归档", "整理",
    "memory", "knowledge", "笔记", "摘要",
    # 股票/投资类
    "股票", "股价", "大盘", "指数", "板块", "涨跌",
    "主力", "净流入", "北向", "资金", "量价", "K线",
    "持仓", "浮亏", "浮盈", "市值", "盈亏",
    # 资讯/新闻类
    "新闻", "资讯", "消息", "动态", "情报", "热点",
    "公告", "财报", "业绩", "研报", "数据",
    # 提醒/健康类
    "提醒", "注意", "关注", "监控", "预警", "告警",
    "月子", "宝宝", "产妇", "喂养", "健康", "护理",
]

def load_state():
    """加载上次备份状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_backup_ts": 0, "last_session_files": {}}

def save_state(state):
    """保存备份状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def extract_user_messages(jsonl_path, since_ts=0):
    """从session文件提取用户消息（仅提取新增部分）"""
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
                if msg.get("role") != "user":
                    continue
                
                ts_str = entry.get("timestamp", "")
                # 解析时间戳
                if ts_str:
                    try:
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        ts = dt.timestamp()
                    except:
                        ts = 0
                else:
                    ts = 0
                
                # 只取自上次备份后的消息
                if ts <= since_ts:
                    continue
                
                # 提取文本内容
                content_blocks = msg.get("content", [])
                text_parts = []
                for block in content_blocks:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            # 过滤掉JSON元数据
                            text = re.sub(r'\{[^{]*"message_id"[^{]*\}', '[消息]', text)
                            text = re.sub(r'Conversation info[^\n]*', '', text)
                            text = re.sub(r'Sender[^\n]*', '', text)
                            text = re.sub(r'\[message_id:[^\]]+\]', '', text)
                            text = text.strip()
                            if text and len(text) > 2:
                                text_parts.append(text)
                    elif isinstance(block, str):
                        text_parts.append(block)
                
                text = "\n".join(text_parts).strip()
                if text and not text.startswith("[") and len(text) > 3:
                    # 时间本地化
                    if ts_str:
                        try:
                            dt_local = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=8)))
                            time_str = dt_local.strftime("%H:%M")
                            date_str = dt_local.strftime("%Y-%m-%d")
                        except:
                            time_str = "??:??"
                            date_str = "????-??-??"
                    else:
                        time_str = "??:??"
                        date_str = "????-??-??"
                    
                    messages.append({
                        "time": time_str,
                        "date": date_str,
                        "text": text[:500]
                    })
    except Exception as e:
        print(f"  ⚠️ 读取失败 {jsonl_path.name}: {e}")
    
    return messages

def is_important(text):
    """判断消息是否重要（包含关键话题）"""
    for kw in KEY_TOPICS:
        if kw in text:
            return True
    return False

def format_memory_entry(messages_by_date):
    """格式化Memory条目"""
    lines = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for date, msgs in sorted(messages_by_date.items()):
        if not msgs:
            continue
        
        lines.append(f"\n## 增量备份 ({date})")
        lines.append(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        for msg in msgs:
            lines.append(f"**{msg['time']}** {msg['text']}")
        
        lines.append("")
    
    return "\n".join(lines)

def main():
    state = load_state()
    last_ts = state.get("last_backup_ts", 0)
    
    # 找到飞书session文件
    sessions_index = SESSIONS_DIR / "sessions.json"
    feishu_sessions = []
    
    for jsonl_file in SESSIONS_DIR.glob("*.jsonl*"):
        if jsonl_file.name.endswith(".lock"):
            continue
        
        size = jsonl_file.stat().st_size
        if size < 1000:
            continue
        
        # 检查文件更新时间（只处理今天的）
        mtime = jsonl_file.stat().st_mtime
        file_date = datetime.fromtimestamp(mtime, tz=timezone(timedelta(hours=8)))
        today = datetime.now(timezone(timedelta(hours=8))).date()
        
        if file_date.date() != today:
            # 也检查是否有新的用户消息
            pass
        
        messages = extract_user_messages(jsonl_file, since_ts=last_ts)
        user_msgs = [m for m in messages if is_important(m["text"])]
        
        if user_msgs:
            feishu_sessions.append((jsonl_file.name, user_msgs, len([m for m in messages if not is_important(m["text"])])))
    
    if not feishu_sessions:
        print(f"ℹ️ 无新增重要对话（上次备份: {datetime.fromtimestamp(last_ts, tz=timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M') if last_ts else '从未'})")
        return
    
    # 按日期分组
    messages_by_date = {}
    total_important = 0
    for fname, msgs, other_count in feishu_sessions:
        for msg in msgs:
            date = msg["date"]
            if date not in messages_by_date:
                messages_by_date[date] = []
            messages_by_date[date].append(msg)
            total_important += 1
        
        print(f"  {fname}: {len(msgs)}条重要消息 (+{other_count}条普通)")
    
    # 写入Memory文件
    memory_content = format_memory_entry(messages_by_date)
    today = datetime.now().strftime("%Y-%m-%d")
    today_memory = MEMORY_DIR / f"{today}.md"
    
    with open(today_memory, 'a', encoding='utf-8') as f:
        f.write(memory_content)
    
    print(f"✅ 写入 {total_important} 条重要消息 → {today_memory.name}")
    
    # 更新状态
    new_ts = datetime.now().timestamp()
    state["last_backup_ts"] = new_ts
    save_state(state)
    
    return total_important

if __name__ == "__main__":
    count = main()
    if count and count > 0:
        # 推送Gitee
        import subprocess
        workspace = Path("/root/.openclaw/workspace")
        subprocess.run(["git", "-C", str(workspace), "add", f"memory/"], capture_output=True)
        result = subprocess.run(["git", "-C", str(workspace), "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["git", "-C", str(workspace), "commit", "-m", f"增量Memory备份 {datetime.now().strftime('%Y-%m-%d %H:%M')}"], capture_output=True)
            subprocess.run(["git", "-C", str(workspace), "push", "origin", "master"], capture_output=True)
            print("✅ Gitee推送完成")
