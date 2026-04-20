# LightRAG 参数说明

## 一、提取参数（初始化配置）

### 文本分块
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chunk_token_size` | 1200 | 每个 chunk 的最大 token 数 |
| `chunk_overlap_token_size` | 100 | chunk 之间的重叠 token 数 |

### Embedding
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `embedding_batch_num` | 32 | embedding 批处理最大大小 |
| `embedding_func_max_async` | 16 | 最大并发异步 embedding 进程数 |

### 实体提取
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `entity_extract_max_gleaning` | 1 | 实体提取的循环次数 |
| `summary_context_size` | 10000 | 摘要生成的最大 token 数 |
| `summary_max_tokens` | 500 | 实体/关系描述的最大 token 数 |

### 并发控制
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_parallel_insert` | 2 | 批处理插入的并发数（建议 < 10）|
| `llm_model_max_async` | 4 | 最大并发异步 LLM 进程数 |

### 缓存
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enable_llm_cache` | True | 启用 LLM 结果缓存 |
| `enable_llm_cache_for_entity_extract` | True | 启用实体提取缓存 |

---

## 二、查询参数（QueryParam）

### 检索模式
| 参数 | 可选值 | 说明 |
|------|--------|------|
| `mode` | `local` / `global` / `hybrid` / `naive` / `mix` / `bypass` | 检索策略 |

- **local**: 侧重上下文相关信息
- **global**: 利用全局知识图谱
- **hybrid**: 结合 local 和 global
- **naive**: 基础搜索
- **mix**: 知识图谱 + 向量检索（配合 reranker 推荐）
- **bypass**: 跳过检索

### 检索数量
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_k` | 60 | local 模式为实体数，global 模式为关系数 |
| `chunk_top_k` | 20 | 检索的文本块数量 |

### Token 控制
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_entity_tokens` | 6000 | 实体上下文最大 token 数 |
| `max_relation_tokens` | 8000 | 关系上下文最大 token 数 |
| `max_total_tokens` | 30000 | 查询上下文总 token 预算 |

### 输出控制
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `only_need_context` | False | 仅返回检索上下文，不生成响应 |
| `only_need_prompt` | False | 仅返回生成的 prompt |
| `response_type` | Multiple Paragraphs | 响应格式：Single Paragraph / Bullet Points |
| `stream` | False | 启用流式输出 |

### 高级功能
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enable_rerank` | True | 启用重排序（需配置 reranker）|
| `conversation_history` | [] | 对话历史：`[{"role": "user/assistant", "content": "..."}]` |
| `model_func` | None | 覆盖本次查询使用的 LLM |
| `user_prompt` | None | 自定义 LLM 的额外指令 |

---

## 三、环境变量

以下参数可通过环境变量设置默认值：

| 环境变量 | 对应参数 | 默认值 |
|----------|----------|--------|
| `TOP_K` | `top_k` | 60 |
| `CHUNK_TOP_K` | `chunk_top_k` | 20 |
| `MAX_ENTITY_TOKENS` | `max_entity_tokens` | 6000 |
| `MAX_RELATION_TOKENS` | `max_relation_tokens` | 8000 |
| `MAX_TOTAL_TOKENS` | `max_total_tokens` | 30000 |

---

## 四、推荐配置

### 高质量场景
```python
QueryParam(
    mode="mix",
    top_k=60,
    chunk_top_k=20,
    enable_rerank=True
)
```

### 快速响应场景
```python
QueryParam(
    mode="local",
    top_k=20,
    chunk_top_k=10
)
```

### 大规模文档场景
```python
LightRAG(
    chunk_token_size=1600,
    max_parallel_insert=8,
    llm_model_max_async=8
)
```
