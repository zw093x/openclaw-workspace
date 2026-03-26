# AgentSkills 规格学习笔记

> 官方文档：https://agentskills.io/specification
> 定义：AI Agent 技能的标准化格式规范，用于模块化扩展 Agent 能力

## 核心概念

AgentSkills 是一套给 AI Agent 设计的"技能包"规范。每个技能是一个目录，包含：
- `SKILL.md`（必须）：元数据 + 指令
- `scripts/`（可选）：可执行代码
- `references/`（可选）：按需加载的文档
- `assets/`（可选）：模板、资源文件

## SKILL.md 格式规范

### Frontmatter（YAML 元数据）

| 字段 | 必填 | 约束 | 说明 |
|------|------|------|------|
| `name` | ✅ | ≤64字符，小写字母+连字符，不能以连字符开头/结尾，不能有连续连字符 | 技能名，必须与目录名一致 |
| `description` | ✅ | ≤1024字符，非空 | 描述功能 + 触发条件（这是技能的触发机制） |
| `license` | ❌ | - | 许可证名称或引用 |
| `compatibility` | ❌ | ≤500字符 | 环境要求（目标产品、系统包、网络等） |
| `metadata` | ❌ | key-value map | 自定义元数据（author、version 等） |
| `allowed-tools` | ❌ | 空格分隔的工具列表 | 预批准的工具（实验性） |

### Body（Markdown 指令）

- 无格式限制，写对 Agent 有用的指令
- 推荐包含：步骤说明、输入输出示例、常见边界情况
- **整个文件在技能触发后才会加载**，所以 description 要写清楚触发条件

## 渐进式加载设计（Progressive Disclosure）

这是最关键的设计原则——三级加载：

| 层级 | 内容 | 何时加载 | Token 预算 |
|------|------|---------|-----------|
| L1 元数据 | name + description | 启动时全部加载 | ~100 tokens |
| L2 指令 | SKILL.md 正文 | 技能触发后加载 | <5000 tokens |
| L3 资源 | scripts/references/assets | 按需加载 | 不限（脚本可不加载直接执行） |

**核心原则：上下文窗口是公共资源**。SKILL.md 正文控制在 500 行以内。

## 目录结构详解

### scripts/ — 可执行代码

- 自包含或明确记录依赖
- 包含有用的错误提示
- 优雅处理边界情况
- 支持 Python、Bash、JavaScript 等
- **价值**：Token 高效、确定性、可直接执行无需加载上下文

### references/ — 按需文档

- REFERENCE.md — 详细技术参考
- FORMS.md — 表单模板
- 领域特定文件（finance.md、legal.md 等）
- **保持文件聚焦**，Agent 按需加载，小文件 = 更少上下文占用
- 大文件（>10k 词）在 SKILL.md 中提供 grep 搜索模式
- **避免重复**：信息要么在 SKILL.md，要么在 references，不要两边都有

### assets/ — 静态资源

- 模板文件、图片、字体、数据文件
- **不会加载到上下文**，仅在输出中使用

## 渐进式拆分模式

### 模式一：高级指南 + 引用

SKILL.md 放核心工作流，详细内容分拆到 references。

### 模式二：按领域组织

```
bigquery-skill/
├── SKILL.md
└── reference/
    ├── finance.md
    ├── sales.md
    └── product.md
```

Agent 按问题类型只加载对应文件。

### 模式三：条件详情

基础内容放 SKILL.md，高级功能链接到单独文件。

**关键规则**：
- 引用深度不超过一级（从 SKILL.md 直接引用）
- 长文件（>100行）顶部加目录
- 不要创建 README.md、CHANGELOG.md 等辅助文件

## 技能创建流程

```
Step 1: 理解用例 → 收集具体示例
Step 2: 规划资源 → 分析哪些 scripts/references/assets 可复用
Step 3: 初始化技能 → 运行 init_skill.py
Step 4: 编辑技能 → 实现资源 + 编写 SKILL.md
Step 5: 打包技能 → 运行 package_skill.py（自动验证）
Step 6: 迭代优化 → 实际使用后改进
```

### 命名规则

- 小写字母、数字、连字符
- 短小动词优先（如 `rotate-pdf`、`analyze-stock`）
- 按工具命名空间化（如 `gh-address-comments`）

### SKILL.md 写作要求

- **使用祈使句/不定式**
- description 包含所有触发条件（body 中不需要"When to Use"章节）
- body 只在触发后加载，所以触发信息必须在 frontmatter

## 权限控制（allowed-tools）

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

- 空格分隔的工具列表
- 支持通配符模式
- 实验性功能，支持因实现而异

## 验证

```bash
skills-ref validate ./my-skill
```

检查 frontmatter 格式、命名规范、描述完整性。

## 对 ComfyUI 工程化的意义

AgentSkills 规格正好解决 ComfyUI 工作流的痛点：

| ComfyUI 痛点 | AgentSkills 解决方案 |
|--------------|---------------------|
| 工作流散乱 | SKILL.md 标准化每个工作流 |
| 参数靠记忆 | references/ 放参数速查表 |
| 无法协作 | 标准目录结构，版本可管理 |
| 质量无标准 | description 定义使用场景，body 定义验收条件 |
| 复用性差 | assets/ 放工作流模板，scripts/ 放批量脚本 |

### 具体映射

```
comfyui-concept-art/          ← 一个 ComfyUI 工作流 = 一个 Skill
├── SKILL.md                  ← 工作流规范（参数、场景、验收）
├── scripts/
│   ├── run_workflow.py       ← 启动工作流
│   ├── batch_generate.py     ← 批量生成
│   └── quality_check.py      ← 质量检查
├── references/
│   ├── sampler-guide.md      ← 采样器对比
│   ├── prompt-library.md     ← 提示词模板
│   └── model-comparison.md   ← 模型对比
└── assets/
    ├── workflow.json         ← ComfyUI 工作流文件
    ├── negative-presets/     ← 负面提示词预设
    └── lora-configs/         ← LoRA 配置
```

## 与 OpenSpec 的关系

| 维度 | AgentSkills | OpenSpec |
|------|------------|---------|
| 核心文件 | SKILL.md（spec + 指令） | spec.md（纯规范） |
| 变更管理 | 无（技能独立） | changes/ 目录 |
| 资源组织 | scripts/references/assets | specs/ + changes/ |
| 适用场景 | Agent 可执行的技能 | 纯规格定义 |

**结论**：对 ComfyUI 来说，AgentSkills 更合适——因为它同时定义了"规范"和"怎么执行"，而 ComfyUI 工作流既需要规范也需要可执行脚本。

---
*学习时间: 2026-03-25 21:30*
*来源: https://agentskills.io/specification + OpenClaw skill-creator 内部文档*
