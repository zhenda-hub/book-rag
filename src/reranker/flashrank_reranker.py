"""FlashRank Reranker 封装"""
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.documents import Document
from typing import List, Dict, Any
from src.logger import get_logger

logger = get_logger("reranker")


class FlashRankReranker:
    """FlashRank Reranker 封装

    使用 LangChain 的 FlashrankRerank 组件进行文档重排序。
    FlashRank 是一个基于 Rust 的快速轻量级 Reranker，支持多种模型。
    """

    def __init__(self, top_k: int = 5, model: str = "") -> None:
        """初始化 FlashRank Reranker

        Args:
            top_k: 保留的文档数量
            model: 使用的模型名称，空字符串使用 FlashRank 默认模型
                   可选值: "", "ms-marco-TinyBERT-L-2-v2", "ms-marco-MiniLM-L-12-v2"
        """
        # 如果指定了模型，传递给 FlashrankRerank；否则使用默认值
        if model:
            self.compressor = FlashrankRerank(top_n=top_k, model=model)
            self.model = model
        else:
            self.compressor = FlashrankRerank(top_n=top_k)
            self.model = "default"
        self.top_k = top_k
        logger.info(f"FlashRank Reranker 初始化完成 | model={self.model}, top_k={top_k}")

    def rerank(self, query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对检索结果进行重排序

        Args:
            query: 用户查询
            sources: 检索结果列表，每个元素包含 content, source, metadata, score

        Returns:
            重排序后的结果列表
        """
        if not sources:
            return []

        # 转换为 LangChain Document 格式
        documents = [
            Document(
                page_content=s.get("content", ""),
                metadata={
                    **s.get("metadata", {}),
                    "source": s.get("source", ""),
                    "original_score": s.get("score", 0.0),  # 保存原始分数
                }
            )
            for s in sources
        ]

        # 调用 FlashRank 压缩（重排序）
        try:
            reranked_docs = self.compressor.compress_documents(documents, query)
        except Exception as e:
            logger.error(f"Rerank 失败: {e}")
            # 失败时返回原始结果
            return sources

        # 转换回原格式
        result = []
        for doc in reranked_docs:
            # FlashRank 不会返回原始的 score，使用 relevance_score 替代
            # relevance_score 是 0-1 之间的值，越高越好
            relevance_score = getattr(doc, "relevance_score", 0.0)
            result.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "metadata": doc.metadata,
                "score": relevance_score,
            })

        logger.info(f"Rerank 完成 | 输入: {len(sources)} 个文档 | 输出: {len(result)} 个文档")

        return result
