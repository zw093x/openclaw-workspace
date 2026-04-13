# 提示词模板库

## 概念设计模板

### 角色设计
```
[角色类型] standing in [环境], [风格], [光照], [视角]

示例：
a female elf warrior standing in an enchanted forest, fantasy concept art, dramatic lighting, low angle view
a cyberpunk samurai walking through neon-lit streets, sci-fi concept art, volumetric lighting, wide shot
```

### 场景设计
```
[地点描述], [氛围], [风格], [时间段]

示例：
an ancient temple overgrown with vines, mysterious atmosphere, matte painting, golden hour
a floating city above clouds, epic scale, concept art, twilight
```

### 道具/机械设计
```
[物品名称], [材质], [风格], [用途说明]

示例：
a plasma rifle, chrome and carbon fiber, sci-fi weapon design, three-view blueprint
an enchanted sword with glowing runes, fantasy weapon, ornate details, close-up
```

## 风格标签速查

| 风格 | 标签 |
|------|------|
| 概念艺术 | concept art, digital painting, matte painting |
| 插画 | illustration, watercolor, ink drawing |
| 写实 | photorealistic, 8k, hyper detailed, RAW photo |
| 动漫 | anime style, cel shading, vibrant colors |
| 像素 | pixel art, 16-bit, retro game |
| 3D 渲染 | 3D render, octane render, cinema4d |

## 负面提示词预设

### 通用（SDXL）
```
ugly, blurry, low quality, distorted, deformed, disfigured, bad anatomy,
extra limbs, extra fingers, mutated hands, poorly drawn hands,
watermark, text, signature, logo
```

### 人物专用
```
bad hands, missing fingers, extra digits, fewer digits, cropped,
worst quality, low quality, normal quality, jpeg artifacts,
extra arms, extra legs, fused fingers, too many fingers
```

### 风景专用
```
people, person, human, figure, blurry, oversaturated,
low resolution, artifacts, watermark, text
```

## 提示词技巧

1. **权重调整**：`(keyword:1.2)` 增强，`[keyword]` 减弱
2. **顺序重要**：前面的关键词权重更高
3. **具体 > 抽象**：`dramatic rim lighting` 比 `good lighting` 更有效
4. **风格组合**：最多2-3种风格混搭，过多会冲突
