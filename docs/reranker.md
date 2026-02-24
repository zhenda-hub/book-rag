# Reranker 重排序

## 概述

Reranker（重排序器）是 RAG 系统中的关键组件，用于对向量检索的结果进行精细排序，提高检索结果的相关性质量。

本项目使用 **FlashRank** 实现 Reranker 功能，这是一个基于 Rust 的快速轻量级重排序模型。

---

## 为什么需要 Reranker？

### 传统向量检索的局限性

| 问题 | 说明 | 影响 |
|------|------|------|
| 语义理解有限 | 向量相似度基于语义距离，无法精确理解查询意图 | 可能返回语义相近但无关的结果 |
| 阈值难以设定 | `SIMILARITY_THRESHOLD` 过高过滤有用文档，过低返回噪声 | 需要反复调优 |
| 无上下文理解 | 独立计算每个文档的相似度，不考虑查询-文档对的匹配度 | 无法区分真正相关的结果 |

### Reranker 的优势

```
向量检索 → Top-10 候选 → Reranker 重排序 → Top-5 精选结果
   ↓                              ↓
 广泛召回                     精准排序
```

- **精准排序**：基于查询-文档对的相关性打分
- **无需阈值**：自动过滤不相关内容
- **端到端优化**：模型专门为检索排序任务训练

---

## 核心组件

### FlashRankReranker

**位置**: `src/reranker/flashrank_reranker.py`

**初始化参数**:

```python
from src.reranker.flashrank_reranker import FlashRankReranker

reranker = FlashRankReranker(
    top_k=5,           # 保留的文档数量
    model=""           # 模型名称（空值使用默认模型）
)
```

**可用模型**:

| 模型 | 大小 | 速度 | 精度 | 推荐场景 |
|------|------|------|------|---------|
| `""` (默认) | TinyBERT-L-2 | ⚡⚡⚡ | ⭐⭐ | 快速响应 |
| `ms-marco-TinyBERT-L-2-v2` | 4.4MB | ⚡⚡⚡ | ⭐⭐ | 开发测试 |
| `ms-marco-MiniLM-L-12-v2` | 34MB | ⚡⚡ | ⭐⭐⭐ | 生产环境 |

**使用方法**:

```python
# 检索结果（来自向量搜索）
sources = [
    {
        "content": "文档内容...",
        "source": "doc1.pdf",
        "metadata": {"page": 1, "chapter": "第一章"},
        "score": 0.75,  # 原始向量相似度
    },
    # ... 更多文档
]

# 重排序
reranked = reranker.rerank("用户查询", sources)

# 返回 Top-K 结果
for doc in reranked:
    print(f"Score: {doc['score']:.4f}")
    print(f"Content: {doc['content'][:50]}...")
```

**返回格式**:

```python
[
    {
        "content": "文档内容...",
        "source": "doc1.pdf",
        "metadata": {
            "page": 1,
            "chapter": "第一章",
            "original_score": 0.75  # 原始向量分数
        },
        "score": 0.92  # Reranker 相关性分数 (0-1)
    },
    ...
]
```

---

## 配置说明

### 环境变量

```bash
# .env 配置
# 启用 Reranker
RERANKER_ENABLED=true
# Reranker 后保留的文档数量
RERANKER_TOP_K=5
# Reranker 模型（空值使用默认模型）
RERANKER_MODEL=
```

### 配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `RERANKER_ENABLED` | `false` | 是否启用 Reranker |
| `RERANKER_TOP_K` | `5` | 重排序后保留的文档数量 |
| `RERANKER_MODEL` | `""` | FlashRank 模型名称 |

**调优建议**:

- **RERANKER_TOP_K**: 设置为 LLM 能够处理的上下文数量（3-10）
- **RERANKER_MODEL**: 开发用默认模型，生产用 MiniLM

---

## 集成方式

### 在 Web 界面中使用

Streamlit 聊天组件已集成 Reranker：

```python
# src/web/streamlit_app.py 中的集成示例
from src.reranker.flashrank_reranker import FlashRankReranker

# 初始化 Reranker（如果启用）
if config.RERANKER_ENABLED:
    reranker = FlashRankReranker(
        top_k=config.RERANKER_TOP_K,
        model=config.RERANKER_MODEL
    )

# 检索 + Rerank
sources = vector_store.search(query, top_k=10)
if config.RERANKER_ENABLED:
    sources = reranker.rerank(query, sources)
```

### 在代码中直接使用

```python
from src.reranker.flashrank_reranker import FlashRankReranker

# 初始化
reranker = FlashRankReranker(top_k=5)

# 检索
from src.vector_store import get_vector_store
vector_store = get_vector_store()
sources = vector_store.search(query, top_k=10)

# 重排序
reranked_sources = reranker.rerank(query, sources)
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                      用户查询                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   向量检索 (Top-K)                       │
│  - 返回前 K 个语义相似的文档                              │
│  - 无过滤，保留所有候选                                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Reranker 重排序                         │
│  - 精确计算查询-文档相关性                                │
│  - 过滤不相关内容                                        │
│  - 返回 Top-N 最相关文档                                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      LLM 生成                            │
│  - 基于精选文档生成答案                                   │
│  - 引用来源信息                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 与相似度阈值的对比

| 特性 | 相似度阈值 | Reranker |
|------|------------|----------|
| 过滤方式 | 硬阈值（0-1） | 智能重排序 |
| 参数调优 | 难以设定 | 无需调优 |
| 结果质量 | 可能误伤有用文档 | 精准排序 |
| 速度 | 无额外开销 | 轻微延迟 |
| 推荐场景 | 简单场景 | 生产环境 |

**迁移指南**:

如果之前使用 `SIMILARITY_THRESHOLD`：

1. 移除阈值配置
2. 启用 Reranker：`RERANKER_ENABLED=true`
3. 设置 `RERANKER_TOP_K` 为期望的结果数量

---

## 性能参考

| 场景 | 模型 | 延迟 | 吞吐量 |
|------|------|------|--------|
| 本地开发 | 默认模型 | ~50ms | ~20 req/s |
| 生产环境 | MiniLM | ~150ms | ~7 req/s |

**注**: 性能取决于硬件配置和文档长度

---

## 测试

```bash
# 运行 Reranker 测试
uv run pytest tests/test_reranker.py -v

# 测试特定功能
uv run pytest tests/test_reranker.py::test_reranker_top_k -v
```

**测试覆盖**:

- ✅ Top-K 结果数量验证
- ✅ 过滤不相关内容
- ✅ 相关性排序验证
- ✅ 空输入处理
- ✅ 结果结构验证

---

## 故障排除

### 问题：Rerank 返回原始结果

**原因**: 模型加载失败或异常

**解决**:
```python
# 检查日志
logger.info(f"Reranker 初始化 | model={config.RERANKER_MODEL}")

# 验证模型安装
pip show flashrank
```

### 问题：结果数量少于 Top-K

**原因**: 候选文档数量不足

**解决**:
```bash
# 增加向量检索的 Top-K
TOP_K_RETRIEVALS=20  # 大于 RERANKER_TOP_K
```

---

## 参考资料

- [FlashRank GitHub](https://github.com/princeton-nlp/FlashRank)
- [LangChain Document Compressors](https://python.langchain.com/docs/how_to/#document-compressors)
- [MS MARCO Dataset](https://microsoft.github.io/msmarco/)
