#!/usr/bin/env python3
"""
船舶板块横向对比分析
对比船舶板块内各股票强弱
"""

import sys
import numpy as np
sys.path.insert(0, "/root/.openclaw/workspace/scripts")
from stock_data_provider import get_stock_quotes, get_kline
from stock_tech_analysis import analyze_stock

# 船舶板块主要标的
SECTOR_STOCKS = [
    ('600150', '中国船舶'),
    ('600482', '中国动力'),
    ('601989', '中国重工'),
    ('600685', '中船防务'),
    ('600072', '中船科技'),
    ('300003', '乐普医疗'),  # 对比非船舶股
]

SECTOR_INDEX = 'sh000030'  # 沪深300作为基准


def compare_sector(codes=None):
    """板块内横向对比"""
    if codes is None:
        codes = SECTOR_STOCKS
    
    results = []
    
    for code, name in codes:
        analysis = analyze_stock(code, name)
        if 'error' in analysis:
            continue
        
        # 获取30日K线计算相对强弱
        df = get_kline(code, frequency=9, offset=30)
        if df is not None and len(df) >= 20:
            close = df['close'].values
            pct_20d = (close[-1] - close[0]) / close[0] * 100
            pct_5d = (close[-1] - close[-6]) / close[-6] * 100 if len(close) > 5 else 0
            vol_avg = np.mean(df['volume'].values[-5:]) if 'volume' in df.columns else np.mean(df['vol'].values[-5:])
            vol_avg_prev = np.mean(df['volume'].values[-10:-5]) if 'volume' in df.columns else np.mean(df['vol'].values[-10:-5])
            vol_trend = vol_avg / vol_avg_prev if vol_avg_prev > 0 else 1
        else:
            pct_20d = 0
            pct_5d = 0
            vol_trend = 1
        
        results.append({
            'code': code,
            'name': name,
            'price': analysis['price'],
            'change_pct': analysis.get('change_pct', 0),
            'rsi': analysis.get('rsi'),
            'macd_signal': analysis.get('macd', {}).get('signal') if analysis.get('macd') else None,
            'ma_trend': ' > '.join(analysis.get('ma_trend', [])[:2]),
            'pct_5d': round(pct_5d, 2),
            'pct_20d': round(pct_20d, 2),
            'vol_trend': round(vol_trend, 2),
        })
    
    # 按20日涨幅排序
    results.sort(key=lambda x: x['pct_20d'], reverse=True)
    
    return results


def format_sector_report(results):
    """格式化板块对比报告"""
    lines = []
    lines.append("📊 船舶板块横向对比")
    lines.append("")
    lines.append(f"{'排名':<4} {'股票':<12} {'现价':>6} {'今日%':>6} {'5日%':>7} {'20日%':>7} {'RSI':>5} {'MACD':>6} {'趋势':>12}")
    lines.append("-" * 75)
    
    for i, r in enumerate(results, 1):
        rsi_str = f"{r['rsi']:.0f}" if r['rsi'] else "?"
        macd_str = r.get('macd_signal') or '?'
        trend_str = r.get('ma_trend', '?')[:12]
        lines.append(
            f"{i:<4} {r['name']}({r['code']}) "
            f"{r['price']:>6.2f} "
            f"{r['change_pct']:>+5.2f} "
            f"{r['pct_5d']:>+6.2f} "
            f"{r['pct_20d']:>+6.2f} "
            f"{rsi_str:>5} "
            f"{macd_str:>6} "
            f"{trend_str:>12}"
        )
    
    # 板块强弱判断
    if results:
        avg_5d = np.mean([r['pct_5d'] for r in results])
        avg_20d = np.mean([r['pct_20d'] for r in results])
        lines.append("")
        lines.append(f"板块均值: 5日 {avg_5d:+.2f}% | 20日 {avg_20d:+.2f}%")
        
        # 相对强弱
        strongest = results[0]
        weakest = results[-1]
        lines.append(f"最强: {strongest['name']}({strongest['pct_20d']:+.2f}%)")
        lines.append(f"最弱: {weakest['name']}({weakest['pct_20d']:+.2f}%)")
        
        if strongest['pct_20d'] - weakest['pct_20d'] > 5:
            lines.append("💡 板块内部分化严重，优先减仓弱股")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    results = compare_sector()
    print(format_sector_report(results))
