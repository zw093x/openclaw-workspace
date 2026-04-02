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
HOLDINGS_FILE = "/root/.openclaw/workspace/config/holdings.json"

def load_holdings():
    """从 holdings.json 加载持仓配置"""
    try:
        with open(HOLDINGS_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ 无法读取 {HOLDINGS_FILE}: {e}")
        return {}, {}

    holdings = {}
    friends = {}

    for item in data.get("holdings", []):
        if item.get("status") == "sold" or item.get("shares", 0) == 0:
            continue  # 跳过已清仓
        code = f"{item['market']}{item['code']}"
        holdings[code] = {
            "name": item["name"],
            "cost": item["cost_price"],
            "shares": item["shares"],
            "reduce_levels": [
                {"range": tuple(r["range"]), "sell": r["sell"], "label": r["label"]}
                for r in item.get("reduce_levels", [])
            ],
            "stop_loss": item.get("stop_loss", 0),
        }

    for item in data.get("watching", []):
        code = f"{item['market']}{item['code']}"
        friends[code] = {
            "name": item["name"],
            "cost": item.get("cost", 0),
            "shares": item.get("shares", 0),
            "stop_loss": item.get("stop_loss", 0),
            "is_watching": True,  # 标记为关注股，即使shares=0也监控
        }

    return holdings, friends

HOLDINGS, FRIEND = load_holdings()

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
    """获取实时行情 - 使用统一数据源（通达信→新浪→腾讯）"""
    import sys
    sys.path.insert(0, "/root/.openclaw/workspace/scripts")
    from stock_data_provider import get_stock_quotes

    # 去掉市场前缀（sh/sz）以适配数据源接口
    code_map = {}  # raw_code -> original_code
    raw_codes = []
    for c in codes:
        if c.startswith("sh") or c.startswith("sz"):
            stripped = c[2:]
        elif c == "sh000001":
            stripped = "000001"
        else:
            stripped = c
        code_map[stripped] = c
        raw_codes.append(stripped)

    raw = get_stock_quotes(raw_codes)
    if raw:
        quotes = {"data": {}, "error": None}
        for stripped_code, q in raw.items():
            # 映射回原始带前缀的代码
            orig_code = code_map.get(stripped_code, stripped_code)
            pct = (q["price"] - q["prev_close"]) / q["prev_close"] * 100 if q["prev_close"] else 0
            quotes["data"][orig_code] = {
                "name": q["name"],
                "price": q["price"],
                "prev_close": q["prev_close"],
                "change_pct": pct,
                "open": q.get("open", 0),
                "high": q.get("high", 0),
                "low": q.get("low", 0),
                "vol": q.get("vol", 0),
                "amount": q.get("amount", 0),
                "source": q.get("source", "?"),
            }
        return quotes
    return {"data": {}, "error": "所有数据源均失败"}

def _fetch_quotes_legacy(codes):
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

# ====== 动态技术指标 ======
TECH_FILE = "/root/.openclaw/workspace/config/tech_levels.json"

def load_tech_levels():
    """加载动态技术指标"""
    try:
        with open(TECH_FILE, "r") as f:
            data = json.load(f)
        return data.get("stocks", {})
    except:
        return {}

TECH_LEVELS = load_tech_levels()

# 动态技术分析（通过通达信K线计算）
def load_dynamic_tech():
    """通过通达信K线计算实时技术指标"""
    try:
        import sys
        sys.path.insert(0, "/root/.openclaw/workspace/scripts")
        from stock_tech_analysis import analyze_stock
        result = {}
        all_stocks = {**HOLDINGS, **FRIEND}
        for code, cfg in all_stocks.items():
            if cfg.get("shares", 0) == 0 and not cfg.get("is_watching", False):
                continue
            analysis = analyze_stock(code, cfg["name"], kline_periods=60)
            if "error" not in analysis:
                result[code] = {
                    "ma5": analysis["ma"].get("MA5"),
                    "ma10": analysis["ma"].get("MA10"),
                    "ma20": analysis["ma"].get("MA20"),
                    "ma60": analysis["ma"].get("MA60"),
                    "rsi_14": analysis["rsi"],
                    "macd_signal": analysis["macd"]["signal"] if analysis["macd"] else None,
                    "macd_dif": analysis["macd"]["DIF"] if analysis["macd"] else None,
                    "macd_dea": analysis["macd"]["DEA"] if analysis["macd"] else None,
                    "kdj_j": analysis["kdj"]["J"] if analysis["kdj"] else None,
                    "bb_upper": analysis["boll"]["UPPER"] if analysis["boll"] else None,
                    "bb_lower": analysis["boll"]["LOWER"] if analysis["boll"] else None,
                    "bb_mid": analysis["boll"]["MID"] if analysis["boll"] else None,
                    "vol_ratio": analysis["vol_ratio"],
                    "high_5d": analysis["high_5d"],
                    "low_5d": analysis["low_5d"],
                    "signals": analysis["signals"],
                }
        return result
    except Exception as e:
        return {}

DYNAMIC_TECH = load_dynamic_tech()

# ====== 专有分析模块 ======
def run_proprietary_analysis(quotes):
    """运行专有分析（板块强弱 + 资金流向）"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from proprietary_analysis import full_analysis
        return full_analysis(quotes)
    except Exception as e:
        return {"error": str(e)}

def check_alerts(quotes):
    """检查所有预警条件"""
    alerts = []
    
    all_stocks = {**HOLDINGS, **FRIEND}
    
    for code, config in all_stocks.items():
        if code not in quotes:
            continue
        # 跳过已清仓的，但保留关注中的（shares=0但无sold标记）
        if config.get("shares", 0) == 0 and not config.get("is_watching", False):
            continue
        q = quotes[code]
        name = config["name"]
        price = q["price"]
        change = q["change_pct"]
        
        if price == 0:
            continue
        
        # 获取动态技术指标（优先用通达信K线计算，其次静态配置）
        tech = DYNAMIC_TECH.get(code, {}) or TECH_LEVELS.get(code, {})
        
        # 1. 涨跌幅异动
        if abs(change) >= ALERT_S2:
            severity = "🚨紧急"
            alerts.append(f"{severity} {name} 涨跌幅 {change:+.2f}%（超±{ALERT_S2}%阈值）")
        elif abs(change) >= ALERT_S1:
            severity = "⚠️警告"
            alerts.append(f"{severity} {name} 涨跌幅 {change:+.2f}%（超±{ALERT_S1}%阈值）")
        
        # 2. 减仓位触发（优先用动态指标）
        reduce_levels = tech.get("reduce_levels", []) or config.get("reduce_levels", [])
        for level in reduce_levels:
            lo, hi = level["range"]
            if lo <= price <= hi:
                alerts.append(f"💰减仓触发 {name} 现价{price:.2f} 进入{level['label']}区间[{lo}-{hi}]，建议卖出{level['sell']}股")
        
        # 3. 止盈位触发（朋友账户）
        if "take_profit" in config:
            for level in config["take_profit"]:
                lo, hi = level["range"]
                if lo <= price <= hi:
                    alerts.append(f"💰止盈触发 {name} 现价{price:.2f} 进入{level['label']}区间[{lo}-{hi}]，建议卖出{level['sell']}股")
        
        # 4. 止损位（动态止损 > 静态止损）
        dynamic_sl = tech.get("dynamic_stop_loss")
        static_sl = config.get("stop_loss", 0)
        effective_sl = dynamic_sl if dynamic_sl else static_sl
        if effective_sl and price <= effective_sl:
            pct = (price - config["cost"]) / config["cost"] * 100
            sl_type = "动态止损" if dynamic_sl else "止损"
            alerts.append(f"🛑{sl_type}警报 {name} 现价{price:.2f} 触及{sl_type}位{effective_sl}，浮亏{pct:.1f}%")
        
        if "stop_loss_hard" in config and price <= config["stop_loss_hard"]:
            alerts.append(f"🛑硬止损 {name} 现价{price:.2f} 跌破硬止损{config['stop_loss_hard']}，建议清仓")
        
        # 5. 关键技术位突破（动态 > 静态）
        key_levels = {}
        if tech:
            key_levels = {
                "MA5": tech.get("ma5"),
                "MA10": tech.get("ma10"),
                "MA20": tech.get("ma20"),
                "support": tech.get("support"),
                "resistance": tech.get("resistance"),
            }
        elif "key_levels" in config:
            key_levels = config["key_levels"]
        
        for label, level_price in key_levels.items():
            if level_price is None:
                continue
            if "MA" in label or label in ["support", "resistance"]:
                # 向上突破
                if q["high"] >= level_price and q["open"] < level_price:
                    direction = "突破" if change > 0 else "触及"
                    alerts.append(f"📊技术信号 {name} 盘中{direction}{label}({level_price:.2f})，当前{price:.2f}")
                # 向下跌破
                elif q["low"] <= level_price and q["open"] > level_price:
                    alerts.append(f"📊技术信号 {name} 盘中跌破{label}({level_price:.2f})，当前{price:.2f}")
        
        # 6. 成交量异常
        if tech and tech.get("volume_ratio"):
            vol_r = tech["volume_ratio"]
            if vol_r >= VOLUME_RATIO:
                alerts.append(f"📈量能异动 {name} 成交量比{vol_r}x（>{VOLUME_RATIO}x阈值）")
        
        # 7. RSI 超买超卖
        rsi = tech.get("rsi_14")
        if rsi:
            if rsi > 75:
                alerts.append(f"🔴RSI超买 {name} RSI={rsi}，强烈建议减仓")
            elif rsi > 70:
                alerts.append(f"🟡RSI偏高 {name} RSI={rsi}，考虑分批减仓")
            elif rsi < 25:
                alerts.append(f"🟢RSI极度超卖 {name} RSI={rsi}，关注反弹机会")
        
        # 8. 布林带触及
        bb_upper = tech.get("bb_upper")
        bb_lower = tech.get("bb_lower")
        if bb_upper and price >= bb_upper * 0.99:
            alerts.append(f"📊触及布林上轨 {name} 现价{price:.2f} 上轨{bb_upper}，短期超涨")
        if bb_lower and price <= bb_lower * 1.01:
            alerts.append(f"📊触及布林下轨 {name} 现价{price:.2f} 下轨{bb_lower}，关注支撑")
        
        # 9. 量价背离
        divergence = tech.get("volume_divergence")
        if divergence == "bearish":
            alerts.append(f"⚠️量价背离 {name} 价涨量缩，趋势弱化信号")
        
        # 7. 盈亏状态（关注股成本可能为0，跳过盈亏分析）
        cost = config.get("cost", 0)
        if cost > 0:
            pnl_pct = (price - cost) / cost * 100
            pnl_amount = (price - cost) * config.get("shares", 0)
            # 大幅亏损警告
            if pnl_pct <= -10:
                alerts.append(f"📉深度套牢 {name} 浮亏{pnl_pct:.1f}%（{pnl_amount:+.0f}元）")
        else:
            pnl_pct = 0
        
        # 大幅亏损警告
        if pnl_pct <= -10:
            alerts.append(f"📉深度套牢 {name} 浮亏{pnl_pct:.1f}%（{pnl_amount:+.0f}元）")
    
    # 10. 策略学习信号（基于最优参数）
    for code, config in all_stocks.items():
        if code not in quotes or config.get("shares", 0) == 0:
            continue
        try:
            import sys as _sys
            _sys.path.insert(0, "/root/.openclaw/workspace/scripts")
            from strategy_linker import load_strategy_params, generate_strategy_signals
            params = load_strategy_params()
            stock_params = params.get('stocks', {}).get(code, {})
            if stock_params:
                tech = DYNAMIC_TECH.get(code, {}) or TECH_LEVELS.get(code, {})
                strategy_name = stock_params.get('best_strategy', '')
                # RSI策略信号
                rsi_buy = stock_params.get('rsi_buy', 30)
                rsi_sell = stock_params.get('rsi_sell', 70)
                rsi_val = tech.get('rsi_14')
                if rsi_val:
                    if rsi_val < rsi_buy:
                        alerts.append(f"🎯策略信号 {config['name']} 最优策略[{strategy_name}]触发买入信号: RSI={rsi_val:.1f}<{rsi_buy}")
                    elif rsi_val > rsi_sell:
                        alerts.append(f"🎯策略信号 {config['name']} 最优策略[{strategy_name}]触发卖出信号: RSI={rsi_val:.1f}>{rsi_sell}")
        except:
            pass
    
    # 10. 专有分析：板块强弱 + 资金流向（仅在有预警时追加）
    if alerts:
        analysis = run_proprietary_analysis(quotes)
        if analysis and not analysis.get("error"):
            ss = analysis.get("sector_strength", {})
            for s in ss.get("stocks", []):
                if s.get("rs_vs_sector", 0) < -1.0:
                    alerts.append(f"📉板块弱跑 {s['name']}跑输板块{abs(s['rs_vs_sector']):.1f}%，优先减仓此股")
            mf = analysis.get("money_flow", {})
            for code, info in mf.items():
                if info.get("main_net", 0) < -3000:
                    alerts.append(f"💸大资金流出 {info['name']}主力净流出{abs(info['main_net']):.0f}万，注意出货风险")
    
    return alerts

def generate_status(quotes):
    """生成持仓状态摘要"""
    lines = ["📊 **持仓盘中快照**\n"]
    total_pnl = 0
    
    all_stocks = {**HOLDINGS, **FRIEND}
    for code, config in all_stocks.items():
        if code not in quotes:
            continue
        if config.get("shares", 0) == 0 and not config.get("is_watching", False):
            continue  # 已清仓且非关注股，跳过
        q = quotes[code]
        price = q["price"]
        if price == 0:
            continue
        
        change = q["change_pct"]
        cost = config.get("cost", 0)
        if cost > 0:
            pnl_pct = (price - cost) / cost * 100
            pnl_amount = (price - cost) * config.get("shares", 0)
        else:
            pnl_pct = 0
            pnl_amount = 0
        total_pnl += pnl_amount
        
        emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"
        
        # 动态技术指标
        tech = DYNAMIC_TECH.get(code, {}) or TECH_LEVELS.get(code, {})
        trend = tech.get("trend", "")
        sl = tech.get("dynamic_stop_loss", config.get("stop_loss", 0))
        
        lines.append(f"{emoji} **{config['name']}** {price:.2f} ({change:+.2f}%) | 成本{config['cost']:.3f} | 浮亏{pnl_pct:+.1f}% ({pnl_amount:+.0f}元)")
        if trend or sl:
            tech_info = []
            if trend:
                tech_info.append(f"趋势:{trend}")
            if sl:
                tech_info.append(f"止损:{sl}")
            lines.append(f"   {' | '.join(tech_info)}")
    
    lines.append(f"\n💰 **总浮亏: {total_pnl:+.0f}元**")

    # 专有分析（板块强弱 + 资金流向）
    analysis = run_proprietary_analysis(quotes)
    if analysis and not analysis.get("error"):
        ss = analysis.get("sector_strength")
        if ss and ss.get("sector"):
            sector = ss["sector"]
            lines.append(f"\n📊 **板块: {sector.get('name','?')} {sector.get('change_pct',0):+.2f}%**")
            for s in ss.get("stocks", []):
                lines.append(f"  {s['name']}: vs板块 {s['rs_vs_sector']:+.2f}% {s['verdict']}")

        mf = analysis.get("money_flow", {})
        for code, info in mf.items():
            lines.append(f"  💰 {info['name']}主力: {info['main_net']:+.0f}万 {info['signal']}")

        for s in analysis.get("summary", []):
            if "BDI" in s:
                lines.append(f"  {s}")

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
    
    codes = list(HOLDINGS.keys()) + list(FRIEND.keys())
    # 上证指数用 mootdx 专用接口获取
    sh_index_quote = None
    try:
        sys.path.insert(0, "/root/.openclaw/workspace/scripts")
        from stock_data_provider import MootdxSource
        if MootdxSource.available():
            from mootdx.quotes import Quotes
            client = Quotes.factory(market='std', timeout=5)
            idx_data = client.quotes(symbol="1A0001")
            if idx_data is not None and not idx_data.empty:
                row = idx_data.iloc[0]
                prev_close = float(row.get("last_close", 0))
                price = float(row.get("price", 0))
                pct = (price - prev_close) / prev_close * 100 if prev_close else 0
                sh_index_quote = {
                    "price": price,
                    "prev_close": prev_close,
                    "change_pct": pct,
                }
    except Exception:
        pass
    quotes = fetch_quotes(codes)
    
    if quotes.get("error"):
        print(f"行情获取失败: {quotes['error']}")
        sys.exit(1)
    
    # 提取行情数据
    quotes_data = quotes.get("data", {})

    # 输出状态
    print(generate_status(quotes_data))
    
    # 检查预警
    alerts = check_alerts(quotes_data)
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
    if sh_index_quote:
        idx = sh_index_quote
        print(f"\n📈 上证指数 {idx['price']:.2f} ({idx['change_pct']:+.2f}%)")
