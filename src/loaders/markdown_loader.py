"""Markdown 文档加载器"""
from typing import List
import re
from src.loaders.base import BaseLoader, Document, CHUNKING_STRATEGY, STRATEGY_MARKDOWN
from src.logger import get_logger

logger = get_logger("markdown_loader")


class MarkdownLoader(BaseLoader):
    """Markdown 文档加载器 - 使用 MarkdownHeaderTextSplitter 按标题切分"""

    def load(self, path: str) -> List[Document]:
        """
        加载 Markdown 文档

        使用 MarkdownHeaderTextSplitter 按标题切分，保留结构信息。
        对过长的块使用 RecursiveCharacterTextSplitter 二次切分。

        Args:
            path: Markdown 文件路径

        Returns:
            切分后的文档列表
        """
        path_obj = self.validate_file_path(path, file_type="Markdown")

        with open(path_obj, 'r', encoding='utf-8') as f:
            content = f.read()

        # 预处理：移除 front matter（Hugo 格式：+++...+++ 或 ---...---）
        processed_content = self._preprocess(content)

        # 第一阶段：按标题切分
        langchain_docs = self._split_by_headers(processed_content)

        # 第二阶段：对过长的块进行二次切分
        chunked_docs = self._split_long_chunks(langchain_docs, path)

        # 更新切分策略标志
        for doc in chunked_docs:
            doc.metadata[CHUNKING_STRATEGY] = STRATEGY_MARKDOWN

        logger.info(f"Markdown 切分完成: {len(chunked_docs)} 个块")
        return chunked_docs

    def _preprocess(self, content: str) -> str:
        """
        预处理 Markdown 内容

        移除 front matter、TOC 标记等。

        Args:
            content: 原始内容

        Returns:
            处理后的内容
        """
        # 移除 front matter（Hugo 格式：+++...+++ 或 ---...---）
        if content.startswith("+++"):
            end_idx = content.find("+++", 3)
            if end_idx != -1:
                content = content[end_idx + 3:].lstrip()
        elif content.startswith("---"):
            end_idx = content.find("---", 3)
            if end_idx != -1:
                content = content[end_idx + 3:].lstrip()

        # 移除常见的 TOC 标记
        content = re.sub(r'^\[(toc|TOC)\]\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^{{<\s*toc\s*>}}\s*$', '', content, flags=re.MULTILINE)

        # 清理多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content.strip())

        return content

    def _split_by_headers(self, content: str):
        """
        使用 MarkdownHeaderTextSplitter 按标题切分

        Args:
            content: Markdown 内容

        Returns:
            LangChain Document 列表
        """
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
                ("#####", "h5"),
                ("######", "h6"),
            ]
        )

        return md_splitter.split_text(content)

    def _split_long_chunks(self, langchain_docs, source_path):
        """
        对过长的块进行二次切分

        Args:
            langchain_docs: 第一阶段切分后的 LangChain Document 列表
            source_path: 源文件路径

        Returns:
            切分后的 Document 列表
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=[
                "\n\n\n",  # 多个空行
                "\n## ",   # 二级标题
                "\n### ",  # 三级标题
                "\n#### ", # 四级标题
                "\n##### ",# 五级标题
                "\n###### ",# 六级标题
                "\n\n",    # 段落间空行
                "。", "！", "？",  # 中文标点
                ". ",      # 英文句号
                " ",       # 空格
                "",        # 字符级切分
            ],
        )

        chunked_docs = []
        chunk_index = 0

        for lc_doc in langchain_docs:
            page_content = lc_doc.page_content

            # 如果内容超过阈值，进行二次切分
            if len(page_content) > 1000:
                sub_chunks = text_splitter.split_text(page_content)
                for sub_chunk in sub_chunks:
                    chunked_doc = Document(
                        content=sub_chunk,
                        metadata={
                            "type": "markdown",
                            **lc_doc.metadata,  # 包含 h1, h2 等标题信息
                            "chunk_index": chunk_index,
                        },
                        source=str(source_path),
                    )
                    chunked_docs.append(chunked_doc)
                    chunk_index += 1
            else:
                # 内容较短，直接作为一个块
                chunked_doc = Document(
                    content=page_content,
                    metadata={
                        "type": "markdown",
                        **lc_doc.metadata,
                        "chunk_index": chunk_index,
                    },
                    source=str(source_path),
                )
                chunked_docs.append(chunked_doc)
                chunk_index += 1

        # 更新 total_chunks
        for doc in chunked_docs:
            doc.metadata["total_chunks"] = len(chunked_docs)

        return chunked_docs
