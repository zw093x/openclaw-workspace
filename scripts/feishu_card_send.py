#!/usr/bin/env python3
"""
飞书卡片投递脚本（独立版）
直接调用飞书 API 发送卡片消息，不依赖 OpenClaw cron agent

用法:
  python3 scripts/feishu_card_send.py --title "标题" --color blue --file content.txt
  echo "内容" | python3 scripts/feishu_card_send.py --title "标题" --color blue
  python3 scripts/feishu_card_send.py --title "标题" --color blue --text "直接文本"

配合 cron 使用:
  openclaw cron edit <job_id> --no-deliver
  # cron 生成内容到文件，此脚本读取并以卡片形式发送
"""
import json
import subprocess
import sys
import argparse
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# === 配置 ===
CONFIG_FILE = Path.home() / ".openclaw" / "openclaw.json"
TARGET = "ou_a6469ccc2902a590994b6777b9c8ae8f"

# 颜色模板
COLOR_TEMPLATES = {
    "blue": "blue",         # 资讯/日报
    "green": "green",       # 健康/养生
    "orange": "orange",     # 股票/交易
    "purple": "purple",     # 科技/AI
    "turquoise": "turquoise",  # 天气
    "red": "red",           # 紧急/预警
    "grey": "grey",         # 次要信息
    "wathet": "wathet",     # 浅蓝
    "indigo": "indigo",     # 靛蓝
    "yellow": "yellow",     # 警告
}


def get_feishu_config():
    """读取飞书配置"""
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    feishu = config.get("channels", {}).get("feishu", {})
    return {
        "app_id": feishu.get("appId", ""),
        "app_secret": feishu.get("appSecret", ""),
        "domain": feishu.get("domain", "https://open.feishu.cn"),
    }


def get_tenant_token(app_id, app_secret, domain):
    """获取飞书 tenant_access_token"""
    url = f"{domain}/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret
    }).encode()
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("code") == 0:
                return data.get("tenant_access_token")
            else:
                print(f"❌ 获取 token 失败: {data}")
                return None
    except Exception as e:
        print(f"❌ 获取 token 异常: {e}")
        return None


def send_card_message(token, domain, chat_id, card):
    """发送飞书卡片消息"""
    url = f"{domain}/open-apis/im/v1/messages?receive_id_type=open_id"
    payload = json.dumps({
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card, ensure_ascii=False)
    }).encode()
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get("code") == 0:
                return True, data.get("data", {}).get("message_id", "")
            else:
                return False, data.get("msg", "unknown error")
    except Exception as e:
        return False, str(e)


def build_card(title, content, color="blue"):
    """将文本内容构建为飞书卡片"""
    elements = []
    sections = content.split("---")
    
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
        if i > 0 and elements:
            elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": section})
    
    return {
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": COLOR_TEMPLATES.get(color, "blue")
        },
        "elements": elements
    }


def send_via_openclaw(title, content, color, target):
    """通过 OpenClaw CLI 发送（备用方案）"""
    card = build_card(title, content, color)
    card_json = json.dumps(card, ensure_ascii=False)
    
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", target,
        "--card", card_json
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0, result.stderr or result.stdout


def main():
    parser = argparse.ArgumentParser(description="飞书卡片投递")
    parser.add_argument("--title", required=True, help="卡片标题")
    parser.add_argument("--color", default="blue", choices=list(COLOR_TEMPLATES.keys()))
    parser.add_argument("--target", default=TARGET, help="飞书 open_id")
    parser.add_argument("--file", help="从文件读取内容")
    parser.add_argument("--text", help="直接传入文本")
    parser.add_argument("--dry-run", action="store_true", help="仅输出卡片 JSON")
    parser.add_argument("--via", choices=["api", "cli"], default="api", help="发送方式")
    
    args = parser.parse_args()
    
    # 获取内容
    if args.file:
        with open(args.file, "r") as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        content = sys.stdin.read()
    
    if not content.strip():
        print("❌ 无内容", file=sys.stderr)
        sys.exit(1)
    
    card = build_card(args.title, content, args.color)
    
    if args.dry_run:
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return
    
    if args.via == "api":
        config = get_feishu_config()
        token = get_tenant_token(config["app_id"], config["app_secret"], config["domain"])
        if not token:
            print("⚠️ API 方式失败，尝试 CLI 方式...")
            ok, msg = send_via_openclaw(args.title, content, args.color, args.target)
        else:
            ok, msg = send_card_message(token, config["domain"], args.target, card)
    else:
        ok, msg = send_via_openclaw(args.title, content, args.color, args.target)
    
    if ok:
        print(f"✅ 已发送: {args.title}")
    else:
        print(f"❌ 失败: {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
