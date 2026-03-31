#!/usr/bin/env python3
"""
大宗商品 & 航运指数综合播报
黄金/白银/甲醇 一站式获取 + BDI（可选）
"""

import json
import urllib.request
import ssl
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_gold():
    """黄金 COMEX"""
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
    """白银 COMEX"""
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
    """甲醇期货 郑商所"""
    try:
        url = "https://hq.sinajs.cn/list=nf_MA0"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK")
        parts = data.split('"')[1].split(',')
        name = parts[0]
        price = float(parts[6])       # 最新价
        prev_settle = float(parts[9])  # 昨结算
        change = price - prev_settle
        change_pct = change / prev_settle * 100 if prev_settle else 0
        return {"name": f"{name}(郑商所)", "price": price, "prev_settle": prev_settle, "change": change, "change_pct": change_pct, "unit": "CNY", "ok": True}
    except Exception as e:
        return {"name": "甲醇", "error": str(e), "ok": False}

def fetch_usdcny():
    """USD/CNY 汇率"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        return {"rate": data["rates"]["CNY"], "ok": True}
    except:
        return {"rate": None, "ok": False}

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    gold = fetch_gold()
    silver = fetch_silver()
    methanol = fetch_methanol()
    fx = fetch_usdcny()
    
    # 预警判断
    alerts = []
    for item in [gold, silver, methanol]:
        if not item.get("ok"):
            continue
        pct = abs(item.get("change_pct", 0))
        if pct >= 3:
            alerts.append(f"🚨 {item['name']} 涨跌 {item.get('change_pct',0):+.2f}% (S2紧急)")
        elif pct >= 2:
            alerts.append(f"⚠️ {item['name']} 涨跌 {item.get('change_pct',0):+.2f}% (S1预警)")
    
    # 关键价位突破检测
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
