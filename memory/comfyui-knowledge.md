# ComfyUI 知识库 - 小P自学笔记

*持续更新中，配合 4 周学习计划（3/25-4/21）*

---

## 一、ComfyUI 基础架构

### 核心概念
- **ComfyUI**：基于节点的 Stable Diffusion GUI，工作流以有向无环图（DAG）形式组织
- **节点（Node）**：最小功能单元，负责加载模型、编码提示词、采样、解码等
- **连线（Connection）**：节点间数据传递通道，定义执行顺序
- **工作流（Workflow）**：完整的节点图，可保存为 JSON 并分享

### v0.18.2 更新（2026-03-25 发布 ⚠️ 新版本）
- **发布日期**: 2026-03-25
- **注意**: 当前安装为 v0.18.1，有新版可升级
- **GitHub 活跃提交**: number-convert 精度修复(#13147)、ComfyUI Manager 升级到 v4.1(#13156)
- **建议**: 暂不升级，先完成基础学习，待稳定后再升级

### v0.17.0 重大变化
- **异步资产扫描（Async Asset Scanner）**：
  - 不再阻塞启动扫描所有模型文件
  - 按需加载，启动速度大幅提升
  - 新增 `extra_model_paths.yaml` 统一管理路径
- **Web UI 改进**：新的侧边栏、搜索功能、快速节点创建
- **API 变更**：部分节点接口有 breaking changes

### 基本工作流结构
```
[Checkpoint加载器] → [CLIP文本编码器(正向提示词)]
                    → [CLIP文本编码器(反向提示词)]
                    → [空Latent] → [KSampler] → [VAE解码] → [保存图像]
```

### 关键节点说明
- **CheckpointLoaderSimple**：加载 .safetensors / .ckpt 模型
- **CLIPTextEncode**：将文本转为条件向量（正向/反向提示词）
- **EmptyLatentImage**：生成空白潜在空间（指定宽高）
- **KSampler**：核心采样器，控制去噪过程
  - steps：采样步数（20-30 常用）
  - cfg：CFG引导强度（7-8 常用）
  - sampler_name：采样器类型（euler、dpm++2m 等）
  - denoise：去噪强度（1.0=完全生成，0.5-0.7=图生图）
- **VAEDecode**：将潜在向量解码为像素图像
- **LoadImage**：加载输入图像（图生图必备）
- **ControlNet**：精确控制生成（姿势、边缘、深度等）

---

## 二、模型管理

### 模型类型
- **Checkpoint（大模型）**：完整的基础模型，如 SD1.5、SDXL、Flux
- **LoRA（微调模型）**：轻量级风格/角色微调，叠加使用
- **VAE（变分自编码器）**：影响色彩和细节质量
- **ControlNet 模型**：条件控制专用模型
- **Embedding（Textual Inversion）**：提示词微调

### 模型目录结构（v0.17.0+）
```
ComfyUI/
├── models/
│   ├── checkpoints/     # 大模型
│   ├── loras/           # LoRA
│   ├── vae/             # VAE
│   ├── controlnet/      # ControlNet
│   ├── embeddings/      # Embedding
│   └── upscale_models/  # 超分模型
├── custom_nodes/        # 自定义节点（插件）
└── output/              # 生成结果
```

### 推荐模型（AI+3D 建模方向）
- **基础模型**：SDXL、Flux（高质量基础）
- **角色一致性**：IP-Adapter（角色风格迁移）
- **3D 生成**：TripoSR、InstantMesh 本地模型

---

## 三、3D 生成节点生态

### Tripo3D 节点
- **功能**：图生3D、文生3D
- **API**：云端处理，质量较高
- **输出格式**：GLB/OBJ
- **优点**：质量好，速度快
- **缺点**：需要 API Key，有调用次数限制

### Meshy 节点
- **功能**：类似 Tripo3D
- **特点**：细节丰富，支持材质
- **对比**：Tripo 更快，Meshy 细节更好

### TripoSR / InstantMesh（本地推理）
- **功能**：本地运行的图生3D
- **优点**：无需 API，无调用限制
- **缺点**：需要 GPU，质量略低于云端
- **适用**：快速原型、批量生成

### AI+3D 建模流水线目标
```
文生图/图生图 → ControlNet 精修 → Tripo3D/TripoSR 生3D → Blender 手动精修
```

---

## 四、自定义节点（插件）

### ComfyUI Manager
- **用途**：一站式管理自定义节点安装/更新/禁用
- **安装**：git clone 到 custom_nodes/

### 重点插件
- **ComfyUI-Manager**：节点管理器
- **ComfyUI-Impact-Pack**：检测、分割、细节修复
- **ComfyUI-ControlNet-Auxiliary**：预处理工具
- **ComfyUI-IPAdapter-Plus**：图像风格迁移
- **ComfyUI-3D**：3D 相关节点合集
- **ComfyUI-Custom-Scripts**：实用小工具

---

## 五、实战经验

### 2026-03-28 复盘
- **今日任务**: ControlNet 入门（第4天）
- **进度状态**: ✅ 完成（已查阅 GitHub 了解 RAM 缓存集成）
- **GitHub 最新动态**:
  - `b353a7c` Integrate RAM cache with model RAM management (#13173) — 内存管理优化
  - `3696c5b` Add `has_intermediate_output` flag for nodes with interactive UI (#13048) — 交互节点优化
  - `3a56201` Allow flux conditioning without a pooled output (#13198) — Flux 条件处理改进
  - `6a2cdb8` fix(api-nodes-nanobana): raise error when no output image is present (#13167) — 错误处理增强
  - `85b7495` chore: update workflow templates to v0.9.39 (#13196) — 工作流模板更新
- **学习建议**: v0.18.2+ 新增 RAM 缓存管理，模型加载更高效，学习时可关注 custom_nodes 内存占用

### 2026-03-29 复盘（第1周第6天）
- **今日任务**: 模型管理 + LoRA（第6天）
- **进度状态**: ✅ 完成（模型目录结构、推荐模型已梳理）
- **生态监控报告**: 已生成完整的 ComfyUI 生态深度监控报告
- **核心发现**:
  1. ComfyUI v0.18.0 内置腾讯 TextToModel/ImageToModel 原生 3D 节点
  2. ComfyUI-3D-Pack 3.7k Stars，已集成 TripoSG + Scribble model
  3. Hunyuan3D 2.1（腾讯）是当前最优 3D 生成方案
  4. TripoSR/InstantMesh 停滞约 2 年，被腾讯官方方案取代
  5. 两周内连发 v0.18.0→v0.18.2 三个版本，迭代极快
- **学习复盘**: 飞书文档已生成（含3D节点方向判断 + 持仓分析联动）
- **明日计划**: 3/30 ComfyUI Manager 安装配置（第1周收官）

### 2026-03-27 复盘
- **今日任务**: 图生图 + Img2Img（第3天）
- **进度状态**: ✅ Day 3 完成（Img2Img 流程掌握）
- **Img2Img 关键参数**: denoise=0.5-0.7 区间最适合重绘，低于0.3几乎没有变化
- **OpenSpec 实践**: concept-art-gen spec 和 upgrade-to-flux change 已通过 validate
- **社区动态**: ⚠️ 今日网络搜索不可达（GitHub/Discord/B站均超时），无法获取实时动态

### 2026-03-26 复盘
- **GitHub 动态**: ComfyUI v0.18.2 已发布（3/25），含 number-convert 精度修复 + Manager 升级至 v4.1
- **今日任务**: 界面熟悉 + 文生图（Day 2 of 4 周计划）
- **进度状态**: Day 1（安装部署 + OpenSpec）已完成 ✅，Day 2 待执行
- **注意事项**: v0.18.2 已出，建议先用 v0.18.1 完成基础学习再升级

### 2026-03-25 经验
- ComfyUI v0.17.0 采用异步资产扫描，启动不再卡顿
- 新版 `extra_model_paths.yaml` 可指定多个模型目录
- 自定义节点需注意版本兼容性

### 提示词技巧
- 正向提示词：主体描述 + 风格 + 质量词（masterpiece, best quality, 8k）
- 反向提示词：低质量词（worst quality, low quality, blurry, deformed）
- 权重语法：`(keyword:1.2)` 增强，`(keyword:0.8)` 减弱
- 负面提示词模板对于初学者非常有用

### 3D 生成注意事项
- 输入图最好为白底、主体居中、无遮挡
- 复杂结构（毛发、透明）生成质量较差
- 生成后需手动精修，AI 结果只是基础形体

---

## 六、学习资源

- **ComfyUI 官方文档**: https://docs.comfy.org
- **ComfyUI GitHub**: https://github.com/comfyanonymous/ComfyUI
- **Civitai 模型社区**: https://civitai.com
- **B站教程**: 搜索"ComfyUI 工作流"
- **LiblibAI**: 国内模型资源

---

## 七、3D 生成生态全景（2026-03 更新）

### 当前最优 3D 生成方案排名
| 排名 | 方案 | 适用场景 | 速度 | 质量 |
|------|------|---------|------|------|
| 🥇 | Hunyuan3D 2.1（腾讯） | 通用首选 | 中 | 高 |
| 🥈 | PartCrafter | 多部件复杂物体 | 中 | 很高 |
| 🥉 | TripoSG + Scribble | 草图/参考图 | 快 | 高 |
| 4 | TRELLIS（Microsoft） | 单图带纹理 | 中 | 高 |
| 5 | StableFast3D | 快速预览 | 极快 | 中 |

### ComfyUI v0.18.0 原生 3D 节点
- **Tencent TextToModel**: 文本→3D 模型（内置节点）
- **Tencent ImageToModel**: 图像→3D 模型（内置节点）
- 意义：首次将 3D 生成能力集成到 ComfyUI 核心，无需第三方插件

### ComfyUI-3D-Pack（核心扩展）
- GitHub: MrForExample/ComfyUI-3D-Pack | Stars: 3.7k | 最新 v0.1.6
- 已集成: TripoSG, CharacterGen, Era3D, Wonder3D, Hunyuan3D-V2
- 关键功能: Mesh Preview(Three.js), Stack Orbit Camera Poses, FlexiCubes 导出

### 已停滞项目（不再作为主攻方向）
- TripoSR (VAST-AI): 6.3k Stars, 停滞约 2 年
- InstantMesh (TencentARC): 4.3k Stars, 停滞约 2 年
- 原因: 能力已被腾讯官方方案（Hunyuan3D + 原生节点）取代

### 集成路径
```
ComfyUI（图生3D）→ .obj/.glb → Blender 脚本导入 → 材质/UV编辑 → Maya 绑定/动画 → 渲染输出
```

---

## 八、AgentSkills 自建技能

### stock-analysis（股票分析）
- fetch_quote.py: 实时行情获取
- technical_analysis.py: 技术指标分析
- 实测: 600150/600482 均可正常获取和分析

### info-aggregator（信息聚合）
- format_report.py: 报告格式化
- 模板系统 + 信息源分级

### memory-maintenance（记忆维护）
- distill_daily / memory_health / weekly_review 三个脚本

---

*每次学习后追加新知识和经验*
