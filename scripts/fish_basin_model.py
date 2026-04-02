#!/usr/bin/env python3
"""
鱼盆模型 2.0 — 市场结构X光机
数据源：AKShare（腾讯API + 申万API）
"""
import json, os, datetime, time
import akshare as ak

# ===== 配置 =====
INDEXES = [
    {"symbol": "sh000001", "code": "000001", "name": "上证指数", "tag": "大盘蓝筹"},
    {"symbol": "sz399001", "code": "399001", "name": "深证成指", "tag": "深市主板"},
    {"symbol": "sz399006", "code": "399006", "name": "创业板指", "tag": "成长/科技"},
    {"symbol": "sh000688", "code": "000688", "name": "科创50",   "tag": "科创板"},
    {"symbol": "sh000300", "code": "000300", "name": "沪深300",   "tag": "权重核心"},
    {"symbol": "sh000905", "code": "000905", "name": "中证500",   "tag": "中盘"},
    {"symbol": "sz399852", "code": "399852", "name": "中证1000",  "tag": "小盘"},
    {"symbol": "bj899050", "code": "899050", "name": "北证50",    "tag": "北交所"},
]

SECTOR_CODES = [
    "801010","801030","801040","801050","801080","801110","801120",
    "801130","801140","801150","801160","801170","801180","801200",
    "801230","801710","801720","801730","801740","801750","801760",
    "801770","801780","801790","801880","801890"
]

MA_PERIOD = 20
CACHE_DIR = "/root/.openclaw/workspace/memory/fish-basin-cache"
DOC_TOKEN = "RGSFdpCnroGdw3xwucucebFwnef"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== 核心计算 =====
def calc_fish(closes_list, dates_list, ma=MA_PERIOD):
    """计算鱼盆指标"""
    if closes_list is None or len(closes_list) < ma + 1:
        return None
    cur = closes_list[-1]
    prev = closes_list[-2]
    ma20 = sum(closes_list[-ma:]) / ma
    ma20_prev = sum(closes_list[-ma-1:-1]) / ma
    status = "YES" if cur > ma20 else "NO"
    status_prev = "YES" if prev > ma20_prev else "NO"
    deviation = round((cur - ma20) / ma20 * 100, 2)
    change_pct = round((cur - prev) / prev * 100, 2)

    duration = 1
    for i in range(2, min(len(closes_list), 60)):
        check_closes = closes_list[-i:]
        if len(check_closes) < ma:
            break
        check_ma = sum(check_closes[-ma:]) / ma
        prev_status = "YES" if check_closes[-1] > check_ma else "NO"
        if prev_status == status:
            duration += 1
        else:
            break

    return {
        'current': round(cur, 2), 'prev': round(prev, 2),
        'ma20': round(ma20, 2),
        'status': status, 'status_prev': status_prev,
        'changed': status != status_prev,
        'deviation': deviation, 'change_pct': change_pct,
        'duration': duration,
        'date': dates_list[-1] if dates_list else ''
    }

def save_cache(date_str, data):
    path = os.path.join(CACHE_DIR, f"{date_str}.json")
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def load_cache(date_str):
    path = os.path.join(CACHE_DIR, f"{date_str}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

# ===== 数据获取 =====
def fetch_indexes():
    """获取所有大盘指数K线"""
    results = []
    for idx in INDEXES:
        try:
            df = ak.stock_zh_index_daily(symbol=idx['symbol'])
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['close'].tolist()
                dates = [str(d) for d in df['date'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = idx['name']
                    r['code'] = idx['code']
                    r['tag'] = idx['tag']
                    results.append(r)
                    print(f"  {idx['name']}: {r['status']} ({r['deviation']:+.2f}%)")
                else:
                    print(f"  {idx['name']}: 计算失败")
            else:
                print(f"  {idx['name']}: 数据不足")
        except Exception as e:
            print(f"  {idx['name']}: 获取失败({e})")
        time.sleep(0.3)
    return results

def fetch_sectors():
    """获取申万行业K线"""
    # 先获取行业名称映射
    name_map = {}
    try:
        df_info = ak.index_realtime_sw(symbol="一级行业")
        for _, row in df_info.iterrows():
            name_map[str(row['指数代码'])] = row['指数名称']
    except:
        pass

    results = []
    for code in SECTOR_CODES:
        try:
            df = ak.index_hist_sw(symbol=code, period="day")
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['收盘'].tolist()
                dates = [str(d) for d in df['日期'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = name_map.get(code, code)
                    r['code'] = code
                    results.append(r)
                else:
                    print(f"  {name_map.get(code,code)}: 计算失败")
            else:
                print(f"  {name_map.get(code,code)}: 数据不足")
        except Exception as e:
            print(f"  {name_map.get(code,code)}: 获取失败({e})")
        time.sleep(0.3)
    return results

# ===== 主流程 =====
def run():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"正在计算鱼盆模型 2.0... ({today})")

    print("获取大盘指数...")
    index_results = fetch_indexes()

    print("获取行业板块...")
    sector_results = fetch_sectors()

    # 排序
    index_results.sort(key=lambda x: abs(x['deviation']), reverse=True)
    for i, r in enumerate(index_results, 1):
        r['strength'] = i
    sector_results.sort(key=lambda x: x['deviation'], reverse=True)
    for i, r in enumerate(sector_results, 1):
        r['rank'] = i

    yesterday_data = load_cache(yesterday)

    result = {
        'date': today,
        'indexes': index_results,
        'sectors': sector_results,
        'summary': {
            'index_yes': sum(1 for r in index_results if r['status'] == 'YES'),
            'index_no': sum(1 for r in index_results if r['status'] == 'NO'),
            'sector_yes': sum(1 for r in sector_results if r['status'] == 'YES'),
            'sector_no': sum(1 for r in sector_results if r['status'] == 'NO'),
        }
    }
    save_cache(today, result)

    print(f"\n完成: {len(index_results)}个指数 + {len(sector_results)}个行业")
    print(f"大盘 YES:{result['summary']['index_yes']} NO:{result['summary']['index_no']}")
    print(f"行业 YES:{result['summary']['sector_yes']} NO:{result['summary']['sector_no']}")
    return result, yesterday_data

if __name__ == '__main__':
    result, yesterday = run()
    print("\n===JSON===")
    print(json.dumps(result, ensure_ascii=False, default=str))
