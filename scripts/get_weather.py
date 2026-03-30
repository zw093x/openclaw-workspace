#!/usr/bin/env python3
"""
获取广州/佛山逐时天气预报，输出结构化文本供 cron 任务使用
数据源：wttr.in（免费，无需 API key）
"""
import json
import subprocess
import sys
from datetime import datetime


def get_hourly_weather(city, city_cn):
    """获取城市逐时天气"""
    try:
        # wttr.in JSON 格式
        result = subprocess.run(
            ["curl", "-s", f"https://wttr.in/{city}?format=j1"],
            capture_output=True, text=True, timeout=15,
            env={**__import__('os').environ, "http_proxy": "", "https_proxy": ""}
        )
        if result.returncode != 0:
            return f"{city_cn}：获取失败"
        
        data = json.loads(result.stdout)
        current = data.get("current_condition", [{}])[0]
        today = data.get("weather", [{}])[0] if data.get("weather") else {}
        hourly = today.get("hourly", [])
        
        # 当前天气
        temp = current.get("temp_C", "?")
        humidity = current.get("humidity", "?")
        desc_cn = current.get("lang_zh", [{}])
        desc = desc_cn[0].get("value", current.get("weatherDesc", [{}])[0].get("value", "?")) if desc_cn else current.get("weatherDesc", [{}])[0].get("value", "?")
        wind = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "?")
        feelslike = current.get("FeelsLikeC", "?")
        
        lines = [f"**{city_cn}**：{temp}°C（体感{feelslike}°C）| {desc} | 湿度{humidity}% | {wind_dir}{wind}km/h"]
        
        # 逐时预报（关键时段）
        rain_hours = []
        temp_changes = []
        prev_temp = int(temp) if temp != "?" else None
        
        for h in hourly:
            time_str = h.get("time", "")
            hour = int(time_str) // 100 if time_str.isdigit() else 0
            h_temp = int(h.get("tempC", 0))
            h_desc_cn = h.get("lang_zh", [{}])
            h_desc = h_desc_cn[0].get("value", "") if h_desc_cn else h.get("weatherDesc", [{}])[0].get("value", "")
            h_rain = float(h.get("precipMM", 0))
            h_chance = int(h.get("chanceofrain", 0))
            
            # 标记降雨时段
            if h_rain > 0.5 or h_chance > 60:
                rain_hours.append(f"{hour:02d}:00 {h_desc}（降雨概率{h_chance}%）")
            
            # 标记温度变化 >3度
            if prev_temp is not None and abs(h_temp - prev_temp) >= 3:
                direction = "↑" if h_temp > prev_temp else "↓"
                temp_changes.append(f"{prev_temp}→{h_temp}°C {direction}")
            prev_temp = h_temp
        
        if rain_hours:
            lines.append(f"⏰ 降雨时段：{' | '.join(rain_hours[:4])}")
        
        # 全天温度
        max_temp = today.get("maxtempC", "?")
        min_temp = today.get("mintempC", "?")
        lines.append(f"🌡 全天温度：{min_temp}°C ~ {max_temp}°C")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"{city_cn}：获取失败 ({e})"


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"⏰ 天气数据更新时间：{now}")
    print("---")
    
    # 佛山北滘
    print(get_hourly_weather("Beijiao,Foshan", "佛山北滘"))
    print("---")
    # 广州猎德
    print(get_hourly_weather("Tianhe,Guangzhou", "广州天河"))
    print("---")
    
    # 出行建议汇总
    try:
        result_foshan = subprocess.run(
            ["curl", "-s", "https://wttr.in/Beijiao,Foshan?format=j1"],
            capture_output=True, text=True, timeout=10,
            env={**__import__('os').environ, "http_proxy": "", "https_proxy": ""}
        )
        data = json.loads(result_foshan.stdout)
        hourly = data.get("weather", [{}])[0].get("hourly", [])
        
        # 找最早降雨时间
        first_rain = None
        for h in hourly:
            rain = float(h.get("precipMM", 0))
            chance = int(h.get("chanceofrain", 0))
            if rain > 0.5 or chance > 60:
                time_str = h.get("time", "")
                hour = int(time_str) // 100 if time_str.isdigit() else 0
                first_rain = f"{hour:02d}:00"
                break
        
        if first_rain:
            print(f"🌂 出行建议：预计 {first_rain} 开始降雨，外出请携带雨具")
        else:
            print("🌂 出行建议：今日降雨概率较低，可轻装出行")
    except:
        pass


if __name__ == "__main__":
    main()
