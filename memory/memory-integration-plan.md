# 记忆系统融合方案 — 叶老板 Mem0+Qdrant vs 我们

> 分析日期：2026-04-15  
> 目标：评估叶老板方案融入现有系统的可行性

---

## 一、现状分析：当前多层记忆协作架构

### 系统全景图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OpenClaw 主对话层                             │
│  (memorySearch 工具 / AGENTS.md 上下文注入 / 主动调用 memory_xxx)    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│ LCM SQLite    │  │  文件系统层        │  │ Intel Hub 协调层      │
│ (lcm.db)      │  │                  │  │                      │
│ · 对话压缩     │  │  MEMORY.md       │  │ self_learn ←→        │
│ · summaries   │  │  USER.md         │  │ error_evolution ←→   │
│ · FTS5搜索    │  │  memory/daily    │  │ unified_heal         │
│               │  │  memory/*.json   │  │ memory_evolve        │
│               │  │  skills/         │  │                      │
│               │  │  .learnings/      │  │ → 所有子系统知识同步   │
└───────────────┘  └──────────────────┘  └──────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│ memory_plus   │  │ memory_evolve    │  │ unified_heal         │
│               │  │ (16层进化)        │  │ (5层自愈)            │
│ · 主题索引     │  │                  │  │                      │
│ · 语义检索✗   │  │ M1-M16:         │  │ L1: 根因关联         │
│   (标签匹配)   │  │  压缩/冲突/聚类  │  │ L2: 模式发现         │
│ · 使用统计     │  │  图谱/遗忘曲线   │  │ L3: 自适应阈值       │
│ · 健康修复     │  │  上下文/预测     │  │ L4: 预防性修复       │
│               │  │  场景化输出      │  │ L5: 策略优化         │
│               │  │                  │  │                      │
└───────────────┘  └──────────────────┘  └──────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
┌─────────────────────┐              ┌─────────────────────────────┐
│ learn_evolve        │              │ error_evolution             │
│ (11层自学习)         │              │ (错误进化引擎)               │
│                     │              │                             │
│ L1-L11:             │              │ · 错误分类/根因分析           │
│  自动记录/模式提取    │              │ · 修复策略评分                │
│  跨域迁移/反馈闭环    │              │ · 知识沉淀                    │
│  衰减遗忘/外部学习    │              │                             │
└─────────────────────┘              └─────────────────────────────┘
```

### 各层工作方式

| 层次 | 系统 | 触发方式 | 核心能力 | 现状评估 |
|------|------|---------|---------|---------|
| 存储 | 文件系统 | 手动/脚本 | 持久化记忆 | ✅ 完善 |
| 存储 | LCM SQLite | 自动 | 对话压缩/FTS5搜索 | ✅ 完善 |
| 检索 | LanceDB | memorySearch | 向量语义搜索 | ⚠️ 有但未充分利用 |
| 检索 | memory_plus | 脚本调用 | 主题索引/语义标签 | ⚠️ 伪语义(关键词) |
| 提取 | M10上下文感知 | cron每日 | 遗忘曲线加权 | ⚠️ 被动，需显式调用 |
| 提取 | LCM融合 | distill weekly | 从对话蒸馏精华 | ✅ 有但非实时 |
| 进化 | memory_evolve | cron周日 | 16层自动进化 | ✅ 完善 |
| 学习 | learn_evolve | 报错/纠正 | 11层自学习 | ✅ 完善 |
| 自愈 | unified_heal | cron每日 | 5层自愈 | ✅ 完善 |
| 协调 | intel_hub | 事件驱动 | 子系统知识同步 | ✅ 完善 |

**关键发现：提取层是当前最大短板**

---

## 二、差距分析：我们缺什么，叶老板方案提供了什么

### 叶老板方案核心亮点

| 亮点 | 叶老板实现 | 我们现状 | 差距 |
|------|----------|---------|------|
| **autoCapture** | 对话中自动提取事实/偏好，无需手动触发 | 被动：需调用 memory_evolve 的主动创建 或手动写文件 | 🔴 **核心差距** |
| **autoRecall** | 响应前自动注入相关记忆，无感知 | 需显式调用 memorySearch 或 AGENTS.md 上下文 | 🔴 **核心差距** |
| **独立提取LLM** | MiniMax-M2.7 专门提取，不占主模型算力 | 主模型自己决定何时记录，无专门提取 | 🔴 **架构差距** |
| **Qdrant向量库** | 独立部署，支持过滤/混合搜索 | LanceDB（内置）未充分使用 | 🟡 可替代 |
| **BAAI/bge-m3** | 1024维中文嵌入，向量语义检索 | 无真实嵌入模型，标签关键词匹配 | 🔴 **核心差距** |

### 我们已经有的（无需从叶老板方案学）

✅ **M16 遗忘曲线** — 记忆强度追踪  
✅ **M13 知识图谱** — 实体关系可视化  
✅ **M7 语义聚类** — 按主题自动分组  
✅ **intel_hub** — 跨系统知识同步  
✅ **LCM 对话融合** — distill_from_lcm 已实现  
✅ **M9 时序推理** — 因果链追踪  
✅ **M12 跨系统记忆** — 所有子系统共享状态  

---

## 三、差距根因：为什么我们的"语义检索"是伪语义

```
叶老板方案：
  用户说"我家宝宝" → bge-m3 嵌入 → 向量相似度 → 命中 USER.md
  
我们方案：
  用户说"我家宝宝" → 关键词匹配 "宝宝" → 命中 USER.md
                   → 命中 "婴儿" → 不匹配
                   → 语义相似词 "孩子" → 未配置，不匹配
```

**问题本质**：
1. 没有真实嵌入模型（embedding model）
2. 标签映射是人工维护的（SEMANTIC_MAP），无法自动扩展
3. autoRecall 无感知注入 → 主模型靠 AGENTS.md 指令被动读取

---

## 四、分阶段融合建议

### 短期（1-2天）：立竿见影

**目标**：解决 autoRecall 无感知问题 + 提升语义检索质量

#### Step 1：部署 BAAI/bge-m3 嵌入模型（最关键）

```bash
# 1. 下载模型（中文最强嵌入之一，1024维）
mkdir -p /root/.openclaw/models/bge-m3
cd /root/.openclaw/models/bge-m3

# 使用 huggingface-cli 下载
pip install -q huggingface-hub
huggingface-cli download BAAI/bge-m3-zh --local-dir . --local-dir-use-symlinks False

# 或使用模型链接（如果网络不通用代理）
export https_proxy=http://127.0.0.1:7890
huggingface-cli download BAAI/bge-m3-zh --local-dir . --local-dir-use-symlinks False
```

**bge-m3 优势**：
- 中文嵌入效果最好的开源模型之一
- 支持混合检索（稠密+稀疏）
- 1024维，兼顾精度与速度
- 可本地部署，不依赖外部API

#### Step 2：改造 memory_plus.py 的 semantic_search

```python
# 新增 embedding_search() 函数，替代现有伪语义检索

from sentence_transformers import SentenceTransformer
import numpy as np

# 全局模型（启动时加载一次）
_model = None

def get_embed_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("/root/.openclaw/models/bge-m3")
    return _model

def embedding_search(query: str, top_k: int = 8) -> List[Dict]:
    """
    真实向量语义检索
    1. query → 嵌入向量
    2. 所有记忆文件 → 预计算嵌入（定期更新）
    3. 余弦相似度排序
    """
    model = get_embed_model()
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    
    # 读取预计算的文件嵌入
    embed_index_file = MEMORY_DIR / "embed-index.json"
    if not embed_index_file.exists():
        return []  # 首次需要先运行 Step 3
    
    embed_index = load_json(embed_index_file, {})
    
    results = []
    for file_path, file_data in embed_index.items():
        stored_vec = np.array(file_data["embedding"])
        score = float(np.dot(query_vec, stored_vec))
        results.append({
            "file": file_path,
            "score": score,
            "topics": file_data.get("topics", []),
            "preview": file_data.get("preview", "")
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def build_embed_index():
    """
    定期构建嵌入索引（cron 每日或 memory_evolve 时调用）
    对所有记忆文件分块 → 计算嵌入向量 → 存储
    """
    model = get_embed_model()
    embed_index = {}
    
    for f in get_all_memory_files():
        try:
            content = f.read_text()
            # 分块：每500字符一块（bge-m3 最大输入512 tokens）
            chunks = [content[i:i+500] for i in range(0, len(content), 400)]
            
            # 取所有chunk的平均向量
            if chunks:
                embeddings = model.encode(chunks, normalize_embeddings=True)
                avg_embedding = embeddings.mean(axis=0)
                
                rel = str(f.relative_to(WORKSPACE))
                embed_index[rel] = {
                    "embedding": avg_embedding.tolist(),
                    "topics": _infer_topics(content),  # 用关键词快速推断
                    "preview": content[:200],
                    "updated": datetime.now().isoformat()
                }
        except Exception as e:
            continue
    
    save_json(MEMORY_DIR / "embed-index.json", embed_index)
    return {"indexed": len(embed_index)}
```

#### Step 3：将 semantic_search 改为混合检索

```python
def semantic_search(query: str, top_n: int = 8) -> List[Dict]:
    """
    混合检索：向量语义 + 关键词双路召回 → RRF融合
    """
    # 关键词路（保留现有逻辑，快速兜底）
    keyword_results = _keyword_search(query, top_n=top_n*2)
    
    # 向量路（新增，需要 embed-index.json）
    try:
        embed_results = embedding_search(query, top_k=top_n*2)
    except:
        embed_results = []
    
    # RRF融合（倒数排名融合）
    combined_scores = defaultdict(float)
    for rank, r in enumerate(keyword_results):
        combined_scores[r["file"]] += 0.6 / (60 + rank)
    for rank, r in enumerate(embed_results):
        combined_scores[r["file"]] += 0.4 / (60 + rank)
    
    sorted_files = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 构建最终结果
    file_info = {r["file"]: r for r in keyword_results + embed_results}
    final_results = []
    for file_path, score in sorted_files[:top_n]:
        info = file_info.get(file_path, {})
        final_results.append({
            "file": file_path,
            "score": round(score, 3),
            "topics": info.get("topics", []),
            "preview": info.get("preview", "")[:100],
            "source": "hybrid"
        })
    
    return final_results
```

**预期收益**：语义检索质量大幅提升，中文同义词/近义词自动理解

---

#### Step 4：实现 autoRecall（AGENTS.md 注入改造）

在 AGENTS.md 中添加无感知注入指令：

```markdown
## 🔄 autoRecall 规则（2026-04-15 新增）

**每次响应前自动执行（无需显式调用）：**

1. 从上一轮用户消息中提取：实体（人名/地名/公司名）、关键事件（买入/卖出/修复/决策）、偏好（喜欢/不喜欢）
2. 调用 `memory_search(query=实体或事件, maxResults=3)` 获取相关记忆
3. 相关记忆自动注入上下文（放在 [relevant_memory] 标签下）
4. 输出时检查：若用户信息与记忆矛盾，标注「⚠️ 信息冲突，请核实」

**注入格式：**
```
[relevant_memory]
- 用户偏好：{偏好内容}（来源：记忆文件）
- 相关事件：{事件摘要}（来源：记忆文件）
[/relevant_memory]
```

**执行时机：** 每次用户消息处理前（心跳/cron/主动对话均适用）
```

**注意**：这需要修改 OpenClaw 的 agent loop 执行逻辑，或在 SOUL.md 中强化 autoRecall 指令

---

### 中期（1-2周）：独立提取LLM + Qdrant

**目标**：解放主模型算力 + 向量检索基础设施升级

#### Step 5：独立记忆提取 LLM（MiniMax-M2.7）

叶老板方案最核心的设计：**用专门的MiniMax-M2.7做记忆提取，不占用主模型**

我们实现方案：

```python
# 新建 scripts/memory_capture.py

"""
autoCapture 独立提取模块
使用 MiniMax-M2.7 专门负责从对话中提取记忆
不影响主模型响应速度
"""

MINIMAX_API_KEY = "xxxxx"  # MiniMax API Key
MINIMAX_MODEL = "MiniMax-M2.7"

EXTRACTION_PROMPT = """你是一个记忆提取专家。从用户对话中提取以下信息：

1. 事实（Fact）：可验证的具体信息
   - 人名、地名、日期、数字
   - 格式：{"type":"fact","content":"...","source":"对话"}

2. 偏好（Preference）：用户喜欢/不喜欢的
   - 格式：{"type":"preference","content":"...","source":"对话"}

3. 决定（Decision）：用户做出的重要决定
   - 格式：{"type":"decision","content":"...","reason":"...","source":"对话"}

4. 教训（Lesson）：用户纠正的错误或教训
   - 格式：{"type":"lesson","content":"...","source":"对话"}

只输出JSON数组，不要其他内容。无可提取内容时返回[]。
"""

def capture_from_conversation(messages: List[Dict]) -> List[Dict]:
    """
    从对话历史中自动提取记忆
    触发条件：每N轮对话 或 关键事件发生时
    """
    import httpx
    
    # 构建提取上下文（只送最新10条，避免token浪费）
    recent = messages[-10:]
    context = "\n".join([f"{m['role']}: {m['content'][:500]}" for m in recent])
    
    prompt = f"{EXTRACTION_PROMPT}\n\n对话：\n{context}"
    
    # 使用 MiniMax-M2.7（便宜且支持长上下文）
    response = httpx.post(
        "https://api.minimax.chat/v1/text/chatcompletion_v2",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        json={
            "model": MINIMAX_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.1
        },
        timeout=30.0
    )
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # 解析JSON
    try:
        extractions = json.loads(content)
    except:
        return []
    
    # 写入记忆文件
    for item in extractions:
        _write_memory(item)
    
    return extractions


def _write_memory(item: Dict):
    """根据类型写入对应记忆文件"""
    item_type = item.get("type")
    content = item.get("content", "")
    
    if not content:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if item_type == "fact":
        # 写入当日日记
        _append_to_daily(today, f"[事实] {content}")
    elif item_type == "preference":
        # 写入 USER.md
        _update_user_pref(content)
    elif item_type == "decision":
        # 写入 trade-journal.md 或 MEMORY.md
        _append_decision(content, item.get("reason"))
    elif item_type == "lesson":
        # 触发 learn_evolve
        _record_lesson(content)
```

**触发策略**：
```python
# 在 memory_evolve.py 中集成
def full_evolve():
    # ... 现有逻辑 ...
    
    # 每次进化时，检查是否需要提取新记忆
    if should_trigger_capture():
        try:
            from memory_capture import capture_from_conversation
            convos = get_recent_conversations(days=1)
            for conv in convos:
                msgs = get_conversation_messages(conv["id"])
                capture_from_conversation(msgs)
        except:
            pass  # 静默失败，不影响主流程
```

#### Step 6：Qdrant 替代 LanceDB（可选，如需高级过滤）

```bash
# 安装 Qdrant
docker pull qdrant/qdrant
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v /root/.openclaw/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

```python
# scripts/vector_store.py - Qdrant 客户端

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter

_client = None

def get_qdrant():
    global _client
    if _client is None:
        _client = QdrantClient(url="http://localhost:6333")
    return _client

def search_memories(query: str, top_k: int = 5, topic_filter: str = None):
    """
    Qdrant 语义搜索，支持元数据过滤
    topic_filter: 可按"股票"/"宝宝"/"系统"等过滤
    """
    client = get_qdrant()
    
    # 1. query → 嵌入
    model = get_embed_model()
    query_vec = model.encode([query])[0].tolist()
    
    # 2. 搜索
    filter_cond = None
    if topic_filter:
        filter_cond = Filter(
            should=[Filter(must=[{"key": "topic", "match": {"value": topic_filter}}])]
        )
    
    results = client.search(
        collection_name="memory",
        query_vector=query_vec,
        limit=top_k,
        query_filter=filter_cond,
        with_payload=True
    )
    
    return [{"file": r.payload["file"], "score": r.score, "preview": r.payload["preview"]} 
            for r in results]


def index_memory_file(file_path: str, content: str, topic: str):
    """将记忆文件索引到 Qdrant"""
    client = get_qdrant()
    model = get_embed_model()
    
    # 分块
    chunks = [content[i:i+500] for i in range(0, len(content), 400)]
    vectors = model.encode(chunks)
    
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        client.upsert(
            collection_name="memory",
            points=[{
                "id": f"{file_path}_{i}",
                "vector": vec.tolist(),
                "payload": {"file": file_path, "chunk_idx": i, "topic": topic, "preview": chunk[:100]}
            }]
        )
```

**Qdrant vs LanceDB 选择建议**：

| 场景 | 推荐 |
|------|------|
| 仅需要语义搜索 | LanceDB（内置，无需额外部署）|
| 需要元数据过滤（如只看"股票"类记忆） | Qdrant |
| 需要混合搜索（稠密+稀疏向量） | Qdrant |
| 需要分布式/高可用 | Qdrant |

**我们当前情况**：LanceDB 够用，Qdrant 是锦上添花，除非需要复杂过滤

---

### 长期（持续优化）：记忆进化闭环

#### Step 7：让 autoCapture 触发 learn_evolve（自动学习）

```python
# 在 memory_capture.py 中增强

def _record_lesson(content: str):
    """提取的教训自动触发自学习"""
    from learn_evolve import record_lesson
    
    # 判断类别
    if "股票" in content or "买入" in content or "卖出" in content:
        category = "stock"
    elif "系统" in content or "修复" in content:
        category = "system"
    else:
        category = "general"
    
    record_lesson(
        lesson_type="extracted",
        category=category,
        summary=content,
        details=f"来源：autoCapture自动提取",
        priority="medium"
    )
```

#### Step 8：每周蒸馏融合 LCM + autoCapture

```python
# 在 memory_evolve.py 的 distill_weekly_memories() 中增强

def distill_weekly_memories():
    # ... 现有 LCM 融合逻辑 ...
    
    # 新增：autoCapture 提取的精华
    try:
        from memory_capture import get_captured_memories
        captured = get_captured_memories(days=7)  # 本周自动提取的记忆
        for item in captured:
            if item["type"] == "decision":
                distillations[f"autoCapture:决策"] = [item["content"]]
            elif item["type"] == "lesson":
                distillations[f"autoCapture:教训"] = [item["content"]]
    except:
        pass
```

---

## 五、预期收益汇总

| 阶段 | 融入功能 | 解决的问题 | 复杂度 |
|------|---------|---------|--------|
| 短期 | bge-m3 嵌入 + 混合检索 | 伪语义→真语义，同义词自动理解 | 中（模型部署） |
| 短期 | autoRecall 指令 | 每次响应前自动注入相关记忆 | 低（AGENTS.md指令） |
| 中期 | 独立提取LLM | 主模型不费力提取，主模型响应速度不受影响 | 高（API集成+触发逻辑） |
| 中期 | Qdrant（可选） | 复杂元数据过滤/混合搜索 | 中（Docker部署） |
| 长期 | autoCapture→learn_evolve | 提取的教训自动进入自学习闭环 | 低（代码集成） |

---

## 六、最小可行方案（1天内可完成）

如果时间有限，**最小可行**的提升路径：

```
1. 部署 bge-m3（2小时）
   - 下载模型 + 写 embedding_search()
   - 改造 memory_plus semantic_search → 混合检索

2. autoRecall（30分钟）
   - 在 SOUL.md 添加 autoRecall 指令
   - 每次响应前自动 memory_search

结果：
- 语义检索从"关键词匹配"升级到"向量语义"
- 记忆注入从"被动"升级到"主动无感知"
```

---

## 七、风险与注意事项

1. **bge-m3 模型下载**：需要代理（TOOLS.md 已配置 mihomo）
2. **LanceDB vs Qdrant**：我们已有 LanceDB（OpenClaw 内置），不需要重复部署
3. **独立提取LLM成本**：MiniMax-M2.7 价格极低（$0.001/1K tokens），可忽略
4. **autoRecall 指令污染**：不要在每次响应中输出记忆内容，仅内部注入上下文
5. **Step 2 的 RRF融合权重**：0.6/0.4 是初始值，可根据准确率调整

---

_文档版本：v1.0 | 创建：2026-04-15 | 状态：待评审_
