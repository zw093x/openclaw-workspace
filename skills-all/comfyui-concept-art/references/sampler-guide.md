# 采样器选择指南

## 速查表

| 采样器 | 速度 | 质量 | 推荐场景 |
|--------|------|------|---------|
| euler_ancestral | ⚡⚡⚡ | ★★★☆ | 概念设计、快速迭代 |
| euler | ⚡⚡⚡ | ★★★☆ | 干净风格、插画 |
| dpmpp_2m | ⚡⚡ | ★★★★ | 通用首选 |
| dpmpp_2m_karras | ⚡⚡ | ★★★★☆ | 高质量写实 |
| dpmpp_sde | ⚡ | ★★★★★ | 精细细节 |
| uni_pc | ⚡⚡ | ★★★★ | 快速高质量 |
| lcm | ⚡⚡⚡⚡ | ★★☆ | 超快速预览（4-8步） |

## 推荐组合

### 概念设计（速度优先）
```yaml
sampler: euler_ancestral
steps: 20
cfg: 7.0
```

### 精细化插图（质量优先）
```yaml
sampler: dpmpp_2m_karras
steps: 30
cfg: 7.0
```

### 写实风格
```yaml
sampler: dpmpp_sde
steps: 25
cfg: 6.5
```

### 快速预览
```yaml
sampler: lcm
steps: 6
cfg: 1.5
```

## Flux 模型特殊说明

Flux 模型推荐：
- sampler: euler
- steps: 20-25
- cfg: 3.5-5.0（Flux 对 CFG 更敏感）
