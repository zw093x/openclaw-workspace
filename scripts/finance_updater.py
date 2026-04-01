#!/usr/bin/env python3
"""
股票财报自动更新器
定期检查并采集中国动力(600482)和中国船舶(600150)的最新财务数据
保存到 memory/knowledge-{code}-finance.md
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

MEMORY_DIR = "/root/.openclaw/workspace/memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

# 监控的股票
STOCKS = {
    "600482": {
        "name": "中国动力",
        "code": "600482",
        "knowledge_file": "knowledge-600482-finance.md",
    },
    "600703": {
        "name": "三安光电",
        "code": "600703",
        "knowledge_file": "knowledge-600703-finance.md",
    },
    "600416": {
        "name": "湘电股份",
        "code": "600416",
        "knowledge_file": "knowledge-600416-finance.md",
    },
    "600150": {
        "name": "中国船舶",
        "code": "600150",
        "knowledge_file": "knowledge-600150-finance.md",
    },
}


def get_financial_data(code):
    """从同花顺获取财务数据"""
    import akshare as ak
    try:
        df = ak.stock_financial_abstract_ths(symbol=code, indicator="按年度")
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"  ⚠️ 年度数据获取失败: {e}")

    return None


def get_quarterly_data(code):
    """从同花顺获取季度数据"""
    import akshare as ak
    try:
        df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"  ⚠️ 季度数据获取失败: {e}")
    return None


def parse_number(val_str):
    """解析财务数字字符串"""
    if not val_str or val_str == "--":
        return None
    val_str = str(val_str).replace(",", "").replace(" ", "")
    try:
        if "亿" in val_str:
            return float(val_str.replace("亿", ""))
        elif "万" in val_str:
            return float(val_str.replace("万", "")) / 10000
        else:
            return float(val_str)
    except:
        return val_str


def generate_annual_table(df):
    """生成年报数据表格"""
    if df is None or df.empty:
        return ""

    rows = []
    # 取最近5年数据
    recent = df.tail(5)
    for _, row in recent.iterrows():
        period = row.get("报告期", "")
        revenue = parse_number(row.get("营业总收入", "0"))
        net_profit = parse_number(row.get("净利润", "0"))
        deduct_profit = parse_number(row.get("扣非净利润", "0"))
        revenue_yoy = row.get("营业总收入同比增长率", "--")
        profit_yoy = row.get("净利润同比增长率", "--")
        gross_margin = row.get("销售毛利率", "--")
        net_margin = row.get("销售净利率", "--")
        roe = row.get("净资产收益率", "--")
        eps = row.get("基本每股收益", "--")
        bps = row.get("每股净资产", "--")

        rows.append(
            f"| {period} | {revenue:.2f} | {net_profit:.2f} | {deduct_profit:.2f} | "
            f"{revenue_yoy} | {profit_yoy} | {gross_margin} | {net_margin} | {roe} | {eps} |"
        )

    header = (
        "| 年份 | 营收(亿) | 净利润(亿) | 扣非净利(亿) | "
        "营收同比 | 净利同比 | 毛利率 | 净利率 | ROE | EPS |"
    )
    separator = (
        "|------|---------|-----------|------------|"
        "---------|---------|--------|--------|-----|-----|"
    )

    return f"{header}\n{separator}\n" + "\n".join(rows)


def generate_quarterly_highlights(df):
    """生成最近季度亮点"""
    if df is None or df.empty:
        return "暂无季度数据"

    # 取最近4个季度
    recent = df.tail(4)
    highlights = []
    for _, row in recent.iterrows():
        period = row.get("报告期", "")
        revenue = parse_number(row.get("营业总收入", "0"))
        net_profit = parse_number(row.get("净利润", "0"))
        profit_yoy = row.get("净利润同比增长率", "--")
        highlights.append(f"- **{period}**: 营收{revenue:.2f}亿，净利{net_profit:.2f}亿（同比{profit_yoy}）")

    return "\n".join(highlights)


def generate_report(name, code, annual_df, quarterly_df):
    """生成完整报告"""
    now = datetime.now(timezone(timedelta(hours=8)))
    date_str = now.strftime("%Y-%m-%d %H:%M")

    annual_table = generate_annual_table(annual_df)
    quarterly_highlights = generate_quarterly_highlights(quarterly_df)

    report = f"""# {name}({code}) 财务数据（自动更新）

> 最后更新：{date_str}

## 年报数据（近5年）

{annual_table}

## 季报数据（近4期）

{quarterly_highlights}

## 数据来源
- 同花顺（akshare）
- 通达信（mootdx）
- 更新频率：每季度财报发布后自动采集

---
*本文件由 scripts/finance_updater.py 自动生成*
"""
    return report


def check_and_update(code, info):
    """检查并更新单只股票的财务数据"""
    print(f"\n📊 更新 {info['name']}({code}) 财务数据...")

    # 获取数据
    annual_df = get_financial_data(code)
    quarterly_df = get_quarterly_data(code)

    if annual_df is None:
        print(f"  ❌ 数据获取失败，跳过")
        return False

    # 生成报告
    report = generate_report(info["name"], code, annual_df, quarterly_df)

    # 写入文件
    filepath = os.path.join(MEMORY_DIR, info["knowledge_file"])
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"  ✅ 已更新: {filepath}")

    # 输出最近一年数据用于验证
    if annual_df is not None and not annual_df.empty:
        latest = annual_df.iloc[-1]
        print(f"  最新年份: {latest.get('报告期', '?')}")
        print(f"  营收: {latest.get('营业总收入', '?')}")
        print(f"  净利润: {latest.get('净利润', '?')}")
        print(f"  净利同比: {latest.get('净利润同比增长率', '?')}")

    return True


def main():
    print(f"=== 股票财报更新器 ===")
    print(f"时间: {datetime.now(timezone(timedelta(hours=8))).isoformat()}")

    success = 0
    for code, info in STOCKS.items():
        if check_and_update(code, info):
            success += 1

    print(f"\n完成: {success}/{len(STOCKS)} 只股票已更新")

    # 输出更新摘要（供cron任务使用）
    summary = {
        "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "updated": success,
        "total": len(STOCKS),
        "stocks": list(STOCKS.keys()),
    }
    print(f"\nSUMMARY: {json.dumps(summary, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
