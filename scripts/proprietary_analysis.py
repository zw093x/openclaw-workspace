#!/usr/bin/env python3
"""
专有分析模块 - 板块联动 + 资金流向 + BDI 联动
供 stock_realtime_monitor.py 和 cron 任务调用
"""

import json
import urllib.request
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
TECH_FILE = WORKSPACE / "config" / "tech_levels.json"
HOLDINGS_FILE = WORKSPACE / "config" / "holdings.json"

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.eastmoney.com"}

def fetch_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

# ===== 1. 板块相对强弱 =====

def get_sector_index():
    """获取船舶制造板块指数实时数据（BK0729）"""
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f2,f3,f4,f12,f14&secids=90.BK0729"
    data = fetch_json(url)
    try:
        item = data["data"]["diff"][0]
        return {
            "name": item["f14"],
            "price": item["f2"] / 100,
            "change_pct": item["f3"] / 100,
            "change": item["f4"] / 100,
        }
    except:
        return None

def get_market_index():
    """获取上证指数"""
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f2,f3,f4,f12,f14&secids=1.000001"
    data = fetch_json(url)
    try:
        item = data["data"]["diff"][0]
        return {
            "name": item["f14"],
            "price": item["f2"] / 100,
            "change_pct": item["f3"] / 100,
        }
    except:
        return None

def calc_relative_strength(stock_change, sector_change):
    """计算个股相对板块强弱（正=跑赢，负=跑输）"""
    return round(stock_change - sector_change, 2)

def analyze_sector_strength(stock_quotes):
    """分析板块内相对强弱"""
    sector = get_sector_index()
    market = get_market_index()

    if not sector:
        return {"error": "无法获取板块指数"}

    result = {
        "sector": sector,
        "market": market,
        "stocks": [],
        "recommendation": "",
    }

    weak_stock = None
    strong_stock = None

    for code, q in stock_quotes.items():
        rs = calc_relative_strength(q["change_pct"], sector["change_pct"])
        stock_info = {
            "name": q["name"],
            "change_pct": q["change_pct"],
            "rs_vs_sector": rs,
            "verdict": "跑赢板块" if rs > 0 else "跑输板块",
        }
        result["stocks"].append(stock_info)

        if weak_stock is None or rs < weak_stock["rs_vs_sector"]:
            weak_stock = stock_info
        if strong_stock is None or rs > strong_stock["rs_vs_sector"]:
            strong_stock = stock_info

    # 生成建议
    if weak_stock and strong_stock:
        if weak_stock["rs_vs_sector"] < -0.5:
            result["recommendation"] = f"⚠️ {weak_stock['name']}跑输板块{abs(weak_stock['rs_vs_sector']):.1f}%，优先减仓弱势股"
        elif abs(weak_stock["rs_vs_sector"] - strong_stock["rs_vs_sector"]) < 0.3:
            result["recommendation"] = "两只股票与板块联动一致，无明显分化"
        else:
            result["recommendation"] = f"分化中：{strong_stock['name']}较强，{weak_stock['name']}较弱"

    return result

# ===== 2. 主力资金流向 =====

def get_money_flow(code, market="sh"):
    """获取个股主力资金流向（今日实时）"""
    secid = f"1.{code}" if market == "sh" else f"0.{code}"
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?"
        f"secid={secid}&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56"
        f"&klt=1&lmt=0"
    )
    data = fetch_json(url)
    try:
        klines = data.get("data", {}).get("klines", [])
        if not klines:
            return None
        latest = klines[-1].split(",")
        # 字段：日期, 主力净流入, 超大单净流入, 大单净流入, 中单净流入, 小单净流入（单位：元）
        return {
            "main_net": round(float(latest[1]) / 10000, 0),      # 转万元
            "super_large_net": round(float(latest[2]) / 10000, 0),
            "large_net": round(float(latest[3]) / 10000, 0),
            "medium_net": round(float(latest[4]) / 10000, 0),
            "small_net": round(float(latest[5]) / 10000, 0),
        }
    except Exception as e:
        return None

def get_money_flow_summary(code, market="sh"):
    """获取资金流向汇总（今日实时）"""
    secid = f"1.{code}" if market == "sh" else f"0.{code}"
    url = f"https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={secid}&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56&lmt=5"
    data = fetch_json(url)
    try:
        klines = data.get("data", {}).get("klines", [])
        result = []
        for k in klines[-5:]:
            parts = k.split(",")
            result.append({
                "date": parts[0],
                "main_net": round(float(parts[1]) / 100000000, 2),  # 转亿元
                "super_large_net": round(float(parts[2]) / 100000000, 2),
                "large_net": round(float(parts[3]) / 100000000, 2),
            })
        return result
    except:
        return []

def analyze_money_flow(holdings):
    """分析持仓资金流向"""
    result = {}
    for item in holdings:
        code = item["code"]
        market = item.get("market", "sh")

        # 实时资金流向
        flow = get_money_flow(code, market)
        if flow:
            main_net = flow.get("main_net", 0)
            if main_net > 500:  # 主力净流入 > 500万
                signal = "🟢主力流入"
            elif main_net < -500:
                signal = "🔴主力流出"
            else:
                signal = "⚪资金平衡"

            result[f"{market}{code}"] = {
                "name": item["name"],
                "main_net": main_net,
                "super_large_net": flow.get("super_large_net", 0),
                "signal": signal,
            }

    return result

# ===== 3. BDI 指数 =====

def get_bdi():
    """获取 BDI 波罗的海干散货指数（从 bdi_data.json 读取）"""
    bdi_file = WORKSPACE / "config" / "bdi_data.json"
    try:
        with open(bdi_file, "r") as f:
            data = json.load(f)
        if data.get("value"):
            return {
                "value": data["value"],
                "change": data.get("change", 0),
                "change_pct": data.get("change_pct", 0),
                "date": data.get("date", "?"),
                "source": data.get("source", "?"),
                "signal": data.get("signal", "⚪"),
            }
    except:
        pass
    return {"value": None, "signal": "⚪数据暂缺", "note": "等待BDI cron agent首次更新"}

def analyze_bdi_impact(bdi_data, stock_change_avg):
    """分析 BDI 对持仓的影响"""
    if not bdi_data or bdi_data.get("value") is None:
        return "BDI 数据暂缺，无法判断行业基本面联动"

    bdi_change = bdi_data.get("change_pct", 0)
    if bdi_change > 2 and stock_change_avg < 0:
        return "⚠️ BDI 上涨但股价下跌，可能是短期调整或消息面压制，关注反弹"
    elif bdi_change < -2 and stock_change_avg < 0:
        return "🔴 BDI 和股价同步下跌，基本面+技术面双杀，建议观望"
    elif bdi_change > 0 and stock_change_avg > 0:
        return "🟢 BDI 和股价同步上涨，基本面确认，可持有"
    elif bdi_change < 0 and stock_change_avg > 0:
        return "💡 BDI 下跌但股价上涨，注意是否背离，关注持续性"
    return "BDI 与股价联动不明显"

# ===== 综合分析 =====

def full_analysis(stock_quotes=None):
    """
    综合分析：板块强弱 + 资金流向 + BDI 联动
    stock_quotes: {code: {name, change_pct, price, ...}}
    """
    # 加载持仓
    with open(HOLDINGS_FILE, "r") as f:
        holdings_data = json.load(f)

    holdings = [h for h in holdings_data.get("holdings", []) if h.get("shares", 0) > 0 and h.get("status") != "sold"]

    result = {
        "sector_strength": None,
        "money_flow": None,
        "bdi": None,
        "summary": [],
    }

    # 1. 板块相对强弱
    if stock_quotes:
        result["sector_strength"] = analyze_sector_strength(stock_quotes)

    # 2. 主力资金流向
    result["money_flow"] = analyze_money_flow(holdings)

    # 3. BDI
    result["bdi"] = get_bdi()

    # 4. 综合建议
    summary = []

    # 资金流向建议
    for code, mf in result["money_flow"].items():
        if "流出" in mf["signal"]:
            summary.append(f"🔴 {mf['name']}主力净流出{abs(mf['main_net']):.0f}万，注意出货风险")
        elif "流入" in mf["signal"]:
            summary.append(f"🟢 {mf['name']}主力净流入{mf['main_net']:.0f}万，有资金关注")

    # 板块强弱建议
    ss = result.get("sector_strength")
    if ss and ss.get("recommendation"):
        summary.append(ss["recommendation"])

    # BDI 建议
    bdi = result["bdi"]
    if bdi and bdi.get("value"):
        summary.append(f"📊 BDI: {bdi['value']:.0f} ({bdi['change_pct']:+.1f}%) {bdi['signal']}")

    result["summary"] = summary

    return result

if __name__ == "__main__":
    # 测试
    quotes = {
        "sh600150": {"name": "中国船舶", "change_pct": -1.2, "price": 30.52},
        "sh600482": {"name": "中国动力", "change_pct": -0.8, "price": 31.72},
    }
    result = full_analysis(quotes)

    print("=== 板块相对强弱 ===")
    ss = result.get("sector_strength", {})
    if ss:
        sector = ss.get("sector", {})
        print(f"  板块: {sector.get('name','?')} {sector.get('change_pct',0):+.2f}%")
        for s in ss.get("stocks", []):
            print(f"  {s['name']}: {s['change_pct']:+.2f}% (vs板块: {s['rs_vs_sector']:+.2f}%) {s['verdict']}")
        print(f"  建议: {ss.get('recommendation','')}")

    print("\n=== 主力资金流向 ===")
    for code, mf in result.get("money_flow", {}).items():
        print(f"  {mf['name']}: 主力{mf['main_net']:+.0f}万 {mf['signal']}")

    print("\n=== BDI ===")
    bdi = result.get("bdi", {})
    print(f"  BDI: {bdi.get('value','N/A')} {bdi.get('signal','')}")

    print("\n=== 综合建议 ===")
    for s in result.get("summary", []):
        print(f"  {s}")
