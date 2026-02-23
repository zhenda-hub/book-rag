"""测试网页文档加载器"""
import pytest
from unittest.mock import patch, MagicMock
from src.loaders.web_loader import WebLoader
from src.loaders.base import CHUNKING_STRATEGY, STRATEGY_REGULAR


class TestWebLoader:
    """测试 Web 加载器"""

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    @patch('src.loaders.web_loader.trafilatura.extract')
    def test_load_web_page(self, mock_extract, mock_fetch):
        """测试加载网页内容"""
        # Mock 网页抓取
        mock_fetch.return_value = "<html><body>test content</body></html>".encode('utf-8')
        mock_extract.return_value = "这是测试内容。这是第二段内容。这是第三段内容。"

        loader = WebLoader()
        docs = loader.load("https://example.com")

        # 验证调用
        mock_fetch.assert_called_once_with("https://example.com")
        mock_extract.assert_called_once()

        # 验证返回文档
        assert len(docs) > 0
        assert docs[0].source == "https://example.com"

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    @patch('src.loaders.web_loader.trafilatura.extract')
    def test_chunking_strategy_flag(self, mock_extract, mock_fetch):
        """测试切分策略标志"""
        mock_fetch.return_value = "<html><body>test</body></html>".encode('utf-8')
        mock_extract.return_value = "测试内容。"

        loader = WebLoader()
        docs = loader.load("https://example.com")

        # 所有文档应该标记为 STRATEGY_REGULAR
        for doc in docs:
            assert doc.metadata.get(CHUNKING_STRATEGY) == STRATEGY_REGULAR

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    @patch('src.loaders.web_loader.trafilatura.extract')
    def test_long_content_split(self, mock_extract, mock_fetch):
        """测试长内容被正确切分"""
        # 创建较长的内容（超过默认 chunk_size 500）
        long_content = "这是一段内容。" * 100

        mock_fetch.return_value = "<html><body>test</body></html>".encode('utf-8')
        mock_extract.return_value = long_content

        loader = WebLoader()
        docs = loader.load("https://example.com")

        # 长内容应该被切分成多个块
        assert len(docs) > 1

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    def test_fetch_failure(self, mock_fetch):
        """测试抓取失败"""
        mock_fetch.return_value = None

        loader = WebLoader()

        with pytest.raises(ValueError, match="Failed to fetch URL"):
            loader.load("https://example.com")

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    @patch('src.loaders.web_loader.trafilatura.extract')
    def test_extract_failure(self, mock_extract, mock_fetch):
        """测试提取失败"""
        mock_fetch.return_value = "<html><body>test</body></html>".encode('utf-8')
        mock_extract.return_value = None

        loader = WebLoader()

        with pytest.raises(ValueError, match="Failed to extract content"):
            loader.load("https://example.com")

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    @patch('src.loaders.web_loader.trafilatura.extract')
    def test_metadata_fields(self, mock_extract, mock_fetch):
        """测试 metadata 包含所有必要字段"""
        mock_fetch.return_value = "<html><body>test</body></html>".encode('utf-8')
        mock_extract.return_value = "测试内容。"

        loader = WebLoader()
        docs = loader.load("https://example.com")

        doc = docs[0]
        metadata = doc.metadata
        assert metadata["type"] == "web"
        assert metadata["url"] == "https://example.com"
        assert "chunk_index" in metadata
        assert "total_chunks" in metadata

    @patch('src.loaders.web_loader.trafilatura.fetch_url')
    @patch('src.loaders.web_loader.trafilatura.extract')
    def test_chunk_indexes_sequential(self, mock_extract, mock_fetch):
        """测试块索引是连续的"""
        mock_fetch.return_value = "<html><body>test</body></html>".encode('utf-8')
        # 返回足够长的内容以产生多个块
        mock_extract.return_value = "内容。" * 200

        loader = WebLoader()
        docs = loader.load("https://example.com")

        if len(docs) > 1:
            # 验证 chunk_index 是连续的
            indexes = [doc.metadata["chunk_index"] for doc in docs]
            assert indexes == list(range(len(docs)))
