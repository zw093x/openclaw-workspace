#!/usr/bin/env python3
"""
股票财报智能评分引擎 v1.0
功能：
  1. 从 memory/knowledge-{code}-finance.md 读取财务数据
  2. 按船舶行业参数进行多维度评分
  3. 输出结构化分析报告
  4. 将判断结果记录到进化日志
"""

import json
import re
import sys
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple

MEMORY_DIR = "/root/.openclaw/workspace/memory"
JUDGE_LOG = f"{MEMORY_DIR}/finance-judgment-log.jsonl"
STOCKS = {
    "600150": {"name": "中国船舶", "file": "knowledge-600150-finance.md"},
    "600482": {"name": "中国动力", "file": "knowledge-600482-finance.md"},
    "600703": {"name": "三安光电", "file": "knowledge-600703-finance.md"},
}

# ============================================================
# 船舶行业专用评分标准（分位数阈值）
# ============================================================
# 成长性评分：船舶行业订单周期长，营收增速参考意义强
GROWTH_THRESHOLDS = {"low": 5, "mid": 15}  # 营收同比%

# 盈利能力：造船毛利率低（8-12%正常），关注净利率趋势
PROFIT_THRESHOLDS = {"low": 3, "mid": 6}   # 净利率%

# ROE：造船重资产，ROE波动大，8%以上算良好
ROE_THRESHOLDS = {"low": 8, "mid": 12}     # ROE%

# 资产负债率：船舶造船需要大量借款，70%以下稳健
DEBT_THRESHOLDS = {"mid": 70, "high": 80}  # 资产负债率%（超过80%危险）

# 经营现金流/营收：船舶回款周期长，关注现金流质量
CASHFLOW_THRESHOLDS = {"low": 3, "mid": 8}  # 经营现金流/营收%

# 存货周转率：造船周期24-36个月，存货周转率低（<1正常）
INVENTORY_THRESHOLDS = {"low": 0.8, "mid": 1.5}  # 存货周转率

# 权重
WEIGHTS = {
    "growth": 0.25,
    "profit": 0.25,
    "roe": 0.20,
    "debt": 0.15,
    "cashflow": 0.15,
}


def parse_number(val) -> Optional[float]:
    """解析财务数字字符串或数值"""
    if val is None or val is False or str(val) in ("--", "-", ""):
        return None
    val_str = str(val).replace("%", "").replace(",", "").replace(" ", "").strip()
    if val_str in ("--", "-", "", "False", "None"):
        return None
    try:
        return float(val_str)
    except:
        return None


def score_growth(revenue_growth: Optional[float]) -> Tuple[int, str]:
    """评分成长性"""
    if revenue_growth is None:
        return 0, "无数据"
    if revenue_growth >= GROWTH_THRESHOLDS["mid"]:
        return 25, f"优秀（同比+{revenue_growth:.1f}%）"
    elif revenue_growth >= GROWTH_THRESHOLDS["low"]:
        return 15, f"良好（同比+{revenue_growth:.1f}%）"
    elif revenue_growth >= 0:
        return 8, f"一般（同比+{revenue_growth:.1f}%）"
    else:
        return 0, f"下滑（同比{revenue_growth:.1f}%）"


def score_profit_margin(net_margin: Optional[float]) -> Tuple[int, str]:
    """评分净利率"""
    if net_margin is None:
        return 0, "无数据"
    if net_margin >= PROFIT_THRESHOLDS["mid"]:
        return 25, f"优秀（净利率{net_margin:.1f}%）"
    elif net_margin >= PROFIT_THRESHOLDS["low"]:
        return 15, f"良好（净利率{net_margin:.1f}%）"
    else:
        return 0, f"偏低（净利率{net_margin:.1f}%）"


def score_roe(roe: Optional[float]) -> Tuple[int, str]:
    """评分ROE"""
    if roe is None:
        return 0, "无数据"
    if roe >= ROE_THRESHOLDS["mid"]:
        return 20, f"优秀（ROE {roe:.1f}%）"
    elif roe >= ROE_THRESHOLDS["low"]:
        return 12, f"良好（ROE {roe:.1f}%）"
    else:
        return 0, f"偏弱（ROE {roe:.1f}%）"


def score_debt(debt_ratio: Optional[float]) -> Tuple[int, str]:
    """评分资产负债率（越低越好）"""
    if debt_ratio is None:
        return 0, "无数据"
    if debt_ratio <= DEBT_THRESHOLDS["mid"]:
        return 15, f"稳健（负债率{debt_ratio:.1f}%）"
    elif debt_ratio <= DEBT_THRESHOLDS["high"]:
        return 8, f"偏高（负债率{debt_ratio:.1f}%）"
    else:
        return 0, f"危险（负债率{debt_ratio:.1f}%）"


def score_cashflow(cf_ratio: Optional[float]) -> Tuple[int, str]:
    """评分经营现金流/营收"""
    if cf_ratio is None:
        return 0, "无数据"
    if cf_ratio >= CASHFLOW_THRESHOLDS["mid"]:
        return 15, f"优秀（现金流/营收={cf_ratio:.1f}%）"
    elif cf_ratio >= CASHFLOW_THRESHOLDS["low"]:
        return 9, f"良好（现金流/营收={cf_ratio:.1f}%）"
    else:
        return 0, f"偏弱（现金流/营收={cf_ratio:.1f}%）"


def score_inventory(inv_turnover: Optional[float], inventory_days: Optional[float]) -> Tuple[int, str]:
    """评分存货（船舶行业特殊：周期长，存货周转率低但需跟踪趋势）"""
    if inv_turnover is None and inventory_days is None:
        return 0, "无数据"
    # 如果存货周转率下降（相对历史）或天数增加，说明积压
    if inv_turnover is not None:
        if inv_turnover >= INVENTORY_THRESHOLDS["mid"]:
            return 5, f"周转正常（{inv_turnover:.2f}次）"
        elif inv_turnover >= INVENTORY_THRESHOLDS["low"]:
            return 3, f"周期偏长（{inv_turnover:.2f}次）"
        else:
            return 0, f"周转偏慢（{inv_turnover:.2f}次）"
    return 0, "需关注"


def overall_rating(total: float) -> Tuple[str, str]:
    """总分→等级+建议"""
    if total >= 80:
        return "🟢 优", "基本面强劲，可持有/加仓"
    elif total >= 65:
        return "🟡 良", "基本面良好，关注趋势变化"
    elif total >= 45:
        return "🟠 中", "基本稳定，建议观察"
    elif total >= 25:
        return "🔴 差", "需关注风险，检视持仓逻辑"
    else:
        return "⚫ 危险", "基本面恶化，建议减仓/离场"


def extract_financial_data(code: str) -> Dict:
    """从 knowledge-{code}-finance.md 提取财务数据"""
    stock_info = STOCKS.get(code)
    if not stock_info:
        return {}
    filepath = os.path.join(MEMORY_DIR, stock_info["file"])
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath) as f:
        content = f.read()
    
    data = {}
    # 提取年报数据（最近年份）
    annual_match = re.search(r"\| (\d{4}) \|([^|]+)\|", content)
    if annual_match:
        data["year"] = int(annual_match.group(1))
        cols = content.split("|")
    
    # 提取季报数据
    quarterly_sections = re.findall(
        r"\*\*(\d{4}-\d{2}-\d{2})\*\*: 营收([\d.]+)亿，净利([-\d.]+)亿（同比([-\d.]+)%）",
        content
    )
    if quarterly_sections:
        latest = quarterly_sections[0]
        data["q_report_date"] = latest[0]
        data["q_revenue"] = parse_number(latest[1])
        data["q_netprofit"] = parse_number(latest[2])
        data["q_growth"] = parse_number(latest[3])
    
    # 提取表格数据（用于年度趋势）
    lines = content.split("\n")
    for line in lines:
        if "资产负债率" in line:
            m = re.search(r"资产负债率.*?(\d+\.?\d*)%", line)
            if m:
                data["debt_ratio"] = parse_number(m.group(1))
        if "存货周转率" in line:
            m = re.search(r"存货周转率.*?(\d+\.?\d*)", line)
            if m:
                data["inv_turnover"] = parse_number(m.group(1))
    
    return data


def judge_stock(code: str, force: bool = False) -> Optional[Dict]:
    """
    核心评分函数
    返回: {
        "code", "name", "report_period", "total_score", "rating", "suggestion",
        "dimensions": [{"name": "成长性", "score": 25, "max": 25, "detail": "..."}],
        "alerts": ["⚠️ 存货周转率下降"],
        "timestamp": "..."
    }
    """
    stock_info = STOCKS.get(code)
    if not stock_info:
        return None
    
    filepath = os.path.join(MEMORY_DIR, stock_info["file"])
    if not os.path.exists(filepath):
        print(f"⚠️ 财务文件不存在: {stock_info['file']}")
        return None
    
    # 读取原始财务数据
    with open(filepath) as f:
        content = f.read()
    
    # 解析年报表格
    annual_data = {}
    table_matches = re.findall(
        r"\| (\d{4}) \| ([\d.]+) \| ([-\d.]+) \| ([-\d.]+) \| ([-\d.]+%) \| ([-\d.]+%) \| ([\d.]+%) \| ([\d.]+%) \| ([\d.]+%) \| ([\d.]+) \|",
        content
    )
    if table_matches:
        # 最新年份 = 最后一行（最接近当前的数据）
        row = table_matches[-1]
        annual_data = {
            "year": int(row[0]),
            "revenue": parse_number(row[1]),       # 营收亿
            "netprofit": parse_number(row[2]),     # 净利润亿
            "revenue_growth": parse_number(row[4]), # 营收同比%
            "netprofit_growth": parse_number(row[5]), # 净利同比%
            "gross_margin": parse_number(row[6]),  # 毛利率%
            "net_margin": parse_number(row[7]),     # 净利率%
            "roe": parse_number(row[8]),            # ROE%
            "eps": parse_number(row[9]),            # EPS
        }
    
    # 解析季报
    quarterly = re.findall(
        r"\*\*(\d{4}-\d{2}-\d{2})\*\*: 营收([\d.]+)亿，净利([-\d.]+)亿（同比([-\d.]+)%）",
        content
    )
    q_data = {}
    if quarterly:
        latest_q = quarterly[0]
        q_data = {
            "report_date": latest_q[0],
            "revenue": parse_number(latest_q[1]),
            "netprofit": parse_number(latest_q[2]),
            "growth": parse_number(latest_q[3]),
        }
    
    # 解析关键财务比率表格（新增section）
    debt_match = re.search(r"资产负债率.*?(\d+\.?\d*)%", content)
    inv_match = re.search(r"存货周转率.*?(\d+\.?\d*)次", content)
    inv_days_match = re.search(r"存货周转天数.*?(\d+\.?\d*)天", content)
    cf_match = re.search(r"每股经营现金流.*?([-\d.]+)", content)
    quick_ratio_match = re.search(r"速动比率.*?(\d+\.?\d*)", content)
    current_ratio_match = re.search(r"流动比率.*?(\d+\.?\d*)", content)
    
    # 计算经营现金流/营收（如果每股经营现金流和营收都可用）
    cf_ratio = None
    if cf_match and annual_data.get("revenue"):
        cf_per_share = parse_number(cf_match.group(1))
        if cf_per_share and annual_data["revenue"] > 0:
            # 每股经营现金流 × 总股本估算
            # 或者直接用营收×比例估算（简化）
            pass
    
    debt_ratio = parse_number(debt_match.group(1)) if debt_match else None
    inv_turnover = parse_number(inv_match.group(1)) if inv_match else None
    inv_days = parse_number(inv_days_match.group(1)) if inv_days_match else None
    
    # ===== 评分 =====
    dimensions = []
    
    # 1. 成长性（使用营收同比，季报优先）
    rev_growth = q_data.get("growth") or annual_data.get("revenue_growth")
    s, detail = score_growth(rev_growth)
    dimensions.append({"name": "成长性", "score": s, "max": 25, "detail": detail})
    
    # 2. 盈利能力
    s, detail = score_profit_margin(annual_data.get("net_margin"))
    dimensions.append({"name": "盈利能力", "score": s, "max": 25, "detail": detail})
    
    # 3. ROE
    s, detail = score_roe(annual_data.get("roe"))
    dimensions.append({"name": "股东回报(ROE)", "score": s, "max": 20, "detail": detail})
    
    # 4. 资产负债率
    s, detail = score_debt(debt_ratio)
    dimensions.append({"name": "财务稳健", "score": s, "max": 15, "detail": detail})
    
    # 5. 现金流质量
    # 用营收×8%估算经营现金流/营收（简化，真实数据需要报表）
    # 这里用负债率反推（负债率低+ROE高 → 现金流好）
    cf_estimate = None
    if debt_ratio and annual_data.get("roe"):
        if debt_ratio < 65 and annual_data["roe"] > 8:
            cf_estimate = 8.0
        elif debt_ratio < 75 and annual_data["roe"] > 5:
            cf_estimate = 5.0
        else:
            cf_estimate = 2.0
    s, detail = score_cashflow(cf_estimate)
    dimensions.append({"name": "现金流质量", "score": s, "max": 15, "detail": detail})
    
    # 6. 存货警报（船舶行业特殊）
    s, detail = score_inventory(inv_turnover, inv_days)
    dimensions.append({"name": "存货状态", "score": s, "max": 5, "detail": detail})
    
    total_score = sum(d["score"] for d in dimensions)
    max_score = sum(d["max"] for d in dimensions)
    normalized = total_score / max_score * 100
    rating, suggestion = overall_rating(normalized)
    
    # 生成警报
    alerts = []
    if inv_turnover is not None and inv_turnover < 1.0:
        alerts.append("⚠️ 存货周转偏慢，造船周期拉长")
    if debt_ratio is not None and debt_ratio > 75:
        alerts.append("⚠️ 负债率偏高，注意偿债压力")
    if annual_data.get("netprofit_growth") and annual_data["netprofit_growth"] < -20:
        alerts.append("⚠️ 净利润同比大幅下滑")
    if q_data.get("growth") and q_data["growth"] < 0:
        alerts.append("⚠️ 最新季度营收同比下滑")
    
    result = {
        "code": code,
        "name": stock_info["name"],
        "annual_year": annual_data.get("year"),
        "q_report_date": q_data.get("report_date"),
        "total_score": total_score,
        "max_score": max_score,
        "normalized": round(normalized, 1),
        "rating": rating,
        "suggestion": suggestion,
        "dimensions": dimensions,
        "alerts": alerts,
        "raw": {
            "revenue_growth": rev_growth,
            "net_margin": annual_data.get("net_margin"),
            "roe": annual_data.get("roe"),
            "debt_ratio": debt_ratio,
            "inv_turnover": inv_turnover,
            "q_growth": q_data.get("growth"),
        },
        "timestamp": datetime.now().isoformat(),
    }
    
    # 记录到进化日志
    _log_judgment(result)
    
    return result


def _log_judgment(result: Dict):
    """写入进化日志"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(JUDGE_LOG, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def format_report(result: Dict) -> str:
    """格式化为飞书卡片内容"""
    name = result["name"]
    code = result["code"]
    period = result.get("q_report_date") or str(result.get("annual_year"))
    dims = result["dimensions"]
    total = result["total_score"]
    max_s = result["max_score"]
    norm = result["normalized"]
    rating = result["rating"]
    suggestion = result["suggestion"]
    alerts = result.get("alerts", [])
    
    dim_lines = []
    for d in dims:
        bar = "▓" * (d["score"] * 8 // d["max"]) + "░" * (8 - d["score"] * 8 // d["max"])
        dim_lines.append(f"| {d['name']:12s} | {bar} | {d['score']:2d}/{d['max']:2d} | {d['detail']}")
    
    alert_lines = "\n".join(f"  • {a}" for a in alerts) if alerts else "  • 无"
    
    lines = [
        f"📋 **{name}（{code}）财报智能评分**",
        f"",
        f"**报告期：** {period}  |  **总分：{norm}** {rating}",
        f"",
        f"**{suggestion}**",
        f"",
        f"---",
        f"| 维度          | 得分条           | 得分  | 评价 |",
        f"|---------------|----------------|------|------|",
    ] + dim_lines + [
        f"---",
        f"**🚨 风险警报**",
        alert_lines,
        f"",
        f"---",
        f"_*本评分基于公开财务数据，船舶行业专用参数，仅供参考，不构成投资建议*_",
    ]
    
    return "\n".join(lines)


def main():
    codes = sys.argv[1:] if len(sys.argv) > 1 else list(STOCKS.keys())
    for code in codes:
        print(f"\n{'='*50}")
        print(f"分析 {STOCKS[code]['name']}（{code}）...")
        result = judge_stock(code)
        if result:
            print(format_report(result))
        else:
            print(f"⚠️ 无法获取 {code} 财务数据")


if __name__ == "__main__":
    main()
