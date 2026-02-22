"""RAG 检索器模块"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from src.vector_store import get_vector_store
from src.logger import get_logger

logger = get_logger("retriever")

if TYPE_CHECKING:
    from src.vector_store import VectorStore


class Retriever:
    """RAG 检索器"""

    def __init__(
        self,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        vector_store: Optional["VectorStore"] = None,
    ) -> None:
        """
        初始化检索器

        Args:
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            vector_store: 可选的向量存储实例（用于使用特定的 vector_store）
        """
        self.top_k = top_k
        self.filter_metadata = filter_metadata
        self._vector_store: Optional["VectorStore"] = vector_store

    @property
    def vector_store(self) -> "VectorStore":
        """获取向量存储实例"""
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 查询文本

        Returns:
            检索结果列表
        """
        logger.debug(f"检索文档 | 查询: {query}")
        results = self.vector_store.search(
            query=query,
            top_k=self.top_k,
            filter=self.filter_metadata,
        )
        logger.debug(f"检索完成 | 返回: {len(results)} 个结果")
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
