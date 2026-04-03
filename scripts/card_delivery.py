#!/usr/bin/env python3
"""
统一卡片投递入口
读取 cron 生成的文本内容，自动识别类型，套用对应卡片模板，发送到飞书

用法:
  echo "内容" | python3 scripts/card_delivery.py --type stock_open --title "中国船舶开盘"
  python3 scripts/card_delivery.py --type gold --file /tmp/gold_result.txt
  python3 scripts/card_delivery.py --type alert --text "⚠️ 暴涨预警" --color red
"""

import json
import sys
import os
import argparse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from card_templates import CardTemplates, card_to_json

CONFIG_FILE = Path.home() / ".openclaw" / "openclaw.json"
TARGET = "ou_a6469ccc2902a590994b6777b9c8ae8f"

# 类型 → 颜色映射
TYPE_COLOR = {
    "stock_open": "orange",
    "stock_close": "orange",
    "stock_alert": "red",
    "weather": "turquoise",
    "gold": "orange",
    "health": "green",
    "baby": "green",
    "ai_news": "purple",
    "tech_news": "purple",
    "cg_news": "indigo",
    "daily": "blue",
    "inspiration": "yellow",
    "evening": "blue",
    "system": "indigo",
    "alert": "red",
}


def get_feishu_token():
    """获取飞书 tenant_access_token"""
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    feishu = config["channels"]["feishu"]
    
    url = f"{feishu.get('domain','https://open.feishu.cn')}/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": feishu["appId"], "app_secret": feishu["appSecret"]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())["tenant_access_token"]
    except Exception as e:
        print(f"❌ Token 失败: {e}", file=sys.stderr)
        return None


def send_card(card, token=None):
    """发送卡片到飞书"""
    if token is None:
        token = get_feishu_token()
    if not token:
        return False, "无 token"
    
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    domain = config["channels"]["feishu"].get("domain", "https://open.feishu.cn")
    
    url = f"{domain}/open-apis/im/v1/messages?receive_id_type=open_id"
    payload = json.dumps({
        "receive_id": TARGET,
        "msg_type": "interactive",
        "content": card_to_json(card)
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("code") == 0:
                return True, result.get("data", {}).get("message_id", "")
            return False, result.get("msg", "未知错误")
    except Exception as e:
        return False, str(e)


def send_text_fallback(title, content, color="blue"):
    """纯文本降级发送"""
    token = get_feishu_token()
    if not token:
        return False, "无 token"
    
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    domain = config["channels"]["feishu"].get("domain", "https://open.feishu.cn")
    
    url = f"{domain}/open-apis/im/v1/messages?receive_id_type=open_id"
    text_content = f"【{title}】\n\n{content}"
    payload = json.dumps({
        "receive_id": TARGET,
        "msg_type": "text",
        "content": json.dumps({"text": text_content})
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("code") == 0:
                return True, "text_fallback"
            return False, result.get("msg", "")
    except Exception as e:
        return False, str(e)


def build_simple_card(title, content, color="blue"):
    """构建简单卡片（降级方案）"""
    elements = [{"tag": "markdown", "content": content}]
    elements.append({"tag": "note", "elements": [
        {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
    ]})
    
    return {
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": color
        },
        "elements": elements
    }


def auto_detect_type(title):
    """根据标题自动检测类型"""
    title_lower = title.lower()
    keywords = {
        "stock_open": ["开盘", "早评"],
        "stock_close": ["收盘"],
        "stock_alert": ["预警", "异动", "减仓"],
        "weather": ["天气", "穿衣", "饮食"],
        "gold": ["黄金", "金", "贵金属"],
        "health": ["健康", "养生", "小贴士"],
        "baby": ["宝宝", "成长", "疫苗"],
        "ai_news": ["AI行业", "AI绘画"],
        "tech_news": ["科技资讯"],
        "cg_news": ["CG行业", "ComfyUI"],
        "daily": ["早报"],
        "evening": ["晚间", "复盘"],
        "system": ["系统", "状态", "自愈"],
        "inspiration": ["灵感", "素材", "图片", "元素"],
    }
    
    for type_name, words in keywords.items():
        for w in words:
            if w in title:
                return type_name
    return "daily"


def main():
    parser = argparse.ArgumentParser(description="飞书卡片投递")
    parser.add_argument("--title", required=True, help="卡片标题")
    parser.add_argument("--type", default=None, help="卡片类型（auto=自动检测）")
    parser.add_argument("--color", default=None, help="卡片颜色（覆盖类型默认色）")
    parser.add_argument("--file", help="从文件读取内容")
    parser.add_argument("--text", help="直接传入文本")
    parser.add_argument("--fallback", action="store_true", help="卡片失败时降级为纯文本")
    parser.add_argument("--dry-run", action="store_true", help="仅输出卡片 JSON")
    
    args = parser.parse_args()
    
    # 获取内容
    if args.file:
        with open(args.file) as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        content = sys.stdin.read()
    
    if not content.strip():
        print("❌ 无内容", file=sys.stderr)
        sys.exit(1)
    
    # 确定类型和颜色
    card_type = args.type or auto_detect_type(args.title)
    color = args.color or TYPE_COLOR.get(card_type, "blue")

    # 构建卡片
    if card_type == "inspiration":
        source = next((w for w in ["来源：", "来源:"] if w in content), "")
        card = CardTemplates.inspiration(args.title, content.strip(), source)
    else:
        card = build_simple_card(args.title, content.strip(), color)
    
    if args.dry_run:
        print(card_to_json(card))
        return
    
    # 发送
    ok, result = send_card(card)
    
    if ok:
        print(f"✅ 卡片已发送: {args.title}")
    elif args.fallback:
        print("⚠️ 卡片发送失败，降级为纯文本...")
        ok2, result2 = send_text_fallback(args.title, content, color)
        if ok2:
            print(f"✅ 纯文本已发送: {args.title}")
        else:
            print(f"❌ 完全失败: {result2}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"❌ 发送失败: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
