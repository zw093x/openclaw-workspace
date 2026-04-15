---
name: ai-art-master
description: AI 绘画与视频生成专家技能。覆盖 FLUX/SDXL/Midjourney/即梦 等主流模型的提示词工程，3D 模型师专属风格库，Seedance 分镜模板，ComfyUI 工作流指引。触发词：AI绘画、AI出图、视频分镜、提示词优化、FLUX提示词、Midjourney、写实风格、3D渲染风格、概念设计。
license: MIT
metadata:
  author: pengyu
  version: "1.0"
  updated: "2026-04-15"
trigger:
  - AI绘画
  - AI视频
  - AI出图
  - 视频分镜
  - 提示词优化
  - FLUX
  - Midjourney
  - 即梦
  - 写实风格
  - 3D渲染
  - 概念设计
  - 文生图
  - 图生视频
  - ComfyUI
allowed-tools: Read
---

# AI Art Master — AI 绘画与视频生成专家

## 核心定位

**3D 模型师专属的 AI 绘画/视频生成技能。**

结合 FLUX.1 / SDXL / 即梦 / Seedance 四大平台，提供专业的提示词模板和风格指南。

---

## 一、主流模型选择指南

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 高质量概念图/写实角色 | **FLUX.1 Dev** | 手部好、文字渲染强、提示词遵循度高 |
| 风格探索/LORA实验 | **SDXL** | 生态最丰富、LoRA最多 |
| 快速高质量概念图 | **Midjourney V6** | 美学质量最高 |
| 中文场景/文字 | **即梦** | 中文友好、文字渲染好 |
| 专业分镜/运镜控制 | **Seedance 2.0** | 分镜模板最全 |
| 本地高精度渲染 | **ComfyUI + FLUX** | 最高控制力 |

---

## 二、FLUX.1 提示词指南（重点）

### 2.1 提示词结构公式

```
[主体] + [媒介/材质] + [风格] + [环境/背景] + [光影] + [色彩] + [构图] + [质量词]
```

**示例 — 电影感角色：**
```
A lone samurai at dusk, cinematic film still, 35mm anamorphic lens,
dramatic lighting, foggy mountain background, muted earth tones,
rule-of-thirds composition, 8K, masterpiece, film grain
```

**示例 — 3D渲染风格：**
```
Mechanical robot warrior, 3D render, octane render, unreal engine 5,
studio lighting, reflective metallic surface, clean background,
product visualization style, 8K, physically based rendering
```

### 2.2 FLUX 权重语法

| 语法 | 效果 |
|------|------|
| `(word)` | 增强（等效1.1倍） |
| `((word))` | 双重增强（等效1.2倍） |
| `[word]` | 减弱 |
| `(word:1.5)` | 精确权重 |

### 2.3 FLUX 负向提示词模板

```
Deformed, disfigured, bad anatomy, extra limbs,
watermark, text, logo, signature, username, artist name,
blurry, low quality, worst quality, jpeg artifacts,
mutated hands, extra fingers, missing fingers,
cropped, out of frame, duplicate
```

---

## 三、3D 模型师专属风格库

### 3.1 核心风格指南

| 风格 | 关键词 | 适用场景 |
|------|--------|---------|
| **Pixar/3D动画** | `3D render, pixar style, disney animation, smooth shading, vibrant colors` | 角色概念设计 |
| **UE5写实** | `unreal engine 5, real-time render, cinematic, photorealistic, Lumen, Nanite` | 游戏概念 |
| **ZBrush高模** | `zbrush, sculpt, high poly, subdivision surface, detailed topology, 3D coat` | 雕刻参考 |
| **Cinema 4D** | `cinema 4d, octane render, redshift, metallic materials, studio lighting` | 产品可视化 |
| **Blender Cycles** | `blender, cycles render, path tracing, volumetric lighting, bloom` | 综合3D |
| **写实渲染** | `photorealistic, octane render, subsurface scattering, depth of field, tilt-shift` | 照片级渲染 |
| **半风格化** | `stylized 3D, hand-painted textures, toon shading, NPR, cell shaded` | 风格化项目 |

### 3.2 材质与光线关键词

**材质**：
- `metallic, roughness, subsurface scattering, SSS, glass material, refractive`
- `PBR workflow, physically based rendering, ambient occlusion, cavity map`
- `fabric, leather, brushed metal, matte surface, glossy finish`

**光线**：
- `cinematic lighting, volumetric lighting, rim light, backlight`
- `golden hour, blue hour, studio softbox, three-point lighting`
- `HDRI, environment map, god rays, light leaks`

---

## 四、即梦提示词要点

> 详见 `memory/jimeng-precision-library.md` — 即梦精准词库

### 核心公式
**主体特征 + 核心动作 + 运镜/视角 + 时长 + 画面比例**

### 关键规则
- 图片：主体描述越具体越好，避免泛泛形容词
- 视频：动作描述写慢不写快，单一动作优于复杂动作
- 风格：中文风格词精准定位（如"工笔画"、"敦煌配色"）

---

## 五、Seedance 分镜提示词

> 详见 `memory/ai-video-prompt-engineering.md` — 完整分镜模板

### 快速模板
```
【风格】_____风格，_____秒，画幅_____，_____氛围

【时间轴】
0-X 秒：[景别]，[运镜]，[画面描述+主体动作+环境运动]，[声音]
X-Y 秒：[景别]，[运镜]，[画面描述]，[声音]

【声音】配乐，音效，对白
【参考】@图片/视频 引用素材
```

### 景别速查
| 景别 | 关键词 |
|------|--------|
| 远景 | `establishing shot, wide view, aerial view` |
| 全景 | `full body shot, environmental portrait` |
| 中景 | `medium shot, waist up` |
| 近景 | `close-up, bust shot, expression visible` |
| 特写 | `extreme close-up, detail shot` |

---

## 六、ComfyUI + FLUX 工作流

### 6.1 基础文生图流程

```
CheckpointLoader(SDXL/FLUX) → CLIPTextEncode(正) → CLIPTextEncode(负) →
KSampler → VAEDecode → SaveImage
```

### 6.2 FLUX 专用节点（v0.18.0+）

| 节点 | 作用 |
|------|------|
| `FluxLoader` | 加载 FLUX 模型 |
| `FluxGuidance` | 引导尺度控制 |
| `FluxSampling` | 采样配置 |
| `CLIPTextEncode(Flux)` | FLUX 专用文本编码 |

### 6.3 质量提升组合

```
高细节 → `masterpiece, best quality, highly detailed, 8k`
电影感 → `cinematic lighting, film grain, anamorphic lens, depth of field`
写实 → `photorealistic, octane render, physically based rendering`
动漫 → `anime style, cel shading, vibrant colors, clean lineart`
```

---

## 七、参考文件

- `memory/ai-art-research.md` — AI绘画深度研究报告（FLUX/SDXL/Midjourney全面对比）
- `memory/ai-video-prompt-engineering.md` — AI视频提示词工程（Seedance完整模板）
- `memory/jimeng-precision-library.md` — 即梦精准词库
- `memory/comfyui-knowledge.md` — ComfyUI 核心知识
- `skills/comfyui-concept-art/` — ComfyUI 概念艺术工作流

---

## 八、触发场景示例

| 用户需求 | 调用技能 |
|---------|---------|
| 帮我写一个FLUX提示词生成概念图 | FLUX提示词模板 + 3D风格库 |
| 即梦视频脚本怎么写 | 即梦精准词库 + 运镜指南 |
| ComfyUI出图质量不好怎么调 | ComfyUI工作流 + 质量组合 |
| 要一个电影感的角色概念设计 | 电影感关键词 + FLUX公式 |
| 帮我写Seedance分镜 | Seedance时间轴模板 + 景别速查 |
| 3D渲染风格怎么做AI图 | 3D模型师专属风格库 + ComfyUI工作流 |
