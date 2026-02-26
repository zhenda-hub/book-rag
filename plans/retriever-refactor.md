# 检索器重构计划 - 统一使用 LangChain

## Context

当前项目中语义检索和混合检索是两套割裂的代码：
- `src/retriever/base.py` (Retriever) - 不使用 LangChain，直接调用 VectorStore
- `src/retriever/ensemble.py` (EnsembleRetriever) - 使用 LangChain 的 EnsembleRetriever

**问题**：
- 代码重复（`get_context()`, `get_sources()` 等方法几乎相同）
- 架构不一致，维护成本高
- 两种模式使用不同的向量存储访问方式

**重要发现**：Reranker 会替换原始分数！
- VectorStore 的相似度分数 → 被保存到 `metadata["original_score"]`
- 最终的 `score` 字段 → 被 Reranker 的 `relevance_score` 替代
- **结论**：不需要特殊处理分数，直接用 LangChain 即可

## 目标

统一使用 LangChain 的检索器，完全移除自研的检索器代码。

## 方案：完全用 LangChain

```
UnifiedRetriever (轻量级适配器)
  ├── 内部完全使用 LangChain 检索器
  ├── 对外暴露统一接口 (retrieve, get_context, get_sources)
  └── 不需要特殊处理分数（Reranker 会替换）
```

### 检索器映射

| 用户选择 | mode 参数 | LangChain 实现 |
|----------|-----------|----------------|
| 语义检索 | "semantic" | `LCChroma.as_retriever()` |
| 全文检索 | "fulltext" | `BM25Retriever` |
| 混合检索 | "ensemble" | `LCEnsembleRetriever([BM25, Vector])` |

## 实施步骤

### Step 1: 重写 base.py 为 UnifiedRetriever

**文件**: `src/retriever/base.py`

```python
from langchain_community.vectorstores import Chroma as LCChroma
from langchain.retrievers import EnsembleRetriever as LCEnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document as LCDocument
from langchain_community.embeddings import SentenceTransformerEmbeddings
from src.config import config

class UnifiedRetriever:
    """统一的检索器，内部完全使用 LangChain"""

    def __init__(
        self,
        vector_store: "VectorStore",
        mode: str = "semantic",
        documents: Optional[List[Document]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.vector_store = vector_store
        self.mode = mode
        self.top_k = top_k
        self.filter_metadata = filter_metadata
        self._documents = documents or []
        self._weights = weights or {"semantic": 0.7, "fulltext": 0.3}

        # 创建 LangChain embeddings
        self._embeddings = SentenceTransformerEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': config.EMBEDDING_DEVICE},
            encode_kwargs={
                'batch_size': 32,
                'normalize_embeddings': True,
                'show_progress_bar': False,
            }
        )

        # 初始化 LangChain 检索器
        self._lc_retriever = self._initialize_lc_retriever()

    def _initialize_lc_retriever(self):
        """根据模式创建对应的 LangChain 检索器"""
        vector_retriever = self._create_vector_retriever()

        if self.mode == "semantic":
            return vector_retriever
        elif self.mode == "fulltext":
            return self._create_bm25_retriever()
        else:  # ensemble
            return LCEnsembleRetriever(
                retrievers=[self._create_bm25_retriever(), vector_retriever],
                weights=[self._weights["fulltext"], self._weights["semantic"]]
            )

    def _create_vector_retriever(self):
        """创建 LangChain VectorRetriever"""
        lc_chroma = LCChroma(
            client=self.vector_store.client,
            collection_name=self.vector_store.collection_name,
            embedding_function=self._embeddings,
        )

        search_kwargs = {"k": self.top_k}
        if self.filter_metadata:
            search_kwargs["filter"] = self.filter_metadata

        return lc_chroma.as_retriever(search_kwargs=search_kwargs)

    def _create_bm25_retriever(self) -> BM25Retriever:
        """创建 BM25 全文检索器"""
        lc_docs = [LCDocument(page_content=doc.content, metadata={**doc.metadata, "source": doc.source})
                   for doc in self._documents]
        bm25 = BM25Retriever.from_documents(lc_docs)
        bm25.k = self.top_k
        return bm25

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """检索相关文档"""
        lc_docs = self._lc_retriever.invoke(query)
        return [self._from_lc_doc(doc) for doc in lc_docs]

    def get_sources(self, query: str) -> List[Dict[str, Any]]:
        """获取带来源信息的检索结果（QA 链需要）"""
        lc_docs = self._lc_retriever.invoke(query)
        # 分数会被 Reranker 替换，这里返回 0.0 即可
        return [{
            "content": doc.page_content,
            "source": doc.metadata.get("source", "未知来源"),
            "metadata": doc.metadata,
            "score": 0.0,  # 会被 Reranker 替换
        } for doc in lc_docs]

    def get_context(self, query: str) -> str:
        """获取检索到的上下文文本"""
        results = self.retrieve(query)
        if not results:
            return "未找到相关文档。"

        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "未知来源")
            content = result["content"]
            context_parts.append(f"[参考 {i}] 来源: {source}\n{content}")

        return "\n\n".join(context_parts)

    @staticmethod
    def _from_lc_doc(lc_doc: LCDocument) -> Dict[str, Any]:
        """将 LangChain Document 转换为标准格式"""
        return {
            "content": lc_doc.page_content,
            "metadata": lc_doc.metadata,
            "source": lc_doc.metadata.get("source", ""),
        }
```

### Step 2: 删除 ensemble.py

**文件**: `src/retriever/ensemble.py`

删除此文件，功能已合并到 `UnifiedRetriever`

### Step 3: 删除 embeddings.py

**文件**: `src/embeddings.py`

删除此文件，使用 LangChain 的 `SentenceTransformerEmbeddings`

### Step 4: 更新 vector_store.py（仅 embeddings）

**文件**: `src/vector_store.py`

**保留**：VectorStore 类及其特有方法

**原因**：Web 界面大量使用这些统计方法，LangChain 没有直接支持：

| 方法 | 用途 | 调用位置 |
|------|------|----------|
| `get_all_sources()` | 获取所有文档来源列表 | Web 界面显示文档 |
| `get_chunk_count_by_source()` | 获取某文档的 chunk 数量 | Web 界面显示统计 |
| `get_all_sources_with_counts()` | 获取所有来源及数量 | 文档管理功能 |
| `delete_by_source()` | 按来源删除 | 文档删除功能 |
| `source_exists()` | 检查文档是否存在 | 上传时去重 |

**只修改**：改用 LangChain embeddings

```python
# 删除
from src.embeddings import get_embeddings
self._embeddings = get_embeddings()

# 改为
from langchain_community.embeddings import SentenceTransformerEmbeddings
from src.config import config

self._embeddings = SentenceTransformerEmbeddings(
    model_name=config.EMBEDDING_MODEL,
    model_kwargs={'device': config.EMBEDDING_DEVICE},
    encode_kwargs={'batch_size': 32, 'normalize_embeddings': True}
)
```

### Step 5: 更新调用代码

**文件**: `src/web/components/chat.py`

简化 `_create_retriever()` 函数：

```python
def _create_retriever(vector_store: "VectorStore"):
    from src.retriever.base import UnifiedRetriever

    search_mode = st.session_state.search_mode
    weights = st.session_state.retriever_weights

    filter_dict = None
    if st.session_state.selected_sources:
        filter_dict = {"source": {"$in": st.session_state.selected_sources}}

    documents = None
    if search_mode in ["全文检索", "混合检索"]:
        documents = _get_all_documents(vector_store, filter_dict)

    mode_map = {
        "语义检索": "semantic",
        "全文检索": "fulltext",
        "混合检索": "ensemble",
    }

    return UnifiedRetriever(
        vector_store=vector_store,
        mode=mode_map[search_mode],
        documents=documents,
        weights=weights,
        filter_metadata=filter_dict,
    )
```

## Critical Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/retriever/base.py` | **重写** | 创建 `UnifiedRetriever`，完全用 LangChain |
| `src/retriever/ensemble.py` | **删除** | 功能合并到 `base.py` |
| `src/embeddings.py` | **删除** | 用 LangChain 替代 |
| `src/vector_store.py` | **部分修改** | 保留特有方法，只改 embeddings |
| `src/web/components/chat.py` | **修改** | 简化 `_create_retriever()` |
| `src/chains/qa_chain.py` | **不变** | 继续使用 `get_sources()` 接口 |
| `tests/test_retriever/test_base.py` | **更新** | 添加三种模式测试 |

## 代码复用效果

### 修改前
```
base.py (Retriever)        → 自研，直接调用 VectorStore
ensemble.py (EnsembleRetriever) → 使用 LangChain
  └── 重复：get_context(), get_sources()

embeddings.py (Embeddings) → 自研封装，与 LangChain 功能相同
```

### 修改后
```
UnifiedRetriever
  ├── 内部完全使用 LangChain
  ├── _create_vector_retriever()  ← 共享！
  ├── get_sources()               ← 单一实现
  └── get_context()               ← 单一实现

无需处理分数（Reranker 会替换）

VectorStore → 保留，因为 Web 界面需要特有统计方法
```

## 减少代码量

| 文件 | 删除 | 新增 | 净减少 |
|------|------|------|--------|
| `ensemble.py` | ~250 行 | 0 | -250 |
| `embeddings.py` | ~84 行 | 0 | -84 |
| `base.py` | ~150 行 | ~150 行 | 0 |
| **总计** | **~484 行** | **~150 行** | **-334 行** |

## 关键简化

由于 Reranker 替换原始分数，我们：

1. **不需要** `similarity_search_with_score`
2. **不需要** 保留 `VectorStore.search()` 调用
3. **不需要** 特殊处理分数逻辑
4. **完全**使用 LangChain 的标准 API

这使得 `UnifiedRetriever` 成为一个真正的轻量级适配器，约 150 行代码。

## Verification

1. **语义检索模式**：选择部分文档，确认只返回选中文档的引用
2. **全文检索模式**：选择部分文档，确认只返回选中文档的引用
3. **混合检索模式**：选择部分文档，确认只返回选中文档的引用
4. **分数显示**：确认引用中显示 Reranker 的分数

## Test Commands

```bash
# 运行测试
uv run pytest tests/test_retriever/test_base.py -v

# 启动应用测试
uv run streamlit run src/web/streamlit_app.py
```
