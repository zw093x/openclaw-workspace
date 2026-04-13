# 角色建模专用提示词模板 v1.0
# 适用：即梦AI / ComfyUI / Midjourney / Stable Diffusion
# 更新：2026-04-03

---

## 模板A：角色概念设计图（最常用）

**用途：** 给3D建模师提供角色参考图，生成后精修建模

```
[角色职业/类型], [性别], [年龄层],
[面部特征详细描述],
[发型: 颜色+长度+造型+质感],
[瞳色+眼型],
[服装: 上装+下装+鞋+配色],
[配饰: 武器/道具/头饰/首饰/特殊物品],
standing in [具体场景/环境背景],
[视角], [取景范围],
[光照: 光源类型+方向+质感],
[背景: 简洁/虚化/具体场景描述],
masterpiece, best quality, highly detailed,
[风格标签],
[负面标签]
```

**示例输出：**
```
female knight, young adult woman, beautiful face,
silver hair, long wavy hair, braided crown,
blue eyes, sharp determined eyes,
plate armor, silver and blue color scheme,
white fur collar, flowing cape, gauntlets, greaves,
holding ornate sword, shield with crest on back,
standing in destroyed castle courtyard, broken pillars, stormy sky,
three-quarter view, full body,
dramatic backlighting, volumetric fog, cinematic lighting,
ruins background, dust particles floating, moody atmosphere,
masterpiece, best quality, highly detailed, cinematic lighting,
positive prompt tags here
negative: lowres, bad anatomy, bad hands, text, error, missing fingers
```

---

## 模板B：角色三视图（建模必备）

**用途：** 同时生成正侧背三视图，用于3D建模参考

```
[角色名/类型] character turnaround sheet,
front view, side view, back view,
full body, standing pose, arms slightly away from body,
white background, grey background,
consistent character across all angles,
clean lineart, flat colors, no shading,
separated layers, PSD format,
[详细服装描述],
[发型颜色+造型],
for 3D modeling reference, orthographic projection,
no gradient, no shadow, no highlight,
centered, symmetrical,
highly detailed, professional quality
```

**变体（动漫风格）：**
```
[角色类型] anime character sheet,
front view, side view, back view, 3 views,
white background, cel shading, flat color,
anime style, clean lineart,
consistent eyes across all views,
for 3D modeling, turnaround reference,
[服装详细描述],
[发型+瞳色]
```

---

## 模板C：角色表情变体图

**用途：** 生成同一角色的不同表情，用于表情资产制作

```
[角色描述，和下方完全一致],
[表情1: 开心/微笑/大笑/无表情],
close-up portrait, upper body,
studio lighting, soft light,
highly detailed face, consistent character,
same character as reference,
[负面标签]

---
same character, [表情2],
[角度/构图同上方],
---

same character, [表情3],
[角度/构图同上方],
---
```

---

## 模板D：角色换装变体图

**用途：** 生成同一角色的不同服装版本

```
same character, [角色描述],
wearing [服装1详细描述],
[视角], [场景],
[光影],
highly detailed, consistent character,

same character, [完全相同的面部描述],
wearing [服装2详细描述],
[视角], [场景],
[光影],
highly detailed, consistent character,
```

---

## 模板E：AI视频生成（即梦/Runway/Kling通用）

**用途：** 角色动画/角色表演视频

```
[角色描述，和图像生成保持一致],
[核心动作描述: 站立/行走/战斗/转身/跳跃等],
[运镜方式: 推/拉/摇/移],
[场景描述],
[氛围: 光线/天气/情绪],
 cinematic, smooth motion, high quality,
[时长暗示: quick shot/mid scene/full scene]
```

**即梦专用结构：**
```
[角色]+[场景]+[动作/表情]+[风格]+[运镜]
例：一位身穿机甲的女战士在燃烧的城市废墟中奔跑战斗，电影级光线，科幻风格，追踪镜头
```

---

## 模板F：首帧→尾帧控制（高可控视频）

**用途：** 用图精确控制视频起点和终点

```
首帧：[角色+场景描述]，高细节，正面照，
same character，same scene，
末帧：[角色+动作变化+场景变化描述]，
通过首帧和尾帧之间的动作/表情/场景渐变连接，
 cinematic smooth transition,
[运镜描述]
```

---

## 模板G：角色海报/立绘（展示用）

**用途：** 游戏/项目展示角色全身立绘

```
[角色名/类型] character illustration,
full body, standing pose, heroic pose,
detailed [服装材质+配件],
[场景环境: 简洁背景+品牌标识/花字],
dramatic lighting, [主光源方向+质感],
[背景色调+氛围],
[画面比例: 16:9/9:16/1:1],
[风格: 写实/插画/动漫],
masterpiece, best quality, ultra detailed,
[细节标签],
[风格标签],
[负面标签]
```

---

## 即梦中文专用模板

### 即梦文生图
```
[主体] + [场景] + [风格] + [光线] + [细节质量]
结构：谁+在哪里+做什么+什么风格+光线什么样+多高质量
```

### 即梦视频
```
[主体] + [动作] + [场景] + [运镜] + [风格]
结构：谁+做什么+在哪里+镜头怎么动+什么感觉
```

---

## 角色描述密度分级

| 级别 | 词数 | 适用场景 | 效果 |
|------|------|---------|------|
| L1 基础 | 20-40词 | 快速草图/方向探索 | 一般 |
| L2 标准 | 50-80词 | 常规出图/变体生成 | 较好 |
| L3 详细 | 80-120词 | 建模参考/精细出图 | 很好 |
| L4 极致 | 120词+ | 终稿/比赛/商业项目 | 最佳 |

---

## 负面标签标准包

```
lowres, bad anatomy, bad proportions, bad hands,
text, watermark, signature, username, artist name,
error, missing fingers, extra digit, fewer digits,
worst quality, low quality, normal quality,
jpeg artifacts, blurry, out of focus,
cropped, worst feet, extra ears
```

---

## 更新日志
- 2026-04-03 v1.0: 初版，7个模板 + 密度分级 + 负面标签标准包

---

## ✅ 已验证成功的提示词（豆包实测）

### 2026-04-04 豆包3D动画（首个成功案例）

**你的提示词：**
```
小女孩可爱，穿着白色裙子，魔法扫帚飞在森林里，3D动画风格
```

**提示词结构拆解：**
```
[主体: 小女孩] + [服装: 白色裙子] + [道具: 魔法扫帚] + [动作: 飞] + [场景: 森林里] + [风格: 3D动画]
```

**核心成功要素：**
- ✅ 简洁，无多余技术参数
- ✅ 动词语明确（飞）
- ✅ 风格锁定（3D动画）
- ✅ 场景具体（森林）

**结论：豆包适合"一句话描述场景"的风格，越简单直接越好**

### 2026-04-04 豆包3D动画（第2个成功案例）

**你的提示词：**
```
穿着汉服的小女孩站在有萤火虫的古森林里，3D动画风格，神秘氛围
```

**提示词结构拆解：**
```
[服装风格: 汉服] + [主体: 小女孩] + [场景: 古森林+萤火虫] + [氛围: 神秘] + [风格: 3D动画]
```

**新发现：**
- 汉服 + 古风场景 = 豆包也能做好
- 萤火虫（光点元素）增加氛围感
- 氛围词（神秘）可以单独加入
