#!/usr/bin/env python3
"""
BDI 数据获取器
从多个源尝试获取最新的波罗的海干散货指数
输出: /root/.openclaw/workspace/config/bdi_data.json
"""

import json
import urllib.request
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
BDI_FILE = WORKSPACE / "config" / "bdi_data.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except:
        return None

def try_marine_traffic():
    """从 MarineTraffic 类源获取"""
    # 尝试从 shipping data 网站
    html = fetch_url("https://www.seanews.co.uk/shipping-dry-bulk-index/baltic-dry-index/")
    if html:
        # 匹配 BDI 数值
        m = re.search(r'Baltic Dry Index[^0-9]*(\d{3,4}(?:\.\d+)?)', html)
        if m:
            return float(m.group(1))
    return None

def try_hellenicshipping():
    """从 Hellenic Shipping News 获取"""
    html = fetch_url("https://www.hellenicshippingnews.com/baltic-dry-index/")
    if html:
        m = re.search(r'BDI[^0-9]*(\d{3,4}(?:\.\d+)?)', html)
        if m:
            return float(m.group(1))
    return None

def try_trading_economics():
    """从 Trading Economics 获取"""
    html = fetch_url("https://tradingeconomics.com/commodity/baltic")
    if html:
        m = re.search(r'id="p"(?:[^>]*>)\s*(\d{3,4}(?:\.\d+)?)', html)
        if m:
            return float(m.group(1))
    return None

def load_previous():
    """加载上一次的BDI数据"""
    try:
        with open(BDI_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def save_bdi(value, source):
    """保存BDI数据"""
    prev = load_previous()
    prev_value = prev.get("value") if prev else None
    
    change = round(value - prev_value, 1) if prev_value else 0
    change_pct = round(change / prev_value * 100, 2) if prev_value else 0
    
    data = {
        "value": value,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "source": source,
        "prev_value": prev_value,
        "change": change,
        "change_pct": change_pct,
        "signal": "🟢利好" if change > 0 else "🔴利空" if change < 0 else "⚪持平",
        "updated_at": datetime.now().isoformat(),
    }
    
    with open(BDI_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data

def main():
    print("📊 正在获取 BDI 指数...")
    
    # 按优先级尝试各个源
    sources = [
        ("MarineTraffic/Seanews", try_marine_traffic),
        ("Hellenic Shipping", try_hellenicshipping),
        ("Trading Economics", try_trading_economics),
    ]
    
    for name, func in sources:
        value = func()
        if value and 500 < value < 5000:  # BDI 合理范围
            data = save_bdi(value, name)
            print(f"✅ BDI: {value} (来源: {name})")
            print(f"   变动: {data['change']:+.1f} ({data['change_pct']:+.2f}%) {data['signal']}")
            return 0
    
    # 所有源都失败
    prev = load_previous()
    if prev and prev.get("value"):
        print(f"⚠️ 无法获取最新BDI，使用上次数据: {prev['value']} ({prev.get('date','?')})")
    else:
        print("❌ 所有BDI数据源均不可用")
    return 1

if __name__ == "__main__":
    exit(main())
