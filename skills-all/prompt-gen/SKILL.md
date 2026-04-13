---
name: prompt-gen
description: AI提示词工程技能。覆盖图像/视频/3D生成的全渠道关键词库，角色建模专用提示词模板，持续迭代优化。触发条件：生成AI提示词、写角色描述、优化提示词、查询关键词。
---

# AI 提示词工程技能

## 核心能力

1. **关键词库**：从各渠道（官方/Civitai/HF/社区）收集的结构化关键词
2. **角色建模提示词模板**：针对模型师角色的专用模板
3. **持续迭代机制**：每次使用后根据反馈优化

---

## 关键词库

### 一、图像质量标签（通用）

| 标签 | 作用 |
|------|------|
| `masterpiece, best quality` | 提升整体质量 |
| `highly detailed` | 增加细节 |
| `ultra detailed` | 超高细节 |
| `8k, 4k` | 分辨率标签 |
| `cinematic lighting` | 电影光影 |
| `studio lighting` | 工作室光 |
| ` volumetric lighting` | 体积光 |
| `ambient occlusion` | 环境光遮蔽 |
| `ray tracing` | 光线追踪 |
| `HDR` | 高动态范围 |

### 二、风格标签

#### 写实类
`photorealistic`, `realistic`, `hyperrealistic`, `photo mode`, `digital photograph`

#### 插画/动漫类
`illustration`, `digital art`, `concept art`, `anime`, `manga`, `anime style`, `semi-realistic`

#### 影视/游戏类
`cinematic`, `movie still`, `film grain`, `Blade Runner style`, `GTA style`, `Unity screenshot`, `Unreal Engine`

#### 艺术风格
`oil painting`, `watercolor`, `impressionist`, `art nouveau`, ` Art Deco`, `ukiyo-e`

### 三、角色描述关键词

#### 性别/年龄
`1girl`, `1boy`, `female`, `male`, `young`, `adult`, `elderly`, `teen`

#### 面部特征
`beautiful face`, `detailed eyes`, `heterochromia`, `scar on face`, `freckles`, `eyebrows`

#### 发型发色
`long hair`, `short hair`, `curly hair`, `straight hair`, `blonde`, `black hair`, `white hair`, `red hair`, `blue hair`, `ponytail`, `braid`, `twintails`, `messy hair`

#### 服装
`armor`, `casual clothes`, `formal wear`, `school uniform`, `dress`, `kimono`, `suit`, `jeans and t-shirt`, `military uniform`, `fantasy armor`, `mechanical armor`

#### 角色类型
`warrior`, `mage`, `rogue`, `ranger`, `knight`, `samurai`, `ninja`, `pilot`, `scientist`, `maid`, `idol`, `soldier`

### 四、角色视角/构图

`front view`, `side view`, `back view`, `three-quarter view`, `from above`, `from below`, `dynamic angle`, `wide shot`, `close-up`, `portrait`, `full body`, `half body`, `upper body`, `cowboy shot`

### 五、角色姿势

`standing`, `sitting`, `walking`, `running`, `jumping`, `fighting pose`, `action pose`, `lying down`, `leaning`, `crossed arms`, `hand on hip`, `salute`, `pointing`, `holding weapon`, `cape flowing`

### 六、光影

`rim lighting`, `backlighting`, `frontlighting`, `side lighting`, `soft lighting`, `harsh lighting`, `natural lighting`, `neon lighting`, `sunset lighting`, `moonlight`, `god rays`, `lens flare`

### 七、场景

`indoor`, `outdoor`, `cityscape`, `landscape`, `ruins`, `forest`, `desert`, `space station`, `mechanical workshop`, `battlefield`, `classroom`, `street`, `rooftop`

### 八、负面提示词（通用）

```
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, deformed, ugly
```

### 九、视频生成关键词

#### 运镜
`slow pan`, `fast pan`, `zoom in`, `zoom out`, `tracking shot`, `dolly shot`, `crane shot`, `handheld`, `static`, `drone shot`, `dutch angle`, `rack focus`

#### 动作描述
`smooth motion`, `fluid motion`, `dramatic motion`, `slow motion`, `time lapse`, `frame interpolation`

#### 视频质量
`high quality`, `cinematic`, `movie still`, `8K`, `4K`, `RAW video`, `cinematic color grading`

#### 视频类型
`close-up shot`, `medium shot`, `wide shot`, `establishing shot`, `POV shot`, `aerial view`

### 十、角色三视图关键词

```
front view, side view, back view, full body, three views, orthographic, turntable, 360-degree, character sheet, design sheet, front side back, white background, consistent style, clean lineart, flat color, separated layers
```

---

## 角色建模专用提示词模板

### 模板A：角色概念设计图

```
[角色类型/职业], [性别], [年龄段],
[详细外貌特征],
[发型: 颜色+长度+样式],
[服装: 服装类型+材质+配色],
[配饰: 武器/道具/装饰],
standing in [场景/环境],
[视角], [构图],
[光照类型], [光照方向],
[背景描述],
[画质标签],
[风格标签],
[负面标签]
```

### 模板B：角色三视图（建模参考用）

```
[角色名/类型] character design sheet,
front view, side view, back view,
full body, orthographic projection,
white background,
consistently same character across all views,
clean lineart, flat color,
separate layers,
[角色详细描述],
for 3D modeling reference,
no shading, no gradient,
transparent where needed
```

### 模板C：角色动画/视频

```
[角色描述],
[核心动作],
[运镜方式],
[场景/背景],
[时长/节奏],
[画质],
[风格]
```

---

## 渠道来源

| 渠道 | 类型 | 更新频率 |
|------|------|---------|
| Civitai 标签库 | 社区实战关键词 | 持续 |
| Hugging Face Spaces | 官方标签 | 持续 |
| ComfyUI 节点文档 | 技术标签 | 版本更新时 |
| 即梦AI 官方 | 工具能力 | 持续 |
| Runway/Kling 官方 | 视频提示词 | 版本更新时 |
| B站/YouTube 教程 | 技巧类 | 持续 |

---

## 完整文档（持续更新）

| 文件 | 内容 |
|------|------|
| `references/keywords-character.md` | 角色关键词库（来源：Civitai/HF/社区） |
| `references/templates-character.md` | 角色建模提示词模板（7个） |
| `references/video-workflow-reference.md` | **AI视频制作工作流（朋友实跑总结）** |

---

## 迭代记录

- 2026-04-03 v1.0: 初始化，基础关键词库 + 3个模板
- 2026-04-03 v1.1: 新增视频工作流文档（MidJourney/Ideogram/即梦/海螺/小云雀模板 + 底图评估 + 分镜体系）
- 待补充：即梦关键词专库、角色表情专库
