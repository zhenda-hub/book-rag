"""基础文档加载器"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from src.logger import get_logger

logger = get_logger("loaders")


@dataclass
class Document:
    """文档数据类"""
    content: str
    metadata: Dict[str, Any]
    source: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
        }


class BaseLoader(ABC):
    """文档加载器基类"""

    @staticmethod
    def validate_file_path(path: str, file_type: str = "") -> Path:
        """
        验证文件路径是否存在

        Args:
            path: 文件路径
            file_type: 文件类型描述（用于错误消息，如 "PDF"、"Word"）

        Returns:
            Path 对象

        Raises:
            FileNotFoundError: 当文件不存在时
        """
        logger.debug(f"验证文件路径 | 类型: {file_type or '通用'} | 路径: {path}")
        path_obj = Path(path)
        if not path_obj.exists():
            logger.error(f"文件不存在 | 路径: {path}")
            msg = f"{file_type} file not found" if file_type else "File not found"
            raise FileNotFoundError(f"{msg}: {path}")
        logger.debug(f"文件路径验证通过 | 大小: {path_obj.stat().st_size} 字节")
        return path_obj

    @abstractmethod
    def load(self, path: str) -> List[Document]:
        """
        加载文档

        Args:
            path: 文档路径

        Returns:
            文档列表
        """
        pass
