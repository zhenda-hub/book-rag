"""Markdown 文档加载器"""
from typing import List
from src.loaders.base import BaseLoader, Document


class MarkdownLoader(BaseLoader):
    """Markdown 文档加载器 - 直接读取文件内容，保留 Markdown 结构"""

    def load(self, path: str) -> List[Document]:
        """
        加载 Markdown 文档

        直接读取文件内容，保留 Markdown 结构（标题、列表等），
        切分逻辑由 documents.py 中的 MarkdownHeaderTextSplitter 处理。

        Args:
            path: Markdown 文件路径

        Returns:
            文档列表（整个文档作为一个文档，保留结构信息）
        """
        path_obj = self.validate_file_path(path, file_type="Markdown")

        # 直接读取文件内容，保留 Markdown 结构
        with open(path_obj, 'r', encoding='utf-8') as f:
            content = f.read()

        # 返回单个文档
        return [
            Document(
                content=content,
                metadata={"type": "markdown"},
                source=str(path_obj),
            )
        ]
