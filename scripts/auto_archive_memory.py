#!/usr/bin/env python3
"""
每月自动归档脚本
每月1日执行，将上月memory/*.md文件打包归档并推送Git
"""

import json
import subprocess
import tarfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
GIT_DIR = Path("/root/.openclaw/workspace")


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def main():
    # 确定上月月份
    now = datetime.now(timezone(timedelta(hours=8)))
    prev = now.replace(day=1) - timedelta(days=1)
    prev_month = prev.strftime("%Y-%m")
    prev_prefix = prev.strftime("%Y-%m")

    archive_name = f"memory-{prev_month}-archive.tar.gz"

    # 找到上月所有.md文件（排除知识库和特殊文件）
    files_to_archive = []
    skip_patterns = ["archive", "learn-db", "stock-knowledge", "memory-index",
                     "memory-clusters", "memory-decay", "memory-evolve",
                     "memory-health", "memory-graph", "heal-log",
                     "heartbeat-state", "cron-backup", "alert-cooldown",
                     "intel-hub", "fish-basin", "trade-journal",
                     "stock-strategy", "knowledge-", "friend-account",
                     "comfyui-", "AI绘", "AI绘画", "agentskills",
                     "comfyui-install", "comfyui-tutorial", "spacex",
                     "广桂月子", "育儿月子", "inspiration", "tdx-troubleshoot",
                     "cron-fault", "deep-dive", "info-priority", "review-ev",
                     "migra"]

    for f in sorted(MEMORY_DIR.glob("*.md")):
        fname = f.name
        # 必须是上月的文件（文件名以 YYYY-MM- 开头且月份匹配）
        if not fname.startswith(prev_prefix + "-"):
            continue
        # 排除知识库和特殊文件
        if any(p in fname for p in skip_patterns):
            continue
        files_to_archive.append(f)

    if not files_to_archive:
        print(f"ℹ️ 上月({prev_month})无memory文件需要归档")
        return

    archive_path = MEMORY_DIR / archive_name

    # 打包
    with tarfile.open(archive_path, "w:gz") as tar:
        for f in files_to_archive:
            tar.add(f, arcname=f.name)

    # 获取大小
    size_kb = archive_path.stat().st_size / 1024

    # 删除原文件
    for f in files_to_archive:
        f.unlink()

    # Git提交
    run_cmd(f"cd {GIT_DIR} && git add {archive_path}")
    run_cmd(f"cd {GIT_DIR} && git add memory/*.md")
    msg = f"自动归档: {prev_month}月memory文件 {len(files_to_archive)}个 ({size_kb:.0f}KB)"
    code, out, err = run_cmd(f'cd {GIT_DIR} && git commit -m "{msg}"')
    if code == 0:
        run_cmd(f"cd {GIT_DIR} && git push origin master && git push github master")
        print(f"✅ {msg}")
        print(f"   归档包: {archive_path.name} ({size_kb:.0f}KB)")
        print(f"   已推送Git")
    else:
        print(f"⚠️ Git提交失败: {err[:200]}")


if __name__ == "__main__":
    main()
