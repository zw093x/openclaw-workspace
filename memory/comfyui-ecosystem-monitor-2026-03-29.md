# ComfyUI 生态深度监控报告
**日期**: 2026-03-29（每周日 10:00 定时推送）

---

## 一、ComfyUI 最新版本动态

### 版本发布节奏（近两周极快）
| 版本 | 发布日期 | 距今天数 | 重要性 |
|------|---------|---------|--------|
| **v0.18.2** | 2026-03-25 | 4天 | 🔴 最高 |
| **v0.18.1** | 2026-03-24 | 5天 | 🟡 高 |
| **v0.18.0** | 2026-03-21 | 8天 | 🔴 最高 |
| v0.17.2 | 2026-03-15 | 14天 | 🟡 高 |
| v0.17.1 | 2026-03-14 | 15天 | 🟡 高 |
| **v0.17.0** | 2026-03-13 | 16天 | 🔴 最高 |

### 🔴 v0.18.0 重大变化（与 3D 相关）
1. **Tencent TextToModel / ImageToModel 原生节点**（#12680）
   - ComfyUI 首次内置腾讯图文转 3D 模型节点
   - 原生支持 Text-to-3D 和 Image-to-3D 工作流
2. **mxfp8 支持**（#12907 by @kijai）— 更低显存占用的量化方案
3. **CacheProvider API** — 外部分布式缓存接口（先加后撤，需关注后续）
4. **资产模块化架构重构** — async 两阶段扫描器
5. **LTXV VAE 分块编码** — 大幅降低 VRAM 需求（Chunked encoder + CPU IO chunking）

### v0.18.1 / v0.18.2 热修
- v0.18.1: WAN VAE 光照问题修复，comfyanonymous 例行优化
- v0.18.2: 最新版本，无 changelog（刚发布 4 天）

### ⚠️ v0.17.0 架构变化要点
- Flux KV Cache 节点：`FluxKVCache` 节点支持 flux 2 klein kv cache 模型
- 模型检测：`deep clone pre-edited weights` 改进
- 前端兼容性修复：Float gradient_stops 格式修复
- Python faulthandler 默认开启（崩溃调试增强）

---

## 二、3D 生成节点动态

### ComfyUI-3D-Pack（最核心的 3D 扩展）
| 指标 | 数值 |
|------|------|
| GitHub | MrForExample/ComfyUI-3D-Pack |
| Stars | **3.7k** |
| Forks | 360 |
| 最新 Release | **v0.1.6**（2025-08-07，约 7 个月前） |
| 总 Commits | 281 |

**近期 Commits（2025 年内）**：
| 时间 | 内容 | 方向 |
|------|------|------|
| 4 个月前 | 更新 CharacterGen/Era3D/Wonder3D 的 UNet 模型 | 🟢 维护更新 |
| 7 个月前 | example workflows 重命名为 comfy-manager 风格 | 🟡 体验优化 |
| 8 个月前 | fix diso/spconv/mesh_painter 安装问题 | 🔴 Bug 修复 |
| 10 个月前 | Hunyuan3D-V2 Turbo/Fast/Mini 模型（MV 未实现） | 🟢 新功能 |
| 11 个月前 | 集成 **TripoSG + Scribble model** | 🔴 新功能 |

**v0.1.6（2025-08）特性**：白背景支持、nodes.py 更新

### TripoSG ✅ 有重大更新
- ComfyUI-3D-Pack 已集成（11 个月前 commit）
- 支持：**Single image (Reference or Scribble) to 3D Mesh**
- 权重：https://huggingface.co/VAST-AI/TripoSG + TripoSG-scribble
- 来自 VAST-AI-Research

### TripoSR / InstantMesh ⚠️ 停滞
| 项目 | Stars | 最后更新 | 状态 |
|------|-------|---------|------|
| TripoSR (VAST-AI) | 6.3k | 约 2 年前 | 🔴 停滞 |
| InstantMesh (TencentARC) | 4.3k | 约 2 年前 | 🔴 停滞 |

> 注：Tencent 官方已将能力整合进 ComfyUI v0.18.0 原生节点（TextToModel/ImageToModel）

### Tripo3D 🔍 待确认
- GitHub 路径未找到（可能为闭源或 API 调用方式）
- 建议关注 tripo3d.com 官方服务

### Meshy (meshy.ai) 🔍 待确认
- GitHub 公开 repo 未找到
- 可能为付费 API 服务（非开源）

---

## 三、推荐工作流与最佳实践

### 当前最优 3D 生成方案（2026 年初）
按质量/速度综合推荐：

| 排名 | 方案 | 适用场景 | 速度 | 质量 |
|------|------|---------|------|------|
| 🥇 | **Hunyuan3D 2.1**（Tencent）| 通用首选 | 中 | 高 |
| 🥈 | **PartCrafter** | 多部件复杂物体 | 中 | 很高 |
| 🥉 | **TripoSG + Scribble** | 草图/参考图 | 快 | 高 |
| 4 | TRELLIS (Microsoft) | 单图带纹理 | 中 | 高 |
| 5 | StableFast3D | 快速预览 | 极快 | 中 |

### ComfyUI + Blender/Maya 集成路径
```
ComfyUI（图生3D) → 输出 .obj/.glb → Blender python脚本导入 
→ 材质/UV编辑 → Maya 绑定/动画 → 渲染输出
```
**关键节点**：
- ComfyUI-3D-Pack 的 `Mesh Preview` 节点（Three.js 可视化）
- `Stack Orbit Camera Poses` 自动生成相机路径
- FlexiCubes 网格导出 → Blender 格式兼容

---

## 四、生态关键节点一览

| 节点/工具 | 类型 | 3D 相关性 | 状态 |
|-----------|------|-----------|------|
| ComfyUI-3D-Pack | 自定义节点包 | 🔴 核心 | ✅ 活跃维护 |
| Tencent TextToModel | 原生节点(v0.18+) | 🔴 核心 | ✅ 新增 |
| Tencent ImageToModel | 原生节点(v0.18+) | 🔴 核心 | ✅ 新增 |
| Hunyuan3D 2.1 | 模型+节点 | 🔴 核心 | ✅ 腾讯主推 |
| PartCrafter | 模型+节点 | 🔴 核心 | ✅ 新集成 |
| TripoSG | 模型+节点 | 🟡 重要 | ✅ 集成 |
| TRELLIS | 模型 | 🟡 重要 | ✅ 可用 |
| StableFast3D | 模型 | 🟡 快速 | ✅ 可用 |
| TripoSR | 模型 | 🟡 备选 | ⚠️ 停滞 |
| InstantMesh | 模型 | 🟡 备选 | ⚠️ 停滞 |

---

## 五、行动建议

### 🔴 最高优先级
1. **升级 ComfyUI 到 v0.18.x** — Ten

cent 原生 3D 节点是重大利好
2. **测试 Hunyuan3D 2.1** — 腾讯最新两阶段流水线（Shapegen + Texgen）
3. **关注 ComfyUI-3D-Pack v0.2.x** — 近期更新频率上升，可能有大版本

### 🟡 中优先级
4. **PartCrafter 工作流** — 多部件物体生成质量最佳
5. **安装 ComfyUI-Manager** — 一键管理 3D Pack 依赖
6. **Blender 脚本准备** — ComfyUI 输出 → Blender 的自动化 pipeline

### 🟢 观察
- CacheProvider API 回归时间（影响分布式缓存）
- mxfp8 量化在 3D 模型上的应用
- Tripo3D 是否有开源计划

---

*报告生成时间：2026-03-29 10:09 CST | 数据来源：GitHub / HuggingFace*
