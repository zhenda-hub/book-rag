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
        # 配置 trafilatura 参数
        config = trafilatura.settings.use_config()
        config.DEFAULT_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        config.TIMEOUT = 30

        downloaded = trafilatura.fetch_url(url, config=config)
        if downloaded is None:
            raise ValueError(f"无法获取网页: {url}")

        content = trafilatura.extract(downloaded, config=config)
        if content is None:
            raise ValueError(f"无法提取网页内容: {url}")

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
