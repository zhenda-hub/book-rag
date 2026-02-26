"""使用 LangChain EnsembleRetriever 的混合检索"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from langchain_core.documents import Document as LCDocument
from langchain.retrievers import EnsembleRetriever as LCEnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from src.logger import get_logger

if TYPE_CHECKING:
    from src.vector_store import VectorStore
    from src.loaders.base import Document

logger = get_logger("ensemble_retriever")


class EnsembleRetriever:
    """混合检索器封装 - 结合 BM25 全文检索和语义向量检索"""

    def __init__(
        self,
        vector_store: "VectorStore",
        documents: Optional[List["Document"]] = None,
        semantic_weight: float = 0.7,
        fulltext_weight: float = 0.3,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化混合检索器

        Args:
            vector_store: 向量存储实例
            documents: 用于构建 BM25 索引的文档列表
            semantic_weight: 语义检索权重 (0-1)
            fulltext_weight: 全文检索权重 (0-1)
            top_k: 返回结果数量
            filter_metadata: 向量检索的元数据过滤条件
        """
        self.vector_store = vector_store
        self.semantic_weight = semantic_weight
        self.fulltext_weight = fulltext_weight
        self.top_k = top_k
        self.filter_metadata = filter_metadata
        self._documents: List["Document"] = documents or []

        # 确定检索模式
        if self.semantic_weight == 0 and self.fulltext_weight > 0:
            self._mode = "fulltext"
        elif self.fulltext_weight == 0 and self.semantic_weight > 0:
            self._mode = "semantic"
        else:
            self._mode = "ensemble"

        # 初始化相应的检索器
        self._bm25_retriever: Optional[BM25Retriever] = None
        self._ensemble: Optional[LCEnsembleRetriever] = None
        self._initialize_retrievers()

    def _initialize_retrievers(self) -> None:
        """初始化检索器（根据模式选择对应的检索器）"""
        logger.debug(f"初始化检索器 | 模式: {self._mode} | 语义权重: {self.semantic_weight} | 全文权重: {self.fulltext_weight}")

        # 纯全文检索模式 - 只使用 BM25
        if self._mode == "fulltext":
            if not self._documents:
                logger.warning("全文检索模式但没有文档，回退到语义检索")
                self._mode = "semantic"
                self._vector_retriever = self._create_vector_retriever()
            else:
                self._bm25_retriever = self._create_bm25_retriever()
                logger.debug("使用纯 BM25 全文检索")

        # 纯语义检索模式 - 只使用向量检索
        elif self._mode == "semantic":
            self._vector_retriever = self._create_vector_retriever()
            logger.debug("使用纯向量语义检索")

        # 混合检索模式 - 使用 EnsembleRetriever
        else:
            self._vector_retriever = self._create_vector_retriever()
            if self._documents:
                self._bm25_retriever = self._create_bm25_retriever()
                retrievers = [self._bm25_retriever, self._vector_retriever]
                weights = [self.fulltext_weight, self.semantic_weight]
            else:
                logger.warning("未提供文档，仅使用语义检索")
                retrievers = [self._vector_retriever]
                weights = [1.0]

            self._ensemble = LCEnsembleRetriever(
                retrievers=retrievers,
                weights=weights
            )
            logger.debug("使用 EnsembleRetriever 混合检索")

    def _create_vector_retriever(self):
        """创建向量检索器"""
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
        logger.info(f"{self._mode} 检索 | 查询: {query[:50]}... | Top-K: {self.top_k}")

        # 根据模式调用对应的检索器
        if self._mode == "fulltext":
            lc_docs = self._bm25_retriever.invoke(query)
        elif self._mode == "semantic":
            lc_docs = self._vector_retriever.invoke(query)
        else:
            lc_docs = self._ensemble.invoke(query)

        # 转换并过滤结果
        results = []
        for lc_doc in lc_docs:
            result = self._from_lc_doc(lc_doc)

            # 全文检索模式：只保留包含完整查询词的结果
            if self._mode == "fulltext":
                query_clean = query.replace(" ", "")
                if query_clean in result["content"]:
                    results.append(result)
            else:
                results.append(result)

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
        获取带来源信息的检索结果

        Args:
            query: 查询文本

        Returns:
            来源信息列表
        """
        logger.debug(f"获取来源信息 | 查询: {query}")
        results = self.retrieve(query)

        sources = []
        for result in results:
            sources.append({
                "content": result["content"],
                "source": result["metadata"].get("source", "未知来源"),
                "metadata": result["metadata"],
                "score": 0.0,
            })

        logger.debug(f"来源获取完成 | 数量: {len(sources)}")
        return sources

    def update_documents(self, documents: List["Document"]) -> None:
        """
        更新 BM25 索引文档

        Args:
            documents: 新的文档列表
        """
        logger.info(f"更新 BM25 索引 | 文档数: {len(documents)}")
        self._documents = documents
        self._initialize_retrievers()

    def update_weights(self, semantic_weight: float, fulltext_weight: float) -> None:
        """
        更新检索权重

        Args:
            semantic_weight: 语义检索权重
            fulltext_weight: 全文检索权重
        """
        logger.info(f"更新权重 | 语义: {semantic_weight} | 全文: {fulltext_weight}")
        self.semantic_weight = semantic_weight
        self.fulltext_weight = fulltext_weight

        # 重新确定模式
        if self.semantic_weight == 0 and self.fulltext_weight > 0:
            self._mode = "fulltext"
        elif self.fulltext_weight == 0 and self.semantic_weight > 0:
            self._mode = "semantic"
        else:
            self._mode = "ensemble"

        self._initialize_retrievers()
