#!/usr/bin/env python3
"""
交易决策日志管理器
每次操作自动记录信号→操作→结果→复盘
"""

import json
import os
from datetime import datetime, timezone, timedelta

JOURNAL_FILE = "/root/.openclaw/workspace/memory/trade-journal.json"
JOURNAL_MD = "/root/.openclaw/workspace/memory/trade-journal.md"

def load_journal():
    """加载交易日志"""
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, 'r') as f:
            return json.load(f)
    return {'trades': [], 'last_id': 0}

def save_journal(journal):
    """保存交易日志"""
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(journal, f, ensure_ascii=False, indent=2)
    # 同步更新MD文件
    sync_to_md(journal)

def add_trade(code, name, action, price, shares, signals, reason, notes=""):
    """添加交易记录
    
    Args:
        code: 股票代码
        name: 股票名称
        action: 'buy'/'sell'
        price: 成交价格
        shares: 成交数量
        signals: 触发信号列表
        reason: 操作原因
        notes: 备注
    """
    journal = load_journal()
    journal['last_id'] += 1
    
    now = datetime.now(timezone(timedelta(hours=8)))
    
    trade = {
        'id': journal['last_id'],
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M'),
        'code': code,
        'name': name,
        'action': action,
        'price': price,
        'shares': shares,
        'amount': round(price * shares, 2),
        'signals': signals,
        'reason': reason,
        'notes': notes,
        'result': None,  # 后续更新
        'review': None,  # 复盘
    }
    
    journal['trades'].append(trade)
    save_journal(journal)
    
    return trade

def update_result(trade_id, result_pct, result_amount, review=""):
    """更新交易结果（T+5或平仓后）"""
    journal = load_journal()
    
    for trade in journal['trades']:
        if trade['id'] == trade_id:
            trade['result'] = {
                'pct': result_pct,
                'amount': result_amount,
                'review_date': datetime.now().strftime('%Y-%m-%d'),
            }
            trade['review'] = review
            break
    
    save_journal(journal)

def get_stats():
    """统计交易胜率"""
    journal = load_journal()
    completed = [t for t in journal['trades'] if t.get('result')]
    
    if not completed:
        return {'total': len(journal['trades']), 'completed': 0}
    
    wins = [t for t in completed if t['result']['pct'] > 0]
    
    return {
        'total': len(journal['trades']),
        'completed': len(completed),
        'win_rate': round(len(wins) / len(completed) * 100, 1) if completed else 0,
        'avg_return': round(sum(t['result']['pct'] for t in completed) / len(completed), 2),
        'total_pnl': round(sum(t['result']['amount'] for t in completed), 2),
    }

def sync_to_md(journal):
    """同步到Markdown文件"""
    lines = []
    lines.append("# 交易决策日志\n")
    lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    stats = get_stats()
    if stats['completed'] > 0:
        lines.append(f"## 统计")
        lines.append(f"- 总交易: {stats['total']} | 已复盘: {stats['completed']}")
        lines.append(f"- 胜率: {stats['win_rate']}% | 平均收益: {stats['avg_return']:+.2f}%")
        lines.append("")
    
    lines.append("## 交易记录\n")
    for trade in reversed(journal['trades'][-20:]):  # 最近20条
        action_emoji = '🟢买入' if trade['action'] == 'buy' else '🔴卖出'
        lines.append(f"### {trade['date']} {trade['time']} - {trade['name']}({trade['code']})")
        lines.append(f"- **{action_emoji}**: {trade['price']:.2f} × {trade['shares']}股 = {trade['amount']:,.0f}元")
        lines.append(f"- 触发信号: {', '.join(trade.get('signals', []))}")
        lines.append(f"- 原因: {trade['reason']}")
        if trade.get('result'):
            lines.append(f"- 结果: {trade['result']['pct']:+.2f}% ({trade['result']['amount']:+,.0f}元)")
        if trade.get('review'):
            lines.append(f"- 复盘: {trade['review']}")
        lines.append("")
    
    with open(JOURNAL_MD, 'w') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    # 测试：添加一条模拟交易
    trade = add_trade(
        code='600150',
        name='中国船舶',
        action='sell',
        price=31.50,
        shares=500,
        signals=['RSI超买', '触及减仓位'],
        reason='RSI=72超买 + 价格进入31.50-32.00减仓区间',
    )
    print(f"已添加交易记录: ID={trade['id']}")
    
    stats = get_stats()
    print(f"统计: 总{stats['total']}笔, 已复盘{stats['completed']}笔")
