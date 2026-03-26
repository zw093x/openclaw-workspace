#!/usr/bin/env python3
"""
盘中实时监控脚本
每15分钟运行一次（交易时段 09:30-15:00）
检测涨跌幅异动、关键技术位突破、成交量异常

防消息轰炸：同一只股票同一类型预警，1小时内不重复推送
"""
import subprocess
import json
import sys
import os
from datetime import datetime, timedelta

# ====== 配置 ======
# 持仓股票
HOLDINGS = {
    "sh600150": {
        "name": "中国船舶",
        "cost": 38.696,
        "shares": 3000,
        "reduce_levels": [
            {"range": (32.50, 33.00), "sell": 250, "label": "第一减仓"},
            {"range": (34.00, 34.50), "sell": 250, "label": "第二减仓"},
        ],
        "stop_loss": 29.00,
        "key_levels": {
            "MA5": 32.15, "MA10": 33.46, "MA20": 35.47,
            "support": 30.83, "resistance": 32.15,
        }
    },
    "sh600482": {
        "name": "中国动力",
        "cost": 34.389,
        "shares": 3000,
        "reduce_levels": [
            {"range": (32.50, 33.00), "sell": 250, "label": "第一减仓"},
            {"range": (33.50, 34.00), "sell": 250, "label": "第二减仓"},
        ],
        "stop_loss": 28.50,
        "key_levels": {
            "MA5": 30.25, "MA10": 31.24, "MA20": 32.72,
            "support": 29.10, "resistance": 32.72,
        }
    },
    "sh603656": {
        "name": "泰禾智能",
        "cost": 22.000,
        "shares": 800,
        "reduce_levels": [
            {"range": (22.50, 22.70), "sell": 400, "label": "第一减仓"},
            {"range": (23.00, 99.00), "sell": 400, "label": "清仓"},
        ],
        "stop_loss": 20.00,
        "key_levels": {
            "MA5": 21.34, "MA10": 21.73, "MA20": 22.09,
            "support": 20.46, "resistance": 22.09,
        }
    },
}

# 视源股份（朋友账户）
FRIEND = {
    "sz002841": {
        "name": "视源股份",
        "cost": 33.80,
        "shares": 500,
        "stop_loss": 32.11,
        "stop_loss_hard": 30.42,
        "take_profit": [
            {"range": (34.50, 35.00), "sell": 200, "label": "第一止盈"},
            {"range": (35.00, 35.60), "sell": 300, "label": "第二止盈"},
            {"range": (36.00, 99.00), "sell": 500, "label": "清仓"},
        ],
    },
}

# 异动阈值
ALERT_S1 = 3.0   # ±3%警告
ALERT_S2 = 5.0   # ±5%紧急
VOLUME_RATIO = 1.5  # 成交量>1.5倍均量触发
COOLDOWN_MINUTES = 60  # 同类型预警冷却时间（分钟）
STATE_FILE = "/root/.openclaw/workspace/memory/alert-cooldown.json"

# ====== 工具函数 ======
def load_cooldown_state():
    """加载冷却状态"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_cooldown_state(state):
    """保存冷却状态"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except:
        pass

def filter_alerts_by_cooldown(alerts):
    """根据冷却时间过滤重复预警"""
    state = load_cooldown_state()
    now = datetime.now()
    filtered = []
    
    for alert in alerts:
        # 用预警文本的前30字作为key
        key = alert[:50]
        last_sent = state.get(key)
        
        if last_sent:
            last_time = datetime.fromisoformat(last_sent)
            if now - last_time < timedelta(minutes=COOLDOWN_MINUTES):
                continue  # 冷却期内，跳过
        
        filtered.append(alert)
        state[key] = now.isoformat()
    
    save_cooldown_state(state)
    return filtered

def fetch_quotes(codes):
    """获取实时行情"""
    url = f"https://qt.gtimg.cn/q={','.join(codes)}"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", url],
            capture_output=True, timeout=10
        )
        raw = result.stdout.decode("gbk", errors="replace")
        quotes = {}
        for line in raw.strip().split(";"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            parts = line.split("=", 1)
            var_name = parts[0].strip()
            code = var_name.replace("v_", "")
            data_str = parts[1].strip().strip('"')
            fields = data_str.split("~")
            if len(fields) > 40:
                quotes[code] = {
                    "name": fields[1],
                    "price": float(fields[3]) if fields[3] else 0,
                    "prev_close": float(fields[4]) if fields[4] else 0,
                    "open": float(fields[5]) if fields[5] else 0,
                    "volume": int(fields[6]) if fields[6] else 0,
                    "high": float(fields[33]) if fields[33] else 0,
                    "low": float(fields[34]) if fields[34] else 0,
                    "change_pct": float(fields[32]) if fields[32] else 0,
                    "amount": float(fields[37]) if fields[37] else 0,
                    "time": fields[30] if len(fields) > 30 else "",
                }
        return quotes
    except Exception as e:
        return {"error": str(e)}

def check_alerts(quotes):
    """检查所有预警条件"""
    alerts = []
    
    all_stocks = {**HOLDINGS, **FRIEND}
    
    for code, config in all_stocks.items():
        if code not in quotes:
            continue
        q = quotes[code]
        name = config["name"]
        price = q["price"]
        change = q["change_pct"]
        
        if price == 0:
            continue
        
        # 1. 涨跌幅异动
        if abs(change) >= ALERT_S2:
            severity = "🚨紧急"
            alerts.append(f"{severity} {name} 涨跌幅 {change:+.2f}%（超±{ALERT_S2}%阈值）")
        elif abs(change) >= ALERT_S1:
            severity = "⚠️警告"
            alerts.append(f"{severity} {name} 涨跌幅 {change:+.2f}%（超±{ALERT_S1}%阈值）")
        
        # 2. 减仓位触发
        if "reduce_levels" in config:
            for level in config["reduce_levels"]:
                lo, hi = level["range"]
                if lo <= price <= hi:
                    alerts.append(f"💰减仓触发 {name} 现价{price:.2f} 进入{level['label']}区间[{lo}-{hi}]，建议卖出{level['sell']}股")
        
        # 3. 止盈位触发（朋友账户）
        if "take_profit" in config:
            for level in config["take_profit"]:
                lo, hi = level["range"]
                if lo <= price <= hi:
                    alerts.append(f"💰止盈触发 {name} 现价{price:.2f} 进入{level['label']}区间[{lo}-{hi}]，建议卖出{level['sell']}股")
        
        # 4. 止损位
        if "stop_loss" in config and price <= config["stop_loss"]:
            pct = (price - config["cost"]) / config["cost"] * 100
            alerts.append(f"🛑止损警报 {name} 现价{price:.2f} 触及止损位{config['stop_loss']}，浮亏{pct:.1f}%")
        
        if "stop_loss_hard" in config and price <= config["stop_loss_hard"]:
            alerts.append(f"🛑硬止损 {name} 现价{price:.2f} 跌破硬止损{config['stop_loss_hard']}，建议清仓")
        
        # 5. 关键技术位突破
        if "key_levels" in config:
            levels = config["key_levels"]
            for label, level_price in levels.items():
                if "MA" in label or label in ["support", "resistance"]:
                    # 向上突破
                    if q["high"] >= level_price and q["open"] < level_price:
                        direction = "突破" if change > 0 else "触及"
                        alerts.append(f"📊技术信号 {name} 盘中{direction}{label}({level_price:.2f})，当前{price:.2f}")
                    # 向下跌破
                    elif q["low"] <= level_price and q["open"] > level_price:
                        alerts.append(f"📊技术信号 {name} 盘中跌破{label}({level_price:.2f})，当前{price:.2f}")
        
        # 6. 盈亏状态
        pnl_pct = (price - config["cost"]) / config["cost"] * 100
        pnl_amount = (price - config["cost"]) * config["shares"]
        
        # 大幅亏损警告
        if pnl_pct <= -10:
            alerts.append(f"📉深度套牢 {name} 浮亏{pnl_pct:.1f}%（{pnl_amount:+.0f}元）")
    
    return alerts

def generate_status(quotes):
    """生成持仓状态摘要"""
    lines = ["📊 **持仓盘中快照**\n"]
    total_pnl = 0
    
    all_stocks = {**HOLDINGS, **FRIEND}
    for code, config in all_stocks.items():
        if code not in quotes:
            continue
        q = quotes[code]
        price = q["price"]
        if price == 0:
            continue
        
        change = q["change_pct"]
        pnl_pct = (price - config["cost"]) / config["cost"] * 100
        pnl_amount = (price - config["cost"]) * config["shares"]
        total_pnl += pnl_amount
        
        emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"
        lines.append(f"{emoji} **{config['name']}** {price:.2f} ({change:+.2f}%) | 成本{config['cost']:.3f} | 浮亏{pnl_pct:+.1f}% ({pnl_amount:+.0f}元)")
    
    lines.append(f"\n💰 **总浮亏: {total_pnl:+.0f}元**")
    return "\n".join(lines)

def is_trading_time():
    """判断是否在交易时段（含盘前竞价）"""
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:
        return False
    time_int = now.hour * 100 + now.minute
    return (915 <= time_int <= 1500)  # 含盘前竞价9:15-9:25

# ====== 主逻辑 ======
if __name__ == "__main__":
    if not is_trading_time():
        print("非交易时段，跳过")
        sys.exit(0)
    
    codes = list(HOLDINGS.keys()) + list(FRIEND.keys()) + ["sh000001"]
    quotes = fetch_quotes(codes)
    
    if "error" in quotes:
        print(f"行情获取失败: {quotes['error']}")
        sys.exit(1)
    
    # 输出状态
    print(generate_status(quotes))
    
    # 检查预警
    alerts = check_alerts(quotes)
    if alerts:
        # 过滤冷却期内的重复预警
        alerts = filter_alerts_by_cooldown(alerts)
        if alerts:
            print("\n🔔 **预警信号:**")
            for a in alerts:
                print(f"  {a}")
        else:
            print("\n✅ 暂无新预警（已有预警在冷却期内）")
    else:
        print("\n✅ 暂无预警信号")
    
    # 输出大盘
    if "sh000001" in quotes:
        idx = quotes["sh000001"]
        print(f"\n📈 上证指数 {idx['price']:.2f} ({idx['change_pct']:+.2f}%)")
