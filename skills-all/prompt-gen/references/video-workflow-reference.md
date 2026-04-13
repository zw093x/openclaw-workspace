# AI视频制作工作流参考 v1.0
# 来源：朋友实跑工作流（2026-04-03）
# 用途：提示词模板 + 底图评估 + 分镜提示词

---

## 一、各工具提示词模板

### 1.1 MidJourney — 概念图

**用途：** 角色/场景 概念设计，风格探索

**模板：**
```
[角色或场景描述],
[风格参考],
[构图],
[光线],
[色调/氛围],
[质量标签],
--s [stylize值] --ar [比例] --v [版本]
```

**示例：**
```
a young female warrior in worn tactical armor,
cyberpunk ruins environment, shattered buildings,
dynamic pose, cape flowing in wind,
golden hour cinematic lighting, volumetric fog,
moody teal and orange color grading,
highly detailed, concept art style, artstation trending
--s 400 --ar 16:9 --v 6.1
```

---

### 1.2 MidJourney — 角色概念图

```
[性别+年龄+职业] [外貌描述],
[服装详细描述+材质],
[姿态+表情],
[场景+背景],
[风格],
[光线+色调],
masterpiece, best quality, highly detailed, concept art
--s 300 --ar 3:4 --v 6.1
```

---

### 1.3 Ideogram — 角色三视图

**用途：** 角色多角度图，用于建模参考

**模板：**
```
[角色类型] character turnaround sheet,
front view, side view, back view,
full body, arms slightly away from body,
white background,
[服装材质+颜色详细描述],
[发型+瞳色],
consistent character across all angles,
clean lineart, flat colors, no shading,
for 3D modeling reference, orthographic projection
```

**示例：**
```
female cyber-samurai character turnaround sheet,
front view, side view, back view,
full body, standing pose, arms slightly away from body,
white background,
wearing nanoweave combat suit, dark charcoal with cyan circuit lines,
hooded design, armored shoulders, gauntlets, greaves,
silver hair in low ponytail, determined expression,
consistent character across all angles,
clean lineart, flat colors, no shading,
for 3D modeling, orthographic projection
```

---

### 1.4 Ideogram — 场景多视角图

**模板：**
```
[场景类型] environment turnaround,
front view, side view, back view, 3/4 view,
[场景详细描述],
white background, [配色方案],
consistent style, [风格],
environmental concept art, mattepainting
```

---

### 1.5 Ideogram — 分镜关键帧

**用途：** 根据分镜出关键镜头底图

**模板：**
```
[镜头类型: close-up/medium/wide/establishing],
[场景],
[角色动作],
[镜头运动暗示],
[光线],
[色调],
cinematic composition,
matte painting quality,
for video reference, key frame
```

---

### 1.6 即梦 — 视频生成提示词

**核心结构：**
```
[主体: 角色+场景] + [动作/状态] + [运镜] + [风格/氛围]
```

**模板：**
```
[角色描述], [场景描述],
[核心动作],
[运镜方式],
电影级光影，[色调]，[氛围],
写实/动漫风格,
[时长描述]
```

**示例：**
```
一位身穿机甲的女战士在燃烧的城市废墟中奔跑，
持剑战斗姿态，披风在身后剧烈飘动，
跟踪镜头，从左侧跟随女战士高速运动，
橙红色火光与青色阴影对比，电影级体积光，科幻风格
几秒的动作镜头
```

---

### 1.7 即梦 — 图生视频（底图输入）

**核心结构：**
```
[在底图基础上描述变化] + [镜头运动] + [氛围/光影]
```

**模板：**
```
[以图为准]，角色[具体动作描述]，
镜头[运动方式]，
[光线变化/氛围增强]，
[风格保持]
```

---

### 1.8 海螺/小云雀 — 视频生成

**模板：**
```
[主体+场景],
[动作],
[运镜],
[光线+色调],
[风格],
[时长]
```

---

## 二、底图质量评估标准

### 底图合格标准

| 维度 | 必须达标 | 最好达到 |
|------|---------|---------|
| **光影** | 主光源方向明确，无阴阳脸 | 体积光/氛围光完整 |
| **色调** | 整体色调统一 | 配色有层次，主次分明 |
| **气氛** | 能感受到场景情绪 | 情绪强烈，有故事感 |
| **构图** | 主体明确，不杂乱 | 符合镜头语言，三分/引导线 |
| **细节** | 无明显崩坏/畸形 | 高质量纹理/材质 |
| **角色** | 面部结构正确，比例对 | 表情有戏，特征鲜明 |

### 底图不合格红灯

- ❌ 角色面部崩坏（眼睛/嘴巴/手）
- ❌ 光源混乱（多光源无主次）
- ❌ 色调偏灰/无氛围
- ❌ 构图主体被裁切
- ❌ 背景过于杂乱无章
- ❌ 光影与场景时间不匹配

### 底图各阶段评估重点

| 阶段 | 重点评估 | 不合格动作 |
|------|---------|-----------|
| 概念图 | 风格/氛围/创意 | 继续抽卡 |
| 三视图 | 正面侧背面比例一致 | 换工具重出 |
| 场景图 | 光影/色调/视角 | 必须重出 |
| 分镜帧 | 构图/运动暗示/情绪 | 必须重出 |

---

## 三、分镜头提示词模板

### 分镜体系基础

```
远景(Establishing) → 中景(Medium) → 近景(Close-up) → 特写(Extreme Close-up)
      ↓                  ↓              ↓              ↓
建立场景范围      交代人物关系       强调情绪/细节      极致焦点
```

### 运镜关键词对照

| 运镜 | 中文描述 | 提示词关键词 |
|------|---------|-------------|
| 推进 | 镜头靠近 | zoom in, dolly in, push in |
| 拉远 | 镜头远离 | zoom out, dolly out, pull back |
| 横移 | 镜头左右扫 | slow pan, tracking shot |
| 跟随 | 跟随主体移动 | tracking, follow shot |
| 环绕 | 绕主体旋转 | orbit, 360° shot, circling |
| 俯仰 | 镜头上/下摇 | tilt up/down |
| 固定 | 镜头不动 | static shot, locked off |

### 分镜提示词结构

**固定格式：**
```
[景别] + [主体] + [场景] + [动作] + [运镜] + [光线] + [色调]
```

### 分镜类型提示词模板

**1. 开场 Establishing Shot**
```
wide establishing shot, [场景大貌],
empty [场景类型], [时间段/天气],
[色调], [氛围],
slow zoom in, [时长],
[风格标签]
```

**2. 人物介绍 Person Introduction**
```
medium shot, [性别] [职业/身份],
[站姿/动作], [服装简述],
[场景], [光线],
slow push in, [时长],
character introduction, [风格]
```

**3. 动作序列 Action Sequence**
```
[景别], [角色] performing [动作],
[场景细节],
[动作模糊/速度描述],
dynamic tracking shot, [运镜],
[光影], [色调], [时长]
```

**4. 情感特写 Emotional Close-up**
```
close-up, [角色] [表情类型] expression,
[眼神/嘴角/整体情绪],
[局部打光], [色调],
static, [时长],
cinematic, emotional moment
```

**5. 场景过渡 Scene Transition**
```
[镜头类型], [当前场景] to [下一场景],
[过渡暗示: 叠化/切],
[目标场景建立],
establishing [新场景], [时长]
```

**6. 关键帧 Frame（融合用）**
```
[具体镜头描述],
[精确角色姿态],
[精确场景布局],
[精确光线方向+质感],
[色调],
cinematic key frame, for [动作] video generation
```

---

## 四、工具分工速查

| 工具 | 最擅长 | 不擅长 |
|------|--------|--------|
| MidJourney | 概念图/风格探索 | 角色一致性/多视角 |
| Ideogram | 三视图/多视角/场景 | 视频生成 |
| 即梦 | 中文提示词/视频/图生视频 | 复杂场景/角色一致性 |
| 海螺 | 中文视频生成 | 精细控制 |
| 小云雀 | 视频生成 | 角色一致性 |
| 剪映 | 剪辑/音效/字幕 | 无 |

---

## 更新日志
- 2026-04-03 v1.0: 提炼朋友工作流，初版含模板+评估+分镜体系
