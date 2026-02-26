"""测试 UnifiedRetriever 检索器"""
import pytest
from unittest.mock import Mock, patch
from src.retriever.base import UnifiedRetriever, Retriever
from langchain_core.documents import Document as LCDocument


class TestUnifiedRetriever:
    """测试 UnifiedRetriever 类"""

    def test_to_lc_doc_conversion(self):
        """测试文档转换为 LangChain 格式"""
        from src.loaders.base import Document

        doc = Document(
            content="test content",
            metadata={"page": 1},
            source="doc1.pdf"
        )

        lc_doc = UnifiedRetriever._to_lc_doc(doc)

        assert lc_doc.page_content == "test content"
        assert lc_doc.metadata["page"] == 1
        assert lc_doc.metadata["source"] == "doc1.pdf"

    def test_from_lc_doc_conversion(self):
        """测试 LangChain 文档转换为项目格式"""
        lc_doc = LCDocument(
            page_content="test content",
            metadata={"page": 1, "source": "doc1.pdf"}
        )

        result = UnifiedRetriever._from_lc_doc(lc_doc)

        assert result["content"] == "test content"
        assert result["metadata"]["page"] == 1
        assert result["source"] == "doc1.pdf"

    @patch("langchain_community.embeddings.SentenceTransformerEmbeddings")
    @patch("langchain_community.vectorstores.Chroma")
    def test_get_sources_semantic_mode(self, mock_chroma, mock_embeddings):
        """测试语义检索模式获取来源"""
        # 设置 mock
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        # 创建 mock LangChain retriever
        mock_lc_retriever = Mock()
        mock_lc_retriever.invoke.return_value = [
            LCDocument(
                page_content="test content",
                metadata={"source": "doc1.pdf", "page": 1}
            )
        ]

        mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

        retriever = UnifiedRetriever(
            vector_store=mock_store,
            mode="semantic",
        )

        sources = retriever.get_sources("test query")

        assert len(sources) == 1
        assert sources[0]["content"] == "test content"
        assert sources[0]["source"] == "doc1.pdf"
        assert sources[0]["score"] == 0.0  # Reranker 会替换

    @patch("langchain_community.embeddings.SentenceTransformerEmbeddings")
    @patch("langchain_community.vectorstores.Chroma")
    def test_get_sources_empty_results(self, mock_chroma, mock_embeddings):
        """测试空结果时 get_sources"""
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        # 创建返回空结果的 mock LangChain retriever
        mock_lc_retriever = Mock()
        mock_lc_retriever.invoke.return_value = []

        mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

        retriever = UnifiedRetriever(
            vector_store=mock_store,
            mode="semantic",
        )

        sources = retriever.get_sources("test query")

        assert sources == []

    def test_mode_property(self):
        """测试模式属性"""
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        with patch("langchain_community.embeddings.SentenceTransformerEmbeddings"), \
             patch("langchain_community.vectorstores.Chroma") as mock_chroma:

            mock_lc_retriever = Mock()
            mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

            semantic_retriever = UnifiedRetriever(
                vector_store=mock_store,
                mode="semantic",
            )
            assert semantic_retriever.mode == "semantic"

    def test_top_k_property(self):
        """测试 top_k 属性"""
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        with patch("langchain_community.embeddings.SentenceTransformerEmbeddings"), \
             patch("langchain_community.vectorstores.Chroma") as mock_chroma:

            mock_lc_retriever = Mock()
            mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

            retriever = UnifiedRetriever(
                vector_store=mock_store,
                mode="semantic",
                top_k=15,
            )
            assert retriever.top_k == 15

    def test_filter_metadata_property(self):
        """测试 filter_metadata 属性"""
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"
        filter_meta = {"source": "test.pdf"}

        with patch("langchain_community.embeddings.SentenceTransformerEmbeddings"), \
             patch("langchain_community.vectorstores.Chroma") as mock_chroma:

            mock_lc_retriever = Mock()
            mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

            retriever = UnifiedRetriever(
                vector_store=mock_store,
                mode="semantic",
                filter_metadata=filter_meta,
            )
            assert retriever.filter_metadata == filter_meta


class TestRetrieverCompatibility:
    """测试 Retriever 兼容性别名"""

    @patch("langchain_community.embeddings.SentenceTransformerEmbeddings")
    @patch("langchain_community.vectorstores.Chroma")
    @patch("src.vector_store.get_vector_store")
    def test_retriever_uses_semantic_mode(self, mock_get_vs, mock_chroma, mock_embeddings):
        """测试 Retriever 默认使用语义检索模式"""
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"
        mock_get_vs.return_value = mock_store

        mock_lc_retriever = Mock()
        mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

        retriever = Retriever(top_k=5)

        assert retriever.mode == "semantic"
        assert retriever.top_k == 5
        mock_get_vs.assert_called_once()

    @patch("langchain_community.embeddings.SentenceTransformerEmbeddings")
    @patch("langchain_community.vectorstores.Chroma")
    def test_retriever_with_custom_vector_store(self, mock_chroma, mock_embeddings):
        """测试 Retriever 使用自定义向量存储"""
        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        mock_lc_retriever = Mock()
        mock_chroma.return_value.as_retriever.return_value = mock_lc_retriever

        retriever = Retriever(vector_store=mock_store)

        assert retriever.vector_store is mock_store
