# AI 绘画深度研究报告 v1.0

> 更新日期：2026-04-15
> 信息来源：综合整理（A/B级来源为主）

---

## 一、主流 AI 绘画模型对比（2026年4月）

### 横向对比表

| 模型 | 开发方 | 优势 | 劣势 | 生态 | 适合场景 |
|------|--------|------|------|------|---------|
| **FLUX.1 Pro/Dev** | Black Forest Labs | 文字渲染最强、手部/人体结构好、提示词遵循度高 | 推理速度较慢、Pro闭源 | ComfyUI原生 | 高质量概念图、写实角色 |
| **SDXL** | Stability AI | 生态最丰富、LoRA/ControlNet最多 | 手部问题仍存在、提示词遵循一般 | 极丰富 | 风格探索、LoRA实验 |
| **SD3 Medium** | Stability AI | 质量显著提升、文字渲染改善 | 显存占用高(≥24GB) | 中等 | 精细创作 |
| **Midjourney V6** | Midjourney Inc. | 美学质量最高、社区生态 | 闭源、不可本地化、 Discord依赖 | 封闭 | 快速高质量概念图 |
| **DALL-E 3** | OpenAI | 文字渲染优秀、GPT-4V集成 | 闭源、API成本高 | 中等 | 文字+图片结合场景 |
| **即梦** | 字节跳动 | 中文友好、中文文字渲染 | 视频时长有限 | 国内为主 | 国内项目、中文场景 |

### FLUX.1 深度解析（重点关注）

**发布背景**：Black Forest Labs 成立于2024年，FLUX.1是其首个图像系列模型

**三版本对比**：
| 版本 | 特点 | 适用 |
|------|------|------|
| FLUX.1 Pro | 最高质量，闭源API | 极致质量需求 |
| FLUX.1 Dev | 质量接近Pro，开源可本地部署 | 平衡之选 |
| FLUX.1 Schnell | 4步生成，实时能力 | 快速原型 |

**ComfyUI 支持**：v0.18.0+ 原生集成，节点名称 `FluxLoader` / `FluxGuidance` / `FluxSampling` 系列

**实测优势（相比SDXL）**：
- ✅ 手部畸形大幅减少
- ✅ 文字渲染（word/word）在 prompt 准确时可达可用水平
- ✅ 提示词遵循度高（较少出现"漏元素"）
- ✅ 面部结构稳定性更高
- ❌ 生成速度约 SDXL 的 2-3倍（取决于硬件）

---

## 二、提示词工程最佳实践

### 2.1 提示词结构公式

**通用公式**：主体 → 媒介 → 风格 → 环境 → 光影 → 色彩 → 构图 → 质量修饰

```
[主体] + [媒介/材质] + [风格] + [环境/背景] + [光影] + [色彩] + [构图] + [质量词]
```

**示例（电影感角色）**：
```
A lone samurai at dusk, cinematic film still, 35mm anamorphic lens, 
dramatic lighting, foggy mountain background, muted earth tones, 
rule-of-thirds composition, 8K, masterpiece, film grain
```

**示例（3D渲染风格）**：
```
Cyberpunk character bust, 3D render, octane render, unreal engine 5, 
studio lighting, metallic and leather materials, sharp focus, 
杜邦线细节, 8K resolution, highly detailed
```

### 2.2 权重语法汇总

| 语法 | 效果 | 适用场景 |
|------|------|---------|
| `(word)` | 默认1.1倍权重 | 单次增强 |
| `(word:1.5)` | 1.5倍权重 | 明显强调 |
| `(word:0.6)` | 0.6倍权重 | 减弱 |
| `[word]` | 约0.8倍权重 | 降低（SDXL传统语法） |
| `(word1) AND (word2)` | 两者加权 | 强调组合 |

**FLUX.1 特殊权重语法**：
- FLUX 不支持传统 `()` 权重语法
- 改用 **Soft Constraints**（软约束）：在提示词末尾加 `| word:0.5` 表示弱化
- 或通过 `FluxGuidance` 节点统一控制 cfg 强度

### 2.3 负向提示词模板

**通用负面（SDXL）**：
```
worst quality, low quality, blurry, deformed, disfigured, 
mutated, bad anatomy, wrong anatomy, extra limbs, missing limbs, 
floating limbs, disconnected limbs, malformed hands, 
extra fingers, fewer fingers, fused fingers, crossed eyes, 
jpeg artifacts, noise, oversaturated, underexposed
```

**FLUX.1 负面提示词（简化版）**：
```
blurry, distorted, low quality, deformed, ugly, bad anatomy
```
> 注意：FLUX.1 对负面提示词依赖较低，过多反而影响质量

**动漫风格负面**：
```
realistic, photorealistic, 3D render, cgi, 
human skin, realistic eyes, realistic hair
```

---

## 三、风格研究深度指南

### 3.1 风格词汇库

| 风格 | 关键词 | 适用场景 |
|------|--------|---------|
| **写实摄影** | `photorealistic, hyperrealistic, 8K, shot on Canon EOS R5, natural lighting` | 产品/人物/建筑 |
| **电影感** | `cinematic lighting, film grain, anamorphic, 35mm lens, shallow DOF, dramatic` | 氛围场景/概念图 |
| **动漫/二次元** | `anime style, cel shading, vibrant colors, studio ghibli, crisp lineart` | 角色/插画 |
| **插画/原画** | `digital illustration, artstation trending, vibrant, detailed` | 概念设定/海报 |
| **3D/CG** | `3D render, octane render, redshift, unreal engine 5, Pixar style, zbrush sculpt` | 产品/角色/场景 |
| **油画** | `oil painting, impressionist, brushstrokes visible, canvas texture` | 艺术创作 |
| **水彩** | `watercolor painting, soft edges, paper texture, delicate` | 艺术插画 |
| **建筑摄影** | `architectural photography, wide angle, clean lines, minimalism` | 建筑/室内 |

### 3.2 3D模型师专项风格（重点）

**Pixar/Disney风格**：
```
Pixar style, 3D animated film look, toon shading, 
bright colors, volumetric lighting, disney animation quality
```

**Unreal Engine实时渲染**：
```
Unreal Engine 5, real-time rendering, Lumen, Nanite, 
game engine quality, cinematic, hyperdetailed
```

**ZBrush高精度雕刻感**：
```
zbrush sculpt, digital clay, high poly sculpture, 
substance painter materials, detailed surface texture
```

**写实渲染三要素**：
```
physically based rendering, subsurface scattering, 
caustics, ambient occlusion, realistic fabric simulation
```

---

## 四、ControlNet/可控性深度指南

### 4.1 主流ControlNet类型

| 类型 | 检测器 | 控制内容 | 适用场景 |
|------|--------|---------|---------|
| **Canny** | Canny边缘检测 | 硬边缘线条 | 线稿上色、建筑、精确构图 |
| **Depth (MiDaS)** | 深度估计 | 空间/Z深度结构 | 场景重建、纵深控制 |
| **Depth (ZoeDepth)** | 相对深度 | 更细腻的深度关系 | 室内、多物体场景 |
| **OpenPose** | 骨骼+手+脸 | 全身姿态/表情 | 角色动作控制 |
| **Normal Map** | 法线估计 | 表面凹凸细节 | 材质编辑、3D辅助 |
| **SoftEdge** | HED边缘 | 软边界+主体轮廓 | 场景、人物、通用 |
| **Lineart** | 线稿提取 | 精确线条 | 动漫线稿上色 |
| **MLSD** | 建筑线条 | 直线检测 | 建筑、室内 |
| **Tile/Blur** | 分块+模糊 | 细节/背景控制 | 细节增强、重绘 |
| **IP2P** | 指令理解 | 风格迁移 | "make it X style" |

### 4.2 ComfyUI ControlNet 工作流

```
LoadImage(ControlNet输入) → ControlNet预处理(Apply) → 
[Checkpoint] → [CLIP] → [ControlNet] → [Sampler] → [VAE] → [Image]
```

**关键节点**：
- `ControlNetApply (Advanced)`：支持 strength / start_percent / end_percent 控制
- `ControlNetWeight`：多 ControlNet 加权叠加
- `ControlNetStack`：串联多个 ControlNet

### 4.3 3D建模辅助工作流（重点）

**输入图 → 3D模型 流水线**：
```
输入参考图
    ↓
[ControlNet: Canny/Depth] 精修构图
    ↓
[图生图: 增强特征] 提升结构清晰度
    ↓
[Tripo3D / Hunyuan3D] 生成3D模型
    ↓
[Blender] 手动精修 + 材质/UV
```

**ControlNet选型建议**：
- 角色模型参考 → OpenPose（姿态）+ Canny（轮廓）
- 产品模型参考 → Depth（空间感）+ Normal（表面细节）
- 建筑模型参考 → MLSD（直线）+ Depth（纵深）

---

## 五、主流工具精选推荐

### AI 绘画工具矩阵

| 工具 | 定位 | 推荐指数 | 备注 |
|------|------|---------|------|
| **ComfyUI** | 本地工作流 | ⭐⭐⭐⭐⭐ | 最强可控性，3D+AI工作流首选 |
| **FLUX.1 (Dev)** | 开源最强质量 | ⭐⭐⭐⭐⭐ | ComfyUI原生，替代SDXL首选 |
| **Midjourney** | 快速高质量 | ⭐⭐⭐⭐ | 闭源，美学质量高 |
| **即梦** | 国内中文场景 | ⭐⭐⭐⭐ | 中文友好，视频能力 |
| **Stable Diffusion WebUI** | 生态丰富 | ⭐⭐⭐ | 功能全但比ComfyUI可控性低 |

### AI 视频工具矩阵

| 工具 | 定位 | 推荐指数 | 核心优势 |
|------|------|---------|---------|
| **Runway Gen-3** | 电影级视频 | ⭐⭐⭐⭐⭐ | 运镜精准、文字渲染、高画质 |
| **Sora** | 世界模拟 | ⭐⭐⭐⭐⭐ | 60秒、复杂场景、物理理解 |
| **Pika 2.0** | 角色一致性 | ⭐⭐⭐⭐ | 角色保持、运动平滑 |
| **ComfyUI Video** | 本地可控 | ⭐⭐⭐⭐ | 节点工作流，视频预处理 |
| **Seedance 2.0** | 分镜专家 | ⭐⭐⭐⭐ | 运镜精准、模板丰富 |
| **即梦视频** | 国内生态 | ⭐⭐⭐ | 快速生成、中文支持 |

---

## 六、信息可靠性分级（2026-04-15 更新说明）

| 等级 | 来源 | 适用内容 |
|------|------|---------|
| A | 官方GitHub/论文/官方公告 | 模型架构、版本更新、节点变更 |
| B | arXiv preprint、权威媒体 | 技术原理、模型对比趋势 |
| C | Civitai模型页、社区经验 | LoRA推荐、参数调优 |
| D | 教程视频、自媒体 | 入门指南、非关键技术 |

**本文档内容来源**：综合整理自 ComfyUI 官方文档、Black Forest Labs 官方公告、Stability AI 官方更新、权威技术博客（A/B级为主），时间为2026年4月快照。

---

## 七、关联知识库文件

- `comfyui-knowledge.md` — ComfyUI 核心架构与3D节点生态
- `ai-video-prompt-engineering.md` — AI视频提示词工程（ComfyUI+即梦+Seedance）
- `jimeng-prompt-library.md` — 即梦提示词库（1000+词）
- `comfyui-concept-art/SKILL.md` — ComfyUI概念艺术技能
- `skills/comfyui-concept-art/` — 完整技能目录
