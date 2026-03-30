#!/usr/bin/env python3
"""
推送上限控制器
控制每日飞书推送消息数量，非紧急消息合并发送
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 配置
DAILY_LIMIT = 15  # 每日普通消息上限
EMERGENCY_KEYWORDS = ["预警", "减仓", "止损", "突破", "异动", "⚠️", "🔴", "紧急"]

STATE_FILE = Path("/root/.openclaw/workspace/config/push-state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"date": "", "count": 0, "emergency_count": 0, "queued": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))

def is_emergency(message):
    return any(kw in message for kw in EMERGENCY_KEYWORDS)

def should_send(message):
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 新的一天重置计数
    if state["date"] != today:
        state = {"date": today, "count": 0, "emergency_count": 0, "queued": []}
    
    # 紧急消息不受限制
    if is_emergency(message):
        state["emergency_count"] += 1
        save_state(state)
        return True, "emergency"
    
    # 普通消息检查上限
    if state["count"] < DAILY_LIMIT:
        state["count"] += 1
        save_state(state)
        return True, "normal"
    else:
        # 队列等待
        state["queued"].append({"time": datetime.now().isoformat(), "msg": message[:100]})
        save_state(state)
        return False, "queued"

def get_status():
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    if state["date"] != today:
        return {"date": today, "count": 0, "limit": DAILY_LIMIT, "emergency": 0, "queued": 0}
    return {
        "date": today,
        "count": state["count"],
        "limit": DAILY_LIMIT,
        "emergency": state["emergency_count"],
        "queued": len(state.get("queued", []))
    }

def flush_queued():
    """返回队列中待发送的消息（每日汇总）"""
    state = load_state()
    queued = state.get("queued", [])
    state["queued"] = []
    save_state(state)
    return queued

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            s = get_status()
            print(json.dumps(s, ensure_ascii=False, indent=2))
        elif sys.argv[1] == "flush":
            q = flush_queued()
            print(f"队列消息: {len(q)} 条")
            for item in q:
                print(f"  [{item['time'][:16]}] {item['msg']}")
        elif sys.argv[1] == "check":
            msg = " ".join(sys.argv[2:])
            ok, reason = should_send(msg)
            print(f"{'✅ 允许' if ok else '❌ 队列'} ({reason}): {msg[:50]}")
