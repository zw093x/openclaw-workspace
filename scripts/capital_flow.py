#!/usr/bin/env python3
"""
分笔成交主力资金分析器
基于通达信分笔数据，统计大单买卖、主力资金流向
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace/scripts")
from stock_data_provider import MootdxSource

def analyze_capital_flow(code, name=None, big_order_threshold=100):
    """主力资金分析
    
    Args:
        code: 股票代码
        big_order_threshold: 大单阈值（手），默认100手≈30万+
    """
    name = name or code
    
    from mootdx.quotes import Quotes
    client = Quotes.factory(market='std', timeout=10)
    
    try:
        # 获取分笔成交（最近500笔）
        df = client.transaction(symbol=code, start=0, offset=500)
        if df is None or df.empty:
            return {'error': f'{name} 分笔数据不足'}
        
        total_buy_vol = 0
        total_sell_vol = 0
        big_buy_vol = 0
        big_sell_vol = 0
        big_buy_count = 0
        big_sell_count = 0
        retail_buy_vol = 0
        retail_sell_vol = 0
        
        # 按价格方向统计
        for _, row in df.iterrows():
            vol = row.get('volume', 0)
            bs = row.get('buyorsell', -1)
            
            if bs == 0:  # 买入
                total_buy_vol += vol
                if vol >= big_order_threshold:
                    big_buy_vol += vol
                    big_buy_count += 1
                else:
                    retail_buy_vol += vol
            elif bs == 1:  # 卖出
                total_sell_vol += vol
                if vol >= big_order_threshold:
                    big_sell_vol += vol
                    big_sell_count += 1
                else:
                    retail_sell_vol += vol
        
        total_vol = total_buy_vol + total_sell_vol
        
        # 净流入
        net_flow = total_buy_vol - total_sell_vol
        big_net = big_buy_vol - big_sell_vol
        
        # 主力意图判断
        if big_buy_vol > big_sell_vol * 1.5:
            intent = "主力吸筹🟢"
        elif big_sell_vol > big_buy_vol * 1.5:
            intent = "主力出货🔴"
        elif big_buy_count > big_sell_count * 1.3:
            intent = "主力试探买入"
        else:
            intent = "主力观望"
        
        # 资金活跃度
        buy_ratio = total_buy_vol / total_vol * 100 if total_vol > 0 else 50
        
        return {
            'name': name,
            'code': code,
            'total_vol': total_vol,
            'buy_ratio': round(buy_ratio, 1),
            'net_flow': net_flow,
            'big_buy_vol': big_buy_vol,
            'big_sell_vol': big_sell_vol,
            'big_net': big_net,
            'big_buy_count': big_buy_count,
            'big_sell_count': big_sell_count,
            'retail_buy_vol': retail_buy_vol,
            'retail_sell_vol': retail_sell_vol,
            'intent': intent,
            'sample_count': len(df),
        }
    except Exception as e:
        return {'error': f'{name} 分析失败: {e}'}


def format_flow_report(analyses):
    """格式化资金流向报告"""
    lines = []
    for a in analyses:
        if 'error' in a:
            lines.append(f"❌ {a['error']}")
            continue
        
        lines.append(f"{'━'*25}")
        lines.append(f"💹 {a['name']}({a['code']}) 资金流向")
        lines.append(f"样本: {a['sample_count']}笔")
        
        buy_pct = a['buy_ratio']
        emoji = '🟢' if buy_pct > 55 else '🔴' if buy_pct < 45 else '⚪'
        lines.append(f"{emoji} 买入占比: {buy_pct}% | 卖出占比: {100-buy_pct}%")
        
        lines.append(f"📊 净流入: {a['net_flow']:+d}手")
        lines.append(f"🏦 主力买入: {a['big_buy_vol']}手({a['big_buy_count']}笔) | 卖出: {a['big_sell_vol']}手({a['big_sell_count']}笔)")
        lines.append(f"🎯 主力意图: {a['intent']}")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    codes = [('600150', '中国船舶'), ('600482', '中国动力')]
    results = []
    for code, name in codes:
        r = analyze_capital_flow(code, name)
        results.append(r)
    
    print(format_flow_report(results))
