#!/usr/bin/env python3
"""
A股盘前播报数据生成
- 主源：腾讯行情（qt.gtimg.cn）
- 持仓从 holdings.json 读取（已清仓的不显示）
"""

import sys
import ssl
import urllib.request
import json
from datetime import datetime

# ── 配置 ──────────────────────────────────────────────
HOLDINGS_FILE = '/root/.openclaw/workspace/config/holdings.json'
INDICES = ['000001', '399001', '399006', '000300']

# ── 腾讯行情 ─────────────────────────────────────────
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def load_holdings():
    """从 holdings.json 读取持仓（含已清仓状态）"""
    try:
        with open(HOLDINGS_FILE) as f:
            h = json.load(f)
        holdings = h.get('holdings', [])
        watching = h.get('watching', [])
        notes = h.get('notes', '')

        # 有效持仓（shares > 0）
        active = [x for x in holdings if x.get('shares', 0) > 0]

        # watching 代码列表
        watching_codes = [w['code'] for w in watching if w.get('code')]

        return holdings, active, watching, watching_codes, notes
    except Exception as e:
        print(f"⚠️ 读取holdings.json失败: {e}", file=sys.stderr)
        return [], [], [], [], ''


def tencent_fetch(symbols):
    """腾讯行情（无需代理）"""
    def _sym(s):
        # 指数代码：000开头 → sh（上证），399开头 → sz（深证）
        # 股票代码：6开头 → sh（上交所），0/3开头 → sz（深交所）
        if s.startswith('000') or s.startswith('399'):
            return ('sh' if s.startswith('000') else 'sz') + s
        return ('sh' if s.startswith('6') else 'sz') + s

    url = f'http://qt.gtimg.cn/q={",".join(_sym(s) for s in symbols)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            raw = r.read().decode('gbk')
    except Exception as e:
        print(f"❌ 腾讯行情请求失败: {e}", file=sys.stderr)
        return {}

    results = {}
    for line in raw.strip().split('\n'):
        parts = line.split('~')
        if len(parts) < 33:
            continue
        raw_sym = parts[0].replace('"', '').split('_')[-1].split('=')[0]
        sym = raw_sym[2:]  # 去掉 sh/sz 前缀
        try:
            price = float(parts[3]) if parts[3] else 0
            prev  = float(parts[4]) if parts[4] else 0
            chg   = float(parts[32]) if parts[32] else 0
            results[sym] = {'price': price, 'prev_close': prev, 'chg_pct': chg}
        except Exception:
            continue
    return results


def make_report(data, dt_str, active, watching, watching_codes, notes):
    lines = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines.append(f"📊 A股盘前播报 | {dt_str}")
    lines.append("")

    # ── 大盘指数 ─────────────────────────────────
    lines.append("【大盘】")
    idx_names = {
        '000001': '上证指数', '399001': '深证成指',
        '399006': '创业板指', '000300': '沪深300',
    }
    for idx in INDICES:
        name = idx_names.get(idx, idx)
        if idx in data and data[idx]['price'] > 0:
            d = data[idx]
            e = "📈" if d['chg_pct'] >= 0 else "📉"
            lines.append(f"{e} {name} = {d['price']:.2f} ({d['chg_pct']:+.2f}%)")
        else:
            lines.append(f"⚠️ {name} 数据获取失败")
    lines.append("")

    # ── 有效持仓 ───────────────────────────────
    if active:
        lines.append("【持仓】")
        # code → price 映射
        price_map = {code: data[code] for code in data
                     if code in [x['code'] for x in active]}
        for h in active:
            code = h['code']
            name = h.get('name', code)
            shares = h.get('shares', 0)
            cost   = h.get('cost_price', 0)
            if code in data and data[code]['price'] > 0:
                d = data[code]
                e = "📈" if d['chg_pct'] >= 0 else "📉"
                unrealized = (d['price'] - cost) * shares if cost else 0
                u_str = f"({unrealized:+,.0f})" if cost else ""
                lines.append(f"{e} {name}({code}) × {shares}股 "
                             f"现价{d['price']:.2f} ({d['chg_pct']:+.2f}%) {u_str}")
            else:
                lines.append(f"⚠️ {name}({code}) 数据获取失败")
        lines.append("")
    else:
        lines.append("【持仓】✅ 已清仓")
        lines.append("")

    # ── Watching ────────────────────────────────
    if watching_codes:
        # 过滤掉已经在持仓里的
        held_codes = {h['code'] for h in active}
        watch_display = [c for c in watching_codes if c not in held_codes]
        if watch_display:
            lines.append("【观察】")
            for code in watch_display:
                # 找name
                name = code
                for w in watching:
                    if w.get('code') == code:
                        name = w.get('name', code)
                        break
                if code in data and data[code]['price'] > 0:
                    d = data[code]
                    e = "📈" if d['chg_pct'] >= 0 else "📉"
                    lines.append(f"{e} {name}({code}) = {d['price']:.2f} ({d['chg_pct']:+.2f}%)")
                else:
                    lines.append(f"⚠️ {name}({code}) 数据获取失败")
            lines.append("")

    # ── 市场简评 ────────────────────────────────
    lines.append("【参考】")
    if '000001' in data and data['000001']['price'] > 0:
        c = data['000001']['chg_pct']
        if c > 1.5:
            mood = "市场情绪偏暖，注意获利盘压力"
        elif c > 0:
            mood = "大盘小幅高开，谨慎做多"
        elif c > -1.5:
            mood = "大盘小幅低开，震荡整理"
        else:
            mood = "大盘低开，关注外围扰动"
        lines.append(f"上证 {c:+.2f}% | {mood}")
    lines.append("")
    lines.append(f"⏰ {now} (数据仅供参考，不构成投资建议)")

    return "\n".join(lines)


if __name__ == '__main__':
    dt_str = datetime.now().strftime('%Y-%m-%d')
    print("=== A股盘前数据 ===", file=sys.stderr)

    # 读持仓
    holdings, active, watching, watching_codes, notes = load_holdings()
    print(f"有效持仓: {[x['code'] for x in active]}", file=sys.stderr)
    print(f"观察列表: {watching_codes}", file=sys.stderr)

    # 所有需要拉行情的代码
    all_syms = INDICES + [h['code'] for h in holdings] + watching_codes

    # 去重
    all_syms = list(dict.fromkeys(all_syms))

    # 拉行情
    data = tencent_fetch(all_syms)
    print(f"成功获取: {list(data.keys())}", file=sys.stderr)

    if not data:
        print("❌ 数据获取失败", file=sys.stderr)
        sys.exit(1)

    # 生成报告
    report = make_report(data, dt_str, active, watching, watching_codes, notes)

    with open('/tmp/stock_premarket.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已写入 /tmp/stock_premarket.txt\n", file=sys.stderr)
    print(report)
