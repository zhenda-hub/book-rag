"""文档加载器模块"""
from src.loaders.base import BaseLoader, Document
from src.loaders.pdf_loader import PDFLoader
from src.loaders.docx_loader import DocxLoader
from src.loaders.markdown_loader import MarkdownLoader
from src.loaders.web_loader import WebLoader
from src.loaders.epub_loader import EPUBLoader
from src.loaders.txt_loader import TXTLoader
from src.loaders.bible_loader import BibleLoader, is_bible_text


# 文件扩展名到加载器的映射
LOADER_MAPPING = {
    ".pdf": PDFLoader,
    ".docx": DocxLoader,
    ".doc": DocxLoader,
    ".md": MarkdownLoader,
    ".markdown": MarkdownLoader,
    ".epub": EPUBLoader,
}


def get_loader(file_path: str) -> BaseLoader:
    """
    根据文件扩展名获取对应的加载器

    特殊处理：.txt 文件会先检测是否为圣经格式

    Args:
        file_path: 文件路径

    Returns:
        对应的文档加载器
    """
    from pathlib import Path

    ext = Path(file_path).suffix.lower()

    # .txt 文件特殊处理：检测是否为圣经格式
    if ext == ".txt":
        if is_bible_text(file_path):
            return BibleLoader()
        return TXTLoader()

    if ext in LOADER_MAPPING:
        return LOADER_MAPPING[ext]()

    raise ValueError(f"Unsupported file type: {ext}")


__all__ = [
    "BaseLoader",
    "Document",
    "PDFLoader",
    "DocxLoader",
    "TXTLoader",
    "MarkdownLoader",
    "WebLoader",
    "EPUBLoader",
    "BibleLoader",
    "is_bible_text",
    "get_loader",
]
