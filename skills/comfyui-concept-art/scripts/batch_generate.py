#!/usr/bin/env python3
"""
ComfyUI 批量生成脚本
从配置文件或提示词列表批量生成概念图。

用法:
    python batch_generate.py --config batch_config.yaml
    python batch_generate.py --prompts-file prompts.txt --model sdxl --count 4
"""

import argparse
import json
import os
import sys
import subprocess
import yaml
from pathlib import Path
from datetime import datetime


def load_prompts(args) -> list:
    """加载提示词列表"""
    if args.config:
        with open(args.config) as f:
            config = yaml.safe_load(f)
        return config
    elif args.prompts_file:
        with open(args.prompts_file) as f:
            prompts = [line.strip() for line in f if line.strip()]
        return {
            "model": args.model,
            "prompts": prompts,
            "count_per_prompt": args.count,
            "resolution": args.resolution,
            "sampler": args.sampler,
            "steps": args.steps,
            "cfg": args.cfg,
            "output_dir": args.output_dir,
        }
    else:
        print("错误: 需要 --config 或 --prompts-file")
        sys.exit(1)


def run_single(prompt: str, config: dict, seq: int, total: int) -> str:
    """执行单次生成"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    project = config.get("project", "concept")
    naming = config.get("naming_pattern", "{project}_{date}_{seq}_{seed}")

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_workflow.py"),
        "--prompt", prompt,
        "--model", config.get("model", "sdxl"),
        "--resolution", config.get("resolution", "1024x1024"),
        "--sampler", config.get("sampler", "euler_ancestral"),
        "--steps", str(config.get("steps", 20)),
        "--cfg", str(config.get("cfg", 7.0)),
        "--seed", str(-1),
        "--output-dir", config.get("output_dir", "output"),
    ]

    print(f"[Batch] ({seq}/{total}) 提示词: {prompt[:60]}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[Batch] 错误: {result.stderr}")
        return None

    print(f"[Batch] 完成")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 批量生成")
    parser.add_argument("--config", help="配置文件路径 (YAML)")
    parser.add_argument("--prompts-file", help="提示词文件路径 (每行一个)")
    parser.add_argument("--model", default="sdxl", choices=["sdxl", "flux"])
    parser.add_argument("--count", type=int, default=4, help="每个提示词生成数量")
    parser.add_argument("--resolution", default="1024x1024")
    parser.add_argument("--sampler", default="euler_ancestral")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=7.0)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    config = load_prompts(args)
    prompts = config.get("prompts", [])
    count = config.get("count_per_prompt", args.count)

    total = len(prompts) * count
    print(f"[Batch] 共 {len(prompts)} 个提示词，每个生成 {count} 次，总计 {total} 张")
    print(f"[Batch] 模型: {config.get('model', 'sdxl')}")
    print(f"[Batch] 输出: {config.get('output_dir', 'output')}")

    seq = 0
    for prompt in prompts:
        for _ in range(count):
            seq += 1
            run_single(prompt, config, seq, total)

    print(f"\n[Batch] 全部完成! 共生成 {seq} 张")


if __name__ == "__main__":
    main()
