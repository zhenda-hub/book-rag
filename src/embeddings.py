"""Embedding 封装模块"""
from sentence_transformers import SentenceTransformer
from typing import List
from src.config import config
from src.logger import get_logger

logger = get_logger("embeddings")


class Embeddings:
    """Sentence Transformers Embedding 封装"""

    def __init__(self, model_name: str = None, device: str = None):
        """
        初始化 Embedding 模型

        Args:
            model_name: 模型名称
            device: 设备 (cpu/cuda)
        """
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.device = device or config.EMBEDDING_DEVICE
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """延迟加载模型"""
        if self._model is None:
            logger.info(f"加载 Embedding 模型 | 模型: {self.model_name} | 设备: {self.device}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Embedding 模型加载完成 | 维度: {self._model.get_sentence_embedding_dimension()}")
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        logger.debug(f"批量生成 embeddings | 数量: {len(texts)}")
        # 使用批处理优化性能
        result = self.model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=32,  # 批处理大小，平衡内存和速度
            show_progress_bar=False,  # 禁用内部进度条，避免干扰
            normalize_embeddings=True,
        ).tolist()
        logger.debug(f"批量 embeddings 生成完成 | 数量: {len(result)}")
        return result

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            嵌入向量
        """
        logger.debug(f"生成查询 embedding | 文本长度: {len(text)}")
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def get_dimension(self) -> int:
        """获取嵌入维度"""
        return self.model.get_sentence_embedding_dimension()


# 全局单例
_embeddings_instance = None


def get_embeddings() -> Embeddings:
    """获取全局 Embeddings 实例"""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = Embeddings()
    return _embeddings_instance
