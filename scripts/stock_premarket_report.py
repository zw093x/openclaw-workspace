#!/usr/bin/env python3
"""
A股盘前播报数据生成
主源：mootdx（通达信）- 无需代理
备源：腾讯行情（qt.gtimg.cn）
"""

import sys
import ssl
import urllib.request
from datetime import datetime

# ── mootdx 主源 ──────────────────────────────────────────
try:
    from mootdx.quotes import Quotes
    HAS_MOOTDX = True
except ImportError:
    HAS_MOOTDX = False

# ── 腾讯备源 ───────────────────────────────────────────
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ── 配置 ────────────────────────────────────────────────
CODES = ['600150', '600482', '600703', '002841']
INDICES = ['000001', '399001', '399006', '000300']
NAMES = {
    '600150': '中国船舶', '600482': '中国动力',
    '600703': '三安光电',  '002841': '视源股份',
    '000001': '上证指数',  '399001': '深证成指',
    '399006': '创业板指',  '000300': '沪深300',
}
COSTS = {'600150': 41.04, '600482': 35.079, '600703': 11.44, '002841': 33.80}


def mootdx_fetch(symbols):
    """用通达信(mootdx)拉行情"""
    client = Quotes.factory(market='std', timeout=8)
    results = {}
    for sym in symbols:
        try:
            df = client.quotes(symbol=sym)
            if df is not None and not df.empty:
                row = df.iloc[0]
                p = float(row.get('price', 0))
                pc = float(row.get('last_close', 0))
                chg = round((p - pc) / pc * 100, 2) if pc else 0
                results[sym] = {'price': p, 'prev_close': pc, 'chg_pct': chg}
                print(f"  ✅ mootdx {sym}: {p} ({chg:+.2f}%)", file=sys.stderr)
            else:
                print(f"  ❌ mootdx {sym}: 无数据", file=sys.stderr)
        except Exception as e:
            print(f"  ❌ mootdx {sym}: {e}", file=sys.stderr)
    return results


def tencent_fetch(symbols):
    """用腾讯行情拉行情（备源，无需代理）"""
    def _sym(s):
        return ('sh' if s.startswith('6') else 'sz') + s
    url = f'http://qt.gtimg.cn/q={",".join(_sym(s) for s in symbols)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        raw = r.read().decode('gbk')
    results = {}
    for line in raw.strip().split('\n'):
        parts = line.split('~')
        if len(parts) < 33:
            continue
        raw_sym = parts[0].replace('"', '').split('_')[-1].split('=')[0]
        sym = raw_sym[2:]  # 去掉 sh/sz 前缀
        try:
            price = float(parts[3]) if parts[3] else 0
            prev = float(parts[4]) if parts[4] else 0
            chg = float(parts[32]) if parts[32] else 0
            results[sym] = {'price': price, 'prev_close': prev, 'chg_pct': chg}
            print(f"  ✅ tencent {sym}: {price} ({chg:+.2f}%)", file=sys.stderr)
        except Exception as e:
            print(f"  ❌ tencent {sym}: {e}", file=sys.stderr)
    return results


def make_report(data, dt_str):
    lines = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines.append(f"📊 A股盘前播报 | {dt_str}")
    lines.append("")

    # 大盘指数
    lines.append("【大盘】")
    for idx in INDICES:
        name = NAMES[idx]
        if idx in data and data[idx]['price'] > 0:
            d = data[idx]
            e = "📈" if d['chg_pct'] >= 0 else "📉"
            lines.append(f"{e} {name} = {d['price']:.2f} ({d['chg_pct']:+.2f}%)")
        else:
            lines.append(f"⚠️ {name} 数据获取失败")
    lines.append("")

    # 持仓
    lines.append("【持仓】")
    for code in CODES:
        name = NAMES[code]
        if code in data and data[code]['price'] > 0:
            d = data[code]
            e = "📈" if d['chg_pct'] >= 0 else "📉"
            cost = COSTS[code]
            pnl = (d['price'] - cost) * 1000 if code not in ('002841',) else (d['price'] - cost) * 100
            tag = "浮盈" if pnl >= 0 else "浮亏"
            lines.append(f"{e} {name}({code}) = {d['price']:.2f} [成本{cost:.2f}] {tag}{abs(pnl):.0f}元")
        else:
            lines.append(f"⚠️ {name}({code}) 数据获取失败")
    lines.append("")

    # 简评
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

    all_syms = INDICES + CODES

    # 主源：mootdx
    data = mootdx_fetch(all_syms)

    # 备源：腾讯（填充 mootdx 拿不到的数据）
    if any(data.get(s, {}).get('price', 0) == 0 for s in all_syms):
        print("\n→ mootdx 部分失败，切换腾讯备源...", file=sys.stderr)
        tc = tencent_fetch(all_syms)
        for sym, vals in tc.items():
            if vals['price'] > 0 and data.get(sym, {}).get('price', 0) == 0:
                data[sym] = vals

    if not data or all(v.get('price', 0) == 0 for v in data.values()):
        print("❌ 所有数据源均失败", file=sys.stderr)
        sys.exit(1)

    report = make_report(data, dt_str)
    with open('/tmp/stock_premarket.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已写入 /tmp/stock_premarket.txt\n", file=sys.stderr)
    print(report)
