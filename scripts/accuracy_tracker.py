#!/usr/bin/env python3
"""
分析准确率追踪器
记录每次预测 vs 实际结果，量化学习效果
"""

import json
import os
from datetime import datetime, timezone, timedelta

ACCURACY_FILE = "/root/.openclaw/workspace/memory/analysis-accuracy.json"
ACCURACY_MD = "/root/.openclaw/workspace/memory/analysis-accuracy.md"

def load_accuracy():
    if os.path.exists(ACCURACY_FILE):
        with open(ACCURACY_FILE, 'r') as f:
            return json.load(f)
    return {'predictions': [], 'last_id': 0}

def save_accuracy(data):
    with open(ACCURACY_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    sync_to_md(data)

def add_prediction(code, name, direction, target_price, timeframe, signals, confidence="medium"):
    """记录预测
    
    Args:
        direction: 'up'/'down'/'sideways'
        target_price: 目标价
        timeframe: '5d'/'10d'/'20d'
        signals: 触发信号
        confidence: 'high'/'medium'/'low'
    """
    data = load_accuracy()
    data['last_id'] += 1
    
    now = datetime.now(timezone(timedelta(hours=8)))
    
    pred = {
        'id': data['last_id'],
        'date': now.strftime('%Y-%m-%d'),
        'code': code,
        'name': name,
        'direction': direction,
        'target_price': target_price,
        'timeframe': timeframe,
        'signals': signals,
        'confidence': confidence,
        'result': None,
    }
    
    data['predictions'].append(pred)
    save_accuracy(data)
    return pred

def check_results():
    """检查未验证的预测，与实际行情对比"""
    import sys
    sys.path.insert(0, "/root/.openclaw/workspace/scripts")
    from stock_data_provider import get_stock_quotes
    
    data = load_accuracy()
    updated = 0
    
    for pred in data['predictions']:
        if pred.get('result') is not None:
            continue
        
        pred_date = datetime.strptime(pred['date'], '%Y-%m-%d')
        timeframe_days = {'5d': 5, '10d': 10, '20d': 20}
        days_needed = timeframe_days.get(pred['timeframe'], 5)
        
        now = datetime.now()
        if (now - pred_date).days < days_needed:
            continue  # 还没到期
        
        # 获取当前价格
        quotes = get_stock_quotes([pred['code']])
        if quotes and pred['code'] in quotes:
            current_price = quotes[pred['code']]['price']
            entry_price = pred['target_price']
            
            actual_direction = 'up' if current_price > entry_price * 1.01 else (
                'down' if current_price < entry_price * 0.99 else 'sideways'
            )
            
            correct = (actual_direction == pred['direction'])
            pct_change = (current_price - entry_price) / entry_price * 100
            
            pred['result'] = {
                'actual_price': current_price,
                'actual_direction': actual_direction,
                'pct_change': round(pct_change, 2),
                'correct': correct,
                'check_date': now.strftime('%Y-%m-%d'),
            }
            updated += 1
    
    if updated > 0:
        save_accuracy(data)
    
    return updated

def get_accuracy_stats():
    """统计准确率"""
    data = load_accuracy()
    completed = [p for p in data['predictions'] if p.get('result')]
    
    if not completed:
        return {'total': len(data['predictions']), 'verified': 0}
    
    correct = [p for p in completed if p['result']['correct']]
    
    # 按方向统计
    up_preds = [p for p in completed if p['direction'] == 'up']
    down_preds = [p for p in completed if p['direction'] == 'down']
    
    # 按信号类型统计
    signal_accuracy = {}
    for p in completed:
        for sig in p.get('signals', []):
            if sig not in signal_accuracy:
                signal_accuracy[sig] = {'total': 0, 'correct': 0}
            signal_accuracy[sig]['total'] += 1
            if p['result']['correct']:
                signal_accuracy[sig]['correct'] += 1
    
    return {
        'total': len(data['predictions']),
        'verified': len(completed),
        'overall_accuracy': round(len(correct) / len(completed) * 100, 1),
        'up_accuracy': round(len([p for p in up_preds if p['result']['correct']]) / len(up_preds) * 100, 1) if up_preds else 0,
        'down_accuracy': round(len([p for p in down_preds if p['result']['correct']]) / len(down_preds) * 100, 1) if down_preds else 0,
        'signal_accuracy': {k: round(v['correct']/v['total']*100, 1) for k, v in signal_accuracy.items() if v['total'] >= 2},
    }

def sync_to_md(data):
    """同步到Markdown"""
    stats = get_accuracy_stats()
    completed = [p for p in data['predictions'] if p.get('result')]
    
    lines = []
    lines.append("# 分析准确率追踪\n")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    if stats['verified'] > 0:
        lines.append(f"## 总体统计")
        lines.append(f"- 总预测: {stats['total']} | 已验证: {stats['verified']}")
        lines.append(f"- **整体准确率: {stats['overall_accuracy']}%**")
        lines.append(f"- 看多准确率: {stats['up_accuracy']}% | 看空准确率: {stats['down_accuracy']}%")
        if stats['signal_accuracy']:
            lines.append(f"- 信号准确率:")
            for sig, acc in stats['signal_accuracy'].items():
                lines.append(f"  - {sig}: {acc}%")
        lines.append("")
    
    lines.append("## 最近预测记录\n")
    for p in reversed(data['predictions'][-20:]):
        status = '✅' if (p.get('result') or {}).get('correct') else ('❌' if p.get('result') else '⏳')
        lines.append(f"- {status} {p['date']} {p['name']}({p['code']}) {'看涨' if p['direction']=='up' else '看跌'} @ {p['target_price']:.2f} ({p['timeframe']})")
        if p.get('result'):
            lines.append(f"  实际: {p['result']['actual_price']:.2f} ({p['result']['pct_change']:+.2f}%)")
    
    with open(ACCURACY_MD, 'w') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    # 测试
    pred = add_prediction(
        code='600150',
        name='中国船舶',
        direction='up',
        target_price=31.07,
        timeframe='5d',
        signals=['RSI超卖', 'KDJ低位金叉'],
        confidence='medium',
    )
    print(f"已记录预测: ID={pred['id']}")
    
    updated = check_results()
    print(f"更新验证: {updated}条")
    
    stats = get_accuracy_stats()
    print(f"准确率统计: {stats}")
