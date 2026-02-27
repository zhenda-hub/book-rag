"""测试 UnifiedRetriever 权重配置

验证通过设置权重为0来简化检索器代码的可行性。
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document as LCDocument
from langchain.retrievers import EnsembleRetriever as LCEnsembleRetriever


class TestWeightsConfiguration:
    """测试权重配置逻辑"""

    @patch("src.retriever.base.HuggingFaceEmbeddings")
    def test_mode_to_weights_conversion(self, mock_embeddings):
        """测试 mode 参数自动转换为 weights"""
        from src.retriever.base import UnifiedRetriever

        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        mock_lc_retriever = Mock()
        mock_lc_retriever.invoke.return_value = [
            LCDocument(page_content="语义结果", metadata={"source": "test.txt"})
        ]

        with patch("src.retriever.base.UnifiedRetriever._create_vector_retriever") as mock_create_vec:
            mock_create_vec.return_value = mock_lc_retriever

            # mode="semantic" 应该转换为 weights={"semantic": 1.0, "fulltext": 0.0}
            retriever1 = UnifiedRetriever(
                vector_store=mock_store,
                mode="semantic",
            )
            assert retriever1._weights == {"semantic": 1.0, "fulltext": 0.0}

            # mode="fulltext" 应该转换为 weights={"semantic": 0.0, "fulltext": 1.0}
            retriever2 = UnifiedRetriever(
                vector_store=mock_store,
                mode="fulltext",
            )
            assert retriever2._weights == {"semantic": 0.0, "fulltext": 1.0}

    @patch("src.retriever.base.HuggingFaceEmbeddings")
    def test_direct_weights_configuration(self, mock_embeddings):
        """测试直接配置 weights"""
        from src.retriever.base import UnifiedRetriever

        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        mock_lc_retriever = Mock()
        mock_lc_retriever.invoke.return_value = [
            LCDocument(page_content="结果", metadata={"source": "test.txt"})
        ]

        with patch("src.retriever.base.UnifiedRetriever._create_vector_retriever") as mock_create_vec:
            mock_create_vec.return_value = mock_lc_retriever

            # 纯语义检索
            retriever1 = UnifiedRetriever(
                vector_store=mock_store,
                weights={"semantic": 1.0, "fulltext": 0.0},
            )
            assert retriever1._weights == {"semantic": 1.0, "fulltext": 0.0}

            # 纯全文检索
            retriever2 = UnifiedRetriever(
                vector_store=mock_store,
                weights={"semantic": 0.0, "fulltext": 1.0},
            )
            assert retriever2._weights == {"semantic": 0.0, "fulltext": 1.0}

            # 混合检索
            retriever3 = UnifiedRetriever(
                vector_store=mock_store,
                weights={"semantic": 0.3, "fulltext": 0.7},
            )
            assert retriever3._weights == {"semantic": 0.3, "fulltext": 0.7}

    @patch("src.retriever.base.HuggingFaceEmbeddings")
    def test_default_weights(self, mock_embeddings):
        """测试默认权重配置"""
        from src.retriever.base import UnifiedRetriever

        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        mock_lc_retriever = Mock()
        mock_lc_retriever.invoke.return_value = []

        with patch("src.retriever.base.UnifiedRetriever._create_vector_retriever") as mock_create_vec:
            mock_create_vec.return_value = mock_lc_retriever

            # 不指定 mode 和 weights，应使用默认值
            retriever = UnifiedRetriever(vector_store=mock_store)
            assert retriever._weights == {"semantic": 0.2, "fulltext": 0.8}

    @patch("src.retriever.base.HuggingFaceEmbeddings")
    def test_weights_priority_over_mode(self, mock_embeddings):
        """测试 weights 参数优先级高于 mode"""
        from src.retriever.base import UnifiedRetriever

        mock_store = Mock()
        mock_store.client = Mock()
        mock_store.collection_name = "test_collection"

        mock_lc_retriever = Mock()
        mock_lc_retriever.invoke.return_value = []

        with patch("src.retriever.base.UnifiedRetriever._create_vector_retriever") as mock_create_vec:
            mock_create_vec.return_value = mock_lc_retriever

            # 同时提供 mode 和 weights，应使用 weights
            retriever = UnifiedRetriever(
                vector_store=mock_store,
                mode="semantic",  # 这个应该被忽略
                weights={"semantic": 0.4, "fulltext": 0.6},
            )
            assert retriever._weights == {"semantic": 0.4, "fulltext": 0.6}


class TestLangChainEnsembleBehavior:
    """直接测试 LangChain EnsembleRetriever 的行为"""

    def test_ensemble_accepts_zero_weight(self):
        """验证 LangChain EnsembleRetriever 是否接受零权重"""
        from langchain_community.retrievers import BM25Retriever
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        # 创建测试文档
        docs = [
            LCDocument(page_content="巴黎皇家图书馆收藏了珍贵抄本"),
            LCDocument(page_content="伊索寓言的历史版本"),
        ]

        # 创建 BM25 检索器
        bm25 = BM25Retriever.from_documents(docs)
        bm25.k = 2

        # 创建向量检索器（使用内存向量存储）
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        vector_store = Chroma.from_documents(docs, embeddings)
        vector_retriever = vector_store.as_retriever(search_kwargs={'k': 2})

        # 测试零权重情况
        # fulltext_weight = 0, semantic_weight = 1
        ensemble1 = LCEnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[0.0, 1.0]
        )
        results1 = ensemble1.invoke("巴黎")
        assert len(results1) > 0  # 验证零权重被接受

        # semantic_weight = 0, fulltext_weight = 1
        ensemble2 = LCEnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[1.0, 0.0]
        )
        results2 = ensemble2.invoke("巴黎")
        assert len(results2) > 0  # 验证零权重被接受

    def test_ensemble_both_retrievers_with_zero_weight(self):
        """测试两个检索器都使用零权重的情况

        注意：EnsembleRetriever 不阻止零权重，行为由实现决定。
        此测试仅验证配置不会导致初始化失败。
        """
        from langchain_community.retrievers import BM25Retriever

        docs = [
            LCDocument(page_content="测试文档"),
        ]

        bm25 = BM25Retriever.from_documents(docs)

        # 两个权重都为0（虽然允许，但行为未定义）
        ensemble = LCEnsembleRetriever(
            retrievers=[bm25, bm25],
            weights=[0.0, 0.0]
        )
        # 验证可以成功创建（行为由 LangChain 决定）
        assert ensemble is not None


class TestRealWorldScenario:
    """真实场景测试：巴黎皇家图书馆查询"""

    @pytest.mark.slow
    def test_paris_library_retrieval_comparison(self):
        """对比不同权重配置下的检索结果"""
        pytest.skip("需要真实的向量存储，跳过集成测试")

        # 这个测试需要真实的向量存储
        # 可以作为集成测试运行
        pass
