#!/usr/bin/env python3
"""
股票策略学习引擎
基于通达信历史数据，测试和优化交易策略
记录每次信号，追踪准确率，自动优化参数
"""

import sys
import json
import os
import numpy as np
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/root/.openclaw/workspace/scripts")
from stock_data_provider import get_kline

LEARN_DIR = "/root/.openclaw/workspace/memory/strategy-learning"
os.makedirs(LEARN_DIR, exist_ok=True)

# ====== 策略库 ======

def strategy_ma_cross(close, fast=5, slow=20):
    """均线交叉策略"""
    if len(close) < slow + 1:
        return []
    
    ma_fast = [np.mean(close[max(0,i-fast+1):i+1]) for i in range(len(close))]
    ma_slow = [np.mean(close[max(0,i-slow+1):i+1]) for i in range(len(close))]
    
    signals = []
    for i in range(1, len(close)):
        if ma_fast[i] > ma_slow[i] and ma_fast[i-1] <= ma_slow[i-1]:
            signals.append(('buy', i, f'MA{fast}上穿MA{slow}', ma_fast[i], ma_slow[i]))
        elif ma_fast[i] < ma_slow[i] and ma_fast[i-1] >= ma_slow[i-1]:
            signals.append(('sell', i, f'MA{fast}下穿MA{slow}', ma_fast[i], ma_slow[i]))
    
    return signals


def strategy_macd_cross(close, fast=12, slow=26, signal=9):
    """MACD金叉/死叉策略"""
    if len(close) < slow + signal:
        return []
    
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
    
    signals = []
    for i in range(1, len(close)):
        if dif[i] > dea[i] and dif[i-1] <= dea[i-1]:
            signals.append(('buy', i, 'MACD金叉', dif[i], dea[i]))
        elif dif[i] < dea[i] and dif[i-1] >= dea[i-1]:
            signals.append(('sell', i, 'MACD死叉', dif[i], dea[i]))
    
    return signals


def strategy_rsi_extreme(close, period=14, buy_level=30, sell_level=70):
    """RSI超买超卖策略"""
    if len(close) < period + 1:
        return []
    
    signals = []
    prev_state = None
    
    for i in range(period, len(close)):
        deltas = np.diff(close[i-period:i+1])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        rsi = 100 - 100 / (1 + avg_gain / avg_loss) if avg_loss > 0 else 100
        
        if rsi < buy_level and prev_state != 'oversold':
            signals.append(('buy', i, f'RSI超卖({rsi:.1f})', rsi, buy_level))
            prev_state = 'oversold'
        elif rsi > sell_level and prev_state != 'overbought':
            signals.append(('sell', i, f'RSI超买({rsi:.1f})', rsi, sell_level))
            prev_state = 'overbought'
        elif buy_level <= rsi <= sell_level:
            prev_state = None
    
    return signals


def strategy_kdj_cross(close, high, low, n=9, m1=3, m2=3):
    """KDJ金叉/死叉策略"""
    if len(close) < n:
        return []
    
    k_values, d_values = [], []
    k, d = 50.0, 50.0
    
    for i in range(n - 1, len(close)):
        h_n = max(high[i-n+1:i+1])
        l_n = min(low[i-n+1:i+1])
        rsv = (close[i] - l_n) / (h_n - l_n) * 100 if h_n != l_n else 50
        k = (m1 - 1) / m1 * k + 1 / m1 * rsv
        d = (m2 - 1) / m2 * d + 1 / m2 * k
        k_values.append(k)
        d_values.append(d)
    
    signals = []
    offset = n - 1
    for i in range(1, len(k_values)):
        idx = i + offset
        if k_values[i] > d_values[i] and k_values[i-1] <= d_values[i-1]:
            if k_values[i] < 20:
                signals.append(('buy', idx, 'KDJ低位金叉', k_values[i], d_values[i]))
        elif k_values[i] < d_values[i] and k_values[i-1] >= d_values[i-1]:
            if k_values[i] > 80:
                signals.append(('sell', idx, 'KDJ高位死叉', k_values[i], d_values[i]))
    
    return signals


def strategy_bollinger_reversion(close, period=20, std_mult=2):
    """布林带回归策略"""
    if len(close) < period:
        return []
    
    signals = []
    for i in range(period, len(close)):
        ma = np.mean(close[i-period+1:i+1])
        std = np.std(close[i-period+1:i+1])
        upper = ma + std_mult * std
        lower = ma - std_mult * std
        
        if close[i] <= lower and (i == 0 or close[i-1] > lower):
            signals.append(('buy', i, f'触及布林下轨({lower:.2f})', close[i], lower))
        elif close[i] >= upper and (i == 0 or close[i-1] < upper):
            signals.append(('sell', i, f'触及布林上轨({upper:.2f})', close[i], upper))
    
    return signals


def strategy_volume_price(close, vol, period=5, vol_ratio_threshold=2.0):
    """量价关系策略"""
    if len(close) < period + 1:
        return []
    
    signals = []
    for i in range(period, len(close)):
        avg_vol = np.mean(vol[i-period:i])
        if avg_vol == 0:
            continue
        current_vol_ratio = vol[i] / avg_vol
        price_change = (close[i] - close[i-1]) / close[i-1]
        
        # 放量上涨 → 买入信号
        if current_vol_ratio > vol_ratio_threshold and price_change > 0.01:
            signals.append(('buy', i, f'放量上涨(量比{current_vol_ratio:.1f})', price_change*100, vol_ratio_threshold))
        # 放量下跌 → 卖出信号
        elif current_vol_ratio > vol_ratio_threshold and price_change < -0.01:
            signals.append(('sell', i, f'放量下跌(量比{current_vol_ratio:.1f})', price_change*100, vol_ratio_threshold))
    
    return signals


# ====== 回测引擎 ======

def backtest(close, signals, hold_days=5, cost_pct=0.0015):
    """回测策略信号
    
    Args:
        close: 收盘价列表
        signals: (action, index, reason, value1, value2)
        hold_days: 持仓天数
        cost_pct: 单次交易成本（印花税+佣金）
    
    Returns:
        dict: 回测结果
    """
    if not signals:
        return {'trades': 0, 'win_rate': 0, 'avg_return': 0, 'total_return': 0, 'max_drawdown': 0}
    
    trades = []
    
    for action, idx, reason, v1, v2 in signals:
        if action != 'buy':
            continue
        if idx + hold_days >= len(close):
            continue
        
        entry_price = close[idx]
        exit_price = close[idx + hold_days]
        ret = (exit_price - entry_price) / entry_price - cost_pct * 2  # 买卖各一次成本
        trades.append({
            'entry_idx': idx,
            'exit_idx': idx + hold_days,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': ret * 100,
            'reason': reason,
        })
    
    if not trades:
        return {'trades': 0, 'win_rate': 0, 'avg_return': 0, 'total_return': 0, 'max_drawdown': 0}
    
    returns = [t['return_pct'] for t in trades]
    wins = [r for r in returns if r > 0]
    
    # 最大回撤
    cumulative = np.cumsum(returns)
    max_drawdown = 0
    peak = cumulative[0]
    for c in cumulative:
        if c > peak:
            peak = c
        dd = peak - c
        if dd > max_drawdown:
            max_drawdown = dd
    
    return {
        'trades': len(trades),
        'win_rate': len(wins) / len(returns) * 100 if returns else 0,
        'avg_return': np.mean(returns),
        'total_return': np.sum(returns),
        'max_drawdown': max_drawdown,
        'best_trade': max(returns),
        'worst_trade': min(returns),
        'profit_factor': abs(sum(wins) / sum(r for r in returns if r < 0)) if any(r < 0 for r in returns) else float('inf'),
    }


# ====== 策略优化器 ======

def optimize_parameters(code, name=None):
    """遍历不同参数组合，找到最优策略"""
    name = name or code
    
    # 获取日K线数据
    df = get_kline(code, frequency=9, offset=250)  # 约1年数据
    if df is None or len(df) < 60:
        return {'error': f'{name} 数据不足'}
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    vol = df['volume'].values if 'volume' in df.columns else df['vol'].values
    
    all_results = []
    
    # 1. MA交叉参数扫描
    for fast in [3, 5, 8, 10]:
        for slow in [15, 20, 30]:
            if fast >= slow:
                continue
            signals = strategy_ma_cross(close, fast, slow)
            bt = backtest(close, signals, hold_days=5)
            if bt['trades'] >= 3:
                all_results.append({
                    'strategy': f'MA交叉({fast}/{slow})',
                    **bt,
                })
    
    # 2. MACD参数扫描
    for f, s, sig in [(12,26,9), (8,17,9), (5,35,5)]:
        signals = strategy_macd_cross(close, f, s, sig)
        bt = backtest(close, signals, hold_days=5)
        if bt['trades'] >= 3:
            all_results.append({
                'strategy': f'MACD({f}/{s}/{sig})',
                **bt,
            })
    
    # 3. RSI参数扫描
    for period in [7, 14, 21]:
        for buy_level, sell_level in [(25,75), (30,70), (35,65)]:
            signals = strategy_rsi_extreme(close, period, buy_level, sell_level)
            bt = backtest(close, signals, hold_days=5)
            if bt['trades'] >= 3:
                all_results.append({
                    'strategy': f'RSI({period},{buy_level}/{sell_level})',
                    **bt,
                })
    
    # 4. KDJ
    signals = strategy_kdj_cross(close, high, low)
    bt = backtest(close, signals, hold_days=5)
    if bt['trades'] >= 3:
        all_results.append({'strategy': 'KDJ', **bt})
    
    # 5. 布林带回归
    for period in [15, 20, 25]:
        for mult in [1.5, 2.0, 2.5]:
            signals = strategy_bollinger_reversion(close, period, mult)
            bt = backtest(close, signals, hold_days=5)
            if bt['trades'] >= 3:
                all_results.append({
                    'strategy': f'布林({period},{mult})',
                    **bt,
                })
    
    # 6. 量价关系
    signals = strategy_volume_price(close, vol)
    bt = backtest(close, signals, hold_days=5)
    if bt['trades'] >= 3:
        all_results.append({'strategy': '量价关系', **bt})
    
    # 排序：按夏普比率（收益/波动）排序
    for r in all_results:
        if 'avg_return' in r and r['avg_return'] != 0:
            r['score'] = r['avg_return'] / (abs(r['worst_trade']) + 0.01) * r['win_rate'] / 100
        else:
            r['score'] = 0
    
    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return {
        'name': name,
        'code': code,
        'data_points': len(close),
        'data_range': f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
        'best_strategies': all_results[:5],
        'all_results': all_results,
    }


def format_optimization_report(results):
    """格式化优化报告"""
    lines = []
    lines.append(f"🔍 策略优化报告: {results['name']}({results['code']})")
    lines.append(f"数据: {results['data_points']}条 ({results['data_range']})")
    lines.append("")
    
    lines.append("🏆 Top 5 策略（按得分排序）:")
    lines.append(f"{'策略':<25} {'胜率':>6} {'均收益%':>8} {'总收益%':>8} {'交易数':>6} {'最大回撤':>8} {'得分':>6}")
    lines.append("-" * 80)
    
    for i, s in enumerate(results.get('best_strategies', []), 1):
        lines.append(
            f"{i}. {s['strategy']:<22} "
            f"{s['win_rate']:>5.1f}% "
            f"{s['avg_return']:>+7.2f}% "
            f"{s['total_return']:>+7.2f}% "
            f"{s['trades']:>5} "
            f"{s['max_drawdown']:>7.2f} "
            f"{s['score']:>5.2f}"
        )
    
    return '\n'.join(lines)


# ====== 主入口 ======

if __name__ == "__main__":
    codes = [
        ('600150', '中国船舶'),
        ('600482', '中国动力'),
    ]
    
    all_reports = []
    for code, name in codes:
        print(f"\n正在分析 {name}...")
        results = optimize_parameters(code, name)
        if 'error' not in results:
            report = format_optimization_report(results)
            all_reports.append(report)
            print(report)
            
            # 保存结果
            filepath = os.path.join(LEARN_DIR, f"{code}_strategy_{datetime.now().strftime('%Y%m%d')}.json")
            with open(filepath, 'w') as f:
                json.dump(results, f, ensure_ascii=False, default=str, indent=2)
            print(f"结果已保存: {filepath}")
        else:
            print(f"  ❌ {results['error']}")
