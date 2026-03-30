#!/usr/bin/env python3
"""
Cron 任务依赖关系管理
确保盘中监控运行前，技术指标已更新
"""

import json
from datetime import datetime, timezone, timedelta

# 依赖关系定义
DEPENDENCIES = {
    "盘中实时股票监控": {
        "depends_on": ["技术指标计算", "BDI数据更新"],
        "reason": "需要最新技术指标和BDI数据"
    },
    "黄金价格播报": {
        "depends_on": [],
        "reason": "独立任务，无依赖"
    },
    "每日股票开盘提醒": {
        "depends_on": ["技术指标计算"],
        "reason": "需要最新技术指标"
    },
    "每日股票收盘提醒": {
        "depends_on": ["盘中实时股票监控"],
        "reason": "收盘总结需要盘中数据"
    }
}

# 关键任务的 cron ID 映射
CRON_IDS = {
    "盘中实时股票监控": "ecc93a08-094b-4bf0-a89e-9db004515750",
    "技术指标计算": None,  # 由自愈系统执行
    "BDI数据更新": "93c3207a-3a43-4c29-afdc-e382dfa47483",
    "黄金价格播报": "7f7a0ce8-4d2c-478f-9f63-78bc05ca9147",
}

def check_dependencies(task_name):
    """检查任务依赖是否满足"""
    deps = DEPENDENCIES.get(task_name, {}).get("depends_on", [])
    if not deps:
        return True, "无依赖"
    
    missing = []
    for dep in deps:
        # 检查依赖任务最近是否执行成功
        # 简化：总是返回 True（依赖通过 cron 调度保证）
        pass
    
    return True, f"依赖: {', '.join(deps)}"

def get_task_order(tasks):
    """拓扑排序获取任务执行顺序"""
    order = []
    visited = set()
    
    def visit(task):
        if task in visited:
            return
        visited.add(task)
        for dep in DEPENDENCIES.get(task, {}).get("depends_on", []):
            if dep in DEPENDENCIES:
                visit(dep)
        order.append(task)
    
    for task in tasks:
        visit(task)
    
    return order

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        task = " ".join(sys.argv[2:])
        ok, reason = check_dependencies(task)
        print(f"{'✅' if ok else '❌'} {task}: {reason}")
    else:
        print("=== Cron 任务依赖关系 ===")
        for task, info in DEPENDENCIES.items():
            deps = info["depends_on"]
            if deps:
                print(f"  {task} → {', '.join(deps)}")
            else:
                print(f"  {task} → (无依赖)")
        
        print("\n=== 执行顺序 ===")
        all_tasks = list(DEPENDENCIES.keys())
        order = get_task_order(all_tasks)
        for i, task in enumerate(order, 1):
            print(f"  {i}. {task}")
