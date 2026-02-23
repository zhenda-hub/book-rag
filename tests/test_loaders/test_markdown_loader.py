"""测试 Markdown 文档加载器"""
import pytest
from pathlib import Path
from src.loaders.markdown_loader import MarkdownLoader
from src.loaders.base import CHUNKING_STRATEGY, STRATEGY_MARKDOWN


class TestMarkdownLoader:
    """测试 Markdown 加载器"""

    def test_load_simple_markdown(self, tmp_path):
        """测试加载简单 Markdown 文件"""
        md_file = tmp_path / "test.md"
        md_file.write_text("""# 标题 1

这是第一段内容。

## 标题 2

这是第二段内容。
""")

        loader = MarkdownLoader()
        docs = loader.load(str(md_file))

        # 应该被切分成多个块
        assert len(docs) > 0

        # 检查 metadata
        for doc in docs:
            assert doc.metadata.get("type") == "markdown"
            assert "chunk_index" in doc.metadata
            assert "total_chunks" in doc.metadata

    def test_chunking_strategy_flag(self, tmp_path):
        """测试切分策略标志"""
        md_file = tmp_path / "strategy.md"
        md_file.write_text("""# 测试

内容。
""")

        loader = MarkdownLoader()
        docs = loader.load(str(md_file))

        # 所有文档应该标记为 STRATEGY_MARKDOWN
        for doc in docs:
            assert doc.metadata.get(CHUNKING_STRATEGY) == STRATEGY_MARKDOWN

    def test_headers_preserved(self, tmp_path):
        """测试标题信息被保留在 metadata 中"""
        md_file = tmp_path / "headers.md"
        md_file.write_text("""# 一级标题

内容 1

## 二级标题

内容 2

### 三级标题

内容 3
""")

        loader = MarkdownLoader()
        docs = loader.load(str(md_file))

        # 至少应该有一个块
        assert len(docs) > 0

        # 检查是否有标题 metadata
        has_headers = any(
            "h1" in doc.metadata or "h2" in doc.metadata or "h3" in doc.metadata
            for doc in docs
        )
        assert has_headers, "应该保留标题信息"

    def test_frontmatter_removed(self, tmp_path):
        """测试 front matter 被正确移除"""
        md_file = tmp_path / "frontmatter.md"
        md_file.write_text("""+++
title = "测试"
date = "2024-01-01"
+++

# 实际标题

实际内容。
""")

        loader = MarkdownLoader()
        docs = loader.load(str(md_file))

        # front matter 应该被移除
        assert len(docs) > 0
        assert "+++" not in docs[0].content

    def test_long_content_split(self, tmp_path):
        """测试长内容被正确切分"""
        md_file = tmp_path / "long.md"
        # 创建超过 2000 字符的内容（确保会被切分）
        long_content = "# 长内容\n\n" + "这是一段很长的内容。" * 200
        md_file.write_text(long_content)

        loader = MarkdownLoader()
        docs = loader.load(str(md_file))

        # 长内容应该被切分成多个块
        assert len(docs) > 1


class TestMarkdownLoaderIntegration:
    """集成测试"""

    def test_actual_markdown_file(self):
        """测试实际的 Markdown 文件（如果存在）"""
        # 这里可以添加对 data/documents/ 下实际 Markdown 文件的测试
        pass
