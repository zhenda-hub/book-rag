"""网页文档加载器"""
from typing import List
import trafilatura
from src.loaders.base import BaseLoader, Document, CHUNKING_STRATEGY, STRATEGY_REGULAR
from src.chunking.splitter import get_text_splitter
from src.logger import get_logger

logger = get_logger("web_loader")


class WebLoader(BaseLoader):
    """网页文档加载器 - 使用常规切分器"""

    def load(self, url: str) -> List[Document]:
        """
        加载网页内容

        抓取网页内容，然后使用常规切分器切分。

        Args:
            url: 网页 URL

        Returns:
            切分后的文档列表
        """
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            raise ValueError(f"Failed to fetch URL: {url}")

        content = trafilatura.extract(downloaded)

        if content is None:
            raise ValueError(f"Failed to extract content from: {url}")

        # 使用常规切分器切分
        chunked_docs = []
        text_splitter = get_text_splitter()
        chunks = text_splitter.split_text(content)

        for i, chunk in enumerate(chunks):
            chunked_doc = Document(
                content=chunk,
                metadata={
                    "type": "web",
                    "url": url,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    CHUNKING_STRATEGY: STRATEGY_REGULAR,
                },
                source=url,
            )
            chunked_docs.append(chunked_doc)

        logger.info(f"网页抓取完成: {len(chunked_docs)} 个块 (来自 {url})")
        return chunked_docs
