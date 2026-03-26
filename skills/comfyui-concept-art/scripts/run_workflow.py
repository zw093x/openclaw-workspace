#!/usr/bin/env python3
"""
ComfyUI 工作流执行脚本
通过 API 连接本地 ComfyUI 实例并执行工作流。

用法:
    python run_workflow.py --prompt "a dragon" --model sdxl --resolution 1024x1024
"""

import argparse
import json
import urllib.request
import urllib.parse
import uuid
import time
import os
from pathlib import Path


def load_workflow_template(model: str) -> dict:
    """加载工作流模板"""
    template_path = Path(__file__).parent.parent / "assets" / f"workflow_{model}.json"
    if not template_path.exists():
        # 回退到默认模板
        template_path = Path(__file__).parent.parent / "assets" / "workflow_sdxl.json"
    with open(template_path) as f:
        return json.load(f)


def inject_params(workflow: dict, args) -> dict:
    """将命令行参数注入工作流"""
    # 替换提示词
    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if class_type == "CLIPTextEncode":
            if "text" in inputs:
                if "POSITIVE" in str(node_id).upper() or "positive" in str(inputs):
                    inputs["text"] = args.prompt
                elif "NEGATIVE" in str(node_id).upper() or "negative" in str(inputs):
                    inputs["text"] = args.negative
        elif class_type == "KSampler":
            inputs["sampler_name"] = args.sampler
            inputs["steps"] = args.steps
            inputs["cfg"] = args.cfg
            inputs["seed"] = args.seed if args.seed >= 0 else int(uuid.uuid4().int % 2**32)
        elif class_type == "EmptyLatentImage":
            w, h = args.resolution.split("x")
            inputs["width"] = int(w)
            inputs["height"] = int(h)

    return workflow


def queue_prompt(workflow: dict, server: str) -> str:
    """提交工作流到 ComfyUI"""
    client_id = str(uuid.uuid4())
    payload = json.dumps({
        "prompt": workflow,
        "client_id": client_id
    }).encode()

    req = urllib.request.Request(
        f"http://{server}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result["prompt_id"]


def wait_result(prompt_id: str, server: str, timeout: int = 300) -> list:
    """等待生成完成并返回输出文件路径"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"http://{server}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    images = []
                    for node_out in outputs.values():
                        if "images" in node_out:
                            images.extend([
                                img["filename"]
                                for img in node_out["images"]
                            ])
                    return images
        except:
            pass
        time.sleep(1)
    raise TimeoutError(f"生成超时（{timeout}s）")


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 概念设计工作流")
    parser.add_argument("--prompt", required=True, help="正面提示词")
    parser.add_argument("--negative", default="", help="负面提示词")
    parser.add_argument("--model", default="sdxl", choices=["sdxl", "flux"], help="模型选择")
    parser.add_argument("--sampler", default="euler_ancestral", help="采样器")
    parser.add_argument("--steps", type=int, default=20, help="采样步数")
    parser.add_argument("--cfg", type=float, default=7.0, help="CFG 引导强度")
    parser.add_argument("--resolution", default="1024x1024", help="输出分辨率")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子（-1=随机）")
    parser.add_argument("--server", default="127.0.0.1:8188", help="ComfyUI 服务器地址")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--batch", type=int, default=1, help="批量生成数量")
    args = parser.parse_args()

    print(f"[ComfyUI] 模型: {args.model}")
    print(f"[ComfyUI] 提示词: {args.prompt}")
    print(f"[ComfyUI] 参数: steps={args.steps}, cfg={args.cfg}, resolution={args.resolution}")

    for i in range(args.batch):
        print(f"\n[ComfyUI] 生成 {i+1}/{args.batch}...")

        workflow = load_workflow_template(args.model)
        workflow = inject_params(workflow, args)

        try:
            prompt_id = queue_prompt(workflow, args.server)
            print(f"[ComfyUI] 已提交: {prompt_id}")

            images = wait_result(prompt_id, args.server)
            print(f"[ComfyUI] 完成! 输出文件: {images}")
        except Exception as e:
            print(f"[ComfyUI] 错误: {e}")


if __name__ == "__main__":
    main()
