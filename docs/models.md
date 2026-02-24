## 模型概览

| 类型 | 用途 | 默认模型 |
|------|------|----------|
| Embedding | 文档向量化、语义检索 | `paraphrase-multilingual-MiniLM-L12-v2` |
| LLM | 问答生成、多轮对话 | `deepseek/deepseek-chat` (OpenRouter) |
| Reranker | 检索结果重排序 | FlashRank 默认模型 |

---

## Embedding 模型

**位置**: `src/embeddings.py`

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
```

**查看已下载模型**:
```bash
ls -la ~/.cache/huggingface/hub/
du -sh ~/.cache/huggingface/hub/models--sentence-transformers--*
```

---

## LLM 模型

**位置**: `src/chains/llm_manager.py`

通过 **OpenRouter** 支持多个模型：

| 简写 | 完整路径 | 说明 |
|------|----------|------|
| `deepseek` | `deepseek/deepseek-chat` | 默认，性价比高 |
| `gpt-4` | `openai/gpt-4-turbo` | GPT-4 |
| `claude-opus` | `anthropic/claude-3-opus` | Claude |
| `gemini` | `google/gemini-pro` | Gemini |

**获取免费模型**:
```python
from src.chains.llm_manager import LLMManager

manager = LLMManager(api_key="your-key")
free_models = manager.get_free_models()
```

---

## Reranker 模型

**位置**: `src/reranker/flashrank_reranker.py`

| 模型 | 大小 | 速度 | 场景 |
|------|------|------|------|
| 默认 (MultiBERT-L12) | 162MB | ⚡⚡⚡ | 默认，首次使用自动下载 |
| `ms-marco-MiniLM-L-12-v2` | ~34MB | ⚡⚡ | 生产环境 |

**查看已下载模型**:
```bash
# 默认下载位置
ls -la /tmp/ms-marco-MultiBERT-L-12/

# 查看大小
du -sh /tmp/ms-marco-MultiBERT-L-12/
```

⚠️ **注意**: 模型下载到 `/tmp`，系统重启后需重新下载

详细说明参见 [docs/reranker.md](./reranker.md)
