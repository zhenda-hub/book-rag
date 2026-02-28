"""EPUB 电子书加载器"""
from typing import List
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from src.loaders.base import BaseLoader, Document, CHUNKING_STRATEGY, STRATEGY_REGULAR
from src.chunking.splitter import get_text_splitter
from src.logger import get_logger

logger = get_logger("epub_loader")


def get_toc(documents: List[Document]) -> str:
    """
    从 EPUB 文档列表中提取目录结构

    Args:
        documents: EPUB 文档列表（需要包含 chapter_title, chapter_name metadata）

    Returns:
        格式化的目录结构字符串
    """
    # 从文档的 metadata 中提取章节信息
    chapters = {}  # {book_title: {chapter_title: chapter_name}}

    for doc in documents:
        book_title = doc.metadata.get("book_title", "Unknown")
        chapter_title = doc.metadata.get("chapter_title", "")
        chapter_name = doc.metadata.get("chapter_name", "")

        if book_title not in chapters:
            chapters[book_title] = {}

        # 使用 chapter_title 作为显示名称，chapter_name 用于去重
        if chapter_title and chapter_title not in chapters[book_title]:
            chapters[book_title][chapter_title] = chapter_name

    # 格式化输出
    lines = []
    for book_title, chapter_dict in sorted(chapters.items()):
        lines.append(f"📖 {book_title}")
        for chapter_title in sorted(chapter_dict.keys()):
            lines.append(f"  - {chapter_title}")

    return "\n".join(lines) if lines else "无目录结构"


class EPUBLoader(BaseLoader):
    """EPUB 电子书加载器 - 按章节切分，使用常规切分器"""

    def load(self, path: str) -> List[Document]:
        """
        加载 EPUB 电子书

        按章节提取内容，然后使用常规切分器对每章进行切分。

        Args:
            path: EPUB 文件路径

        Returns:
            切分后的文档列表
        """
        path_obj = self.validate_file_path(path, file_type="EPUB")

        try:
            # 读取 EPUB 文件
            book = epub.read_epub(path)

            # 获取目录结构
            toc = book.get_table_of_contents()
            chapters_info = self._extract_chapters_info(toc)

            # 获取所有 HTML 内容
            items = list(book.get_items())
            epub_items = [item for item in items if isinstance(item, ebooklib.epub.EpubHtml)]

            # 按章节提取内容并切分
            chunked_docs = []
            text_splitter = get_text_splitter()
            chunk_index = 0
            book_title = path_obj.stem

            for idx, item in enumerate(epub_items):
                # 获取章节名称
                chapter_name = item.get_name()
                chapter_title = self._get_chapter_title(chapter_name, chapters_info, book)

                # 提取文本内容
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                text = soup.get_text(separator='\n', strip=True)

                if text.strip():
                    # 使用常规切分器切分章节内容
                    chunks = text_splitter.split_text(text)
                    for chunk in chunks:
                        chunked_doc = Document(
                            content=chunk,
                            metadata={
                                "type": "epub",
                                "chapter_id": f"ch_{idx + 1}",
                                "chapter_title": chapter_title,
                                "chapter_name": chapter_name,
                                "book_title": book_title,
                                "chunk_index": chunk_index,
                                CHUNKING_STRATEGY: STRATEGY_REGULAR,
                            },
                            source=str(path_obj),
                        )
                        chunked_docs.append(chunked_doc)
                        chunk_index += 1

            # 更新 total_chunks
            for doc in chunked_docs:
                doc.metadata["total_chunks"] = len(chunked_docs)

            logger.info(f"EPUB 切分完成: {len(chunked_docs)} 个块 (来自 {len(epub_items)} 章)")
            return chunked_docs

        except Exception as e:
            raise RuntimeError(f"Failed to load EPUB file: {e}")

    def _extract_chapters_info(self, toc) -> List[dict]:
        """从目录结构中提取章节信息"""
        chapters = []

        def process_toc_item(item, level=0):
            if isinstance(item, (list, tuple)):
                for sub_item in item:
                    process_toc_item(sub_item, level)
            elif isinstance(item, ebooklib.epub.Link):
                chapters.append({
                    "title": item.title,
                    "href": item.href,
                    "level": level,
                })
            elif isinstance(item, ebooklib.epub.Section):
                for sub_item in item:
                    process_toc_item(sub_item, level + 1)

        process_toc_item(toc)
        return chapters

    def _get_chapter_title(self, chapter_name: str, chapters_info: List[dict], book) -> str:
        """根据章节名称获取章节标题"""
        # 从目录信息中查找
        for chapter in chapters_info:
            if chapter["href"].startswith(chapter_name) or chapter_name in chapter["href"]:
                return chapter["title"]

        # 如果找不到，尝试从文件名提取
        name = chapter_name.replace('_', ' ').replace('-', ' ').title()
        return name
