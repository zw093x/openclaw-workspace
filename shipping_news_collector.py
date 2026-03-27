
import json
import subprocess
import os

TEMPLATES_DIR = "~/.openclaw/workspace/skills/info-aggregator/assets"

def run_tavily_search(query, num_results=5, topic="general", deep=False):
    command = [
        "node",
        os.path.expanduser("~/.openclaw/workspace/skills/tavily-search/scripts/search.mjs"),
        query,
        "-n", str(num_results),
        "--topic", topic
    ]
    if deep:
        command.append("--deep")
    
    if not os.getenv("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY is not set. Please set the environment variable.")
        return {"results": []}

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running tavily search: {e}")
        print(f"Stderr: {e.stderr}")
        return {"results": []}

def collect_shipping_news():
    all_news_items = []
    
    queries = {
        "航运指数": "BDI/CCFI/SCFI航运指数变动及趋势",
        "中国船舶": "中国船舶(600150) 中国动力(600482) 相关产业链新闻",
        "全球航运市场": "全球航运市场 运价波动 航线变化 港口动态",
        "地缘政治影响": "航运 地缘政治 贸易政策 制裁 航线安全",
        "造船行业": "造船行业 大额订单签约 新船交付 技术突破",
        "环保法规": "EEXI/CII 环保法规 航运业影响",
        "船用设备": "船用设备 发动机 LN",
    }

    for category, query in queries.items():
        print(f"Searching for: {query}")
        results = run_tavily_search(query, num_results=10)
        for item in results.get("results", []):
            all_news_items.append({
                "title": item.get("title", f"No title for {category}"),
                "summary": item.get("content", "No summary available."),
                "url": item.get("url", "#"),
                "source": item.get("domain", "Unknown"),
                "priority": "normal" # Default priority
            })
    return all_news_items

if __name__ == "__main__":
    news_items = collect_shipping_news()

    if not news_items:
        report_config = {
            "type": "daily",
            "topic": "shipping-news",
            "days": 1,
            "sections": [
                {"title": "航运行业资讯汇总", "items": []}
            ],
            "impact": "未能获取到航运行业资讯。请检查 TAVILY_API_KEY 是否已正确配置，或网络连接是否存在问题。",
            "sources": []
        }
    else:
        report_config = {
            "type": "daily",
            "topic": "shipping-news",
            "days": 1,
            "sections": [
                {"title": "航运行业资讯汇总", "items": news_items}
            ],
            "impact": "根据以上资讯，分析对中国船舶(600150)和中国动力(600482)可能的影响，以及全球航运市场的近期走势。",
            "sources": ["Tavily Search"]
        }

    # Write the collected data to a temporary JSON file for format_report.py
    with open("shipping_news_raw.json", "w", encoding="utf-8") as f:
        json.dump(report_config, f, ensure_ascii=False, indent=2)

    # Call format_report.py to generate the final report
    format_command = [
        "python3", 
        os.path.expanduser("~/.openclaw/workspace/skills/info-aggregator/scripts/format_report.py"),
        "--type", "custom",
        "--input", "shipping_news_raw.json",
        "--output", "shipping_news_report.md"
    ]
    try:
        subprocess.run(format_command, check=True)
        with open("shipping_news_report.md", "r", encoding="utf-8") as f:
            print(f.read())
    except subprocess.CalledProcessError as e:
        print(f"Error generating report: {e}")
        print(f"Stderr: {e.stderr}")
