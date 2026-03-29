#!/usr/bin/env python3
"""
Cron 任务健康诊断 & 自动修复脚本
用途：检查所有 cron 任务的 delivery 配置，自动补全缺失的 channel/to
使用：python3 scripts/cron_healthcheck.py [--fix]
"""

import json
import sys
import os

JOBS_FILE = "/root/.openclaw/cron/jobs.json"
DEFAULT_CHANNEL = "feishu"
DEFAULT_TO = "ou_a6469ccc2902a590994b6777b9c8ae8f"

def load_jobs():
    with open(JOBS_FILE) as f:
        return json.load(f)

def save_jobs(data):
    with open(JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def check_and_fix(fix=False):
    data = load_jobs()
    jobs = data.get("jobs", [])

    issues = []
    fixed = 0

    for job in jobs:
        job_id = job.get("id", "?")[:8]
        name = job.get("name", "?")
        delivery = job.get("delivery", {})

        # Check delivery.channel
        channel = delivery.get("channel")
        to = delivery.get("to")

        missing = []
        if not channel:
            missing.append("channel")
        if not to:
            missing.append("to")

        if missing:
            issues.append({
                "id": job_id,
                "name": name,
                "missing": missing,
                "current": delivery
            })

            if fix:
                job["delivery"] = {
                    "mode": delivery.get("mode", "announce"),
                    "channel": channel or DEFAULT_CHANNEL,
                    "to": to or DEFAULT_TO
                }
                fixed += 1

    # Report
    print(f"📊 Cron 健康检查报告")
    print(f"{'='*40}")
    print(f"总任务数: {len(jobs)}")
    print(f"配置完整: {len(jobs) - len(issues)}")
    print(f"配置缺失: {len(issues)}")

    if issues:
        print(f"\n⚠️ 缺失配置的任务:")
        for i in issues:
            print(f"  - [{i['id']}] {i['name']}")
            print(f"    缺失: {', '.join(i['missing'])}")
            print(f"    当前: {json.dumps(i['current'], ensure_ascii=False)}")

    if fix and fixed > 0:
        save_jobs(data)
        print(f"\n✅ 已修复 {fixed} 个任务，配置已写入 jobs.json")
        print(f"   需要重启 gateway 才能生效: openclaw gateway restart")
    elif issues and not fix:
        print(f"\n💡 修复方法: python3 {sys.argv[0]} --fix")

    return len(issues)

if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"用法: python3 {sys.argv[0]} [--fix]")
        print(f"  --fix  自动修复缺失的 delivery 配置")
        print(f"  默认只检查，不修改")
        sys.exit(0)

    issues = check_and_fix(fix=fix_mode)
    sys.exit(1 if issues > 0 else 0)
