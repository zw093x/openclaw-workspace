#!/usr/bin/env python3
"""
航运指数综合获取（方案 A+C 组合）
- CCFI：上海航运交易所集装箱运价指数（基本面）
- 船舶板块（BK0729）：A股市场情绪指标
- 数据源：新浪期货 + 东方财富
"""

import json
import urllib.request
import ssl
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_exchange_rate():
    try:
        with urllib.request.urlopen("https://api.exchangerate-api.com/v4/latest/USD", timeout=10, context=ctx) as r:
            return json.loads(r.read()).get("rates", {}).get("CNY", 6.92)
    except:
        return 6.92

def fetch_ship_sector():
    """新浪船舶板块实时行情（行业板块API）"""
    try:
        url = "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            raw = resp.read().decode("GBK", errors="ignore")
        
        # 解析 JSON：var S_Finance_bankuai_sinaindustry = {...}
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start < 0:
            return {"source": "新浪/船舶板块", "success": False, "error": "格式异常"}
        
        sectors = json.loads(raw[start:end])
        cbzz = sectors.get("new_cbzz", "")
        if not cbzz:
            return {"source": "新浪/船舶板块", "success": False, "error": "无船舶板块数据"}
        
        parts = cbzz.split(",")
        if len(parts) < 12:
            return {"source": "新浪/船舶板块", "success": False, "error": "数据不完整"}
        
        return {
            "source": "新浪/船舶板块",
            "success": True,
            "name": parts[1],               # 船舶制造
            "stock_count": int(parts[2]),   # 个股数量
            "avg_price": float(parts[3]),   # 平均价
            "change": float(parts[4]),      # 涨跌额
            "change_pct": float(parts[5]),  # 涨跌幅%
            "volume": float(parts[6]) if parts[6] else 0,  # 成交量
            "amount": float(parts[7]) if parts[7] else 0,  # 成交额
            "leader_code": parts[8],        # 领涨股代码
            "leader_change": float(parts[10]),      # 领涨股涨跌额
            "leader_change_pct": float(parts[11]),  # 领涨股涨幅%
            "leader_name": parts[12] if len(parts) > 12 else parts[8],  # 领涨股名称
        }
    except Exception as e:
        return {"source": "新浪/船舶板块", "success": False, "error": str(e)}

def fetch_comex_gold():
    """新浪 COMEX 黄金（参考）"""
    try:
        url = "https://hq.sinajs.cn/list=hf_GC"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK", errors="ignore")
        parts = data.split('"')
        if len(parts) > 1 and parts[1]:
            vals = parts[1].split(",")
            if vals[0]:
                price = float(vals[0])
                open_p = float(parts[5]) if len(parts) > 5 else 0
                return {
                    "source": "COMEX黄金",
                    "success": True,
                    "price_usd": price,
                    "open": open_p,
                    "change_pct": (price - open_p) / open_p * 100 if open_p else 0
                }
        return {"source": "COMEX黄金", "success": False}
    except:
        return {"source": "COMEX黄金", "success": False}

def fetch_individual_stocks():
    """新浪获取主要船舶股实时行情"""
    try:
        # 中国船舶600150, 中国动力600482
        codes = "sh600150,sh600482"
        url = f"https://hq.sinajs.cn/list={codes}"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode("GBK", errors="ignore")
        
        results = []
        for line in data.strip().split("\n"):
            if '=""' in line:
                continue
            parts = line.split('"')
            if len(parts) > 1 and parts[1]:
                vals = parts[1].split(",")
                if len(vals) >= 4:
                    name = vals[0]
                    open_p = float(vals[1]) if vals[1] else 0
                    prev_close = float(vals[2]) if vals[2] else 0
                    price = float(vals[3]) if vals[3] else 0
                    high = float(vals[4]) if vals[4] else 0
                    low = float(vals[5]) if vals[5] else 0
                    change = price - prev_close if prev_close else 0
                    change_pct = change / prev_close * 100 if prev_close else 0
                    results.append({
                        "name": name,
                        "price": price,
                        "change": change,
                        "change_pct": change_pct,
                        "high": high,
                        "low": low
                    })
        return results
    except:
        return []

def get_shipping_data():
    """获取航运综合数据"""
    results = {}
    
    sector = fetch_ship_sector()
    if sector["success"]:
        results["sector"] = sector
    
    stocks = fetch_individual_stocks()
    if stocks:
        results["stocks"] = stocks
    
    gold = fetch_comex_gold()
    if gold["success"]:
        results["gold"] = gold
    
    return results

def format_report(data):
    """格式化报告"""
    lines = ["🚢 航运指数播报"]
    
    # 船舶板块
    sector = data.get("sector", {})
    if sector.get("success"):
        change_pct = sector.get("change_pct", 0)
        emoji = "🔴" if change_pct > 0 else "🟢" if change_pct < 0 else "⚪"
        signal = "强势" if change_pct > 1.5 else "偏强" if change_pct > 0.5 else "弱势" if change_pct < -1.5 else "偏弱" if change_pct < -0.5 else "平盘"
        
        lines.append(f"\n{emoji} 船舶板块（{signal}）")
        lines.append(f"   涨跌: {sector.get('change', '?'):+.3f} ({change_pct:+.2f}%)")
        lines.append(f"   成交额: {sector.get('amount', 0)/1e8:.1f}亿")
        leader = sector.get("leader_name", "")
        leader_pct = sector.get("leader_change_pct", 0)
        if leader:
            lines.append(f"   领涨: {leader} ({leader_pct:+.2f}%)")
    
    # 个股
    stocks = data.get("stocks", [])
    if stocks:
        lines.append(f"\n📊 个股行情")
        for s in stocks:
            sign = "+" if s["change"] >= 0 else ""
            lines.append(f"   {s['name']}: ¥{s['price']:.2f} ({sign}{s['change_pct']:.2f}%)")
    
    # 黄金
    gold = data.get("gold", {})
    if gold.get("success"):
        sign = "+" if gold["change_pct"] >= 0 else ""
        lines.append(f"\n💰 黄金参考: ${gold['price_usd']:.2f}/oz ({sign}{gold['change_pct']:.2f}%)")
    
    # 综合判断
    if sector.get("success"):
        pct = float(sector.get("change_pct", 0))
        if pct > 2:
            lines.append("\n💡 板块强势，关注放量个股")
        elif pct < -2:
            lines.append("\n💡 板块弱势，注意风险控制")
    
    return "\n".join(lines)

if __name__ == "__main__":
    data = get_shipping_data()
    print(format_report(data))
