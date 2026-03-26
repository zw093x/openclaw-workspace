#!/usr/bin/env python3
"""
Fetch real-time A-share stock quotes.
Uses free public APIs (no key required).

Usage:
    python fetch_quote.py 600150
    python fetch_quote.py 600150 600482
"""

import json
import sys
import urllib.request
from datetime import datetime


def fetch_quote_sina(code: str) -> dict:
    """Fetch quote from Sina Finance API"""
    # Determine market prefix
    if code.startswith("6"):
        symbol = f"sh{code}"
    elif code.startswith(("0", "3")):
        symbol = f"sz{code}"
    else:
        symbol = code

    url = f"https://hq.sinajs.cn/list={symbol}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("gbk")
            # Format: var hq_str_sh600150="name,open,prev_close,price,high,low,..."
            parts = data.split('"')[1].split(",")
            if len(parts) < 32:
                return None

            name = parts[0]
            open_price = float(parts[1]) if parts[1] else 0
            prev_close = float(parts[2]) if parts[2] else 0
            price = float(parts[3]) if parts[3] else 0
            high = float(parts[4]) if parts[4] else 0
            low = float(parts[5]) if parts[5] else 0
            volume = float(parts[8]) if parts[8] else 0  # 手
            amount = float(parts[9]) if parts[9] else 0  # 元

            change = price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            return {
                "code": code,
                "name": name,
                "price": price,
                "open": open_price,
                "high": high,
                "low": low,
                "prev_close": prev_close,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume_lots": volume,
                "volume_yuan": amount,
                "time": parts[30] if len(parts) > 30 else "",
            }
    except Exception as e:
        return {"code": code, "error": str(e)}


def format_quote(quote: dict) -> str:
    """Format quote for display"""
    if "error" in quote:
        return f"[Error] {quote['code']}: {quote['error']}"

    sign = "+" if quote["change"] >= 0 else ""
    return (
        f"[{quote['name']}] {quote['code']}\n"
        f"价格: {quote['price']} | 涨跌: {sign}{quote['change_pct']}%\n"
        f"今开: {quote['open']} | 最高: {quote['high']} | 最低: {quote['low']}\n"
        f"昨收: {quote['prev_close']}\n"
        f"成交额: {quote['volume_yuan']/1e8:.2f}亿"
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_quote.py <code1> [code2] ...")
        sys.exit(1)

    codes = sys.argv[1:]
    results = []

    for code in codes:
        quote = fetch_quote_sina(code)
        if quote:
            results.append(quote)
            print(format_quote(quote))
            print()

    # Output JSON for programmatic use
    if "--json" in sys.argv:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
