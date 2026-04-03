#!/usr/bin/env python3
"""
鱼盆模型 2.0 — 市场结构X光机
数据源：AKShare（sina/申万/SGE）+ yfinance（全球指数，通过代理）
"""
import json, os, datetime, time
import akshare as ak

# ===== 配置 =====
# src: 'sina'=stock_zh_index_daily, 'csindex'=stock_zh_index_hist_csindex,
#      'hk'=stock_hk_index_daily_sina, 'yf'=yfinance(通过代理), 'sge'=spot_hist_sge
INDEXES = [
    # 国内A股 - sina
    {"symbol": "sh000001", "code": "000001", "name": "上证指数",  "tag": "大盘蓝筹",  "src": "sina"},
    {"symbol": "sz399001", "code": "399001", "name": "深证成指",  "tag": "深市主板",  "src": "sina"},
    {"symbol": "sz399006", "code": "399006", "name": "创业板指",  "tag": "成长/科技", "src": "sina"},
    {"symbol": "sh000688", "code": "000688", "name": "科创50",    "tag": "科创板",    "src": "sina"},
    {"symbol": "sh000300", "code": "000300", "name": "沪深300",   "tag": "权重核心",  "src": "sina"},
    {"symbol": "sh000905", "code": "000905", "name": "中证500",   "tag": "中盘",      "src": "sina"},
    {"symbol": "sh000852", "code": "000852", "name": "中证1000",  "tag": "小盘",      "src": "sina"},
    {"symbol": "bj899050", "code": "899050", "name": "北证50",    "tag": "北交所",    "src": "sina"},
    # 国内A股 - csindex (中证指数公司)
    {"symbol": "sh000016", "code": "000016", "name": "上证50",    "tag": "大盘蓝筹",  "src": "sina"},
    {"symbol": "sh000510", "code": "000510", "name": "中证A500",  "tag": "核心宽基",  "src": "csindex"},
    {"symbol": "932000",   "code": "932000", "name": "中证2000",  "tag": "微小盘",    "src": "csindex"},
    # 港股 - sina HK
    {"symbol": "HSI",      "code": "HSI",    "name": "恒生指数",  "tag": "港股核心",  "src": "hk"},
    {"symbol": "HSCEI",    "code": "HSCEI",  "name": "国企指数",  "tag": "港股中概",  "src": "hk"},
    {"symbol": "HSTECH",   "code": "HSTECH", "name": "恒生科技",  "tag": "港股科技",  "src": "hk"},
    # 全球 - yfinance (需代理)
    {"symbol": "SPY",      "code": "SPY",    "name": "标普500",   "tag": "美股核心",  "src": "yf"},
    {"symbol": "QQQ",      "code": "QQQ",    "name": "纳指100",   "tag": "美股科技",  "src": "yf"},
    {"symbol": "^N225",    "code": "N225",   "name": "日经225",   "tag": "日股",      "src": "yf"},
    # 大宗商品 - SGE
    {"symbol": "Au99.99",  "code": "AUUSDO", "name": "黄金现价",  "tag": "贵金属",    "src": "sge"},
    {"symbol": "Ag99.99",  "code": "AGUSDO", "name": "白银现价",  "tag": "贵金属",    "src": "sge"},
]

# 板块/行业/主题指数（多数据源）
# src: 'sw'=申万(index_hist_sw), 'sina'=stock_zh_index_daily, 'csindex'=stock_zh_index_hist_csindex
SECTORS = [
    # === 原有申万一级行业 ===
    {"code": "801010", "name": "农林牧渔",   "src": "sw"},
    {"code": "801030", "name": "基础化工",   "src": "sw"},
    {"code": "801040", "name": "钢铁",       "src": "sw"},
    {"code": "801050", "name": "有色金属",   "src": "sw"},
    {"code": "801080", "name": "电子",       "src": "sw"},
    {"code": "801110", "name": "家用电器",   "src": "sw"},
    {"code": "801120", "name": "食品饮料",   "src": "sw"},
    {"code": "801130", "name": "纺织服饰",   "src": "sw"},
    {"code": "801140", "name": "轻工制造",   "src": "sw"},
    {"code": "801150", "name": "医药生物",   "src": "sw"},
    {"code": "801160", "name": "公用事业",   "src": "sw"},
    {"code": "801170", "name": "交通运输",   "src": "sw"},
    {"code": "801180", "name": "房地产",     "src": "sw"},
    {"code": "801200", "name": "商贸零售",   "src": "sw"},
    {"code": "801230", "name": "综合",       "src": "sw"},
    {"code": "801710", "name": "建筑材料",   "src": "sw"},
    {"code": "801720", "name": "建筑装饰",   "src": "sw"},
    {"code": "801730", "name": "电力设备",   "src": "sw"},
    {"code": "801740", "name": "国防军工",   "src": "sw"},
    {"code": "801750", "name": "计算机",     "src": "sw"},
    {"code": "801760", "name": "传媒",       "src": "sw"},
    {"code": "801770", "name": "通信",       "src": "sw"},
    {"code": "801780", "name": "银行",       "src": "sw"},
    {"code": "801790", "name": "非银金融",   "src": "sw"},
    {"code": "801880", "name": "汽车",       "src": "sw"},
    {"code": "801890", "name": "机械设备",   "src": "sw"},
    # === 新增申万二级行业（替代无法获取的中证/国证代码） ===
    {"code": "801081", "name": "半导体",     "src": "sw"},    # 替代 881121
    {"code": "801738", "name": "电网设备",   "src": "sw"},    # 替代 881278
    {"code": "801735", "name": "光伏设备",   "src": "sw"},    # 替代 881279
    {"code": "801741", "name": "航天装备",   "src": "sw"},    # 替代 886078 商业航天
    {"code": "801181", "name": "房地产开发", "src": "sw"},    # 房地产细分
    {"code": "801951", "name": "煤炭开采",   "src": "sw"},    # 煤炭细分
    {"code": "801193", "name": "证券Ⅱ",      "src": "sw"},    # 证券细分
    # === 新增中证/国证主题指数（sina） ===
    {"symbol": "sz399989", "code": "399989", "name": "中证医疗", "src": "sina"},
    {"symbol": "sh000922", "code": "000922", "name": "中证红利", "src": "sina"},
    {"symbol": "sz399998", "code": "399998", "name": "中证煤炭", "src": "sina"},
    {"symbol": "sz000813", "code": "000813", "name": "细分化工", "src": "sina"},
    {"symbol": "sz399975", "code": "399975", "name": "证券公司", "src": "sina"},
    {"symbol": "sh000932", "code": "000932", "name": "中证消费", "src": "sina"},
    # === 新增中证主题指数（csindex） ===
    {"code": "H30590", "name": "中证机器人", "src": "csindex"},
    {"code": "931775", "name": "中证房地产", "src": "csindex"},
    {"code": "000941", "name": "中证新能源", "src": "csindex"},
]

# 向后兼容别名
SECTOR_CODES = [s['code'] for s in SECTORS if s['src'] == 'sw']

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
def _fetch_yf_batch(symbols_info):
    """通过yfinance批量获取全球指数（需代理）"""
    import subprocess, sys
    # 用子进程隔离代理环境变量，避免影响国内API
    symbols_json = json.dumps(symbols_info).replace("'", "\\'")
    script = f"""
import os, json, sys
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
import yfinance as yf

symbols = json.loads('{symbols_json}')
results = {{}}
for info in symbols:
    sym = info['symbol']
    code = info['code']
    try:
        t = yf.Ticker(sym)
        hist = t.history(period='120d')
        if len(hist) >= 21:
            closes = hist['Close'].tolist()
            dates = [str(d.date()) if hasattr(d, 'date') else str(d) for d in hist.index]
            results[code] = {{'closes': closes, 'dates': dates, 'name': info['name'],
                            'tag': info['tag'], 'code': code}}
    except Exception as e:
        print(f"yf {{sym}}: {{e}}", file=sys.stderr)
print(json.dumps(results))
"""
    try:
        r = subprocess.run([sys.executable, '-c', script],
                          capture_output=True, text=True, timeout=60,
                          env={**os.environ})
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout.strip())
    except Exception as e:
        print(f"  yfinance批处理失败: {e}")
    return {}

def fetch_indexes():
    """获取所有大盘指数K线（多数据源）"""
    results = []

    # 分组：国内sina / 中证csindex / 港股hk / 全球yf / 大宗sge
    sina_items = [idx for idx in INDEXES if idx['src'] == 'sina']
    csindex_items = [idx for idx in INDEXES if idx['src'] == 'csindex']
    hk_items = [idx for idx in INDEXES if idx['src'] == 'hk']
    yf_items = [idx for idx in INDEXES if idx['src'] == 'yf']
    sge_items = [idx for idx in INDEXES if idx['src'] == 'sge']

    # 1) 国内指数 - sina
    for idx in sina_items:
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
                    print(f"  [sina] {idx['name']}: {r['status']} ({r['deviation']:+.2f}%)")
            else:
                print(f"  [sina] {idx['name']}: 数据不足")
        except Exception as e:
            print(f"  [sina] {idx['name']}: 获取失败({e})")
        time.sleep(0.3)

    # 2) 中证指数 - csindex
    for idx in csindex_items:
        try:
            start = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y%m%d")
            end = datetime.datetime.now().strftime("%Y%m%d")
            df = ak.stock_zh_index_hist_csindex(symbol=idx['code'], start_date=start, end_date=end)
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['收盘'].tolist()
                dates = [str(d) for d in df['日期'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = idx['name']
                    r['code'] = idx['code']
                    r['tag'] = idx['tag']
                    results.append(r)
                    print(f"  [csindex] {idx['name']}: {r['status']} ({r['deviation']:+.2f}%)")
            else:
                print(f"  [csindex] {idx['name']}: 数据不足")
        except Exception as e:
            print(f"  [csindex] {idx['name']}: 获取失败({e})")
        time.sleep(0.3)

    # 3) 港股指数 - sina HK
    for idx in hk_items:
        try:
            df = ak.stock_hk_index_daily_sina(symbol=idx['symbol'])
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['close'].tolist()
                dates = [str(d) for d in df['date'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = idx['name']
                    r['code'] = idx['code']
                    r['tag'] = idx['tag']
                    results.append(r)
                    print(f"  [hk] {idx['name']}: {r['status']} ({r['deviation']:+.2f}%)")
            else:
                print(f"  [hk] {idx['name']}: 数据不足")
        except Exception as e:
            print(f"  [hk] {idx['name']}: 获取失败({e})")
        time.sleep(0.3)

    # 4) 全球指数 - yfinance (子进程代理)
    if yf_items:
        print("  [yf] 通过代理获取全球指数...")
        yf_data = _fetch_yf_batch(yf_items)
        for idx in yf_items:
            code = idx['code']
            if code in yf_data:
                d = yf_data[code]
                r = calc_fish(d['closes'], d['dates'])
                if r:
                    r['name'] = idx['name']
                    r['code'] = idx['code']
                    r['tag'] = idx['tag']
                    results.append(r)
                    print(f"  [yf] {idx['name']}: {r['status']} ({r['deviation']:+.2f}%)")
                else:
                    print(f"  [yf] {idx['name']}: 计算失败")
            else:
                print(f"  [yf] {idx['name']}: 获取失败")

    # 5) 大宗商品 - SGE
    for idx in sge_items:
        try:
            df = ak.spot_hist_sge(symbol=idx['symbol'])
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['close'].tolist()
                dates = [str(d) for d in df['date'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = idx['name']
                    r['code'] = idx['code']
                    r['tag'] = idx['tag']
                    results.append(r)
                    print(f"  [sge] {idx['name']}: {r['status']} ({r['deviation']:+.2f}%)")
            else:
                print(f"  [sge] {idx['name']}: 数据不足")
        except Exception as e:
            print(f"  [sge] {idx['name']}: 获取失败({e})")
        time.sleep(0.3)

    return results

def fetch_sectors():
    """获取行业/板块K线（多数据源）"""
    # 分组
    sw_items = [s for s in SECTORS if s['src'] == 'sw']
    sina_items = [s for s in SECTORS if s['src'] == 'sina']
    csindex_items = [s for s in SECTORS if s['src'] == 'csindex']

    # 申万行业名称映射
    name_map = {}
    try:
        df_info = ak.index_realtime_sw(symbol="二级行业")
        for _, row in df_info.iterrows():
            name_map[str(row['指数代码'])] = row['指数名称']
    except:
        pass

    results = []

    # 1) 申万行业
    for s in sw_items:
        code = s['code']
        try:
            df = ak.index_hist_sw(symbol=code, period="day")
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['收盘'].tolist()
                dates = [str(d) for d in df['日期'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = name_map.get(code, s.get('name', code))
                    r['code'] = code
                    results.append(r)
                else:
                    print(f"  [sw] {s.get('name',code)}: 计算失败")
            else:
                print(f"  [sw] {s.get('name',code)}: 数据不足")
        except Exception as e:
            print(f"  [sw] {s.get('name',code)}: 获取失败({e})")
        time.sleep(0.3)

    # 2) sina 中证/国证
    for s in sina_items:
        try:
            df = ak.stock_zh_index_daily(symbol=s['symbol'])
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['close'].tolist()
                dates = [str(d) for d in df['date'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = s['name']
                    r['code'] = s['code']
                    results.append(r)
                else:
                    print(f"  [sina] {s['name']}: 计算失败")
            else:
                print(f"  [sina] {s['name']}: 数据不足")
        except Exception as e:
            print(f"  [sina] {s['name']}: 获取失败({e})")
        time.sleep(0.3)

    # 3) csindex 中证
    for s in csindex_items:
        try:
            start = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y%m%d")
            end = datetime.datetime.now().strftime("%Y%m%d")
            df = ak.stock_zh_index_hist_csindex(symbol=s['code'], start_date=start, end_date=end)
            if df is not None and len(df) >= MA_PERIOD + 1:
                closes = df['收盘'].tolist()
                dates = [str(d) for d in df['日期'].tolist()]
                r = calc_fish(closes, dates)
                if r:
                    r['name'] = s['name']
                    r['code'] = s['code']
                    results.append(r)
                else:
                    print(f"  [csindex] {s['name']}: 计算失败")
            else:
                print(f"  [csindex] {s['name']}: 数据不足")
        except Exception as e:
            print(f"  [csindex] {s['name']}: 获取失败({e})")
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
