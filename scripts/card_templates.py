#!/usr/bin/env python3
"""
飞书卡片模板库
为不同类型的 cron 推送提供精美卡片模板
"""

import json
from datetime import datetime

class CardTemplates:
    """飞书卡片模板"""
    
    @staticmethod
    def stock_open(name, code, price, change, change_pct, news_items, bdi, analysis):
        """股票开盘卡片"""
        is_up = change >= 0
        emoji = "📈" if is_up else "📉"
        color = "red" if is_up else "green"
        sign = "+" if is_up else ""
        
        # 价格行
        price_line = f"**{name}({code})**  ¥{price:.2f}"
        change_line = f"{emoji} {sign}{change:.2f} ({sign}{change_pct:.2f}%)"
        
        # BDI
        bdi_line = f"🚢 BDI: {bdi}" if bdi else ""
        
        # 新闻
        news_md = ""
        if news_items:
            news_md = "\n---\n**📰 相关新闻**\n"
            for item in news_items[:3]:
                news_md += f"• {item}\n"
        
        # 分析
        analysis_md = ""
        if analysis:
            analysis_md = f"\n---\n**💡 分析**\n{analysis}"
        
        content = f"{price_line}\n{change_line}\n{bdi_line}{news_md}{analysis_md}"
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 {name} 开盘播报"},
                "template": color
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ]}
            ]
        }
    
    @staticmethod
    def stock_close(name, code, price, change, change_pct, volume, high, low, news_items, analysis):
        """股票收盘卡片"""
        is_up = change >= 0
        emoji = "📈" if is_up else "📉"
        color = "red" if is_up else "green"
        sign = "+" if is_up else ""
        
        content = f"**{name}({code})**  ¥{price:.2f}\n"
        content += f"{emoji} {sign}{change:.2f} ({sign}{change_pct:.2f}%)\n"
        content += f"📊 最高: ¥{high:.2f} | 最低: ¥{low:.2f}"
        if volume:
            content += f" | 成交量: {volume}"
        
        if news_items:
            content += "\n---\n**📰 盘后新闻**\n"
            for item in news_items[:3]:
                content += f"• {item}\n"
        
        if analysis:
            content += f"\n---\n**💡 收盘分析**\n{analysis}"
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 {name} 收盘播报"},
                "template": color
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ]}
            ]
        }
    
    @staticmethod
    def stock_alert(name, code, price, alert_type, alert_msg, analysis=""):
        """股票预警卡片（红色紧急）"""
        emoji_map = {
            "limit_up": "🔴 涨停",
            "limit_down": "🟢 跌停",
            "surge": "🚨 暴涨",
            "crash": "🚨 暴跌",
            "volume": "📊 放量",
            "support": "📉 跌破支撑",
            "resistance": "📈 突破阻力",
            "reduce": "⚠️ 减仓信号",
        }
        
        alert_label = emoji_map.get(alert_type, f"⚠️ {alert_type}")
        
        content = f"**{name}({code})**  ¥{price:.2f}\n"
        content += f"**{alert_label}**\n"
        content += f"{alert_msg}"
        
        if analysis:
            content += f"\n---\n**💡 建议**\n{analysis}"
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"🚨 {name} 异动预警"},
                "template": "red"
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} | 请关注仓位风险"}
                ]}
            ]
        }
    
    @staticmethod
    def weather(city, temp, weather, humidity, wind, suggestion, food_tips=""):
        """天气卡片"""
        # 温度颜色
        if temp >= 35:
            temp_color = "🔴 高温"
        elif temp >= 28:
            temp_color = "🟠 偏热"
        elif temp <= 10:
            temp_color = "🔵 寒冷"
        elif temp <= 18:
            temp_color = "🟢 偏凉"
        else:
            temp_color = "🟢 舒适"
        
        content = f"**{city}** {weather}\n"
        content += f"🌡️ {temp}°C ({temp_color})\n"
        content += f"💧 湿度: {humidity}% | 💨 风力: {wind}\n"
        content += f"\n---\n**👔 穿衣建议**\n{suggestion}"
        
        if food_tips:
            content += f"\n---\n**🍲 月子饮食**\n{food_tips}"
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"🌤️ {city} 天气预报"},
                "template": "turquoise"
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ]}
            ]
        }
    
    @staticmethod
    def gold(price_usd, price_cny, change, change_pct, source, alert=""):
        """黄金价格卡片"""
        is_up = change >= 0
        emoji = "📈" if is_up else "📉"
        sign = "+" if is_up else ""
        color = "orange"
        
        if abs(change_pct) > 3:
            color = "red"
            alert = "🚨 S2 预警: 单日涨跌幅超±3%！"
        elif abs(change_pct) > 2:
            color = "yellow"
            alert = "⚠️ S1 预警: 单日涨跌幅超±2%！"
        
        content = f"**COMEX 黄金**\n"
        content += f"💰 ${price_usd:.2f}/oz | ¥{price_cny:.1f}/克\n"
        content += f"{emoji} {sign}{change:.2f} ({sign}{change_pct:.2f}%)\n"
        content += f"📊 数据源: {source}"
        
        if alert:
            content += f"\n---\n{alert}"
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": "💰 黄金价格播报"},
                "template": color
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ]}
            ]
        }
    
    @staticmethod
    def daily_briefing(title, sections):
        """每日早报卡片（多板块）"""
        elements = []
        for i, section in enumerate(sections):
            if i > 0:
                elements.append({"tag": "hr"})
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            if section_title:
                elements.append({"tag": "markdown", "content": f"**{section_title}**\n{section_content}"})
            else:
                elements.append({"tag": "markdown", "content": section_content})
        
        elements.append({"tag": "note", "elements": [
            {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        ]})
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "blue"
            },
            "elements": elements
        }
    
    @staticmethod
    def info_news(title, categories, color="purple"):
        """资讯类卡片（AI/科技/CG）"""
        elements = []
        for i, cat in enumerate(categories):
            if i > 0:
                elements.append({"tag": "hr"})
            cat_name = cat.get("name", "")
            items = cat.get("items", [])
            if cat_name:
                md = f"**{cat_name}**\n"
            else:
                md = ""
            for item in items[:5]:
                md += f"• {item}\n"
            elements.append({"tag": "markdown", "content": md})
        
        elements.append({"tag": "note", "elements": [
            {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        ]})
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": elements
        }
    
    @staticmethod
    def health_tip(title, tips, weather_info="", color="green"):
        """健康小贴士卡片"""
        elements = []
        
        if weather_info:
            elements.append({"tag": "markdown", "content": weather_info})
            elements.append({"tag": "hr"})
        
        elements.append({"tag": "markdown", "content": tips})
        elements.append({"tag": "note", "elements": [
            {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        ]})
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": elements
        }
    
    @staticmethod
    def baby_care(title, week_info, vaccine_reminder="", feeding_tips=""):
        """宝宝成长卡片"""
        elements = []
        
        if week_info:
            elements.append({"tag": "markdown", "content": week_info})
        
        if vaccine_reminder:
            elements.append({"tag": "hr"})
            elements.append({"tag": "markdown", "content": f"**💉 疫苗提醒**\n{vaccine_reminder}"})
        
        if feeding_tips:
            elements.append({"tag": "hr"})
            elements.append({"tag": "markdown", "content": f"**🍼 喂养建议**\n{feeding_tips}"})
        
        elements.append({"tag": "note", "elements": [
            {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        ]})
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "green"
            },
            "elements": elements
        }
    
    @staticmethod
    def system_status(title, status_items, color="indigo"):
        """系统状态卡片"""
        elements = []
        for item in status_items:
            name = item.get("name", "")
            status = item.get("status", "")
            detail = item.get("detail", "")
            emoji = "✅" if "ok" in status.lower() or "正常" in status else "⚠️" if "warn" in status.lower() else "❌"
            md = f"{emoji} **{name}**: {status}"
            if detail:
                md += f"\n   {detail}"
            elements.append({"tag": "markdown", "content": md})
        
        elements.append({"tag": "note", "elements": [
            {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        ]})
        
        return {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": elements
        }

    @staticmethod
    def inspiration(title, elements_content, source=""):
        """灵感库更新卡片"""
        content = elements_content
        if source:
            content = f"**来源：** {source}\n---\n{elements_content}"

        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"🖼️ {title}"},
                "template": "yellow"
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} · 灵感库更新"}
                ]}
            ]
        }


def card_to_json(card):
    """将卡片对象转为 JSON 字符串"""
    return json.dumps(card, ensure_ascii=False)


def save_card_template(name, card):
    """保存卡片模板到文件"""
    path = Path("/root/.openclaw/workspace/config/card-templates")
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{name}.json").write_text(json.dumps(card, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # 示例：生成各种卡片模板
    templates = CardTemplates()
    
    # 股票开盘
    card = templates.stock_open(
        "中国船舶", "600150", 32.50, 0.85, 2.69,
        ["中国船舶获新订单", "航运指数上涨"],
        "BDI: 1850 (+2.3%)",
        "技术面站稳MA20，短线看涨"
    )
    print("=== 股票开盘卡片 ===")
    print(card_to_json(card))
    print()
    
    # 股票预警
    card = templates.stock_alert(
        "中国船舶", "600150", 34.20, "surge",
        "单日涨幅超5%，触发S2预警",
        "建议关注是否需要减仓"
    )
    print("=== 股票预警卡片 ===")
    print(card_to_json(card))
    print()
    
    # 黄金
    card = templates.gold(
        4592.11, 1021.7, 67.81, 1.50, "新浪/COMEX"
    )
    print("=== 黄金价格卡片 ===")
    print(card_to_json(card))
