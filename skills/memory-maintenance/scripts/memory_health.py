#!/usr/bin/env python3
"""
记忆健康检查脚本
检查记忆文件的完整性、大小、格式是否正常。

用法:
    python memory_health.py
    python memory_health.py --fix  # 自动修复可修复的问题
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/root/.openclaw/workspace"))


def check_memory_size(memory_path: Path) -> dict:
    """检查 MEMORY.md 大小"""
    if not memory_path.exists():
        return {"status": "error", "message": "MEMORY.md 不存在"}
    
    content = memory_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    size_kb = len(content.encode("utf-8")) / 1024
    
    issues = []
    if len(lines) > 200:
        issues.append(f"行数过多 ({len(lines)} > 200)，建议精简")
    if size_kb > 30:
        issues.append(f"体积过大 ({size_kb:.1f}KB > 30KB)，建议拆分")
    
    return {
        "status": "warn" if issues else "pass",
        "lines": len(lines),
        "size_kb": round(size_kb, 1),
        "issues": issues,
    }


def check_daily_files(memory_dir: Path) -> dict:
    """检查每日文件完整性"""
    if not memory_dir.exists():
        return {"status": "error", "message": "memory/ 目录不存在"}
    
    daily_files = sorted(memory_dir.glob("????-??-??.md"))
    if not daily_files:
        return {"status": "warn", "message": "无每日记录文件"}
    
    # 检查最近7天是否有缺失
    today = datetime.now()
    missing = []
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        expected = memory_dir / f"{date}.md"
        if not expected.exists():
            missing.append(date)
    
    # 检查文件大小（空文件或过小）
    tiny_files = []
    for f in daily_files[-7:]:
        size = f.stat().st_size
        if size < 50:
            tiny_files.append(f.name)
    
    issues = []
    if missing:
        issues.append(f"最近7天缺失: {', '.join(missing)}")
    if tiny_files:
        issues.append(f"文件过小 (<50B): {', '.join(tiny_files)}")
    
    return {
        "status": "warn" if issues else "pass",
        "total_files": len(daily_files),
        "oldest": daily_files[0].name if daily_files else None,
        "newest": daily_files[-1].name if daily_files else None,
        "issues": issues,
    }


def check_state_files(memory_dir: Path) -> dict:
    """检查 JSON 状态文件格式"""
    json_files = list(memory_dir.glob("*.json"))
    if not json_files:
        return {"status": "pass", "message": "无状态文件"}
    
    issues = []
    for f in json_files:
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            issues.append(f"{f.name}: JSON 格式错误 - {e}")
    
    return {
        "status": "fail" if issues else "pass",
        "total": len(json_files),
        "issues": issues,
    }


def check_learnings() -> dict:
    """检查 .learnings/ 目录"""
    learnings_dir = WORKSPACE / ".learnings"
    if not learnings_dir.exists():
        return {"status": "pass", "message": ".learnings/ 不存在（非必须）"}
    
    files = list(learnings_dir.glob("*.md"))
    entries = 0
    for f in files:
        content = f.read_text(encoding="utf-8")
        entries += content.count("## ")  # 统计条目数
    
    return {
        "status": "pass",
        "files": len(files),
        "entries": entries,
    }


def main():
    parser = argparse.ArgumentParser(description="记忆健康检查")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")
    args = parser.parse_args()
    
    memory_path = WORKSPACE / "MEMORY.md"
    memory_dir = WORKSPACE / "memory"
    
    print("=" * 50)
    print("  记忆健康检查")
    print("=" * 50)
    
    checks = [
        ("MEMORY.md 大小", check_memory_size(memory_path)),
        ("每日文件完整性", check_daily_files(memory_dir)),
        ("状态文件格式", check_state_files(memory_dir)),
        ("学习记录", check_learnings()),
    ]
    
    all_pass = True
    for name, result in checks:
        status = result["status"]
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "error": "🔴"}.get(status, "❓")
        
        if status != "pass":
            all_pass = False
        
        print(f"\n{icon} {name}")
        for key, value in result.items():
            if key not in ("status", "issues"):
                print(f"   {key}: {value}")
        for issue in result.get("issues", []):
            print(f"   → {issue}")
    
    print(f"\n{'=' * 50}")
    if all_pass:
        print("  总体状态: ✅ 健康")
    else:
        print("  总体状态: ⚠️ 有问题需要关注")


if __name__ == "__main__":
    main()
