#!/bin/bash
# 天气数据预加载脚本
# 在每日早报 cron 之前运行，将天气数据写入文件供 agent 读取

WEATHER_FILE="/root/.openclaw/workspace/memory/weather-latest.txt"

python3 /root/.openclaw/workspace/scripts/get_weather.py > "$WEATHER_FILE" 2>&1

echo "Weather data saved to $WEATHER_FILE"
cat "$WEATHER_FILE"
