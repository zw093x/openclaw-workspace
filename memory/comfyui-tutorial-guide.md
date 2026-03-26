# ComfyUI 工作流学习计划 - 教程资源指南

**制定日期：** 2026-03-22
**适用对象：** 3D 模型师（有 CG 基础）
**学习周期：** 4 周

---

## 第一周：环境搭建 + 基础工作流

### Day 1-2：独立环境搭建

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI 官方安装指南 | GitHub | https://github.com/comfyanonymous/ComfyUI | 官方 README，最权威 |
| ComfyUI 新手安装教程（Windows） | B站 | 搜索 "ComfyUI 安装教程 独立环境" | 中文视频，手把手教学 |
| ComfyUI Manager 安装使用 | GitHub | https://github.com/ltdrdata/ComfyUI-Manager | 节点管理器官方文档 |
| ComfyUI 整合包 vs 独立环境对比 | B站 | 搜索 "ComfyUI 整合包 独立安装 区别" | 帮助理解为什么要用独立环境 |

**推荐 UP 主（B站）：**
- **Nenly** — ComfyUI 系列教程，讲解清晰，适合入门
- **秋葉aaaki** — 整合包作者，也有独立安装教程
- **迷藏** — ComfyUI 工作流进阶

### Day 3-4：基础文生图工作流

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI Official Examples | 官方 | https://comfyanonymous.github.io/ComfyUI_examples/ | 官方示例工作流，必看 |
| ComfyUI 文生图全流程 | B站 | 搜索 "ComfyUI 文生图 教程" | 中文入门视频 |
| Stable Diffusion 节点原理 | YouTube | 搜索 "ComfyUI basics tutorial" | Understanding Nodes |
| 提示词编写指南 | Civitai | https://civitai.com/articles | 社区提示词技巧文章 |

**核心节点学习顺序：**
1. `Load Checkpoint` → 加载模型
2. `CLIP Text Encode` → 正/负面提示词
3. `KSampler` → 采样器（理解 seed/steps/cfg）
4. `VAE Decode` → 图像解码
5. `Save Image` → 保存输出

### Day 5-7：图生图 + ControlNet

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI ControlNet 教程 | B站 | 搜索 "ComfyUI ControlNet 使用" | 中文教程 |
| ControlNet 模型下载与使用 | Civitai | https://civitai.com/models?tag=controlnet | ControlNet 模型资源 |
| OpenPose / Canny / Depth 教程 | YouTube | 搜索 "ComfyUI ControlNet openpose depth" | 英文视频教程 |
| ControlNet 预处理器安装 | GitHub | https://github.com/Fannovel16/comfyui_controlnet_aux | ControlNet 辅助节点 |

**必装 ControlNet 模型：**
- `control_v11p_sd15_canny` — 线稿控制
- `control_v11f1p_sd15_depth` — 深度图控制
- `control_v11p_sd15_openpose` — 姿势控制

---

## 第二周：高级工作流 + 模型管理

### Day 8-9：LoRA / Checkpoint 管理

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| LoRA 叠加使用教程 | B站 | 搜索 "ComfyUI LoRA 叠加 多LoRA" | 多 LoRA 组合技巧 |
| 模型管理最佳实践 | Civitai | https://civitai.com | 下载 LoRA/Checkpoint 的主要平台 |
| LiblibAI 国内模型资源 | LiblibAI | https://www.liblibai.com | 国内模型下载，速度快 |

### Day 10-11：批量出图 + 参数矩阵

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI 批量出图技巧 | B站 | 搜索 "ComfyUI 批量出图 XY Plot" | 参数对比测试 |
| Efficiency Nodes | GitHub | https://github.com/LucianoCirino/efficiency-nodes-comfyui | 效率节点包，集成批量功能 |
| ComfyUI Impact Pack | GitHub | https://github.com/ltdrdata/ComfyUI-Impact-Pack | 高级检测和处理节点 |

### Day 12-14：工作流模块化

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| Group Nodes 使用教程 | B站 | 搜索 "ComfyUI 节点组 Group Node" | 工作流打包复用 |
| 工作流模板管理 | GitHub | https://github.com/comfyanonymous/ComfyUI/wiki | 官方 Wiki 文档 |

---

## 第三周：3D 生成节点（核心重点）⭐

### Day 15-16：Tripo3D API

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| Tripo3D 官方文档 | Tripo3D | https://platform.tripo3d.ai/docs | API 文档和 Key 获取 |
| comfyui-tripo3d 节点 | GitHub | https://github.com/1038lab/ComfyUI-tripo3d | ComfyUI 节点安装 |
| Tripo3D Image-to-3D 教程 | YouTube | 搜索 "Tripo3D image to 3D tutorial" | 图片转 3D 操作演示 |
| Tripo3D 文生 3D 演示 | B站 | 搜索 "Tripo3D 文字生成3D" | 中文教程 |

### Day 17-18：Meshy API

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| Meshy 官方文档 | Meshy | https://docs.meshy.ai | API 文档 |
| Meshy 文生 3D / 图生 3D | YouTube | 搜索 "Meshy AI 3D generation" | 官方操作演示 |
| Meshy PBR 材质生成 | YouTube | 搜索 "Meshy PBR texture generation" | 材质贴图生成 |
| Meshy vs Tripo3D 对比 | B站 | 搜索 "Meshy Tripo3D 对比" | 质量对比评测 |

### Day 19-20：开源 3D 方案

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| TripoSR 本地部署 | GitHub | https://github.com/VAST-AI-Research/TripoSR | Stability AI 开源 |
| ComfyUI-TripoSR 节点 | GitHub | 搜索 "ComfyUI-TripoSR" | ComfyUI 集成节点 |
| InstantMesh 教程 | GitHub | https://github.com/TencentARC/InstantMesh | 腾讯开源，多视角方案 |
| 3D Gaussian Splatting 入门 | YouTube | 搜索 "3D Gaussian Splatting tutorial" | 新兴 3D 表示技术 |

### Day 21：完整 3D 工作流

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| SD 出图 → AI 生 3D → Blender 精修 | B站 | 搜索 "AI 建模流程 Stable Diffusion 3D" | 完整流水线演示 |
| ComfyUI + Blender 集成 | YouTube | 搜索 "ComfyUI Blender workflow" | 集成方案 |

---

## 第四周：流水线集成 + 效率优化

### Day 22-23：ComfyUI + Blender 集成

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| Blender ComfyUI 插件 | GitHub | https://github.com/AIGODLIKE/AIGODLIKE-ComfyUI-Blender | Blender 内调用 ComfyUI |
| Blender-AI-3D 工具集 | GitHub | 搜索 "Blender AI 3D generation addon" | AI 建模相关插件 |
| Python API 调用 ComfyUI | GitHub | https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples | 官方 API 示例 |

### Day 24-25：批量资产生产

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI API 调用教程 | 官方 | https://comfyanonymous.github.io/ComfyUI_examples/api/ | API 模式使用 |
| ComfyUI 服务器部署 | YouTube | 搜索 "ComfyUI server deployment" | 远程运行方案 |
| 批量生成脚本 | GitHub | 搜索 "ComfyUI batch generation script" | Python 批量调用 |

### Day 26-27：v0.17.0+ 新特性

| 教程 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI Release Notes | GitHub | https://github.com/comfyanonymous/ComfyUI/releases | 官方更新日志 |
| 异步资产扫描说明 | GitHub | 搜索 ComfyUI issues/PRs | 相关技术说明 |
| 腾讯 TextToModel/ImageToModel | GitHub | 搜索 "ComfyUI tencent 3D node" | 国内免费 3D 节点 |
| --fp16-intermediates 参数 | 官方 | ComfyUI launch options 文档 | 显存优化参数 |

### Day 28：总结与进阶

| 资源 | 平台 | 链接 | 说明 |
|------|------|------|------|
| ComfyUI 社区工作流 | Civitai | https://civitai.com/search?query=comfyui%20workflow | 海量社区工作流 |
| ComfyUI 工作流分享 | OpenArt | https://openart.ai/workflows | 工作流市场 |
| ComfyUI Discord | Discord | https://discord.gg/comfyui | 官方社区，最新动态 |
| Civitai 3D 资源 | Civitai | https://civitai.com/tag/3d | 3D 相关模型和工作流 |

---

## 📺 推荐 UP 主 / YouTube 频道

### B站（中文）

| UP 主 | 擅长方向 | 推荐理由 |
|--------|---------|---------|
| **Nenly** | ComfyUI 全系列 | 讲解最清晰的 ComfyUI 中文教程 |
| **秋葉aaaki** | SD 整合包/ComfyUI | 入门友好，工具整合 |
| **迷藏** | ComfyUI 进阶工作流 | 高级技巧和节点组合 |
| **林超超超超** | AI+3D | AI 建模与 CG 结合 |
| **CG 民工** | CG 行业技术 | 3D/CG 行业视角 |

### YouTube（英文）

| 频道 | 擅长方向 | 推荐理由 |
|------|---------|---------|
| **Olivio Sarikas** | ComfyUI 教程 | 系统全面的英文教程 |
| **Latent Vision** | ComfyUI 节点详解 | 深入理解每个节点 |
| **Sebastian Kamph** | SD/ComfyUI | 实用技巧丰富 |
| **Mickmm** | ComfyUI 工作流 | 高级工作流搭建 |
| **Scott Detweiler** | ComfyUI 进阶 | Quality AI 内容 |

---

## 📥 必装节点包

| 节点包 | 用途 | 安装方式 |
|--------|------|---------|
| ComfyUI Manager | 节点管理器 | `git clone` 到 custom_nodes |
| ControlNet Aux | ControlNet 预处理器 | Manager 一键安装 |
| Efficiency Nodes | 效率节点集 | Manager 一键安装 |
| Impact Pack | 高级检测处理 | Manager 一键安装 |
| comfyui-tripo3d | Tripo3D API | Manager 一键安装 |
| ComfyUI-Custom-Scripts | 实用脚本集 | Manager 一键安装 |
| rgthree | 工作流美化 | Manager 一键安装 |

---

## 🔗 模型下载资源

| 平台 | 链接 | 特点 |
|------|------|------|
| Civitai | https://civitai.com | 全球最大，模型最全 |
| LiblibAI | https://www.liblibai.com | 国内平台，下载快 |
| HuggingFace | https://huggingface.co | 开源模型主阵地 |
| Tripo3D | https://platform.tripo3d.ai | 3D 生成 API |
| Meshy | https://www.meshy.ai | 3D 生成 API |

---

*持续更新。如发现更好的教程资源，请告知补充。*
