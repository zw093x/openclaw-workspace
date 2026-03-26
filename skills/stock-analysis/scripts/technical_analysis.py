#!/usr/bin/env python3
"""
Technical analysis for A-share stocks.
Calculates MA, volume ratio, trend signals from historical data.

Usage:
    python technical_analysis.py 600150 --period 60
    python technical_analysis.py 600150 600482 --period 30 --json
"""

import json
import sys
import urllib.request
from datetime import datetime, timedelta


def fetch_history(code: str, days: int = 60) -> list:
    """Fetch daily K-line data from Sina"""
    if code.startswith("6"):
        symbol = f"sh{code}"
    elif code.startswith(("0", "3")):
        symbol = f"sz{code}"
    else:
        symbol = code

    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={days}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data
    except Exception as e:
        print(f"[Error] 获取 {code} 历史数据失败: {e}")
        return []


def calc_ma(data: list, period: int) -> float:
    """Calculate Moving Average"""
    if len(data) < period:
        return None
    closes = [float(d["close"]) for d in data[-period:]]
    return round(sum(closes) / period, 2)


def calc_volume_ratio(data: list) -> float:
    """Volume ratio: today's volume / 5-day average volume"""
    if len(data) < 6:
        return None
    today_vol = float(data[-1]["volume"])
    avg_vol = sum(float(d["volume"]) for d in data[-6:-1]) / 5
    return round(today_vol / avg_vol, 2) if avg_vol > 0 else 0


def analyze_trend(data: list) -> dict:
    """Comprehensive technical analysis"""
    if not data:
        return {"error": "No data"}

    latest = data[-1]
    close = float(latest["close"])
    prev_close = float(data[-2]["close"]) if len(data) > 1 else close

    # Moving averages
    ma5 = calc_ma(data, 5)
    ma10 = calc_ma(data, 10)
    ma20 = calc_ma(data, 20)

    # Volume analysis
    vol_ratio = calc_volume_ratio(data)

    # Price change
    change_pct = round((close - prev_close) / prev_close * 100, 2) if prev_close else 0

    # Trend determination
    ma_status = "unknown"
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            ma_status = "多头排列"
        elif ma5 < ma10 < ma20:
            ma_status = "空头排列"
        else:
            ma_status = "震荡整理"

    # Position relative to MA20
    ma20_signal = ""
    if ma20:
        if close > ma20 and float(data[-2]["close"]) <= ma20:
            ma20_signal = "站上MA20"
        elif close < ma20 and float(data[-2]["close"]) >= ma20:
            ma20_signal = "跌破MA20"

    # Volume-price relationship
    vp_signal = ""
    if vol_ratio:
        if change_pct > 0 and vol_ratio > 1.3:
            vp_signal = "放量上涨"
        elif change_pct < 0 and vol_ratio > 1.3:
            vp_signal = "放量下跌"
        elif change_pct > 0 and vol_ratio < 0.7:
            vp_signal = "缩量上涨"
        elif change_pct < 0 and vol_ratio < 0.7:
            vp_signal = "缩量下跌"

    # Alert level
    alert = "none"
    if abs(change_pct) >= 5:
        alert = "S2"
    elif abs(change_pct) >= 3:
        alert = "S1"

    return {
        "close": close,
        "change_pct": change_pct,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "ma_status": ma_status,
        "ma20_signal": ma20_signal,
        "vol_ratio": vol_ratio,
        "vp_signal": vp_signal,
        "alert": alert,
        "date": latest.get("day", ""),
        "period_days": len(data),
    }


def format_analysis(code: str, result: dict) -> str:
    """Format analysis result"""
    if "error" in result:
        return f"[Error] {code}: {result['error']}"

    sign = "+" if result["change_pct"] >= 0 else ""
    lines = [
        f"[Analysis] {code} ({result['date']})",
        f"收盘: {result['close']} | 涨跌: {sign}{result['change_pct']}%",
        f"MA5: {result['ma5']} | MA10: {result['ma10']} | MA20: {result['ma20']}",
        f"均线状态: {result['ma_status']}",
        f"量比: {result['vol_ratio']}",
    ]

    if result["vp_signal"]:
        lines.append(f"信号: {result['vp_signal']}")
    if result["ma20_signal"]:
        lines.append(f"均线突破: {result['ma20_signal']}")
    if result["alert"] != "none":
        lines.append(f"⚠️ 预警级别: {result['alert']}")

    return "\n".join(lines)


def main():
    period = 60
    json_output = "--json" in sys.argv
    
    # Parse args, filtering out flags and their values
    codes = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--json":
            i += 1
        elif arg == "--period":
            if i + 1 < len(sys.argv):
                period = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        elif not arg.startswith("--"):
            codes.append(arg)
            i += 1
        else:
            i += 1

    if not codes:
        print("Usage: python technical_analysis.py <code1> [code2] [--period 60] [--json]")
        sys.exit(1)

    results = {}
    for code in codes:
        data = fetch_history(code, period)
        result = analyze_trend(data)
        results[code] = result
        if not json_output:
            print(format_analysis(code, result))
            print()

    if json_output:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
