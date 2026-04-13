---
name: comfyui-concept-art
description: ComfyUI 概念设计文生图工作流。用于快速生成高质量概念艺术图。支持 SDXL/Flux 模型，内置批量生成和质量检查。使用场景：(1) 游戏/影视概念设计 (2) 角色/场景/道具设计 (3) 快速视觉原型 (4) 风格探索。触发词：概念设计、文生图、AI 出图、ComfyUI 出图、批量生成、风格探索。
license: MIT
metadata:
  author: pengyu
  version: "1.0"
  models: SDXL, Flux
  gpu_min: 8GB VRAM
allowed-tools: Bash(comfyui:*) Read Write
---

# ComfyUI 概念设计文生图工作流

## 快速启动

```bash
# 1. 启动 ComfyUI（确保已安装）
python main.py --listen 0.0.0.0 --port 8188

# 2. 执行工作流
python scripts/run_workflow.py \
  --prompt "a majestic dragon on a cliff at sunset, concept art" \
  --model sdxl \
  --resolution 1024x1024 \
  --seed -1
```

## 参数标准

### 必填参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `--prompt` | string | 正面提示词，英文，逗号分隔风格标签 |
| `--model` | enum | 模型选择：`sdxl` / `flux` |

### 可选参数

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| `--negative` | 预设 | string | 负面提示词，见 `references/prompt-library.md` |
| `--sampler` | euler_ancestral | - | 采样器，见 `references/sampler-guide.md` |
| `--steps` | 20 | 15-30 | 采样步数，低于15细节不足 |
| `--cfg` | 7.0 | 5-12 | CFG 引导强度，过高导致过饱和 |
| `--resolution` | 1024x1024 | - | 输出分辨率 |
| `--seed` | -1 | -1 或 0-4294967295 | -1 为随机，固定值可复现 |
| `--batch` | 1 | 1-16 | 批量生成数量 |

## 输出规范

- **格式**：PNG（保留 ComfyUI workflow metadata）
- **命名**：`{project}_{date}_{seq}_{seed}.png`
- **存储**：`output/{project}/{date}/`
- **质量标准**：无明显畸变、主体清晰、符合提示词描述

## 工作流程

```
1. 确定主题和风格 → 参考 references/prompt-library.md 选择模板
2. 选择模型和参数 → 参考 references/model-comparison.md
3. 执行生成 → scripts/run_workflow.py
4. 质量检查 → scripts/quality_check.py（可选）
5. 批量生产 → scripts/batch_generate.py（可选）
```

## 验收场景

```
Given: 提示词 "a warrior standing on a ruined castle, dark fantasy, cinematic lighting"
When:  使用 SDXL 模型，默认参数
Then:  输出 1024×1024 PNG，画面中人物和城堡清晰可见，光影效果符合 cinematic lighting 描述

Given: 使用 Flux 模型生成人物
When:  steps=25, cfg=6.0
Then:  人物面部无畸变，手指正常（Flux 优势）
```

## 常见问题

- **显存不足**：降低分辨率到 768×768，或使用 `--batch 1`
- **画面过饱和**：降低 `--cfg` 到 5-6
- **细节不足**：增加 `--steps` 到 25-30
- **无法复现**：使用固定 `--seed` 值

## 文件引用

- 采样器选择指南：[references/sampler-guide.md](references/sampler-guide.md)
- 提示词模板库：[references/prompt-library.md](references/prompt-library.md)
- 模型对比：[references/model-comparison.md](references/model-comparison.md)
- 批量生成配置：[references/batch-config.md](references/batch-config.md)
