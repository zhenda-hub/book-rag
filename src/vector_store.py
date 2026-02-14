"""向量存储模块"""
from typing import List, Dict, Any, Optional
from chromadb import PersistentClient, Collection
from src.config import config
from src.embeddings import get_embeddings
from src.loaders.base import Document
from src.logger import get_logger

logger = get_logger("vector_store")


class VectorStore:
    """Chroma 向量存储封装"""

    def __init__(self, collection_name: str = None):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self._client: Optional[PersistentClient] = None
        self._collection: Optional[Collection] = None
        self._embeddings = get_embeddings()

    @property
    def client(self) -> PersistentClient:
        """获取 Chroma 客户端"""
        if self._client is None:
            self._client = PersistentClient(path=config.CHROMA_PERSIST_DIR)
        return self._client

    @property
    def collection(self) -> Collection:
        """获取或创建集合"""
        if self._collection is None:
            # 检查集合是否存在
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
            except Exception:
                # 集合不存在，创建新集合
                self._collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
        return self._collection

    def add_documents(self, documents: List[Document], chunk_ids: List[str] = None):
        """
        添加文档到向量存储

        Args:
            documents: 文档列表
            chunk_ids: 可选的 chunk ID 列表
        """
        if not documents:
            logger.warning("尝试添加空文档列表")
            return

        logger.info(f"开始添加文档 | 数量: {len(documents)}")

        # 提取文本和元数据
        texts = [doc.content for doc in documents]
        metadatas = [
            {**doc.metadata, "source": doc.source}
            for doc in documents
        ]

        # 生成 embeddings
        logger.debug("开始生成 embeddings")
        embeddings = self._embeddings.embed_documents(texts)

        # 生成 IDs
        if chunk_ids is None:
            chunk_ids = [f"{doc.source}_{i}" for i, doc in enumerate(documents)]

        # 添加到集合
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=chunk_ids,
        )

        logger.info(f"文档添加成功 | 数量: {len(documents)} | Embeddings: {len(embeddings)}")

    def search(
        self,
        query: str,
        top_k: int = None,
        filter: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        top_k = top_k or config.TOP_K_RETRIEVALS

        logger.info(f"向量搜索 | 查询: {query[:50]}... | Top-K: {top_k} | 过滤: {filter}")

        # 生成查询 embedding
        query_embedding = self._embeddings.embed_query(query)

        # 搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter,
        )

        # 格式化结果
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 0.0,  # Chroma 暂不返回分数
                })

        logger.info(f"搜索完成 | 返回: {len(formatted_results)} 个结果")

        return formatted_results

    def delete_by_source(self, source: str):
        """
        删除指定来源的所有文档

        Args:
            source: 文档来源
        """
        logger.info(f"删除文档 | 来源: {source}")

        # 获取该来源的所有文档 ID
        results = self.collection.get(where={"source": source})

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"删除成功 | 数量: {len(results['ids'])}")
        else:
            logger.debug(f"无文档需要删除 | 来源: {source}")

    def source_exists(self, source: str) -> bool:
        """
        检查指定来源的文档是否已存在

        Args:
            source: 文档来源（文件路径）

        Returns:
            文档是否存在
        """
        results = self.collection.get(where={"source": source})
        return bool(results["ids"])

    def get_all_sources(self) -> List[str]:
        """
        获取数据库中所有文档来源

        Returns:
            来源列表（文件路径）
        """
        # 获取所有文档的 metadata
        results = self.collection.get()

        if not results["metadatas"]:
            return []

        # 提取唯一的 source
        sources = set()
        for metadata in results["metadatas"]:
            if "source" in metadata:
                sources.add(metadata["source"])

        return sorted(list(sources))

    def clear(self):
        """清空集合"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self._collection = None
        except Exception:
            pass


# 全局单例
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """获取全局 VectorStore 实例"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
