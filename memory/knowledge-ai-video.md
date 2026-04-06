# AI视频生成深度知识库
> 基于Sora/AnimateDiff/Rectified Flow三篇核心论文 + 豆包AI绘画提示词课程
> 整合：论文原理 + 提示词工程 + ComfyUI实践
> 更新：2026-04-06

---

## 核心认知（必读）

> AI绘画/视频提示词 ≠ 写文案，而是通过文本精准对齐模型的**视觉语义、空间逻辑、风格范式**，以及视频的**时序连贯性、运动规律与镜头叙事逻辑**，最终实现生成效果的可控化、可复现化、最优化。

---

## 一、扩散模型基础（前置知识）

### 1.1 扩散模型原理

```
训练：图片 + 噪声 → 模型学习预测噪声
推理：从纯噪声开始 → 逐步去噪 → 生成清晰图片
```

**与GAN的区别**：GAN一次生成（不稳定），扩散模型逐步生成（稳定），但推理慢（100-1000步）。

### 1.2 CLIP — 文本到视觉的桥梁

```
论文：Learning Transferable Visual Models From Natural Language Supervision (2021)

核心：CLIP = Contrastive Language-Image Pre-training

训练：大规模图文对（400M）→ 对比学习
  - 文本编码器：Transformer (63M params, 12 layers)
  - 图像编码器：ViT (86M params)
  - 目标：图文配对 → 高相似度；图文不配对 → 低相似度

推理：给定文本 → 编码 → 映射到视觉特征空间 → 控制生成

提示词 → CLIP编码 → 视觉特征 → 扩散模型生成

关键：提示词的本质是"给CLIP提供无歧义的视觉锚点"
```

### 1.3 视频生成的特殊挑战

| 挑战 | 描述 |
|------|------|
| 时间一致性 | 帧与帧之间要连贯，不能跳变 |
| 长视频 | 显存随帧数线性增长 |
| 运动自然 | 物理运动要符合常识 |
| 文本对齐 | 动作与描述要匹配 |

---

## 二、干线提示词工程（豆包课程精华）

### 2.1 主流模型提示词逻辑对比

**必须先选定1个模型深耕，不同模型混学会导致效果失控。**

| 模型类型 | 代表 | 提示词逻辑 | 适用场景 |
|---------|------|-----------|---------|
| 闭源创意 | Midjourney / DALL-E 3 | 自然语言长句优先，依赖模型原生语义理解 | 创意设计、商业插画、快速出图 |
| 开源可控 | SD / SDXL / Flux | **结构化关键词+权重**，反向提示词至关重要 | 专业精细化创作、本地化部署 |
| 长视频 | Sora | 电影级完整叙事文本，多镜头自然语言 | 长视频叙事、影视级 |
| 短视频 | Pika / Runway Gen-3 | 精准动作+镜头描述，图生视频 | 短视频、动态海报 |
| 开源视频 | SVD / AnimateDiff | 兼容SD体系，需配合运动模块 | 可控动画、本地创作 |

### 2.2 万能提示词框架（六段式）

**按权重优先级排序，核心主体放最前端：**

```
核心主体（带核心特征权重） + 场景环境 + 构图视角 + 光影色调 + 视觉风格 + 画质标准
```

**示例（AnimateDiff风格）：**
```
(1girl:1.3), (long flowing dress:1.1), walking forward through ancient chinese palace, 
cherry blossoms falling slowly, golden sunset light, volumetric fog, anime style, 
cinematic composition, 8K ultra detailed, soft color palette, bokeh depth
```

### 2.3 SD权重语法

| 语法 | 作用 | 示例 |
|------|------|------|
| `(关键词)` | 提升权重 | `(cat)` 强化猫 |
| `[关键词]` | 降低权重 | `[cat]` 弱化猫 |
| `(关键词:1.2)` | 精准权重赋值 | `(cat:1.3)` 权重1.3 |
| `((关键词))` | 叠加提升 | 等价于权重×1.1² |

**权重分配原则：**
- 核心主体：1.2-1.5
- 关键风格：1.1-1.3
- 次要元素：0.8-1.0
- 画质层：0.9-1.0

> **核心规则：前置权重＞后置权重，关键词越多越稀释核心语义**

### 2.4 关键参数

| 参数 | 说明 | 常规范围 |
|------|------|---------|
| CFG Scale | 提示词遵从度，过低跑题、过高过饱和 | 7-12 |
| 采样器 | DPM++ 2M Karras（精细）/ Euler a（快速） | — |
| 采样步数 | SD=20-30步 / SDXL=30-50步 | — |
| Seed | 固定种子做对照实验，实现效果复现 | — |

### 2.5 反向提示词（解决80%画面崩坏）

**三类模板：**
```
画质低质类：worst quality, low quality, blurry, jpeg artifacts, noise
主体崩坏类：deformed, bad anatomy, extra fingers, missing limbs, mutated
画面干扰类：watermark, text, logo, signature, username, crop
```

### 2.6 风格锁定三要素

三者结合才能避免风格跑偏：

| 要素 | 示例 |
|------|------|
| 艺术家/IP风格 | 宫崎骏、莫奈、新海诚、Moebius |
| 艺术流派 | 印象派、赛博朋克、国潮水墨、浮世绘 |
| 媒介材质 | 油画、水彩、C4D渲染、OC渲染、胶片摄影 |

**进阶能力：** 固定种子 + 固定风格关键词 + 固定参数 → 仅改主体/场景 → 实现系列风格一致性

### 2.7 构图·光影·空间专业术语

**构图：**
- 景别：特写、近景、中景、全景、远景
- 镜头类型：广角、长焦、微距、鱼眼
- 构图方式：三分法、对称构图、引导线构图、框架构图
- 视角：平视、俯视、仰视、鸟瞰、虫视

**光影：**
- 光源类型：逆光、侧光、伦勃朗光、丁达尔效应
- 光线质感：柔和漫射光、硬光、边缘光
- 色调：暖色调、冷色调、莫兰迪色系、赛博霓虹

---

## 三、可控生成三大技术

### 3.1 模型/LoRA适配

> 新手最易踩坑：下载模型必须查看作者说明，加入专属触发词才能激活模型能力。

### 3.2 ControlNet（构图精准控制）

```
提示词负责：风格、光影、画质
ControlNet负责：构图、结构、姿态

常用ControlNet类型：
  - 线稿控制（canny / softedge）：保持轮廓结构
  - 深度图控制（depth）：保持空间深度关系
  - 姿态控制（openpose）：精准人体姿态
  - 语义分割（seg）：分区控制不同区域
  - 法线图（normal）：表面凹凸细节
```

**视频ControlNet：**
- TemporalNet：跨帧姿态一致性控制
- I2V（Image to Video）：图生视频，保持原图结构
- Video ControlNet：光流引导，保持时间连贯性

### 3.3 区域提示词

给画面不同分区写独立提示词，适配多主体复杂场景。

---

## 四、Sora — Video Generation as World Simulators（2024-02）

### 核心创新

**架构：DiT（Diffusion Transformer）**

- 视频 → 时空Patches → Transformer处理
- 视频压缩网络（类似VAE，但同时压缩时间+空间）
- 最长60秒，支持任意分辨率/宽高比
- 世界模拟能力：碰撞、液体流动、3D一致性

### 对P工的价值

- 长视频生成标杆
- 电影级多镜头叙事基础
- DiT架构是Flux / Stable Video底层

---

## 五、AnimateDiff — Motion Module（立即可用⭐⭐⭐）

### 核心原理

**AnimateDiff = 冻结的SD + 可学习的Motion Module**

```
[冻结SD] + [新插入Motion Module] = 输出动画帧序列

Motion Module = 3D卷积 + Temporal Attention
  - 3D卷积：提取时序运动特征
  - Temporal Attention：帧间注意力，保持连贯性
  - 不改变SD权重 → 保持图像质量
```

### AnimateDiff提示词要点（与图片的区别）

| 要点 | 说明 |
|------|------|
| 主体固定 | 换场景不换主体 |
| 环境词单一 | 多环境词导致帧间不一致 |
| 动作词放主体后 | `(1girl), walking, cherry blossoms` |
| 帧数建议 | 16-32帧（更短更稳定） |
| Motion LoRA强度 | 0.7-0.9（太高形变） |

### 推荐参数组合

**AnimateDiff + LCM（最实用，速度最快）：**
```
Steps: 4-8步（LCM专用）
CFG: 1.0-2.0（LCM低CFG）
Denoise: 1.0（全强度）
帧数: 16-24帧
```

---

## 六、Rectified Flow — 加速推理

### 核心思想

```
传统扩散：曲折路径，100-1000步
Rectified Flow：直线路径，4-8步

原理：最优传输理论（Optimal Transport）
→ 将噪声到数据的路径"拉直"
```

### ComfyUI节点对应

| 模型 | 步数 | ComfyUI节点 |
|------|------|------------|
| 标准SD | 100步 | KSampler |
| SD+DDIM | 20步 | KSampler（ddim）|
| LCM | 2-8步 | LCM Loader |
| SDXL-Turbo | 1-4步 | SDXL-Turbo |

---

## 七、ComfyUI节点地图

| 底层技术 | ComfyUI节点 | 用途 |
|---------|------------|------|
| Latent Diffusion | KSampler / KSamplerAdvanced | 采样器核心 |
| CLIP Text Encoder | CLIP Text Encode | 文本条件注入 |
| VAE | VAE Decode / VAE Encode | 潜空间↔像素 |
| Motion Module | AnimateDiff / Animatediff Community | 运动生成 |
| LCM | LCM / LCM Loader | 快速采样（2-8步） |
| SDXL-Turbo | SDXL-Turbo / TurboVision | 1-4步生成 |
| ControlNet | ControlNet Apply / Stacker | 条件控制 |
| IP-Adapter | IPAdapter | 图像条件 |
| Regional Prompter | Regional Prompter | 分区提示词 |

---

## 八、AI视频提示词词库（镜头运动）

| 效果 | 提示词 |
|------|--------|
| 慢速平移 | `slow pan left/right` |
| 推进/拉远 | `dolly in/out` |
| 跟踪镜头 | `tracking shot` |
| 固定 | `static / locked off` |
| 缩放 | `zoom in/out` |
| 环绕 | `slow orbit` |
| 升格慢动作 | `slow motion, cinematic slow motion` |
| 镜头推进 | `camera push in slowly` |
| 风拂发 | `wind blows hair gently` |
| 烟雾升腾 | `smoke rises slowly` |
| 水波荡漾 | `water rippling` |
| 粒子飘散 | `particles drifting in air` |

---

## 九、技术路线全景图

| 路线 | 代表 | 成熟度 | P工价值 |
|------|------|--------|--------|
| DiT/Transformer | Sora、Stable Video | 发展中 | 长期储备 |
| 扩散+运动模块 | AnimateDiff | ⭐⭐⭐可用 | **立即可用** |
| 一致性模型 | LCM、SDXL-Turbo | ⭐⭐⭐可用 | **立即可用** |
| 3D Gaussian | 3DGS | ⭐⭐发展中 | AI+3D工作流 |
| 光流引导 | I2VGen-XL | ⭐发展中 | 图像动画化 |

---

## 十、必读论文清单

| 论文 | 年 | 状态 | 核心贡献 |
|------|---|------|---------|
| CLIP | 2021 | ✅ | 文本-视觉对齐基础 |
| Latent Diffusion | 2021 | ✅ | SD开山，潜空间扩散 |
| DiT | 2022 | ✅ | Transformer扩散架构 |
| AnimateDiff | 2023 | ✅ | Motion Module |
| Rectified Flow | 2023 | ✅ | 直线流加速 |
| LCM | 2023 | ✅ | 4步生成 |
| SDXL-Turbo | 2023 | ✅ | 1-2步生成 |
| 3D Gaussian Splatting | 2023 | ✅ | 高斯渲染 |
| Instant NGP | 2022 | ✅ | 多分辨率哈希极速NeRF |
| DeepSDF | 2020 | ✅ | SDF隐式表征 |
| Point-NeRF | 2022 | ✅ | 点云+NeRF |
| Sora | 2024 | ✅ | 视频世界模拟 |

---

*整合：Sora/AnimateDiff/Rectified Flow论文 + 豆包AI绘画提示词课程*
*持续更新，结合P工ComfyUI学习计划*
