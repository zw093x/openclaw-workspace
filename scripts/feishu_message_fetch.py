#!/usr/bin/env python3
"""
飞书消息内容获取工具
通过飞书 API 根据 message_id 获取消息真实内容（包括 Interactive Card）
解决 OpenClaw 只显示 "[Interactive Card]" 占位符的问题

用法:
  python3 scripts/feishu_message_fetch.py <message_id>
  python3 scripts/feishu_message_fetch.py om_x100b52331e31d0b4c3fd8164977da47
"""

import json
import sys
import urllib.request
from pathlib import Path

# === 配置 ===
CONFIG_FILE = Path.home() / ".openclaw" / "openclaw.json"
APP_ID = "cli_a9489e1f4c78dbb6"
APP_SECRET = "mKeApaf2UE3CDN8wlh1IJcDSxcJlYlhD"


def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read()).get("tenant_access_token", "")


def get_message_content(message_id: str, token: str) -> dict:
    """获取飞书消息详情"""
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        if result.get("code") == 0:
            return result.get("data", {}).get("items", [{}])[0]
        else:
            return {"error": result.get("msg", result.get("code"))}


def download_image(image_key: str, token: str) -> bytes:
    """下载飞书图片，返回图片数据"""
    url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def parse_interactive_card(content_str: str) -> dict:
    """解析 interactive 类型卡片的内容"""
    try:
        data = json.loads(content_str)
        title = data.get("title", "")
        elements = data.get("elements", [])
        
        parsed = {"type": "interactive", "title": title, "elements": []}
        
        def extract_text(elem):
            if isinstance(elem, list):
                return [extract_text(e) for e in elem]
            elif isinstance(elem, dict):
                tag = elem.get("tag", "")
                if tag == "text":
                    return {"type": "text", "text": elem.get("text", "")}
                elif tag == "img":
                    return {"type": "image", "image_key": elem.get("image_key", "")}
                elif tag == "note":
                    return {"type": "note", "text": elem.get("text", "")}
                elif tag == "button":
                    return {
                        "type": "button",
                        "text": elem.get("text", ""),
                        "value": elem.get("value", ""),
                    }
                else:
                    return {"type": tag, "raw": elem}
            return str(elem)
        
        for elem in elements:
            parsed["elements"].append(extract_text(elem))
        
        return parsed
    except json.JSONDecodeError:
        return {"type": "unknown", "raw": content_str}


def format_output(msg: dict) -> str:
    """格式化输出"""
    msg_type = msg.get("msg_type", "unknown")
    body = msg.get("body", {})
    content_str = body.get("content", "")
    
    lines = []
    lines.append(f"消息ID: {msg.get('message_id', '')}")
    lines.append(f"类型: {msg_type}")
    lines.append(f"发送者: {msg.get('sender_id', msg.get('senderOpenId', '?'))}")
    lines.append(f"时间: {msg.get('create_time', '')}")
    lines.append("")
    
    if msg_type == "text":
        parsed = json.loads(content_str)
        text = parsed.get("text", "") if isinstance(parsed, dict) else content_str
        lines.append(f"文本内容: {text}")
    
    elif msg_type == "interactive":
        parsed = parse_interactive_card(content_str)
        lines.append(f"卡片标题: {parsed.get('title', '(无)')}")
        lines.append("卡片元素:")
        for i, elem in enumerate(parsed.get("elements", []), 1):
            if isinstance(elem, list):
                for e in elem:
                    if isinstance(e, dict) and e.get("type") == "text":
                        lines.append(f"  {i}. 📝 {e.get('text', '')}")
                    elif isinstance(e, dict) and e.get("type") == "image":
                        lines.append(f"  {i}. 🖼️ 图片: {e.get('image_key', '')}")
                    elif isinstance(e, dict):
                        lines.append(f"  {i}. [{e.get('type')}]")
            elif isinstance(elem, dict):
                if elem.get("type") == "text":
                    lines.append(f"  {i}. 📝 {elem.get('text', '')}")
                elif elem.get("type") == "image":
                    lines.append(f"  {i}. 🖼️ 图片: {elem.get('image_key', '')}")
                elif elem.get("type") == "button":
                    lines.append(f"  {i}. 🔘 按钮: {elem.get('text', '')} = {elem.get('value', '')}")
    
    else:
        lines.append(f"原始内容: {content_str[:300]}")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/feishu_message_fetch.py <message_id>")
        sys.exit(1)
    
    message_id = sys.argv[1]
    
    token = get_tenant_token()
    if not token:
        print("❌ 获取 token 失败")
        sys.exit(1)
    
    msg = get_message_content(message_id, token)
    
    if "error" in msg:
        print(f"❌ 获取失败: {msg['error']}")
        sys.exit(1)
    
    output = format_output(msg)
    print(output)
    
    # 如果有图片，同时下载
    if msg.get("msg_type") == "interactive":
        try:
            parsed = parse_interactive_card(msg.get("body", {}).get("content", ""))
            for elem in parsed.get("elements", []):
                if isinstance(elem, list):
                    for e in elem:
                        if isinstance(e, dict) and e.get("type") == "image":
                            key = e.get("image_key", "")
                            if key:
                                img_data = download_image(key, token)
                                img_path = f"/tmp/feishu_card_{key}.png"
                                with open(img_path, "wb") as f:
                                    f.write(img_data)
                                print(f"\n🖼️ 图片已下载: {img_path} ({len(img_data)/1024:.1f}KB)")
        except Exception as ex:
            print(f"\n⚠️ 图片下载失败: {ex}")


if __name__ == "__main__":
    main()
