#!/usr/bin/env python3
"""
盘中监控结果 → 发飞书卡片
有预警才发，无预警静默
"""
import subprocess
import sys
from datetime import datetime

# 读取监控输出
try:
    result = subprocess.run(
        ['python3', '/root/.openclaw/workspace/scripts/stock_realtime_monitor.py'],
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
except Exception as e:
    print(f'监控脚本执行失败: {e}')
    sys.exit(1)

# 检查是否有预警
has_alert = '预警信号' in output and ('⚠️' in output or '🚨' in output or '🔴' in output)

if not has_alert:
    print('✅ 无预警信号，静默')
    sys.exit(0)

# 有预警，写入临时文件并发送卡片
tmp_file = '/tmp/stock_alert.txt'
with open(tmp_file, 'w', encoding='utf-8') as f:
    f.write(output)

now = datetime.now().strftime('%m-%d %H:%M')
title = f'🚨 盘中预警 | {now}'

# 发送卡片
try:
    sub_result = subprocess.run(
        ['python3', '/root/.openclaw/workspace/scripts/card_delivery.py',
         '--title', title,
         '--type', 'stock_alert',
         '--file', tmp_file,
         '--fallback'],
        capture_output=True, text=True, timeout=30
    )
    if sub_result.returncode == 0:
        print(f'✅ 预警卡片已发送')
    else:
        print(f'⚠️ 卡片发送失败: {sub_result.stderr[:200]}')
except Exception as e:
    print(f'⚠️ 卡片发送异常: {e}')

print('处理完成')
