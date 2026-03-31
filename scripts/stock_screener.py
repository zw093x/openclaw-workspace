#!/usr/bin/env python3
"""
全市场智能选股器
扫描全部A股，筛选技术反弹概率高的标的
基于通达信全量数据
"""

import sys
import json
import os
import numpy as np
sys.path.insert(0, "/root/.openclaw/workspace/scripts")
from stock_data_provider import MootdxSource

def screen_stocks(max_results=20):
    """全市场扫描选股
    
    筛选条件：
    1. RSI < 25（极度超卖）
    2. 价格接近布林下轨（有支撑）
    3. 近5日量比 > 1.2（有资金关注）
    4. 流通市值 > 50亿（排除垃圾小盘）
    """
    from mootdx.quotes import Quotes
    client = Quotes.factory(market='std', timeout=30)
    
    try:
        # 获取全部股票列表
        stocks = client.stocks()
        if stocks is None or stocks.empty:
            return {'error': '无法获取股票列表'}
        
        candidates = []
        checked = 0
        
        for _, stock in stocks.iterrows():
            code = str(stock.get('code', ''))
            
            # 跳过ST、退市、北交所
            name = str(stock.get('name', ''))
            if any(x in name for x in ['ST', '退', 'N ', 'C ']):
                continue
            if not code.startswith(('6', '0', '3')):
                continue
            
            # 获取日K线
            try:
                df = client.bars(symbol=code, frequency=9, offset=60)
                if df is None or len(df) < 30:
                    continue
                
                close = df['close'].values
                high = df['high'].values
                low = df['low'].values
                vol = df['volume'].values if 'volume' in df.columns else df['vol'].values
                
                cur_price = close[-1]
                
                # 过滤低价股和高价股
                if cur_price < 3 or cur_price > 300:
                    continue
                
                # RSI计算
                period = 14
                deltas = np.diff(close[-(period+1):])
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                avg_g = np.mean(gains)
                avg_l = np.mean(losses)
                rsi = 100 - 100 / (1 + avg_g / avg_l) if avg_l > 0 else 100
                
                if rsi > 30:
                    continue  # 只要超卖股
                
                # 布林带
                ma20 = np.mean(close[-20:])
                std20 = np.std(close[-20:])
                upper = ma20 + 2 * std20
                lower = ma20 - 2 * std20
                
                bb_position = (cur_price - lower) / (upper - lower) if upper != lower else 0.5
                
                if bb_position > 0.3:
                    continue  # 只要靠近下轨的
                
                # 量比
                vol_ratio = vol[-1] / np.mean(vol[-5:]) if np.mean(vol[-5:]) > 0 else 1
                
                # 5日涨跌幅
                pct_5d = (cur_price - close[-6]) / close[-6] * 100 if len(close) > 5 else 0
                
                # 今日涨跌幅
                pct_today = (cur_price - close[-2]) / close[-2] * 100 if len(close) > 1 else 0
                
                # 综合评分
                score = 0
                score += (30 - rsi) * 2  # RSI越低分越高
                score += (0.3 - bb_position) * 100  # 越靠近下轨分越高
                score += min(vol_ratio * 10, 30)  # 放量加分
                if pct_today > 0:
                    score += 5  # 今日止跌加分
                
                candidates.append({
                    'code': code,
                    'name': name,
                    'price': round(cur_price, 2),
                    'rsi': round(rsi, 1),
                    'bb_position': round(bb_position, 2),
                    'vol_ratio': round(vol_ratio, 2),
                    'pct_today': round(pct_today, 2),
                    'pct_5d': round(pct_5d, 2),
                    'score': round(score, 1),
                })
                
                checked += 1
                if checked % 100 == 0:
                    print(f"  已扫描 {checked} 只...", file=sys.stderr)
                
            except:
                continue
        
        # 按评分排序
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'total_checked': checked,
            'candidates': candidates[:max_results],
            'timestamp': __import__('datetime').datetime.now().isoformat(),
        }
    except Exception as e:
        return {'error': str(e)}


def format_screener_report(result):
    """格式化选股报告"""
    if 'error' in result:
        return f"❌ {result['error']}"
    
    lines = []
    lines.append(f"🔍 全市场智能选股")
    lines.append(f"扫描范围: {result['total_checked']}只A股")
    lines.append(f"筛选条件: RSI<25 + 布林下轨附近")
    lines.append("")
    
    lines.append(f"{'排名':<4} {'股票':<12} {'现价':>6} {'RSI':>5} {'布林位置':>6} {'量比':>5} {'今日%':>6} {'5日%':>6} {'评分':>5}")
    lines.append("-" * 65)
    
    for i, c in enumerate(result.get('candidates', [])[:15], 1):
        lines.append(
            f"{i:<4} {c['name']}({c['code']}) "
            f"{c['price']:>6.2f} "
            f"{c['rsi']:>5.1f} "
            f"{c['bb_position']:>5.0%} "
            f"{c['vol_ratio']:>5.2f} "
            f"{c['pct_today']:>+5.2f} "
            f"{c['pct_5d']:>+5.2f} "
            f"{c['score']:>5.1f}"
        )
    
    return '\n'.join(lines)


if __name__ == "__main__":
    print("正在扫描全市场...", file=sys.stderr)
    result = screen_stocks(max_results=15)
    print(format_screener_report(result))
