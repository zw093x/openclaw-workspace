#!/usr/bin/env python3
"""
盘中实时股票监控 - 事件驱动版
触发条件才推送，无预警静默
"""
import json
import sys
import os
import urllib.request
import ssl
from datetime import datetime, timedelta

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HOLDINGS_FILE = "/root/.openclaw/workspace/config/holdings.json"
STATE_FILE = "/root/.openclaw/workspace/memory/stock-alert-state.json"
ALERT_COOLDOWN = 60  # 分钟

def load_holdings():
    with open(HOLDINGS_FILE) as f:
        data = json.load(f)
    holdings = {}
    for item in data.get("holdings", []):
        if item.get("status") == "sold" or item.get("shares", 0) == 0:
            continue
        code = f"{item['market']}{item['code']}"
        holdings[code] = {
            "name": item["name"],
            "cost": item["cost_price"],
            "shares": item["shares"],
            "reduce_levels": item.get("reduce_levels", []),
            "stop_loss": item.get("stop_loss", 0),
            "watch_mode": False,
        }
    for item in data.get("watching", []):
        code = f"{item['market']}{item['code']}"
        holdings[code] = {
            "name": item["name"],
            "cost": item.get("cost", 0),
            "shares": item.get("shares", 0),
            "stop_loss": item.get("stop_loss", 0),
            "watch_mode": True,
        }
    return holdings

def fetch_realtime(codes):
    if not codes:
        return {}
    secids = ",".join([f"0.{c[1:]}" if c.startswith("0") else f"1.{c}" for c in codes])
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f12,f14,f2,f3,f4,f5,f6&secids={secids}&ut=fa5fd1943c7b386f172d6893dbfba10b"
    try:
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        result = {}
        for item in data["data"]["diff"]:
            code = item["f12"]
            price = item["f2"] / 100
            chg_pct = item["f3"] / 100
            vol_ratio = item["f5"]
            result[code] = {
                "price": price,
                "chg_pct": chg_pct,
                "vol_ratio": vol_ratio,
            }
        return result
    except Exception as e:
        return {"error": str(e)}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"last_alerts": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_cooldown(key, state):
    last = state["last_alerts"].get(key)
    if last:
        last_time = datetime.fromisoformat(last)
        if datetime.now() - last_time < timedelta(minutes=ALERT_COOLDOWN):
            return False
    return True

def trigger_alert(key, state):
    state["last_alerts"][key] = datetime.now().isoformat()

def is_trading_time():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.hour * 100 + now.minute
    return 900 <= t <= 1130 or 1300 <= t <= 1500

def main():
    if not is_trading_time():
        print("NON_TRADING")
        sys.exit(0)

    holdings = load_holdings()
    if not holdings:
        print("NO_HOLDINGS")
        sys.exit(0)

    codes = list(holdings.keys())
    quotes = fetch_realtime(codes)

    if "error" in quotes:
        print(f"ERROR:{quotes['error']}")
        sys.exit(1)

    state = load_state()
    alerts = []
    summary_lines = []

    for code, q in quotes.items():
        pos = holdings[code]
        price = q["price"]
        chg_pct = q["chg_pct"]
        vol_ratio = q.get("vol_ratio", 1)
        cost = pos["cost"]
        pnl_pct = (price / cost - 1) * 100
        pnl_amount = (price - cost) * pos["shares"]
        emoji = "🔴" if chg_pct < 0 else "🟢"

        # 1. 涨跌幅预警
        for level, threshold, label in [(5.0, "S2紧急"), (3.0, "S1警告")]:
            if abs(chg_pct) >= level:
                key = f"{code}_chg_{label}"
                if check_cooldown(key, state):
                    alerts.append(f"🚨 {pos['name']}({code}) 涨跌 {chg_pct:+.2f}% [{label}] | 现价{price} | 成本{cost}")
                    trigger_alert(key, state)

        # 2. 跌破止损
        if pos["stop_loss"] > 0 and price <= pos["stop_loss"]:
            key = f"{code}_stoploss"
            if check_cooldown(key, state):
                alerts.append(f"🚨 {pos['name']}({code}) 触发止损！现价{price} <= 止损{pos['stop_loss']}")
                trigger_alert(key, state)

        # 3. 触及减仓价位
        for level in pos.get("reduce_levels", []):
            rng = level["range"]
            if rng[0] <= price <= rng[1]:
                key = f"{code}_reduce_{level['label']}"
                if check_cooldown(key, state):
                    alerts.append(f"⚠️ {pos['name']}({code}) 触及减仓价位 {level['label']} [{price}] | 成本{cost} | 浮亏{pnl_pct:+.1f}%")
                    trigger_alert(key, state)

        # 4. 成交量异常
        if vol_ratio >= 1.5:
            key = f"{code}_volume"
            if check_cooldown(key, state):
                alerts.append(f"📊 {pos['name']}({code}) 成交量放大 {vol_ratio:.1f}倍 | 均量触发")

        # 5. 技术破位（收盘<布林下轨）
        bl_bottom = cost * 0.85  # 简化：布林下轨估算
        if price < bl_bottom and not pos.get("watch_mode"):
            key = f"{code}_boll"
            if check_cooldown(key, state):
                alerts.append(f"⚠️ {pos['name']}({code}) 技术破位 | 现价{price} < 布林下轨估算{bl_bottom:.2f}")
                trigger_alert(key, state)

        # 行情摘要（总有）
        summary_lines.append(f"{emoji} {pos['name']} {price} ({chg_pct:+.2f}%) 浮亏{pnl_pct:+.1f}%")

    save_state(state)

    if alerts:
        output = {
            "type": "ALERT",
            "time": datetime.now().strftime("%H:%M"),
            "alerts": alerts,
            "summary": summary_lines,
        }
        print("HAS_ALERT")
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("NO_ALERT")
        for line in summary_lines:
            print(line)

if __name__ == "__main__":
    main()
