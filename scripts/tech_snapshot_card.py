#!/usr/bin/env python3
"""
午间技术面快照
午间休盘时段自动生成技术分析卡片
包含MA排列、RSI水位、MACD信号、KDJ、布林带
"""

import sys
import json
sys.path.insert(0, "/root/.openclaw/workspace/scripts")
from stock_tech_analysis import analyze_stock, format_analysis_card
from stock_data_provider import get_stock_quotes


def generate_tech_snapshot():
    """生成午间技术分析卡片内容"""
    # 加载持仓
    with open("/root/.openclaw/workspace/config/holdings.json", "r") as f:
        config = json.load(f)
    
    codes = []
    names = {}
    costs = {}
    shares_map = {}
    
    for item in config.get("holdings", []):
        if item.get("status") == "sold" or item.get("shares", 0) == 0:
            continue
        codes.append(item["code"])
        names[item["code"]] = item["name"]
        costs[item["code"]] = item.get("cost_price", 0)
        shares_map[item["code"]] = item["shares"]
    
    # 上证指数（腾讯源 sh000001 才是上证指数，000001是平安银行）
    index_quote = None
    try:
        import ssl, urllib.request, json as _json
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = "https://qt.gtimg.cn/q=sh000001"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            raw = resp.read().decode('gbk')
        parts = raw.split('~')
        if len(parts) > 4:
            index_quote = {
                'name': parts[1],
                'price': float(parts[3]) if parts[3] else 0,
                'prev_close': float(parts[4]) if parts[4] else 0,
            }
    except:
        pass
    
    # 获取实时行情（仅持仓股）
    quotes = get_stock_quotes(codes)
    analyses = []
    for code in codes:
        name = names.get(code, code)
        analysis = analyze_stock(code, name)
        
        # 添加盈亏信息
        if code in costs and costs[code] > 0:
            analysis["cost"] = costs[code]
            analysis["shares"] = shares_map.get(code, 0)
            if "price" in analysis and "error" not in analysis:
                analysis["pnl_pct"] = (analysis["price"] - costs[code]) / costs[code] * 100
                analysis["pnl_amount"] = (analysis["price"] - costs[code]) * shares_map.get(code, 0)
        
        # 从实时行情获取涨跌幅
        if quotes and code in quotes:
            analysis["source"] = quotes[code].get("source", "?")
        
        analyses.append(analysis)
    
    # 格式化输出
    lines = []
    lines.append("📊 午间技术面快照")
    lines.append(f"时间: {datetime_str()}")
    
    # 大盘指数（从实时行情获取）
    if index_quote:
        idx_pct = (index_quote['price'] - index_quote['prev_close']) / index_quote['prev_close'] * 100 if index_quote['prev_close'] else 0
        lines.append(f"上证 {index_quote['price']:.2f} ({idx_pct:+.2f}%)")
    
    lines.append("")
    
    for a in analyses:
        if "error" in a:
            lines.append(f"❌ {a['error']}")
            continue
        
        trend_emoji = '📈' if a.get('change_pct', 0) > 0 else '📉' if a.get('change_pct', 0) < 0 else '➡️'
        
        lines.append(f"{'━'*28}")
        lines.append(f"{trend_emoji} {a['name']}({a['code']})")
        
        # 盈亏
        if 'pnl_pct' in a:
            lines.append(f"现价 {a['price']:.2f} | 涨跌 {a['change_pct']:+.2f}% | 浮亏 {a['pnl_pct']:+.1f}% ({a['pnl_amount']:+,.0f}元)")
        else:
            lines.append(f"现价 {a['price']:.2f} | 涨跌 {a['change_pct']:+.2f}%")
        
        # 均线
        ma_parts = []
        for period in [5, 10, 20, 60]:
            key = f'MA{period}'
            if a['ma'].get(key):
                indicator = '🟢' if a['price'] > a['ma'][key] else '🔴'
                ma_parts.append(f"{indicator}{key}={a['ma'][key]:.2f}")
        lines.append(f"均线: {' '.join(ma_parts)}")
        
        # 趋势
        trend = ' > '.join(a.get('ma_trend', [])[:3])
        lines.append(f"趋势: {trend or '数据不足'}")
        
        # 技术信号
        for sig in a.get('signals', []):
            lines.append(f"  • {sig}")
        
        # 5日区间
        lines.append(f"5日: {a.get('low_5d', 0):.2f} - {a.get('high_5d', 0):.2f}")
        lines.append("")
    
    # 操作建议汇总
    lines.append("━" * 28)
    lines.append("💡 操作建议")
    
    for a in analyses:
        if "error" in a or a.get('code') == '000001':
            continue
        
        suggestions = []
        
        rsi = a.get('rsi')
        if rsi:
            if rsi > 70:
                suggestions.append(f"RSI={rsi} 超买，建议减仓")
            elif rsi < 30:
                suggestions.append(f"RSI={rsi} 超卖，持有观望")
        
        macd = a.get('macd')
        if macd:
            if macd.get('signal') == '金叉':
                suggestions.append("MACD金叉，可关注加仓")
            elif macd.get('signal') == '死叉':
                suggestions.append("MACD死叉，注意风险")
        
        ma = a.get('ma', {})
        price = a.get('price', 0)
        ma20 = ma.get('MA20')
        if ma20 and price:
            if price > ma20:
                suggestions.append("站上MA20，趋势偏多")
            else:
                suggestions.append("MA20下方，趋势偏空")
        
        vol_ratio = a.get('vol_ratio')
        if vol_ratio and vol_ratio > 1.5:
            suggestions.append(f"量比{vol_ratio}，放量中")
        
        if suggestions:
            lines.append(f"  {a['name']}: {'; '.join(suggestions)}")
        else:
            lines.append(f"  {a['name']}: 持有观望")
    
    return '\n'.join(lines)


def datetime_str():
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone(timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    print(generate_tech_snapshot())
