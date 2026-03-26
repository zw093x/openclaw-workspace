#!/usr/bin/env python3
"""
股票技术分析工具
功能：K线均线分析、成交量异常检测、买卖信号
"""
import json
import sys
import urllib.request

STOCKS = {
    "sh600150": "中国船舶",
    "sh600482": "中国动力",
    "sh603656": "泰禾智能"
}

# 朋友账户（单独推送）
FRIEND_STOCKS = {
    "sz002841": "视源股份"
}

# 朋友账户减仓策略
FRIEND_REDUCE_PLAN = {
    "视源股份": [
        {"level": 1, "range": (34.50, 35.00), "shares": 200, "label": "第一止盈"},
        {"level": 2, "range": (35.00, 35.60), "shares": 300, "label": "第二止盈/清仓"},
        {"level": -1, "range": (32.11, 32.45), "shares": 200, "label": "止损-5%"},
        {"level": -2, "range": (0, 30.42), "shares": 500, "label": "强止损-10%/清仓"},
    ],
}

# 减仓策略（2026-03-25）
REDUCE_PLAN = {
    "中国船舶": [
        {"level": 1, "range": (32.50, 33.00), "shares": 250, "label": "第一减仓"},
        {"level": 2, "range": (34.00, 34.50), "shares": 250, "label": "第二减仓"},
    ],
    "中国动力": [
        {"level": 1, "range": (32.50, 33.00), "shares": 250, "label": "第一减仓"},
        {"level": 2, "range": (33.50, 34.00), "shares": 250, "label": "第二减仓"},
    ],
    "泰禾智能": [
        {"level": 1, "range": (22.50, 22.70), "shares": 400, "label": "第一减仓"},
        {"level": 2, "range": (23.00, 99.99), "shares": 400, "label": "第二减仓/清仓"},
    ],
}

def fetch_kline(symbol, days=30):
    """获取日K线数据"""
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={days}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def fetch_realtime(symbol):
    """获取实时行情"""
    url = f"https://hq.sinajs.cn/list={symbol}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read().decode("gbk")
        parts = data.split('"')[1].split(",")
        return {
            "name": parts[0],
            "open": float(parts[1]),
            "pre_close": float(parts[2]),
            "price": float(parts[3]),
            "high": float(parts[4]),
            "low": float(parts[5]),
            "volume": int(parts[8]),
            "amount": float(parts[9]),
            "date": parts[30],
            "time": parts[31]
        }

def calc_ma(data, n):
    """计算N日均线"""
    closes = [float(d["close"]) for d in data]
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n

def calc_volume_ma(data, n):
    """计算成交量N日均量"""
    volumes = [int(d["volume"]) for d in data]
    if len(volumes) < n:
        return None
    return sum(volumes[-n:]) / n

def analyze_stock(symbol, name):
    """综合分析一只股票"""
    signals = []
    
    # 获取K线和实时数据
    kline = fetch_kline(symbol, 30)
    rt = fetch_realtime(symbol)
    
    closes = [float(d["close"]) for d in kline]
    volumes = [int(d["volume"]) for d in kline]
    
    current_price = rt["price"]
    pre_close = rt["pre_close"]
    current_volume = rt["volume"]
    
    # 涨跌幅
    change_pct = (current_price - pre_close) / pre_close * 100
    
    # 均线
    ma5 = calc_ma(kline, 5)
    ma10 = calc_ma(kline, 10)
    ma20 = calc_ma(kline, 20)
    vol_ma5 = calc_volume_ma(kline, 5)
    vol_ma10 = calc_volume_ma(kline, 10)
    
    # 前日成交量
    prev_volume = volumes[-1] if volumes else 0
    
    # ===== 信号检测 =====
    
    # 1. 涨跌幅异动
    if abs(change_pct) >= 5:
        direction = "暴涨" if change_pct > 0 else "暴跌"
        signals.append(f"🔴 S2-{direction}：{change_pct:+.2f}%")
    elif abs(change_pct) >= 3:
        direction = "大涨" if change_pct > 0 else "大跌"
        signals.append(f"🟡 S1-{direction}：{change_pct:+.2f}%")
    
    # 2. 成交量异常
    if vol_ma5 and current_volume > 0:
        vol_ratio = current_volume / vol_ma5
        if vol_ratio >= 2.0:
            signals.append(f"🔴 成交量异常放大：今日/5日均量 = {vol_ratio:.1f}倍")
        elif vol_ratio >= 1.5:
            signals.append(f"🟡 成交量温和放大：今日/5日均量 = {vol_ratio:.1f}倍")
        elif vol_ratio <= 0.5:
            signals.append(f"🟡 成交量极度萎缩：今日/5日均量 = {vol_ratio:.1f}倍")
    
    # 3. 均线突破/跌破
    ma_signals = []
    for ma_name, ma_val in [("MA5", ma5), ("MA10", ma10), ("MA20", ma20)]:
        if ma_val is None:
            continue
        prev_close = closes[-1] if closes else pre_close
        # 当前价站上均线
        if prev_close < ma_val <= current_price:
            ma_signals.append(f"📈 站上{ma_name}({ma_val:.2f})")
        # 当前价跌破均线
        elif prev_close > ma_val >= current_price:
            ma_signals.append(f"📉 跌破{ma_name}({ma_val:.2f})")
    signals.extend(ma_signals)
    
    # 4. 均线排列
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            signals.append("🟢 多头排列：MA5>MA10>MA20")
        elif ma5 < ma10 < ma20:
            signals.append("🔴 空头排列：MA5<MA10<MA20")
    
    # 5. 量价配合
    if vol_ma5 and change_pct > 2 and current_volume / vol_ma5 > 1.3:
        signals.append("🟢 量价齐升：放量上涨")
    elif vol_ma5 and change_pct < -2 and current_volume / vol_ma5 > 1.3:
        signals.append("🔴 放量下跌")
    elif vol_ma5 and change_pct > 1 and current_volume / vol_ma5 < 0.7:
        signals.append("🟡 缩量上涨，注意量能不足")
    elif vol_ma5 and change_pct < -1 and current_volume / vol_ma5 < 0.7:
        signals.append("🟡 缩量下跌，抛压减弱")
    
    return {
        "name": name,
        "price": current_price,
        "change_pct": change_pct,
        "volume": current_volume,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "signals": signals,
        "high": rt["high"],
        "low": rt["low"],
        "reduce_alerts": check_reduce_zone(name, current_price, rt["high"])
    }

def check_reduce_zone(name, current_price, day_high):
    """检测是否接近或触及减仓位"""
    alerts = []
    plan = REDUCE_PLAN.get(name, [])
    for p in plan:
        lo, hi = p["range"]
        # 盘中最高价触及减仓区间
        if day_high >= lo and day_high <= hi:
            alerts.append(f"⚠️ {p['label']}：盘中触及{lo}-{hi}区间（已触达），建议减仓{p['shares']}股")
        elif day_high > hi:
            alerts.append(f"⚠️ {p['label']}：盘中突破{hi}（已越过），建议减仓{p['shares']}股")
        # 当前价接近减仓位（5%以内）
        elif current_price >= lo * 0.95 and current_price < lo:
            dist = (lo - current_price) / current_price * 100
            alerts.append(f"📌 {p['label']}：距{lo}-{hi}仅{dist:.1f}%，关注触达机会")
    return alerts

def check_friend_reduce_zone(name, current_price, day_high, day_low):
    """检测朋友账户止盈止损位"""
    alerts = []
    plan = FRIEND_REDUCE_PLAN.get(name, [])
    cost = 33.80
    for p in plan:
        lo, hi = p["range"]
        level = p["level"]
        if level > 0:  # 止盈
            if day_high >= lo:
                alerts.append(f"📈 {p['label']}：盘中触及{lo}-{hi}区间，建议止盈{p['shares']}股")
            elif current_price >= lo * 0.97:
                dist = (lo - current_price) / current_price * 100
                alerts.append(f"📌 {p['label']}：距{lo}仅{dist:.1f}%，关注止盈机会")
        else:  # 止损
            if day_low <= hi:
                alerts.append(f"🔴 {p['label']}：盘中触及{hi}以下（{lo}-{hi}），建议止损{p['shares']}股")
            elif current_price <= hi * 1.03:
                dist = (current_price - hi) / current_price * 100
                alerts.append(f"⚠️ {p['label']}：距止损位{hi}仅{dist:.1f}%，注意风险")
    return alerts

def format_report(results):
    """格式化分析报告"""
    lines = ["📊 股票技术面分析报告", "=" * 30, ""]
    
    has_alert = False
    
    for r in results:
        lines.append(f"【{r['name']}】")
        lines.append(f"  现价：{r['price']:.2f}  涨跌：{r['change_pct']:+.2f}%")
        lines.append(f"  最高：{r['high']:.2f}  最低：{r['low']:.2f}")
        lines.append(f"  MA5：{r['ma5']:.2f}  MA10：{r['ma10']:.2f}  MA20：{r['ma20']:.2f}")
        
        if r["signals"]:
            has_alert = True
            lines.append("  信号：")
            for s in r["signals"]:
                lines.append(f"    {s}")
        else:
            lines.append("  信号：无异常")
        
        # 减仓位提醒
        if r.get("reduce_alerts"):
            has_alert = True
            lines.append("  🎯 减仓提醒：")
            for a in r["reduce_alerts"]:
                lines.append(f"    {a}")
        
        lines.append("")
    
    return "\n".join(lines), has_alert

def main():
    results = []
    for symbol, name in STOCKS.items():
        try:
            r = analyze_stock(symbol, name)
            results.append(r)
        except Exception as e:
            results.append({"name": name, "error": str(e)})
    
    report, has_alert = format_report(results)
    print(report)
    
    # 朋友账户股票（单独分析）
    friend_results = []
    for symbol, name in FRIEND_STOCKS.items():
        try:
            r = analyze_stock(symbol, name)
            friend_results.append(r)
        except Exception as e:
            friend_results.append({"name": name, "error": str(e)})
    
    if friend_results:
        print("📱 朋友账户 - 视源股份")
        print("=" * 30)
        for r in friend_results:
            if "error" in r:
                print(f"【{r['name']}】获取失败：{r['error']}")
                continue
            print(f"【{r['name']}】")
            print(f"  现价：{r['price']:.2f}  涨跌：{r['change_pct']:+.2f}%")
            print(f"  最高：{r['high']:.2f}  最低：{r['low']:.2f}")
            print(f"  MA5：{r['ma5']:.2f}  MA10：{r['ma10']:.2f}  MA20：{r['ma20']:.2f}")
            if r["signals"]:
                print("  信号：")
                for s in r["signals"]:
                    print(f"    {s}")
            else:
                print("  信号：无异常")
            # 盈亏计算（朋友账户：500股@33.80）
            cost = 33.80
            pnl = (r["price"] - cost) * 500
            pnl_pct = (r["price"] - cost) / cost * 100
            print(f"  💰 持仓盈亏：{pnl:+.0f} 元（{pnl_pct:+.2f}%，成本33.80）")
            # 止盈止损提醒
            friend_reduce = check_friend_reduce_zone(r["name"], r["price"], r["high"], r["low"])
            if friend_reduce:
                print("  🎯 止盈止损提醒：")
                for a in friend_reduce:
                    print(f"    {a}")
            print()
    
    # 输出JSON供调用方判断是否需要推送
    if "--json" in sys.argv:
        print("\n---JSON---")
        print(json.dumps({
            "has_alert": has_alert,
            "results": results,
            "friend_results": friend_results
        }, ensure_ascii=False))

if __name__ == "__main__":
    main()
