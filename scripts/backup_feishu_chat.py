#!/usr/bin/env python3
"""
飞书聊天记录备份
每天从飞书 API 拉取与用户的私聊记录，保存为 JSON 文件
只备份到 Gitee（不推送到 GitHub）
"""

import json
import urllib.request
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
BACKUP_DIR = WORKSPACE / "memory" / "feishu-chat-backup"
CONFIG_FILE = Path("/root/.openclaw/openclaw.json")

def get_feishu_config():
    """从 OpenClaw 配置读取飞书 App 凭证"""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        feishu = config.get("channels", {}).get("feishu", {})
        return feishu.get("appId", ""), feishu.get("appSecret", ""), feishu.get("domain", "https://open.feishu.cn")
    except:
        return "", "", ""

def get_tenant_token(app_id, app_secret, domain):
    """获取飞书 tenant_access_token"""
    url = f"{domain}/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("tenant_access_token")
    except Exception as e:
        print(f"❌ 获取 token 失败: {e}")
        return None

def get_chat_id(token, domain, user_id):
    """获取与用户的私聊 chat_id"""
    url = f"{domain}/open-apis/im/v1/chats?page_size=50"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            chats = result.get("data", {}).get("items", [])
            for chat in chats:
                if chat.get("chat_mode") == "p2p":
                    return chat.get("chat_id")
    except Exception as e:
        print(f"❌ 获取 chat_id 失败: {e}")
    return None

def fetch_messages(token, domain, chat_id, start_time, end_time):
    """分页拉取消息"""
    messages = []
    page_token = None
    
    while True:
        url = f"{domain}/open-apis/im/v1/messages?container_id_type=chat&container_id={chat_id}&start_time={start_time}&end_time={end_time}&sort_type=ByCreateTimeAsc&page_size=50"
        if page_token:
            url += f"&page_token={page_token}"
        
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                items = result.get("data", {}).get("items", [])
                for item in items:
                    body = item.get("body", {})
                    content = body.get("content", "")
                    try:
                        content_dict = json.loads(content)
                        text = content_dict.get("text", content)
                    except:
                        text = content
                    
                    messages.append({
                        "msg_id": item.get("message_id", ""),
                        "sender_id": item.get("sender", {}).get("id", ""),
                        "sender_type": item.get("sender", {}).get("sender_type", ""),
                        "msg_type": item.get("msg_type", ""),
                        "text": text,
                        "create_time": item.get("create_time", ""),
                    })
                
                if not result.get("data", {}).get("has_more"):
                    break
                page_token = result.get("data", {}).get("page_token")
                time.sleep(0.2)  # 避免限流
        except Exception as e:
            print(f"❌ 拉取消息失败: {e}")
            break
    
    return messages

def main():
    app_id, app_secret, domain = get_feishu_config()
    if not app_id or not app_secret:
        print("❌ 无法读取飞书配置")
        return 1
    
    token = get_tenant_token(app_id, app_secret, domain)
    if not token:
        return 1
    
    # 获取最近 2 天的消息（防止漏备份）
    now = int(time.time())
    two_days_ago = now - 2 * 86400
    
    # 备份目录按月份组织
    month_dir = BACKUP_DIR / datetime.now().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    backup_file = month_dir / f"chat-{today}.json"
    
    # 获取 chat_id（P2P 私聊）
    chat_id = get_chat_id(token, domain, None)
    if not chat_id:
        print("❌ 未找到 P2P 聊天")
        return 1
    
    messages = fetch_messages(token, domain, chat_id, str(two_days_ago), str(now))
    
    if messages:
        # 加载已有数据（合并去重）
        existing = []
        if backup_file.exists():
            try:
                with open(backup_file, "r") as f:
                    existing = json.load(f)
            except:
                pass
        
        existing_ids = {m.get("msg_id") for m in existing}
        new_messages = [m for m in messages if m.get("msg_id") not in existing_ids]
        
        if new_messages:
            all_messages = existing + new_messages
            with open(backup_file, "w") as f:
                json.dump(all_messages, f, ensure_ascii=False, indent=2)
            print(f"✅ 备份完成: {len(new_messages)} 条新消息 → {backup_file}")
        else:
            print(f"ℹ️ 无新消息（已有 {len(existing)} 条）")
    else:
        print("ℹ️ 未获取到消息")
    
    return 0

if __name__ == "__main__":
    exit(main())
