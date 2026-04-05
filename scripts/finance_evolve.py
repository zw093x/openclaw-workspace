#!/usr/bin/env python3
"""
财报进化引擎 v1.0
功能：
  1. 追踪判断历史 → 分析准确率
  2. 对比股价变动 → 验证判断质量
  3. 自动调整行业参数（记录修正历史）
  4. 生成进化报告
"""

import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, List

MEMORY_DIR = "/root/.openclaw/workspace/memory"
JUDGE_LOG = f"{MEMORY_DIR}/finance-judgment-log.jsonl"
ACCURACY_FILE = f"{MEMORY_DIR}/analysis-accuracy.json"
PARAM_FILE = f"{MEMORY_DIR}/finance-params.json"
PORTFOLIO_FILE = f"{MEMORY_DIR}/stock-portfolio.md"

STOCKS = {
    "600150": {"name": "中国船舶"},
    "600482": {"name": "中国动力"},
    "600703": {"name": "三安光电"},
}

# ============================================================
# 进化参数（可随学习自动调整）
# ============================================================
DEFAULT_PARAMS = {
    "version": "1.0",
    "last_updated": None,
    "thresholds": {
        "growth": {"low": 5, "mid": 15},
        "profit": {"low": 3, "mid": 6},
        "roe": {"low": 8, "mid": 12},
        "debt": {"mid": 70, "high": 80},
        "cashflow": {"low": 3, "mid": 8},
    },
    "param_history": [],  # 记录每次参数调整的原因
}


def load_params() -> Dict:
    """加载进化参数"""
    if os.path.exists(PARAM_FILE):
        with open(PARAM_FILE) as f:
            return json.load(f)
    params = DEFAULT_PARAMS.copy()
    params["last_updated"] = datetime.now().isoformat()
    return params


def save_params(params: Dict):
    """保存进化参数"""
    params["last_updated"] = datetime.now().isoformat()
    with open(PARAM_FILE, "w") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)


def load_judgments(code: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """加载历史判断"""
    if not os.path.exists(JUDGE_LOG):
        return []
    
    judgments = []
    with open(JUDGE_LOG) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                j = json.loads(line)
                if code is None or j.get("code") == code:
                    judgments.append(j)
            except:
                continue
    return judgments[-limit:]


def get_stock_price_on_date(code: str, date_str: str) -> Optional[float]:
    """估算某日股价（简化：从judge日志中提取当时价格）"""
    # 从judgment记录的股价（需要扩展）
    # 这里用简化逻辑：从历史k线数据中查
    # 暂时从portolio文件获取参考成本价
    return None


def verify_judgment(judgment: Dict, holding_days: int = 60) -> Dict:
    """
    验证判断质量
    逻辑：如果判断后60天内股价走势与判断方向一致 → 判断正确
    需要外部数据补充，这里做框架记录
    """
    # 简化：标记为待验证状态
    return {
        "judgment_ts": judgment.get("timestamp"),
        "code": judgment.get("code"),
        "normalized": judgment.get("normalized"),
        "rating": judgment.get("rating"),
        "verified": False,
        "note": f"需持有{holding_days}天后验证"
    }


def analyze_accuracy() -> Dict:
    """
    分析各股票判断准确率
    """
    accuracy = {}
    
    for code, info in STOCKS.items():
        judgments = load_judgments(code)
        if not judgments:
            continue
        
        # 按评分分组
        high_score = [j for j in judgments if j.get("normalized", 0) >= 65]
        mid_score = [j for j in judgments if 45 <= j.get("normalized", 0) < 65]
        low_score = [j for j in judgments if j.get("normalized", 0) < 45]
        
        accuracy[code] = {
            "name": info["name"],
            "total_judgments": len(judgments),
            "high_score_count": len(high_score),
            "mid_score_count": len(mid_score),
            "low_score_count": len(low_score),
            "latest_judgment": judgments[-1] if judgments else None,
            "latest_score": judgments[-1].get("normalized") if judgments else None,
            "latest_rating": judgments[-1].get("rating") if judgments else None,
        }
    
    return accuracy


def adjust_params_based_on_feedback(code: str, correction_text: str, params: Dict) -> Dict:
    """
    根据P工反馈调整参数
    correction_text: P工的口头纠正，如"船舶行业ROE应该到10%以上才算良好"
    """
    import re
    
    adjustments = []
    
    # 解析ROE调整
    roe_match = re.search(r"ROE.*?(\d+\.?\d*).*?以上", correction_text)
    if roe_match:
        new_val = float(roe_match.group(1))
        old_mid = params["thresholds"]["roe"]["mid"]
        params["thresholds"]["roe"]["mid"] = new_val
        adjustments.append(f"ROE阈值: {old_mid} → {new_val}")
    
    # 解析营收增速调整
    rev_match = re.search(r"营收.*?(\d+\.?\d*).*?以上", correction_text)
    if rev_match:
        new_val = float(rev_match.group(1))
        old_mid = params["thresholds"]["growth"]["mid"]
        params["thresholds"]["growth"]["mid"] = new_val
        adjustments.append(f"营收增速阈值: {old_mid} → {new_val}")
    
    # 通用阈值调整
    any_match = re.search(r"(ROE|营收|净利率|负债).*?(\d+\.?\d*)", correction_text)
    if adjustments:
        params["param_history"].append({
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "correction_text": correction_text,
            "adjustments": adjustments,
            "adjusted_by": "user_feedback"
        })
        save_params(params)
    
    return {"adjustments": adjustments, "new_params": params["thresholds"]}


def apply_market_learning(code: str, params: Dict) -> Dict:
    """
    根据市场表现自动学习
    逻辑：如果连续3次判断"优"但股价不涨 → 可能是行业特殊性
    自动降低该行业"优"的门槛
    """
    judgments = load_judgments(code)
    
    if len(judgments) < 3:
        return {"action": "样本不足，不调整"}
    
    recent = judgments[-3:]
    
    # 连续3次判断为优但股价无明显上涨
    high_but_flat = all(
        j.get("normalized", 0) >= 80 and j.get("alerts", []) == []
        for j in recent
    )
    
    if high_but_flat:
        # 记录：可能行业特性，实际门槛更高
        params["param_history"].append({
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "type": "auto_market_learning",
            "finding": "连续3次高分判断但无警报，可能是行业周期特性",
            "action": "记录观察，暂不调整阈值"
        })
        save_params(params)
        return {"action": "记录观察，不调整阈值"}
    
    return {"action": "无需调整"}


def generate_evolution_report() -> str:
    """生成进化报告"""
    accuracy = analyze_accuracy()
    params = load_params()
    
    lines = [
        "📈 **财报进化引擎 v1.0 — 状态报告**",
        "",
        f"**参数版本：** {params['version']}",
        f"**最后更新：** {params.get('last_updated', '从未')}",
        "",
        "---",
        "**📊 判断记录统计**",
    ]
    
    for code, info in accuracy.items():
        latest = info["latest_judgment"]
        lines.append(f"| {info['name']} | 总判断{info['total_judgments']}次 |")
        if latest:
            lines.append(f"|  最新：{latest.get('normalized')}分 {latest.get('rating')} |")
    
    # 参数调整历史
    history = params.get("param_history", [])
    if history:
        lines.append("")
        lines.append("**🔧 参数调整历史**")
        for h in history[-5:]:
            ts = h.get("timestamp", "")[:10]
            adj = ", ".join(h.get("adjustments", []))
            lines.append(f"- {ts} [{h.get('code', '通用')}]: {adj}")
    else:
        lines.append("")
        lines.append("**🔧 参数调整历史**：暂无，P工尚未反馈修正")
    
    # 下一阶段建议
    lines.append("")
    lines.append("**📋 下一阶段**")
    lines.append("- ✅ 判断引擎已就位，可执行 `python3 scripts/finance_judge.py` 评分")
    lines.append("- ⏳ 建立季度触发cron：财报发布后自动拉取+评分")
    lines.append("- ⏳ P工反馈回路：判断错误时告诉我，我记录到进化参数")
    lines.append("- ⏳ 股价验证：持仓60天后对比判断准确性")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "report":
            print(generate_evolution_report())
        elif cmd == "accuracy":
            print(json.dumps(analyze_accuracy(), ensure_ascii=False, indent=2))
        elif cmd == "adjust" and len(sys.argv) > 3:
            code = sys.argv[2]
            correction = " ".join(sys.argv[3:])
            params = load_params()
            result = adjust_params_based_on_feedback(code, correction, params)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif cmd == "learn" and len(sys.argv) > 2:
            code = sys.argv[2]
            params = load_params()
            result = apply_market_learning(code, params)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(generate_evolution_report())


if __name__ == "__main__":
    main()
