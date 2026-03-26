# ComfyUI × OpenSpec：AI+3D 建模工作流学习路径

> 创建时间：2026-03-25 08:34 | 优先级：🔴 最高

---

## 一、学习目标

**核心目标**：掌握 ComfyUI 工作流搭建 + OpenSpec 规范管理，构建可追溯、可复现的 AI+3D 建模流水线。

**具体产出**：
1. 一套完整的"文生图→图生3D→精修"ComfyUI 工作流
2. 配套的 OpenSpec 规范文档（输入输出定义、质量标准、变更记录）
3. 至少 1 个自定义 ComfyUI 节点（AI 自动拓扑/UV 生成）

---

## 二、工具概览

### ComfyUI — 微观执行层
- **定位**：节点式 AI 图像/3D 生成工作流引擎
- **核心能力**：SD/SDXL/Flux 文生图、ControlNet 精确控制、img2img、3D 生成节点
- **学习重点**：节点连接、参数调优、批量处理、自定义节点开发

### OpenSpec — 宏观管理层
- **定位**：AI 驱动的规范驱动开发框架
- **安装**：`npm install -g @fission-ai/openspec@latest` ✅ 已安装
- **核心概念**：
  - `specs/` — 存放功能规范（每个能力一个目录）
  - `changes/` — 存放变更提案（proposal + design + tasks + delta）
  - `spec.md` — 用 GIVEN/WHEN/THEN 格式描述需求
  - `delta` — 变更 diff，记录需求如何演进
- **工作流**：`/opsx:propose "想法"` → 生成 proposal/design/tasks → 人工审核 → `/opsx:impl` 实现 → `/opsx:archive` 归档

---

## 三、4 周学习计划（详细版）

### 📅 第 1 周（3/25-3/31）：基础搭建

#### ComfyUI 部分

| 日期 | 学习内容 | 产出 | 资源 |
|------|---------|------|------|
| 3/25 周二 | 安装部署（秋叶整合包 or 手动） | 可运行的 ComfyUI 环境 | [秋叶整合包](https://www.bilibili.com/video/BV1Ai4y1S79V) |
| 3/26 周三 | 界面熟悉 + 基础文生图 | 第一张 AI 生成图 | 官方文档 Quick Start |
| 3/27 周四 | 图生图 + Img2Img | 风格迁移作品 | ComfyUI Examples |
| 3/28 周五 | ControlNet 入门（Canny/Depth） | 精确控制构图 | [ControlNet 教程](https://civitai.com/articles/2560) |
| 3/29 周六 | 模型管理 + LoRA 使用 | 不同风格对比图 | Civitai 模型库 |
| 3/30 周日 | ComfyUI Manager + 插件生态 | 安装 5+ 常用插件 | ComfyUI Manager |

**第 1 周检查点**：能独立搭建文生图工作流，输出 3 种不同风格的概念图

#### OpenSpec 部分

| 日期 | 学习内容 | 产出 |
|------|---------|------|
| 3/25 周二 | 理解核心概念（spec/change/delta） | 笔记 |
| 3/26 周三 | 实操：`openspec init` + 目录结构 | 理解文件组织 |
| 3/27 周四 | 编写第一个 spec.md（GIVEN/WHEN/THEN） | `concept-gen/spec.md` |
| 3/28 周五 | 练习：为 ControlNet 工作流写 spec | `controlnet/spec.md` |
| 3/29-30 | 复习 + 整理笔记 | 个人 spec 模板 |

**第 1 周检查点**：能用规范格式描述一个 ComfyUI 工作流

---

### 📅 第 2 周（4/1-4/7）：3D 生成 + 规范深化

#### ComfyUI 部分

| 日期 | 学习内容 | 产出 |
|------|---------|------|
| 4/1 周二 | Tripo3D 节点安装配置 | 可调用的 3D 生成节点 |
| 4/2 周三 | Meshy 节点 + 两个平台对比测试 | 质量对比报告 |
| 4/3 周四 | 图生3D 完整流程 | **第一个 AI 3D 模型** |
| 4/4 周五 | 3D 模型后处理（Blender 导入） | 可编辑的 3D 模型 |
| 4/5 周六 | 批量生成 + 参数矩阵测试 | 最佳参数配置 |
| 4/6 周日 | Prompt 工程进阶 | Prompt 模板库 |

**第 2 周检查点**：完成"概念图→3D模型"完整流程，产出 5+ 个 3D 模型

#### OpenSpec 部分

| 日期 | 学习内容 | 产出 |
|------|---------|------|
| 4/1 周二 | Delta 规范编写 | 变更记录格式掌握 |
| 4/2 周三 | 为 3D 生成流程写完整 spec | `3d-generation/spec.md` |
| 4/3 周四 | Practice: 用 spec 记录第一次 3D 生成 | 完整文档 |
| 4/4-6 | Spec 版本管理 + 变更追踪 | 项目规范体系 |

**第 2 周检查点**：为 AI+3D 流水线建立完整的规范文档

---

### 📅 第 3 周（4/8-4/14）：自定义节点开发

#### ComfyUI 部分

| 日期 | 学习内容 | 产出 |
|------|---------|------|
| 4/8 周二 | Python 节点开发基础 | Hello World 节点 |
| 4/9 周三 | 节点输入输出定义 | 带参数的处理节点 |
| 4/10 周四 | 节点 UI 定制 | 美化后的节点界面 |
| 4/11 周五 | 自定义 3D 相关节点 | AI 自动拓扑节点 v0.1 |
| 4/12-14 | 节点测试 + 调试 + 文档 | 可发布的节点包 |

#### OpenSpec 部分

| 日期 | 学习内容 | 产出 |
|------|---------|------|
| 4/8 周二 | 用 explore 分析节点需求 | 需求分析报告 |
| 4/9 周三 | 为自定义节点写 proposal spec | `auto-retopo/proposal.md` |
| 4/10 周四 | 用 impl 驱动节点开发 | spec 驱动的开发流程 |
| 4/11-14 | 完整的 spec → impl → archive 循环 | 归档的变更记录 |

**第 3 周检查点**：完成 1 个自定义 ComfyUI 节点，全程用 OpenSpec 管理

---

### 📅 第 4 周（4/15-4/21）：流水线整合 + 工程化

| 日期 | 学习内容 | 产出 |
|------|---------|------|
| 4/15 周二 | 完整流水线搭建 | 文生图→图生3D→精修 全链路 |
| 4/16 周三 | 批量处理 + 错误处理 | 自动化脚本 |
| 4/17 周四 | Pipeline spec 编写 | 流水线规范文档 |
| 4/18 周五 | Quality gate 设计 | 质量控制标准 |
| 4/19-20 | 端到端测试 + 优化 | 性能报告 |
| 4/21 周一 | **最终总结** | 项目文档 + 博客/分享稿 |

**第 4 周检查点**：完整的 AI+3D 工作流 + 配套规范文档体系

---

## 四、学习资源汇总

### ComfyUI
| 资源 | 链接 | 说明 |
|------|------|------|
| 官方文档 | https://docs.comfy.org/ | 最权威参考 |
| GitHub | github.com/comfyanonymous/ComfyUI | 源码 + Issues |
| B站教程 | 搜索 "ComfyUI 教程" + "秋叶整合包" | 中文视频教程 |
| Civitai | https://civitai.com/ | 模型 + 工作流社区 |
| ComfyUI Manager | 内置插件管理器 | 一键安装插件/节点 |

### OpenSpec
| 资源 | 链接 | 说明 |
|------|------|------|
| 官网 | https://openspec.dev/ | 概览 + 安装 |
| GitHub | github.com/Fission-AI/OpenSpec/ | 源码 + 文档 |
| Discord | https://discord.gg/YctCnvvshC | 社区交流 |

### 3D 生成
| 资源 | 说明 |
|------|------|
| Tripo3D | AI 3D 生成，ComfyUI 节点支持 |
| Meshy | 另一个 3D 生成平台 |
| TripoSR | 开源 3D 重建模型 |
| InstantMesh | 单图→3D 网格 |

---

## 五、关键里程碑

```
3/25 ────── 4/1 ────── 4/8 ────── 4/15 ────── 4/21
  │           │          │           │           │
  ▼           ▼          ▼           ▼           ▼
 M1:环境搭建  M2:3D生成   M3:自定义节点  M4:流水线整合  M5:总结交付
 第一张AI图   第一个3D模型  第一个自定义节点  完整工作流    项目文档
```

---

## 六、当前状态

- ✅ OpenSpec 已安装（v?）
- ⏳ ComfyUI 待安装（需本地 GPU 环境）
- 📋 学习计划已制定
- 📝 演示项目已初始化（comfyui-openspec-demo/）

---

*此文档随学习进度持续更新*
