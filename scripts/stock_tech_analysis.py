#!/usr/bin/env python3
"""
股票技术指标计算器
基于通达信K线数据，计算MA/MACD/RSI/KDJ/布林带
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace/scripts")
from stock_data_provider import get_kline
import numpy as np


def calc_ma(close, periods=[5, 10, 20, 60]):
    """计算移动平均线"""
    result = {}
    for p in periods:
        if len(close) >= p:
            result[f'MA{p}'] = float(np.mean(close[-p:]))
        else:
            result[f'MA{p}'] = None
    return result


def calc_rsi(close, period=14):
    """计算RSI指标"""
    if len(close) < period + 1:
        return None
    deltas = np.diff(close[-(period+1):])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def calc_macd(close, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    if len(close) < slow + signal:
        return None
    
    def ema(data, span):
        alpha = 2 / (span + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[-1])
        return result
    
    ema_fast = ema(list(close), fast)
    ema_slow = ema(list(close), slow)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = ema(dif, signal)
    macd = [2 * (d - e) for d, e in zip(dif, dea)]
    
    return {
        'DIF': round(dif[-1], 4),
        'DEA': round(dea[-1], 4),
        'MACD': round(macd[-1], 4),
        'signal': '金叉' if dif[-1] > dea[-1] and dif[-2] <= dea[-2] else
                  '死叉' if dif[-1] < dea[-1] and dif[-2] >= dea[-2] else
                  '多头' if dif[-1] > dea[-1] else '空头',
    }


def calc_kdj(high, low, close, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    if len(close) < n:
        return None
    
    k, d = 50.0, 50.0
    for i in range(n - 1, len(close)):
        h_n = max(high[i-n+1:i+1])
        l_n = min(low[i-n+1:i+1])
        if h_n == l_n:
            rsv = 50.0
        else:
            rsv = (close[i] - l_n) / (h_n - l_n) * 100
        k = (m1 - 1) / m1 * k + 1 / m1 * rsv
        d = (m2 - 1) / m2 * d + 1 / m2 * k
    
    j = 3 * k - 2 * d
    return {
        'K': round(k, 2),
        'D': round(d, 2),
        'J': round(j, 2),
        'signal': '超买' if j > 80 else '超卖' if j < 20 else '中性',
    }


def calc_bollinger(close, period=20, std_mult=2):
    """计算布林带"""
    if len(close) < period:
        return None
    ma = np.mean(close[-period:])
    std = np.std(close[-period:])
    return {
        'UPPER': round(ma + std_mult * std, 2),
        'MID': round(ma, 2),
        'LOWER': round(ma - std_mult * std, 2),
        'position': '上轨外' if close[-1] > ma + std_mult * std else
                    '上轨附近' if close[-1] > ma + std * std_mult * 0.8 else
                    '下轨外' if close[-1] < ma - std_mult * std else
                    '下轨附近' if close[-1] < ma - std * std_mult * 0.8 else
                    '中轨',
    }


def calc_volume_ratio(vol, period=5):
    """计算量比（当前成交量/过去N日均量）"""
    if len(vol) < period + 1:
        return None
    avg_vol = np.mean(vol[-(period+1):-1])
    if avg_vol == 0:
        return None
    return round(vol[-1] / avg_vol, 2)


def analyze_stock(code, name=None, kline_periods=60):
    """综合分析单只股票
    
    Returns:
        dict: 包含所有技术指标和综合判断
    """
    # 获取日K线
    df = get_kline(code, frequency=9, offset=kline_periods)
    if df is None or len(df) < 20:
        return {'error': f'{code} K线数据不足'}
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    vol = df['volume'].values if 'volume' in df.columns else df['vol'].values
    
    name = name or code
    
    # 计算所有指标
    ma = calc_ma(close)
    rsi = calc_rsi(close)
    macd = calc_macd(close)
    kdj = calc_kdj(high, low, close)
    boll = calc_bollinger(close)
    vol_ratio = calc_volume_ratio(vol)
    
    # 趋势判断
    cur = close[-1]
    ma_trend = []
    for period in [5, 10, 20, 60]:
        key = f'MA{period}'
        if ma.get(key):
            if cur > ma[key]:
                ma_trend.append(f'MA{period}上方')
            else:
                ma_trend.append(f'MA{period}下方')
    
    # 综合信号
    signals = []
    if rsi:
        if rsi > 70:
            signals.append(f'RSI={rsi}超买⚠️')
        elif rsi < 30:
            signals.append(f'RSI={rsi}超卖💡')
        else:
            signals.append(f'RSI={rsi}中性')
    
    if macd:
        signals.append(f'MACD{macd["signal"]}({macd["DIF"]:.4f}/{macd["DEA"]:.4f})')
    
    if kdj:
        signals.append(f'KDJ K={kdj["K"]} D={kdj["D"]} J={kdj["J"]}({kdj["signal"]})')
    
    if boll:
        signals.append(f'布林{boll["position"]}(上{boll["UPPER"]}中{boll["MID"]}下{boll["LOWER"]})')
    
    if vol_ratio:
        if vol_ratio > 2.0:
            signals.append(f'量比{vol_ratio}🔥异常放量')
        elif vol_ratio > 1.5:
            signals.append(f'量比{vol_ratio}放量')
        elif vol_ratio < 0.5:
            signals.append(f'量比{vol_ratio}缩量')
        else:
            signals.append(f'量比{vol_ratio}正常')
    
    # 涨跌幅
    pct = (cur - close[-2]) / close[-2] * 100 if len(close) > 1 else 0
    
    return {
        'name': name,
        'code': code,
        'price': round(cur, 2),
        'change_pct': round(pct, 2),
        'ma': ma,
        'ma_trend': ma_trend,
        'rsi': rsi,
        'macd': macd,
        'kdj': kdj,
        'boll': boll,
        'vol_ratio': vol_ratio,
        'signals': signals,
        'high_5d': round(max(high[-5:]), 2),
        'low_5d': round(min(low[-5:]), 2),
        'data_points': len(close),
    }


def format_analysis_card(analyses):
    """将分析结果格式化为文字卡片"""
    lines = []
    for a in analyses:
        if 'error' in a:
            lines.append(f"❌ {a['error']}")
            continue
        
        # 标题行
        trend_emoji = '📈' if a['change_pct'] > 0 else '📉' if a['change_pct'] < 0 else '➡️'
        lines.append(f"{'='*30}")
        lines.append(f"{trend_emoji} {a['name']}({a['code']})")
        lines.append(f"现价 {a['price']:.2f} | 涨跌 {a['change_pct']:+.2f}%")
        lines.append(f"5日区间 {a['low_5d']:.2f} - {a['high_5d']:.2f}")
        
        # 均线排列
        ma_parts = []
        for period in [5, 10, 20, 60]:
            key = f'MA{period}'
            if a['ma'].get(key):
                indicator = '🟢' if a['price'] > a['ma'][key] else '🔴'
                ma_parts.append(f"{indicator}{key}={a['ma'][key]:.2f}")
        lines.append(f"均线: {' '.join(ma_parts)}")
        
        # 趋势
        lines.append(f"趋势: {' > '.join(a['ma_trend'][:3]) if a['ma_trend'] else '数据不足'}")
        
        # 技术信号
        for sig in a['signals']:
            lines.append(f"  • {sig}")
        
        lines.append("")
    
    return '\n'.join(lines)


# ====== 测试 ======
if __name__ == "__main__":
    print("=== 技术指标分析 ===\n")
    codes = [
        ('600150', '中国船舶'),
        ('600482', '中国动力'),
    ]
    
    results = []
    for code, name in codes:
        result = analyze_stock(code, name)
        results.append(result)
    
    print(format_analysis_card(results))
