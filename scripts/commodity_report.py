#!/usr/bin/env python3
"""
大宗商品 & 航运指数综合播报
黄金/白银/甲醇 一站式获取 + 持续S2预警标记
"""

import json
import urllib.request
import ssl
import os
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

S2_STATE_FILE = "/root/.openclaw/workspace/memory/commodity-s2-state.json"

def fetch_gold():
    try:
        url = "https://hq.sinajs.cn/list=hf_GC"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK")
        parts = data.split('"')[1].split(',')
        price = float(parts[0])
        open_p = float(parts[7])
        return {"name": "黄金(XAU/USD)", "price": price, "open": open_p, "change": price - open_p, "change_pct": (price - open_p) / open_p * 100, "unit": "USD", "ok": True}
    except Exception as e:
        return {"name": "黄金", "error": str(e), "ok": False}

def fetch_silver():
    try:
        url = "https://hq.sinajs.cn/list=hf_SI"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK")
        parts = data.split('"')[1].split(',')
        price = float(parts[0])
        open_p = float(parts[7])
        return {"name": "白银(XAG/USD)", "price": price, "open": open_p, "change": price - open_p, "change_pct": (price - open_p) / open_p * 100, "unit": "USD", "ok": True}
    except Exception as e:
        return {"name": "白银", "error": str(e), "ok": False}

def fetch_methanol():
    try:
        url = "https://hq.sinajs.cn/list=nf_MA0"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK")
        parts = data.split('"')[1].split(',')
        name = parts[0]
        price = float(parts[6])
        prev_settle = float(parts[9])
        change = price - prev_settle
        change_pct = change / prev_settle * 100 if prev_settle else 0
        return {"name": f"{name}(郑商所)", "price": price, "prev_settle": prev_settle, "change": change, "change_pct": change_pct, "unit": "CNY", "ok": True}
    except Exception as e:
        return {"name": "甲醇", "error": str(e), "ok": False}

def fetch_usdcny():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        return {"rate": data["rates"]["CNY"], "ok": True}
    except:
        return {"rate": None, "ok": False}

def load_s2_state():
    if os.path.exists(S2_STATE_FILE):
        try:
            with open(S2_STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_s2_state(state):
    with open(S2_STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def format_s2_tag(name, state):
    """返回持续S2标记文字，如果未达阈值返回空字符串"""
    if not state or not state.get("s2_since"):
        return ""
    from datetime import datetime
    s2_time = datetime.fromisoformat(state["s2_since"])
    hours = int((datetime.now() - s2_time).total_seconds() / 3600)
    if hours < 6:
        return f"[持续{hours}小时]"
    elif hours < 12:
        return f"[持续{hours}小时]⚠️"
    else:
        return f"[持续{hours}小时]🔴"

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    gold = fetch_gold()
    silver = fetch_silver()
    methanol = fetch_methanol()
    fx = fetch_usdcny()
    
    # 加载S2历史状态
    s2_state = load_s2_state()
    
    # 判断当前S2品种
    current_s2 = set()
    for item in [gold, silver, methanol]:
        if not item.get("ok"):
            continue
        pct = abs(item.get("change_pct", 0))
        if pct >= 3:
            current_s2.add(item["name"])
    
    # 更新S2持续时间状态
    for name in ["黄金(XAU/USD)", "白银(XAG/USD)", "甲醇(郑商所)"]:
        if name in current_s2:
            if not s2_state.get("s2_since") or s2_state.get("active_name") != name:
                # 新触发或切换品种
                s2_state["s2_since"] = datetime.now().isoformat()
                s2_state["active_name"] = name
            else:
                # 持续中，更新时长
                s2_state["active_name"] = name
        else:
            # 非S2状态，清除
            if s2_state.get("active_name") == name:
                s2_state.pop("s2_since", None)
                s2_state.pop("active_name", None)
    
    save_s2_state(s2_state)
    
    # 预警判断
    alerts = []
    for item in [gold, silver, methanol]:
        if not item.get("ok"):
            continue
        pct = abs(item.get("change_pct", 0))
        
        # S2持续标记
        if item["name"] in current_s2:
            tag = format_s2_tag(item["name"], s2_state if s2_state.get("active_name") == item["name"] else {})
            if pct >= 3:
                alerts.append(f"🚨 {item['name']} {item.get('change_pct',0):+.2f}% 🚨 S2紧急 {tag}")
        elif pct >= 2:
            alerts.append(f"⚠️ {item['name']} {item.get('change_pct',0):+.2f}% S1预警")
    
    # 关键价位突破
    if gold.get("ok") and gold["price"] >= 5000:
        alerts.append("🚨 黄金突破 $5000 整数关口！")
    if silver.get("ok") and silver["price"] >= 80:
        alerts.append("🚨 白银突破 $80 整数关口！")
    
    result = {
        "time": now,
        "gold": gold,
        "silver": silver,
        "methanol": methanol,
        "usdcny": fx,
        "alerts": alerts,
        "has_alert": len(alerts) > 0
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
