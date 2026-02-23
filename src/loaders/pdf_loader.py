"""PDF 文档加载器"""
from typing import List
import pypdf
from src.loaders.base import BaseLoader, Document, CHUNKING_STRATEGY, STRATEGY_REGULAR
from src.chunking.splitter import get_text_splitter
from src.logger import get_logger

logger = get_logger("pdf_loader")


class PDFLoader(BaseLoader):
    """PDF 文档加载器 - 按页面切分，使用常规切分器"""

    def load(self, path: str) -> List[Document]:
        """
        加载 PDF 文档

        按页面提取内容，然后使用常规切分器对每页进行切分。

        Args:
            path: PDF 文件路径

        Returns:
            切分后的文档列表
        """
        path_obj = self.validate_file_path(path, file_type="PDF")

        with open(path, "rb") as f:
            pdf_reader = pypdf.PdfReader(f)
            num_pages = len(pdf_reader.pages)

        # 提取所有页面
        pages = []
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text.strip():
                pages.append({
                    "page_num": page_num + 1,
                    "text": text
                })

        # 使用常规切分器切分
        chunked_docs = []
        text_splitter = get_text_splitter()
        chunk_index = 0

        for page_info in pages:
            page_num = page_info["page_num"]
            page_text = page_info["text"]

            chunks = text_splitter.split_text(page_text)
            for chunk in chunks:
                chunked_doc = Document(
                    content=chunk,
                    metadata={
                        "type": "pdf",
                        "page": page_num,
                        "total_pages": num_pages,
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

        logger.info(f"PDF 切分完成: {len(chunked_docs)} 个块 (来自 {num_pages} 页)")
        return chunked_docs
