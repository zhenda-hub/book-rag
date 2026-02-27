"""纯文本文档加载器"""
from typing import List
from src.loaders.base import BaseLoader, Document
from src.chunking.splitter import get_text_splitter, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from src.logger import get_logger

logger = get_logger("txt_loader")


class TXTLoader(BaseLoader):
    """
    纯文本文档加载器

    处理策略：
    - 读取整个文件内容
    - 使用 RecursiveCharacterTextSplitter 进行切分
    - 支持中文和英文的智能切分
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """
        初始化 TXTLoader

        Args:
            chunk_size: 切分块大小
            chunk_overlap: 切分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = get_text_splitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def load(self, path: str) -> List[Document]:
        """
        加载纯文本文档并切分

        Args:
            path: 文本文件路径

        Returns:
            切分后的文档列表
        """
        path_obj = self.validate_file_path(path, file_type="Text")

        # 读取整个文件内容
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info(f"开始处理 TXT 文件 | 大小: {len(content)} 字符")

        # 使用文本切分器进行切分
        chunks = self.text_splitter.split_text(content)

        # 转换为 Document 列表
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    content=chunk,
                    metadata={
                        "type": "txt",
                        "char_count": len(chunk),
                        "file_size": path_obj.stat().st_size,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                    source=str(path_obj),
                )
            )

        logger.info(f"TXT 文件切分完成 | 原始: {len(content)} 字符 | 分块: {len(documents)} 个")
        return documents

