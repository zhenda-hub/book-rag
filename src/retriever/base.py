"""统一 RAG 检索器模块 - 完全使用 LangChain"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from langchain_core.documents import Document as LCDocument
from langchain.retrievers import EnsembleRetriever as LCEnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from src.config import config, get_embeddings
from src.logger import get_logger

if TYPE_CHECKING:
    from src.vector_store import VectorStore
    from src.loaders.base import Document

logger = get_logger("unified_retriever")


class UnifiedRetriever:
    """统一检索器 - 通过权重配置支持语义、全文、混合检索

    完全使用 LangChain 的 EnsembleRetriever 实现。
    """

    def __init__(
        self,
        vector_store: "VectorStore",
        mode: Optional[str] = None,
        documents: Optional[List["Document"]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化统一检索器

        Args:
            vector_store: 向量存储实例
            mode: 检索模式 ("semantic", "fulltext", "ensemble") - 向后兼容参数，优先级低于 weights
            documents: 用于 BM25 索引的文档列表（需要全文检索时必须提供）
            weights: 检索权重 {"semantic": 0.7, "fulltext": 0.3}，默认 {"semantic": 0.2, "fulltext": 0.8}
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
        """
        self.vector_store = vector_store
        self.top_k = top_k
        self.filter_metadata = filter_metadata
        self._documents = documents or []

        # 处理权重配置：mode 参数转换为 weights（向后兼容）
        if weights is None:
            if mode == "semantic":
                weights = {"semantic": 1.0, "fulltext": 0.0}
            elif mode == "fulltext":
                weights = {"semantic": 0.0, "fulltext": 1.0}
            else:
                # 默认配置：偏向全文检索（更适合专有名词查询）
                weights = {"semantic": 0.2, "fulltext": 0.8}

        self._weights = weights

        # 使用统一的 embeddings 工厂函数
        self._embeddings = get_embeddings()

        self._lc_retriever = None
        self._initialize_lc_retriever()

    def _initialize_lc_retriever(self) -> None:
        """初始化 LangChain 检索器 - 统一使用 EnsembleRetriever"""
        logger.debug(f"初始化检索器 | 权重: {self._weights}")

        vector_retriever = self._create_vector_retriever()
        semantic_weight = self._weights.get("semantic", 0)
        fulltext_weight = self._weights.get("fulltext", 0)

        # 构建检索器列表和权重列表
        retrievers = []
        weights = []

        # 添加语义检索器（如果权重 > 0）
        if semantic_weight > 0:
            retrievers.append(vector_retriever)
            weights.append(semantic_weight)

        # 添加全文检索器（如果权重 > 0 且有文档）
        if fulltext_weight > 0:
            bm25_retriever = self._create_bm25_retriever()
            if bm25_retriever is not None:
                retrievers.append(bm25_retriever)
                weights.append(fulltext_weight)
            elif semantic_weight == 0:
                # 没有文档且语义权重为0，回退到语义检索
                logger.warning("没有文档用于 BM25 检索，回退到语义检索")
                retrievers.append(vector_retriever)
                weights.append(1.0)

        # 创建 EnsembleRetriever
        if len(retrievers) == 1:
            # 只有一个检索器，直接使用（优化性能）
            self._lc_retriever = retrievers[0]
            logger.debug(f"使用单一检索器 | 类型: {type(self._lc_retriever).__name__}")
        else:
            self._lc_retriever = LCEnsembleRetriever(
                retrievers=retrievers,
                weights=weights
            )
            logger.debug(f"使用混合检索 | 权重: {weights}")

    def _create_vector_retriever(self):
        """创建 LangChain 向量检索器"""
        from langchain_chroma import Chroma

        lc_chroma = Chroma(
            client=self.vector_store.client,
            collection_name=self.vector_store.collection_name,
            embedding_function=self._embeddings,
        )

        search_kwargs = {"k": self.top_k}
        if self.filter_metadata:
            search_kwargs["filter"] = self.filter_metadata

        return lc_chroma.as_retriever(search_kwargs=search_kwargs)

    def _create_bm25_retriever(self) -> Optional[BM25Retriever]:
        """创建 BM25 全文检索器"""
        if not self._documents:
            logger.warning("没有文档用于 BM25 检索，回退到语义检索")
            # 返回 None 表示回退到语义检索
            return None

        lc_docs = [self._to_lc_doc(doc) for doc in self._documents]
        bm25 = BM25Retriever.from_documents(lc_docs)
        bm25.k = self.top_k
        logger.debug(f"BM25 检索器创建完成 | 文档数: {len(lc_docs)}")
        return bm25

    @staticmethod
    def _to_lc_doc(document: "Document") -> LCDocument:
        """将项目 Document 转换为 LangChain Document"""
        return LCDocument(page_content=document.content, metadata={**document.metadata, "source": document.source})

    @staticmethod
    def _from_lc_doc(lc_doc: LCDocument) -> Dict[str, Any]:
        """将 LangChain Document 转换为标准格式"""
        return {
            "content": lc_doc.page_content,
            "metadata": lc_doc.metadata,
            "source": lc_doc.metadata.get("source", ""),
        }

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 查询文本

        Returns:
            检索结果列表
        """
        logger.info(f"检索 | 权重: {self._weights} | 查询: {query[:50]}... | Top-K: {self.top_k}")

        lc_docs = self._lc_retriever.invoke(query)
        results = [self._from_lc_doc(doc) for doc in lc_docs]

        # 全文检索模式：只保留包含完整查询词的结果
        if self._weights.get("fulltext", 0) > 0 and self._weights.get("semantic", 0) == 0:
            filtered_results = []
            query_clean = query.replace(" ", "")
            for result in results:
                if query_clean in result["content"]:
                    filtered_results.append(result)
            results = filtered_results

        logger.info(f"检索完成 | 返回: {len(results)} 个结果")
        return results

    def get_context(self, query: str) -> str:
        """
        获取检索到的上下文文本

        Args:
            query: 查询文本

        Returns:
            合并后的上下文文本
        """
        results = self.retrieve(query)

        if not results:
            return "未找到相关文档。"

        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "未知来源")
            content = result["content"]
            context_parts.append(f"[参考 {i}] 来源: {source}\n{content}")

        return "\n\n".join(context_parts)

    def get_sources(self, query: str) -> List[Dict[str, Any]]:
        """
        获取带来源信息的检索结果（QA 链需要）

        Args:
            query: 查询文本

        Returns:
            来源信息列表，score 设为 0.0（由 Reranker 替换）
        """
        logger.debug(f"获取来源信息 | 查询: {query}")

        lc_docs = self._lc_retriever.invoke(query)
        results = [self._from_lc_doc(doc) for doc in lc_docs]

        # 全文检索模式：只保留包含完整查询词的结果
        if self._weights.get("fulltext", 0) > 0 and self._weights.get("semantic", 0) == 0:
            filtered_results = []
            query_clean = query.replace(" ", "")
            for result in results:
                if query_clean in result["content"]:
                    filtered_results.append(result)
            results = filtered_results

        sources = []
        for result in results:
            sources.append({
                "content": result["content"],
                "source": result["metadata"].get("source", "未知来源"),
                "metadata": result["metadata"],
                "score": 0.0,  # Reranker 会替换
            })

        # 汇总来源信息
        unique_sources = set(s["source"] for s in sources)
        if len(unique_sources) == 1:
            logger.info(f"来源: {next(iter(unique_sources))} | 检索到 {len(sources)} 个文档块")
        else:
            for source in unique_sources:
                count = sum(1 for s in sources if s["source"] == source)
                logger.info(f"来源: {source} | {count} 个文档块")
        return sources


# 保留旧类名以兼容现有代码
class Retriever(UnifiedRetriever):
    """兼容旧代码的别名

    默认使用纯语义检索（通过 mode="semantic" 自动转换为权重配置）。
    """

    def __init__(
        self,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        vector_store: Optional["VectorStore"] = None,
    ) -> None:
        """初始化检索器（兼容接口）

        Args:
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            vector_store: 可选的向量存储实例
        """
        from src.vector_store import get_vector_store

        if vector_store is None:
            vector_store = get_vector_store()

        # mode="semantic" 会被自动转换为 weights={"semantic": 1.0, "fulltext": 0.0}
        super().__init__(
            vector_store=vector_store,
            mode="semantic",  # 向后兼容
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
