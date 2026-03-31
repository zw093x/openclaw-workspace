#!/usr/bin/env python3
"""
策略信号联动模块
将学习引擎的最优参数同步到监控系统
"""

import json
import os
import sys

sys.path.insert(0, "/root/.openclaw/workspace/scripts")

PARAMS_FILE = "/root/.openclaw/workspace/config/strategy_params.json"
HOLDINGS_FILE = "/root/.openclaw/workspace/config/holdings.json"


def load_strategy_params():
    """加载最优策略参数"""
    if os.path.exists(PARAMS_FILE):
        with open(PARAMS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_strategy_params(params):
    """保存策略参数"""
    os.makedirs(os.path.dirname(PARAMS_FILE), exist_ok=True)
    with open(PARAMS_FILE, 'w') as f:
        json.dump(params, f, ensure_ascii=False, indent=2)


def update_params_from_learning():
    """从策略学习结果更新参数"""
    from strategy_learner import optimize_parameters
    
    with open(HOLDINGS_FILE, 'r') as f:
        holdings = json.load(f)
    
    params = {
        'updated': __import__('datetime').datetime.now().isoformat(),
        'stocks': {},
    }
    
    for item in holdings.get('holdings', []):
        if item.get('status') == 'sold' or item.get('shares', 0) == 0:
            continue
        
        code = item['code']
        name = item['name']
        
        print(f"  优化 {name}...")
        result = optimize_parameters(code, name)
        
        if 'error' not in result and result.get('best_strategies'):
            best = result['best_strategies'][0]
            
            # 解析最优策略参数
            strategy_name = best['strategy']
            stock_params = {
                'best_strategy': strategy_name,
                'win_rate': best['win_rate'],
                'avg_return': best['avg_return'],
                'score': best['score'],
                'all_top5': [s['strategy'] for s in result['best_strategies'][:5]],
            }
            
            # 提取具体参数
            if 'MA' in strategy_name:
                import re
                nums = re.findall(r'\d+', strategy_name)
                if len(nums) >= 2:
                    stock_params['ma_fast'] = int(nums[0])
                    stock_params['ma_slow'] = int(nums[1])
            
            elif 'RSI' in strategy_name:
                import re
                nums = re.findall(r'\d+', strategy_name)
                if len(nums) >= 3:
                    stock_params['rsi_period'] = int(nums[0])
                    stock_params['rsi_buy'] = int(nums[1])
                    stock_params['rsi_sell'] = int(nums[2])
            
            elif 'MACD' in strategy_name:
                import re
                nums = re.findall(r'\d+', strategy_name)
                if len(nums) >= 3:
                    stock_params['macd_fast'] = int(nums[0])
                    stock_params['macd_slow'] = int(nums[1])
                    stock_params['macd_signal'] = int(nums[2])
            
            elif '布林' in strategy_name:
                import re
                nums = re.findall(r'[\d.]+', strategy_name)
                if len(nums) >= 2:
                    stock_params['bb_period'] = int(nums[0])
                    stock_params['bb_mult'] = float(nums[1])
            
            params['stocks'][code] = stock_params
    
    save_strategy_params(params)
    return params


def generate_strategy_signals(code, name, current_price, rsi, macd_signal, ma_values, vol_ratio):
    """基于最优策略参数生成信号"""
    params = load_strategy_params()
    stock_params = params.get('stocks', {}).get(code, {})
    
    signals = []
    
    if not stock_params:
        return signals
    
    strategy = stock_params.get('best_strategy', '')
    
    # RSI信号
    rsi_period = stock_params.get('rsi_period', 14)
    rsi_buy = stock_params.get('rsi_buy', 30)
    rsi_sell = stock_params.get('rsi_sell', 70)
    
    if rsi:
        if rsi < rsi_buy:
            signals.append(f"🟢RSI{rsi_period}超卖({rsi:.1f}<{rsi_buy}) - 买入信号")
        elif rsi > rsi_sell:
            signals.append(f"🔴RSI{rsi_period}超买({rsi:.1f}>{rsi_sell}) - 卖出信号")
    
    # MA交叉信号
    ma_fast = stock_params.get('ma_fast')
    ma_slow = stock_params.get('ma_slow')
    if ma_fast and ma_slow and ma_values:
        fast_val = ma_values.get(f'MA{ma_fast}')
        slow_val = ma_values.get(f'MA{ma_slow}')
        if fast_val and slow_val:
            if fast_val > slow_val:
                signals.append(f"🟢MA{ma_fast}/{ma_slow}多头排列({fast_val:.2f}>{slow_val:.2f})")
            else:
                signals.append(f"🔴MA{ma_fast}/{ma_slow}空头排列({fast_val:.2f}<{slow_val:.2f})")
    
    # MACD信号
    if macd_signal:
        if macd_signal == '金叉':
            signals.append("🟢MACD金叉")
        elif macd_signal == '死叉':
            signals.append("🔴MACD死叉")
    
    # 布林带信号
    bb_period = stock_params.get('bb_period')
    bb_mult = stock_params.get('bb_mult')
    if bb_period and bb_mult and ma_values:
        bb_mid = ma_values.get(f'MA{bb_period}')
        if bb_mid:
            import numpy as np
            upper = bb_mid + bb_mult * bb_mid * 0.05  # 近似
            lower = bb_mid - bb_mult * bb_mid * 0.05
            if current_price < lower:
                signals.append(f"🟢触及布林下轨({lower:.2f}) - 反弹概率高")
            elif current_price > upper:
                signals.append(f"🔴触及布林上轨({upper:.2f}) - 短期超涨")
    
    return signals, stock_params


if __name__ == "__main__":
    print("=== 更新策略参数 ===")
    params = update_params_from_learning()
    print(f"\n最优策略:")
    for code, p in params.get('stocks', {}).items():
        print(f"  {code}: {p['best_strategy']} (胜率{p['win_rate']}%, 得分{p['score']})")
