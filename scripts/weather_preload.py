#!/usr/bin/env python3
"""
天气预加载脚本：获取天气数据并更新 cron 任务 prompt
通过系统 crontab 在每日早报前5分钟运行
"""
import json
import subprocess
import sys
import os
from datetime import datetime

WEATHER_SCRIPT = "/root/.openclaw/workspace/scripts/get_weather.py"
DAILY_BRIEFING_JOB_ID = "17468e27-b4e1-4858-a735-491cb1ec1712"
WEATHER_REMINDER_JOB_ID = "e1a5659e-5cf0-4da9-bf86-9564ccda671b"

def get_weather():
    """运行天气脚本获取天气数据"""
    result = subprocess.run(
        ["python3", WEATHER_SCRIPT],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def get_cron_message(job_id):
    """获取 cron 任务当前的 message"""
    result = subprocess.run(
        "openclaw cron list --json 2>&1",
        shell=True, capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    for j in data["jobs"]:
        if j["id"] == job_id:
            return j.get("payload", {}).get("message", "")
    return None

def update_cron_message(job_id, new_message):
    """更新 cron 任务的 message"""
    cmd = ["openclaw", "cron", "edit", job_id, "--message", new_message]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0

def inject_weather(message, weather_data):
    """将天气数据注入到 prompt 中（替换已有注入，避免重复）"""
    marker = "【WEATHER_DATA_INJECTED】"
    injection_block = f"\n\n以下是今日天气数据（已自动获取，直接引用即可）：\n{weather_data}\n{marker}\n"
    
    if marker in message:
        # 找到已有注入块的起止位置，整块替换
        marker_pos = message.find(marker)
        # 向前找到注入块开头（双换行 + "以下是今日天气数据"）
        search_start = message.rfind("以下是今日天气数据", 0, marker_pos)
        if search_start > 0:
            # 向前找最近的双换行作为块开头
            block_start = message.rfind("\n\n", 0, search_start)
            if block_start < 0:
                block_start = search_start
            block_end = marker_pos + len(marker)
            return message[:block_start] + injection_block + message[block_end:]
        # 找不到开头，用 marker 之后的内容重建
        return message[:message.rfind("\n\n", 0, marker_pos)] + injection_block + message[marker_pos + len(marker):]
    
    # 首次注入，在末尾追加
    return message + injection_block

def main():
    print(f"[{datetime.now().isoformat()}] 开始天气预加载...")
    
    # 获取天气数据
    weather = get_weather()
    if not weather or "获取失败" in weather:
        print(f"❌ 天气数据获取失败: {weather}")
        sys.exit(1)
    print(f"✅ 天气数据获取成功")
    
    # 更新每日早报
    msg = get_cron_message(DAILY_BRIEFING_JOB_ID)
    if msg:
        new_msg = inject_weather(msg, weather)
        if update_cron_message(DAILY_BRIEFING_JOB_ID, new_msg):
            print(f"✅ 每日早报 prompt 已更新")
        else:
            print(f"❌ 每日早报 prompt 更新失败")
    
    # 更新天气穿衣提醒
    msg2 = get_cron_message(WEATHER_REMINDER_JOB_ID)
    if msg2:
        new_msg2 = inject_weather(msg2, weather)
        if update_cron_message(WEATHER_REMINDER_JOB_ID, new_msg2):
            print(f"✅ 天气穿衣提醒 prompt 已更新")
        else:
            print(f"❌ 天气穿衣提醒 prompt 更新失败")
    
    # 保存天气数据到文件（备份）
    weather_file = "/root/.openclaw/workspace/memory/weather-latest.txt"
    with open(weather_file, "w") as f:
        f.write(weather)
    print(f"✅ 天气数据已保存到 {weather_file}")

if __name__ == "__main__":
    main()
