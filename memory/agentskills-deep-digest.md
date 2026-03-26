# AgentSkills 规格深度消化

> 来源：https://agentskills.io/specification + OpenClaw skill-creator 源码 + init_skill.py + quick_validate.py

## 第一层理解：规格表面

已记录于 `memory/agentskills-spec-study.md`。基础结构、三级加载、目录规范。

## 第二层理解：源码揭示的真实规则

### Frontmatter 严格白名单

**验证器实际接受的字段**（quick_validate.py）：
```
✅ name          - 必填，≤64字符，小写+连字符
✅ description   - 必填，≤1024字符，不能含 < >
✅ license       - 选填
✅ allowed-tools - 选填，空格分隔
✅ metadata      - 选填，key-value map
❌ compatibility - 规格页面提了，但验证器拒绝！
```

**教训**：规格文档 ≠ 验证器规则。验证器才是真相。

### Description 是真正的触发机制

不是"元数据的一部分"，而是**技能的触发条件**。Agent 启动时只加载 name + description，靠 description 决定是否激活技能。

写法要点：
- 包含「做什么」+「什么时候用」
- 包含具体触发词/场景关键词
- **不要**在 body 里写 "When to Use" — body 只在触发后才加载
- 不能含 `<` 或 `>`（YAML 冲突）

### SKILL.md 四种组织模式（init_skill.py 模板）

| 模式 | 适用场景 | 结构 |
|------|---------|------|
| Workflow-Based | 顺序流程 | Overview → Decision Tree → Step 1 → Step 2 |
| Task-Based | 工具集合 | Overview → Quick Start → Task 1 → Task 2 |
| Reference/Guidelines | 标准规范 | Overview → Guidelines → Specifications |
| Capabilities-Based | 多功能系统 | Overview → Capabilities → Feature 1 → Feature 2 |

可以混合使用。

### 资源目录的「按需创建」原则

init_skill.py 的模板明确说：
> "Not every skill requires all three types of resources."

- scripts/ — 重复执行的代码才需要
- references/ — SKILL.md 放不下才需要
- assets/ — 输出用到的静态文件才需要
- **不要为了完整而创建空目录**

### 渐进式加载的深层逻辑

```
启动时：所有技能的 name + description 加载（~100 tokens × N个技能）
  ↓ 这就是为什么 description 必须精准 — 它决定技能能否被正确触发
触发后：SKILL.md body 加载（<5000 tokens）
  ↓ body 要精简，只放核心流程
执行时：按需读取 references/ 或执行 scripts/
  ↓ 脚本可以不加载上下文直接执行 — 这是省 token 的关键
```

**上下文窗口是公共资源** — 不只是口号，是每个设计决策的约束条件。

## 第三层理解：对我自己写技能的启示

### 我之前犯的错误

1. ❌ 在 frontmatter 加了 `compatibility` — 验证器不接受
2. ❌ description 用了 YAML 多行 `|` 格式 — 容易出问题
3. ❌ 一上来就建三个资源目录 — 应该按需创建
4. ❌ SKILL.md body 写太多解释性内容 — 应该简洁指令式

### 正确的技能设计流程

```
1. 问自己：这个技能解决什么问题？什么时候会被触发？
   → 写 description

2. 问自己：Agent 需要知道什么步骤来完成任务？
   → 写 SKILL.md body（指令式，不解释为什么，只说怎么做）

3. 问自己：哪些代码/信息会反复用到？
   → 决定是否需要 scripts/ references/ assets/

4. 验证：运行 quick_validate.py

5. 实际使用一轮，迭代
```

### 我真正需要的技能

不是"什么都做成技能"，而是：

| 判断标准 | 做成技能 | 不做技能 |
|---------|---------|---------|
| 反复执行的复杂流程 | ✅ | |
| 一次性的简单任务 | | ❌ 只需 AGENTS.md 指令 |
| 需要脚本支持 | ✅ | |
| 纯知识性的 | | ❌ 放 MEMORY.md 或 references |
| 可以标准化的 | ✅ | |
| 每次都不同的 | | ❌ |

### 对 ComfyUI 的重新思考

ComfyUI 技能的价值在于：
- 工作流模板（assets/workflow.json）确实每次复用
- 参数标准确实可以标准化
- 批量脚本确实反复执行

但不应该：
- 把每个 ComfyUI 功能都做成技能（过度碎片化）
- 在 SKILL.md 里写 ComfyUI 教学内容（放 references）

**一个技能 = 一个可复用的工作流模式**，不是一个功能点。

## 与其他规范的关系

| 规范 | 核心 | 适用 |
|------|------|------|
| AgentSkills | 给 AI Agent 用的技能包 | 我（AI）执行任务 |
| OpenSpec | 纯规格定义 + 变更管理 | 团队协作、需求管理 |
| ACP | Agent 间通信协议 | 多 Agent 协作 |

对 P工 的建模场景：
- AgentSkills → 我执行 ComfyUI 工作流
- OpenSpec → 管理工作流的需求变更（如果团队用）
- 个人使用 → AgentSkills 足够

---
*深度消化时间: 2026-03-25 21:40*
*基于源码验证器和初始化脚本的逆向理解*
