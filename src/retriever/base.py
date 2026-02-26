"""统一 RAG 检索器模块 - 使用 LangChain"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from langchain_core.documents import Document as LCDocument
from langchain.retrievers import EnsembleRetriever as LCEnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from src.logger import get_logger

if TYPE_CHECKING:
    from src.vector_store import VectorStore
    from src.loaders.base import Document

logger = get_logger("unified_retriever")


class UnifiedRetriever:
    """统一检索器 - 支持语义检索、全文检索、混合检索

    内部使用 LangChain 检索器，对外暴露统一接口。
    """

    def __init__(
        self,
        vector_store: "VectorStore",
        mode: str = "semantic",
        documents: Optional[List["Document"]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化统一检索器

        Args:
            vector_store: 向量存储实例
            mode: 检索模式 ("semantic", "fulltext", "ensemble")
            documents: 用于 BM25 索引的文档列表（fulltext/ensemble 模式需要）
            weights: 检索权重 {"semantic": 0.7, "fulltext": 0.3}
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
        """
        self.vector_store = vector_store
        self.mode = mode
        self.top_k = top_k
        self.filter_metadata = filter_metadata
        self._documents = documents or []
        self._weights = weights or {"semantic": 0.7, "fulltext": 0.3}
        self._lc_retriever = None
        self._initialize_lc_retriever()

    def _initialize_lc_retriever(self) -> None:
        """初始化 LangChain 检索器"""
        logger.debug(f"初始化检索器 | 模式: {self.mode}")

        vector_retriever = self._create_vector_retriever()

        if self.mode == "semantic":
            self._lc_retriever = vector_retriever
            logger.debug("使用语义检索")

        elif self.mode == "fulltext":
            bm25_retriever = self._create_bm25_retriever()
            if bm25_retriever is None:
                # 没有文档，回退到语义检索
                self._lc_retriever = vector_retriever
            else:
                self._lc_retriever = bm25_retriever
            logger.debug("使用全文检索")

        else:  # ensemble
            bm25_retriever = self._create_bm25_retriever()
            if bm25_retriever is not None:
                retrievers = [bm25_retriever, vector_retriever]
                weights = [self._weights["fulltext"], self._weights["semantic"]]
            else:
                logger.warning("未提供文档，仅使用语义检索")
                retrievers = [vector_retriever]
                weights = [1.0]

            self._lc_retriever = LCEnsembleRetriever(
                retrievers=retrievers,
                weights=weights
            )
            logger.debug(f"使用混合检索 | 权重: {weights}")

    def _create_vector_retriever(self):
        """创建 LangChain 向量检索器"""
        from langchain_community.vectorstores import Chroma as LCChroma
        from src.embeddings import get_embeddings

        embeddings = get_embeddings()
        lc_chroma = LCChroma(
            client=self.vector_store.client,
            collection_name=self.vector_store.collection_name,
            embedding_function=embeddings,
        )

        search_kwargs = {"k": self.top_k}
        if self.filter_metadata:
            search_kwargs["filter"] = self.filter_metadata

        return lc_chroma.as_retriever(search_kwargs=search_kwargs)

    def _create_bm25_retriever(self) -> BM25Retriever:
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

    def _vector_store_search_with_score(self, query: str) -> List[Dict[str, Any]]:
        """直接使用 VectorStore.search() 获取带分数的结果"""
        return self.vector_store.search(
            query=query,
            top_k=self.top_k,
            filter=self.filter_metadata,
        )

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 查询文本

        Returns:
            检索结果列表
        """
        logger.info(f"检索 | 模式: {self.mode} | 查询: {query[:50]}... | Top-K: {self.top_k}")

        lc_docs = self._lc_retriever.invoke(query)
        results = [self._from_lc_doc(doc) for doc in lc_docs]

        # 全文检索模式：只保留包含完整查询词的结果
        if self.mode == "fulltext":
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
            来源信息列表，包含分数
        """
        logger.debug(f"获取来源信息 | 查询: {query}")

        # 对于语义检索，使用 similarity_search_with_score 获取分数
        if self.mode == "semantic":
            results = self._vector_store_search_with_score(query)
        else:
            lc_docs = self._lc_retriever.invoke(query)
            results = [self._from_lc_doc(doc) for doc in lc_docs]

            # 全文检索模式：只保留包含完整查询词的结果
            if self.mode == "fulltext":
                filtered_results = []
                query_clean = query.replace(" ", "")
                for result in results:
                    if query_clean in result["content"]:
                        filtered_results.append(result)
                results = filtered_results

        sources = []
        for result in results:
            score = result.get("score", 0.0)
            sources.append({
                "content": result["content"],
                "source": result["metadata"].get("source", "未知来源"),
                "metadata": result["metadata"],
                "score": score,
            })
            logger.info(f"来源: {result['metadata'].get('source', '未知来源')} | 相似度: {score:.2%}")

        logger.debug(f"来源获取完成 | 数量: {len(sources)}")
        return sources


# 保留旧类名以兼容现有代码
class Retriever(UnifiedRetriever):
    """兼容旧代码的别名，使用语义检索模式"""

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

        super().__init__(
            vector_store=vector_store,
            mode="semantic",
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
