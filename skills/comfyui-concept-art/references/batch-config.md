# 批量生成配置

## 使用方法

```bash
# 基础批量生成
python scripts/batch_generate.py \
  --prompts-file prompts.txt \
  --model sdxl \
  --count 4 \
  --output-dir output/batch_001

# 从配置文件生成
python scripts/batch_generate.py --config batch_config.yaml
```

## 配置文件格式（batch_config.yaml）

```yaml
model: sdxl
resolution: 1024x1024
sampler: euler_ancestral
steps: 20
cfg: 7.0

# 提示词列表
prompts:
  - "a warrior on a cliff, fantasy art, dramatic lighting"
  - "a wizard in a tower, mystical atmosphere"
  - "a dragon flying over a castle, epic scale"

# 每个提示词生成数量
count_per_prompt: 4

# 输出设置
output_dir: "output/batch_concepts"
naming_pattern: "{project}_{date}_{seq}_{seed}"

# 质量过滤（可选）
quality_filter:
  enabled: true
  min_score: 0.7  # CLIP score 阈值
```

## 命名规则

```
{project}_{YYYY-MM-DD}_{序号3位}_{seed值}.png

示例：
concept_warrior_2026-03-25_001_12345.png
concept_wizard_2026-03-25_002_67890.png
```

## 质量控制

批量生成后可运行质量检查：
```bash
python scripts/quality_check.py --input-dir output/batch_001
```

检查项：
- 分辨率是否正确
- 是否存在明显畸变
- CLIP score（与提示词匹配度）
- 文件大小异常（过小 = 生成失败）
