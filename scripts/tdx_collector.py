#!/usr/bin/env python3
"""
通达信全量数据采集器
统一接口获取行情/K线/分笔/财务/板块/指数数据
"""

import sys
import json
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/root/.openclaw/workspace/scripts")

DATA_DIR = "/root/.openclaw/workspace/data/tdx"
os.makedirs(DATA_DIR, exist_ok=True)

def get_tdx_client():
    """获取通达信客户端"""
    from mootdx.quotes import Quotes
    return Quotes.factory(market='std', timeout=10)


class TDXCollector:
    """通达信全量数据采集"""
    
    def __init__(self):
        self.client = get_tdx_client()
        self.now = datetime.now(timezone(timedelta(hours=8)))
    
    def get_realtime_quotes(self, code):
        """实时行情（5档盘口）"""
        try:
            q = self.client.quotes(symbol=code)
            if q is not None and not q.empty:
                row = q.iloc[0]
                return {
                    'code': code,
                    'name': str(row.get('code', code)),
                    'price': float(row['price']),
                    'prev_close': float(row['last_close']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'vol': int(row['vol']),
                    'amount': float(row['amount']),
                    'bid1': float(row['bid1']),
                    'ask1': float(row['ask1']),
                    'bid_vol1': int(row['bid_vol1']),
                    'ask_vol1': int(row['ask_vol1']),
                    'bid2': float(row.get('bid2', 0)),
                    'ask2': float(row.get('ask2', 0)),
                    'bid_vol2': int(row.get('bid_vol2', 0)),
                    'ask_vol2': int(row.get('ask_vol2', 0)),
                    'bid3': float(row.get('bid3', 0)),
                    'ask3': float(row.get('ask3', 0)),
                    'bid_vol3': int(row.get('bid_vol3', 0)),
                    'ask_vol3': int(row.get('ask_vol3', 0)),
                    'time': str(row.get('servertime', '')),
                    'source': '通达信',
                }
        except Exception as e:
            pass
        return None
    
    def get_kline(self, code, frequency=9, offset=120):
        """K线数据
        frequency: 1=1min, 5=5min, 15=15min, 30=30min, 60=60min, 9=日K, 7=周K, 13=月K
        """
        try:
            df = self.client.bars(symbol=code, frequency=frequency, offset=offset)
            if df is not None and not df.empty:
                return df.to_dict('records')
        except Exception as e:
            pass
        return None
    
    def get_transactions(self, code, offset=100):
        """分笔成交数据"""
        try:
            df = self.client.transaction(symbol=code, start=0, offset=offset)
            if df is not None and not df.empty:
                return df.to_dict('records')
        except Exception as e:
            pass
        return None
    
    def get_minute_data(self, code):
        """当日1分钟数据"""
        try:
            df = self.client.minute(symbol=code)
            if df is not None and not df.empty:
                return df.to_dict('records')
        except Exception as e:
            pass
        return None
    
    def get_finance(self, code):
        """财务数据"""
        try:
            fin = self.client.finance(symbol=code)
            if fin is not None and not fin.empty:
                return fin.iloc[0].to_dict()
        except Exception as e:
            pass
        return None
    
    def get_xdxr(self, code):
        """除权除息"""
        try:
            df = self.client.xdxr(symbol=code)
            if df is not None and not df.empty:
                return df.tail(5).to_dict('records')
        except Exception as e:
            pass
        return None
    
    def get_index_kline(self, symbol='000001', frequency=9, offset=60):
        """指数K线"""
        try:
            df = self.client.index_bars(symbol=symbol, frequency=frequency, offset=offset)
            if df is not None and not df.empty:
                return df.to_dict('records')
        except Exception as e:
            pass
        return None
    
    def collect_all(self, codes):
        """采集所有数据"""
        result = {
            'timestamp': self.now.isoformat(),
            'quotes': {},
            'kline_daily': {},
            'kline_15min': {},
            'transactions': {},
            'minute': {},
            'finance': {},
            'index_daily': None,
        }
        
        for code in codes:
            result['quotes'][code] = self.get_realtime_quotes(code)
            result['kline_daily'][code] = self.get_kline(code, frequency=9, offset=120)
            result['kline_15min'][code] = self.get_kline(code, frequency=15, offset=60)
            result['transactions'][code] = self.get_transactions(code, offset=50)
            result['minute'][code] = self.get_minute_data(code)
            result['finance'][code] = self.get_finance(code)
        
        # 上证指数
        result['index_daily'] = self.get_index_kline('000001', frequency=9, offset=60)
        
        return result
    
    def save_snapshot(self, codes):
        """保存数据快照"""
        data = self.collect_all(codes)
        date_str = self.now.strftime('%Y-%m-%d')
        time_str = self.now.strftime('%H%M')
        
        snapshot_dir = os.path.join(DATA_DIR, date_str)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        filepath = os.path.join(snapshot_dir, f"snapshot_{time_str}.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, ensure_ascii=False, default=str, indent=2)
        
        return filepath, data


if __name__ == "__main__":
    collector = TDXCollector()
    codes = ['600150', '600482']
    
    print("=== 全量数据采集测试 ===\n")
    
    # 实时行情
    for code in codes:
        q = collector.get_realtime_quotes(code)
        if q:
            pct = (q['price'] - q['prev_close']) / q['prev_close'] * 100
            print(f"📊 {code}: {q['price']:.2f} ({pct:+.2f}%)")
            print(f"   买1: {q['bid1']:.2f}({q['bid_vol1']}) | 卖1: {q['ask1']:.2f}({q['ask_vol1']})")
    
    # 日K线
    print(f"\n📈 日K线(600150):")
    kline = collector.get_kline('600150', frequency=9, offset=5)
    if kline:
        for k in kline[-3:]:
            print(f"   {k.get('datetime','')} O:{k['open']:.2f} C:{k['close']:.2f} H:{k['high']:.2f} L:{k['low']:.2f} V:{k['vol']:.0f}")
    
    # 分笔成交
    print(f"\n💹 分笔成交(600150, 最近5笔):")
    txns = collector.get_transactions('600150', offset=5)
    if txns:
        for t in txns:
            bs = '买' if t.get('buyorsell') == 0 else '卖'
            print(f"   {t.get('time','')} {t.get('price',''):.2f} {bs} {t.get('volume','')}")
    
    # 财务数据
    print(f"\n💰 财务数据(600150):")
    fin = collector.get_finance('600150')
    if fin:
        key_fields = ['zongguben', 'province', 'industry', 'ipo_date']
        for f in key_fields:
            if f in fin:
                print(f"   {f}: {fin[f]}")
    
    # 保存快照
    print(f"\n💾 保存快照...")
    filepath, data = collector.save_snapshot(codes)
    print(f"   已保存: {filepath}")
