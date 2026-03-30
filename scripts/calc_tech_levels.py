#!/usr/bin/env python3
"""
技术指标计算器
每天收盘后运行，计算最新技术指标，更新持仓监控标准

输出: /root/.openclaw/workspace/config/tech_levels.json
供 stock_realtime_monitor.py 盘中引用
"""

import json
import urllib.request
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
HOLDINGS_FILE = WORKSPACE / "config" / "holdings.json"
TECH_FILE = WORKSPACE / "config" / "tech_levels.json"

def fetch_kline(code, market, days=60):
    """获取日K线数据（东方财富API）"""
    secid = f"1.{code}" if market == "sh" else f"0.{code}"
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        f"secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&klt=101&fqt=1&end=20500101&lmt={days}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.eastmoney.com"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        klines = data.get("data", {}).get("klines", [])
        result = []
        for k in klines:
            parts = k.split(",")
            result.append({
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": float(parts[5]),
                "amount": float(parts[6]),
            })
        return result
    except Exception as e:
        print(f"⚠️ 获取 {code} K线失败: {e}")
        return []

def calc_ma(klines, period):
    """计算均线"""
    if len(klines) < period:
        return None
    closes = [k["close"] for k in klines[-period:]]
    return round(sum(closes) / len(closes), 2)

def calc_support_resistance(klines, lookback=20):
    """计算支撑位和阻力位（近N日高低点）"""
    if len(klines) < lookback:
        lookback = len(klines)
    recent = klines[-lookback:]
    highs = [k["high"] for k in recent]
    lows = [k["low"] for k in recent]
    
    resistance = round(max(highs), 2)
    support = round(min(lows), 2)
    
    # 次级支撑（去掉最低的3天后的最低点，更稳健）
    sorted_lows = sorted(lows)
    if len(sorted_lows) > 5:
        secondary_support = round(sorted_lows[3], 2)  # 去掉最低3个极端值
    else:
        secondary_support = support
    
    return support, secondary_support, resistance

def calc_atr(klines, period=14):
    """计算 ATR（平均真实波幅）"""
    if len(klines) < period + 1:
        return None
    trs = []
    for i in range(1, len(klines)):
        h = klines[i]["high"]
        l = klines[i]["low"]
        pc = klines[i-1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if len(trs) < period:
        return None
    return round(sum(trs[-period:]) / period, 3)

def calc_volume_ratio(klines, period=20):
    """计算今日成交量 / 近N日均量"""
    if len(klines) < period + 1:
        return 1.0
    today_vol = klines[-1]["volume"]
    avg_vol = sum(k["volume"] for k in klines[-(period+1):-1]) / period
    if avg_vol == 0:
        return 1.0
    return round(today_vol / avg_vol, 2)

def calc_rsi(klines, period=14):
    """计算 RSI（相对强弱指标）"""
    if len(klines) < period + 1:
        return None
    closes = [k["close"] for k in klines[-(period+1):]]
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 1)

def calc_macd(klines, fast=12, slow=26, signal=9):
    """计算 MACD（指数移动平均）"""
    if len(klines) < slow + signal:
        return None, None, None
    closes = [k["close"] for k in klines]

    def ema(data, period):
        k = 2 / (period + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(data[i] * k + result[-1] * (1 - k))
        return result

    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = ema(dif, signal)
    macd_bar = [(d - e) * 2 for d, e in zip(dif, dea)]

    return round(dif[-1], 3), round(dea[-1], 3), round(macd_bar[-1], 3)

def calc_bollinger(klines, period=20, std_dev=2):
    """计算布林带"""
    if len(klines) < period:
        return None, None, None
    closes = [k["close"] for k in klines[-period:]]
    ma = sum(closes) / period
    variance = sum((c - ma) ** 2 for c in closes) / period
    std = variance ** 0.5
    upper = round(ma + std_dev * std, 2)
    middle = round(ma, 2)
    lower = round(ma - std_dev * std, 2)
    return upper, middle, lower

def calc_turnover_rate(klines, period=20):
    """计算换手率趋势（今日 vs 近N日均值）"""
    # 换手率需要流通股本数据，这里用成交量变化率近似
    if len(klines) < period + 1:
        return 1.0
    today_vol = klines[-1]["volume"]
    avg_vol = sum(k["volume"] for k in klines[-(period+1):-1]) / period
    if avg_vol == 0:
        return 1.0
    return round(today_vol / avg_vol, 2)

def check_volume_price_divergence(klines, lookback=10):
    """检测量价背离"""
    if len(klines) < lookback + 1:
        return "none"
    recent = klines[-(lookback+1):]
    prices = [k["close"] for k in recent]
    volumes = [k["volume"] for k in recent]

    # 价格趋势
    price_up = prices[-1] > prices[0]
    # 量能趋势
    vol_recent = sum(volumes[-3:]) / 3
    vol_early = sum(volumes[:3]) / 3
    vol_down = vol_recent < vol_early

    if price_up and vol_down:
        return "bearish"  # 价涨量缩 → 危险
    elif not price_up and not vol_down:
        return "bullish"  # 价跌量增 → 恐慌抛售可能见底
    return "none"

def analyze_stock(code, name, market, klines):
    """综合分析单只股票"""
    if not klines:
        return None
    
    latest = klines[-1]
    price = latest["close"]
    
    ma5 = calc_ma(klines, 5)
    ma10 = calc_ma(klines, 10)
    ma20 = calc_ma(klines, 20)
    ma60 = calc_ma(klines, 60)
    
    support, secondary_support, resistance = calc_support_resistance(klines, 20)
    atr = calc_atr(klines, 14)
    vol_ratio = calc_volume_ratio(klines, 20)
    
    # 动态止损线：基于支撑位 - 1 ATR（给一定的容错空间）
    if atr and secondary_support:
        dynamic_stop_loss = round(secondary_support - atr, 2)
    elif secondary_support:
        dynamic_stop_loss = round(secondary_support * 0.98, 2)
    else:
        dynamic_stop_loss = None
    
    # 动态减仓线：基于均线压力
    reduce_levels = []
    if ma10 and price < ma10:
        # 价格在 MA10 下方，反弹到 MA10 附近可减仓
        reduce_levels.append({
            "range": [round(ma10 * 0.995, 2), round(ma10 * 1.005, 2)],
            "sell": 250,
            "label": f"MA10减仓({ma10:.2f})",
            "trigger": "price_in_range"
        })
    if ma20 and price < ma20:
        reduce_levels.append({
            "range": [round(ma20 * 0.995, 2), round(ma20 * 1.005, 2)],
            "sell": 250,
            "label": f"MA20减仓({ma20:.2f})",
            "trigger": "price_in_range"
        })
    if resistance and price < resistance:
        reduce_levels.append({
            "range": [round(resistance * 0.98, 2), resistance],
            "sell": 250,
            "label": f"阻力位减仓({resistance:.2f})",
            "trigger": "price_in_range"
        })
    
    # 趋势判断
    trend_signals = []
    if ma5 and ma10:
        if ma5 > ma10:
            trend_signals.append("MA5>MA10 金叉")
        else:
            trend_signals.append("MA5<MA10 死叉")
    if ma20 and ma60:
        if price > ma60:
            trend_signals.append("站上MA60")
        else:
            trend_signals.append("跌破MA60")

    # RSI
    rsi = calc_rsi(klines, 14)
    if rsi:
        if rsi > 70:
            trend_signals.append(f"RSI={rsi}(超买)")
        elif rsi < 30:
            trend_signals.append(f"RSI={rsi}(超卖)")
        else:
            trend_signals.append(f"RSI={rsi}")

    # MACD
    dif, dea, macd_bar = calc_macd(klines)
    if dif is not None:
        if dif > dea:
            trend_signals.append("MACD金叉")
        else:
            trend_signals.append("MACD死叉")
        if dif > 0 and dea > 0:
            trend_signals.append("零轴上方")

    # 布林带
    bb_upper, bb_middle, bb_lower = calc_bollinger(klines, 20, 2)

    # 量价背离
    divergence = check_volume_price_divergence(klines, 10)
    if divergence == "bearish":
        trend_signals.append("⚠️价涨量缩背离")
    elif divergence == "bullish":
        trend_signals.append("💡价跌量增可能见底")

    # RSI 减仓信号
    if rsi and rsi > 70:
        reduce_levels.insert(0, {
            "range": [price - 0.05, price + 0.05],
            "sell": 250,
            "label": f"RSI超买减仓(RSI={rsi})",
            "trigger": "rsi_overbought"
        })
    elif rsi and rsi > 65:
        reduce_levels.append({
            "range": [price - 0.05, price + 0.05],
            "sell": 250,
            "label": f"RSI偏高注意(RSI={rsi})",
            "trigger": "rsi_high"
        })

    # 布林带减仓信号
    if bb_upper and price >= bb_upper * 0.98:
        reduce_levels.insert(0, {
            "range": [round(bb_upper * 0.98, 2), bb_upper],
            "sell": 250,
            "label": f"布林上轨减仓({bb_upper})",
            "trigger": "bb_upper"
        })

    return {
        "code": code,
        "name": name,
        "market": market,
        "date": latest["date"],
        "price": price,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "ma60": ma60,
        "support": support,
        "secondary_support": secondary_support,
        "resistance": resistance,
        "atr_14": atr,
        "volume_ratio": vol_ratio,
        "rsi_14": rsi,
        "macd_dif": dif,
        "macd_dea": dea,
        "macd_bar": macd_bar,
        "bb_upper": bb_upper,
        "bb_middle": bb_middle,
        "bb_lower": bb_lower,
        "volume_divergence": divergence,
        "dynamic_stop_loss": dynamic_stop_loss,
        "reduce_levels": reduce_levels,
        "trend": " ".join(trend_signals),
        "updated_at": datetime.now().isoformat()
    }

def main():
    # 加载持仓
    with open(HOLDINGS_FILE, "r") as f:
        holdings = json.load(f)
    
    results = {}
    
    # 分析持仓股票
    for item in holdings.get("holdings", []):
        if item.get("status") == "sold" or item.get("shares", 0) == 0:
            continue
        
        code = item["code"]
        name = item["name"]
        market = item.get("market", "sh")
        
        print(f"📊 分析 {name}({code})...")
        klines = fetch_kline(code, market, days=60)
        if klines:
            result = analyze_stock(code, name, market, klines)
            if result:
                results[f"{market}{code}"] = result
                print(f"   ✅ MA5={result['ma5']} MA10={result['ma10']} MA20={result['ma20']}")
                print(f"   支撑={result['support']} 次级支撑={result['secondary_support']} 阻力={result['resistance']}")
                print(f"   ATR={result['atr_14']} 动态止损={result['dynamic_stop_loss']}")
                print(f"   RSI={result.get('rsi_14','N/A')} MACD:DIF={result.get('macd_dif','N/A')} DEA={result.get('macd_dea','N/A')}")
                print(f"   布林:上={result.get('bb_upper','N/A')} 中={result.get('bb_middle','N/A')} 下={result.get('bb_lower','N/A')}")
                print(f"   量价背离: {result.get('volume_divergence','none')} 量比: {result['volume_ratio']}")
                print(f"   趋势: {result['trend']}")
    
    # 保存
    output = {
        "updated_at": datetime.now().isoformat(),
        "stocks": results
    }
    with open(TECH_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 技术指标已保存到 {TECH_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
