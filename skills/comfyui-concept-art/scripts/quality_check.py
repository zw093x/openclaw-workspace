#!/usr/bin/env python3
"""
ComfyUI 输出质量检查脚本
检查生成图片的分辨率、文件大小、是否存在明显问题。

用法:
    python quality_check.py --input-dir output/batch_001
    python quality_check.py --input-dir output/batch_001 --min-size 100000 --expected-resolution 1024x1024
"""

import argparse
import os
import sys
from pathlib import Path


def check_image(filepath: str, min_size: int, expected_res: tuple) -> dict:
    """检查单张图片"""
    result = {
        "file": filepath,
        "status": "pass",
        "issues": []
    }

    # 文件大小检查
    size = os.path.getsize(filepath)
    result["size_kb"] = round(size / 1024, 1)
    if size < min_size:
        result["status"] = "fail"
        result["issues"].append(f"文件过小 ({result['size_kb']}KB < {min_size/1024}KB)，可能生成失败")

    # 分辨率检查（需要 PIL）
    try:
        from PIL import Image
        img = Image.open(filepath)
        result["resolution"] = f"{img.width}x{img.height}"

        if expected_res and (img.width != expected_res[0] or img.height != expected_res[1]):
            result["status"] = "warn"
            result["issues"].append(f"分辨率不符: {result['resolution']} (期望 {expected_res[0]}x{expected_res[1]})")

        # 检查是否纯色（可能生成失败）
        colors = img.getcolors(maxcolors=2)
        if colors and len(colors) <= 2:
            result["status"] = "fail"
            result["issues"].append("图片几乎为纯色，生成可能失败")

    except ImportError:
        result["issues"].append("未安装 PIL，跳过分辨率检查")
    except Exception as e:
        result["status"] = "fail"
        result["issues"].append(f"无法打开图片: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 输出质量检查")
    parser.add_argument("--input-dir", required=True, help="图片目录")
    parser.add_argument("--min-size", type=int, default=50000, help="最小文件大小 (bytes)")
    parser.add_argument("--expected-resolution", default="1024x1024", help="期望分辨率")
    parser.add_argument("--output-report", default=None, help="输出报告路径")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"错误: 目录不存在 {input_dir}")
        sys.exit(1)

    expected_res = None
    if args.expected_resolution:
        w, h = args.expected_resolution.split("x")
        expected_res = (int(w), int(h))

    # 收集所有图片
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = sorted([
        f for f in input_dir.rglob("*")
        if f.suffix.lower() in image_exts
    ])

    if not images:
        print("未找到图片文件")
        sys.exit(0)

    print(f"[QC] 检查 {len(images)} 张图片...")

    results = []
    pass_count = 0
    warn_count = 0
    fail_count = 0

    for img_path in images:
        result = check_image(str(img_path), args.min_size, expected_res)
        results.append(result)

        if result["status"] == "pass":
            pass_count += 1
            icon = "✅"
        elif result["status"] == "warn":
            warn_count += 1
            icon = "⚠️"
        else:
            fail_count += 1
            icon = "❌"

        print(f"  {icon} {img_path.name} ({result['size_kb']}KB) - {result.get('resolution', 'N/A')}")
        for issue in result["issues"]:
            print(f"     → {issue}")

    # 汇总
    print(f"\n[QC] 结果: ✅ {pass_count} 通过 | ⚠️ {warn_count} 警告 | ❌ {fail_count} 失败")

    # 输出报告
    if args.output_report:
        import json
        report = {
            "total": len(images),
            "pass": pass_count,
            "warn": warn_count,
            "fail": fail_count,
            "details": results,
        }
        with open(args.output_report, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[QC] 报告已保存: {args.output_report}")

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
