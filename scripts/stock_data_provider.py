#!/usr/bin/env python3
"""
统一股票数据源管理
主源：通达信(mootdx)
备源1：东方财富(eastmoney)
备源2：腾讯行情(qt.gtimg.cn)
自动降级，无需代理
"""

import json
import ssl
import urllib.request
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class MootdxSource:
    """通达信数据源（主源）"""
    name = "通达信"
    
    @staticmethod
    def available():
        try:
            from mootdx.quotes import Quotes
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_quotes(codes):
        """获取实时行情
        
        Args:
            codes: ['600150', '600482'] 格式的代码列表
        Returns:
            dict: {code: {name, price, prev_close, open, high, low, vol, amount, ...}}
        """
        from mootdx.quotes import Quotes
        client = Quotes.factory(market='std', timeout=5)
        result = {}
        
        for code in codes:
            try:
                data = client.quotes(symbol=code)
                if data is not None and not data.empty:
                    row = data.iloc[0]
                    result[code] = {
                        'name': _code_to_name(code),
                        'price': float(row.get('price', 0)),
                        'prev_close': float(row.get('last_close', 0)),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'vol': int(row.get('vol', 0)),
                        'amount': float(row.get('amount', 0)),
                        'bid1': float(row.get('bid1', 0)),
                        'ask1': float(row.get('ask1', 0)),
                        'source': '通达信',
                    }
            except Exception as e:
                continue
        
        return result if result else None
    
    @staticmethod
    def get_kline(code, frequency=9, offset=30):
        """获取K线数据
        
        Args:
            frequency: 1=1min, 5=5min, 15=15min, 30=30min, 60=60min, 9=日K, 7=周K, 13=月K
            offset: 获取条数
        Returns:
            DataFrame with columns: open, close, high, low, vol, amount, datetime
        """
        from mootdx.quotes import Quotes
        client = Quotes.factory(market='std', timeout=10)
        try:
            df = client.bars(symbol=code, frequency=frequency, offset=offset)
            return df if df is not None and not df.empty else None
        except:
            return None


class SinaSource:
    """新浪行情数据源（备源1）"""
    name = "新浪"
    
    @staticmethod
    def available():
        return True
    
    @staticmethod
    def get_quotes(codes):
        """新浪实时行情"""
        result = {}
        
        for code in codes:
            try:
                prefix = 'sh' if code.startswith('6') else 'sz'
                url = f"https://hq.sinajs.cn/list={prefix}{code}"
                req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    data = resp.read().decode("GBK")
                
                raw = data.split('"')[1] if '"' in data else ""
                if not raw:
                    continue
                parts = raw.split(',')
                if len(parts) < 10:
                    continue
                
                result[code] = {
                    'name': parts[0],
                    'open': float(parts[1]) if parts[1] else 0,
                    'prev_close': float(parts[2]) if parts[2] else 0,
                    'price': float(parts[3]) if parts[3] else 0,
                    'high': float(parts[4]) if parts[4] else 0,
                    'low': float(parts[5]) if parts[5] else 0,
                    'vol': int(parts[8]) if parts[8] else 0,
                    'amount': float(parts[9]) if parts[9] else 0,
                    'source': '新浪',
                }
            except Exception:
                continue
        
        return result if result else None


class TencentSource:
    """腾讯行情数据源（备源2）"""
    name = "腾讯"
    
    @staticmethod
    def available():
        return True
    
    @staticmethod
    def get_quotes(codes):
        """腾讯实时行情"""
        code_map = {}
        for c in codes:
            prefix = 'sh' if c.startswith('6') else 'sz'
            code_map[f"{prefix}{c}"] = c
        
        try:
            url = f"https://qt.gtimg.cn/q={','.join(code_map.keys())}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                raw = resp.read().decode('gbk')
            
            result = {}
            for line in raw.strip().split(';'):
                if '~' not in line:
                    continue
                parts = line.split('~')
                if len(parts) < 40:
                    continue
                
                # 反查原始代码
                full_code = parts[2]
                code = code_map.get(full_code, full_code)
                
                result[code] = {
                    'name': parts[1],
                    'price': float(parts[3]) if parts[3] else 0,
                    'prev_close': float(parts[4]) if parts[4] else 0,
                    'open': float(parts[5]) if parts[5] else 0,
                    'high': float(parts[33]) if parts[33] else 0,
                    'low': float(parts[34]) if parts[34] else 0,
                    'vol': int(parts[6]) if parts[6] else 0,
                    'amount': float(parts[37]) if parts[37] else 0,
                    'source': '腾讯',
                }
            
            return result if result else None
        except Exception:
            return None


# ====== 代码-名称映射 ======
_CODE_NAMES = {
    '600150': '中国船舶',
    '600482': '中国动力',
    '603656': '泰禾智能',
    '000001': '上证指数',
}

def _code_to_name(code):
    return _CODE_NAMES.get(code, code)


# ====== 统一接口 ======
def get_stock_quotes(codes):
    """统一行情获取接口，自动降级
    
    Args:
        codes: ['600150', '600482'] 格式
    Returns:
        dict: {code: {name, price, prev_close, ...}}
    """
    sources = [MootdxSource, SinaSource, TencentSource]
    
    for source_cls in sources:
        if not source_cls.available():
            continue
        try:
            result = source_cls.get_quotes(codes)
            if result and len(result) > 0:
                return result
        except Exception:
            continue
    
    return None


def get_kline(code, frequency=9, offset=30):
    """获取K线（仅通达信支持）"""
    if MootdxSource.available():
        return MootdxSource.get_kline(code, frequency, offset)
    return None


# ====== 测试 ======
if __name__ == "__main__":
    codes = ['600150', '600482']
    
    print("=== 统一行情接口测试 ===")
    quotes = get_stock_quotes(codes)
    if quotes:
        for code, q in quotes.items():
            pct = (q['price'] - q['prev_close']) / q['prev_close'] * 100 if q['prev_close'] else 0
            print(f"{q['name']}({code}) [{q['source']}]: 现价 {q['price']:.2f} | 涨跌 {pct:+.2f}%")
    else:
        print("❌ 所有数据源均失败")
    
    print()
    print("=== K线测试 ===")
    kline = get_kline('600150', frequency=9, offset=5)
    if kline is not None:
        print(f"日K线: {len(kline)} 条")
        print(kline.tail(3).to_string())
    else:
        print("K线获取失败")
