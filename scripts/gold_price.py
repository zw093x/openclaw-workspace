#!/usr/bin/env python3
"""
黄金价格多源获取（三级降级）
新浪 → 东方财富 → CoinGecko
"""

import json
import subprocess
import urllib.request
import ssl

# 跳过 SSL 验证（某些源可能有问题）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_sina():
    """新浪期货 COMEX"""
    try:
        url = "https://hq.sinajs.cn/list=hf_GC"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK")
        parts = data.split('"')[1].split(',')
        price = float(parts[0])
        open_p = float(parts[7])
        high = float(parts[3])
        low = float(parts[4])
        return {
            "source": "新浪/COMEX",
            "price_usd": price,
            "open": open_p,
            "high": high,
            "low": low,
            "change": price - open_p,
            "change_pct": (price - open_p) / open_p * 100
        }
    except Exception as e:
        return {"source": "新浪", "error": str(e)}

def fetch_eastmoney():
    """东方财富"""
    try:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=113.XAUUSD&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56&klt=101&fqt=1&end=20500101&lmt=2"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        klines = data.get("data", {}).get("klines", [])
        if len(klines) >= 2:
            today = klines[-1].split(",")
            yesterday = klines[-2].split(",")
            price = float(today[2])
            prev_close = float(yesterday[2])
            return {
                "source": "东方财富",
                "price_usd": price,
                "open": float(today[1]),
                "high": float(today[3]),
                "low": float(today[4]),
                "prev_close": prev_close,
                "change": price - prev_close,
                "change_pct": (price - prev_close) / prev_close * 100
            }
        return {"source": "东方财富", "error": "无数据"}
    except Exception as e:
        return {"source": "东方财富", "error": str(e)}

def fetch_coingecko():
    """CoinGecko PAXG"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd&include_24hr_change=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read())
        paxg = data.get("pax-gold", {})
        price = paxg.get("usd")
        change_pct = paxg.get("usd_24h_change", 0)
        if price:
            return {
                "source": "CoinGecko/PAXG",
                "price_usd": price,
                "change_pct": change_pct,
                "change": price * change_pct / 100
            }
        return {"source": "CoinGecko", "error": "无数据"}
    except Exception as e:
        return {"source": "CoinGecko", "error": str(e)}

def get_exchange_rate():
    """获取 USD/CNY 汇率"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        with urllib.request.urlopen(url, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        return data.get("rates", {}).get("CNY", 6.92)
    except:
        return 6.92

def fetch_with_fallback():
    """三级降级获取黄金价格"""
    sources = [fetch_sina, fetch_eastmoney, fetch_coingecko]
    errors = []
    
    for fetch_fn in sources:
        result = fetch_fn()
        if "error" not in result:
            return result
        errors.append(f"{result['source']}: {result['error']}")
    
    return {"source": "全部失败", "error": " | ".join(errors), "price_usd": None}

def format_report(result, cny_rate=None):
    """格式化报告"""
    if cny_rate is None:
        cny_rate = get_exchange_rate()
    
    lines = []
    lines.append(f"💰 黄金价格 ({result['source']})")
    
    price = result.get("price_usd")
    if price:
        cny_gram = price * cny_rate / 31.1035
        lines.append(f"   最新: ${price:.2f}/oz (¥{cny_gram:.1f}/克)")
    
    if "open" in result:
        lines.append(f"   开盘: ${result['open']:.2f}")
    if "high" in result:
        lines.append(f"   最高: ${result['high']:.2f}")
    if "low" in result:
        lines.append(f"   最低: ${result['low']:.2f}")
    
    change = result.get("change", 0)
    change_pct = result.get("change_pct", 0)
    if change:
        lines.append(f"   {'📈' if change > 0 else '📉'} 涨跌: {change:+.2f} ({change_pct:+.2f}%)")
    
    lines.append(f"   💱 USD/CNY: {cny_rate}")
    
    # 预警
    if abs(change_pct) > 3:
        lines.append("   🚨 S2 预警: 单日涨跌幅超±3%！")
    elif abs(change_pct) > 2:
        lines.append("   ⚠️ S1 预警: 单日涨跌幅超±2%！")
    
    return "\n".join(lines)

if __name__ == "__main__":
    result = fetch_with_fallback()
    cny = get_exchange_rate()
    print(format_report(result, cny))
