"""测试 FlashRank Reranker"""
import pytest
from src.reranker.flashrank_reranker import FlashRankReranker

# 使用已下载的小模型
MODEL = "ms-marco-TinyBERT-L-2-v2"


@pytest.fixture
def reranker():
    """Reranker 实例"""
    return FlashRankReranker(top_k=3, model=MODEL)


@pytest.fixture
def sample_sources():
    """示例检索结果"""
    return [
        {
            "content": "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
            "source": "doc1.pdf",
            "metadata": {"page": 1},
            "score": 0.75,
        },
        {
            "content": "深度学习是机器学习的一个子领域，使用神经网络进行学习。",
            "source": "doc2.pdf",
            "metadata": {"page": 5},
            "score": 0.65,
        },
        {
            "content": "Python 是一种流行的编程语言，广泛用于数据科学和机器学习。",
            "source": "doc3.pdf",
            "metadata": {"page": 10},
            "score": 0.60,
        },
        {
            "content": "机器学习算法可以分为监督学习、无监督学习和强化学习。",
            "source": "doc4.pdf",
            "metadata": {"page": 2},
            "score": 0.85,
        },
        {
            "content": "烹饪是一种艺术形式，需要练习和耐心来掌握。",
            "source": "cookbook.pdf",
            "metadata": {"page": 15},
            "score": 0.50,
        },
    ]


def test_reranker_top_k(reranker, sample_sources):
    """测试返回 Top K 结果"""
    result = reranker.rerank("什么是机器学习？", sample_sources)
    assert len(result) == 3


def test_reranker_filters_irrelevant(reranker, sample_sources):
    """测试过滤不相关内容"""
    result = reranker.rerank("什么是机器学习？", sample_sources)
    sources = [r["source"] for r in result]
    assert "cookbook.pdf" not in sources


def test_reranker_ranks_relevant_first(reranker, sample_sources):
    """测试相关内容排在前面"""
    result = reranker.rerank("什么是机器学习？", sample_sources)
    sources = [r["source"] for r in result]
    # doc4.pdf 内容最相关，应该在前两个结果中
    assert "doc4.pdf" in sources[:2]


def test_reranker_empty_sources(reranker):
    """测试空输入"""
    result = reranker.rerank("测试查询", [])
    assert result == []


def test_reranker_structure(reranker, sample_sources):
    """测试结果结构"""
    result = reranker.rerank("测试查询", sample_sources)
    for item in result:
        assert "content" in item
        assert "source" in item
        assert "metadata" in item
        assert "score" in item
