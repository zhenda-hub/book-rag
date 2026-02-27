"""测试 QAChain 问答链"""
import pytest
from unittest.mock import Mock, patch
from src.chains.qa_chain import QAChain, QAResult, Citation


class TestCitation:
    """测试 Citation 数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        citation = Citation(
            book_title="测试书",
            chapter_title="第一章",
            page_num=10,
            excerpt="这是一段摘录"
        )

        result = citation.to_dict()

        assert result["book_title"] == "测试书"
        assert result["chapter_title"] == "第一章"
        assert result["page_num"] == 10
        assert result["excerpt"] == "这是一段摘录"

    def test_format_chinese(self):
        """测试中文格式化"""
        citation = Citation(
            book_title="测试书",
            chapter_title="第一章",
            page_num=10,
            excerpt="摘录"
        )

        result = citation.format(language="zh")

        assert "《测试书》" in result
        assert "第一章" in result
        assert "第10页" in result
        assert "摘录" in result

    def test_format_english(self):
        """测试英文格式化"""
        citation = Citation(
            book_title="Test Book",
            chapter_title="Chapter 1",
            page_num=5,
            excerpt="excerpt"
        )

        result = citation.format(language="en")

        assert "Test Book" in result
        assert "Chapter 1" in result
        assert "page 5" in result

    def test_str(self):
        """测试 __str__ 方法"""
        citation = Citation(
            book_title="测试书",
            chapter_title="第一章",
            page_num=10,
            excerpt="摘录",
            full_content="这是完整的引用内容"
        )

        result = str(citation)

        assert result == "《测试书》-第一章 (第10页) [0%]"

    def test_format_full(self):
        """测试 format_full 方法"""
        citation = Citation(
            book_title="测试书",
            chapter_title="第一章",
            page_num=10,
            excerpt="摘录",
            full_content="这是完整的引用内容"
        )

        result = citation.format_full()

        assert "**《测试书》**" in result
        assert "第一章" in result
        assert "第10页" in result
        assert "这是完整的引用内容" in result


class TestQAResult:
    """测试 QAResult 数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        citation = Citation(
            book_title="书",
            chapter_title="章",
            page_num=1,
            excerpt="摘录"
        )

        result = QAResult(
            answer="测试答案",
            sources=[{"content": "内容"}],
            citations=[citation]
        )

        dict_result = result.to_dict()

        assert dict_result["answer"] == "测试答案"
        assert len(dict_result["citations"]) == 1
        assert dict_result["citations"][0]["book_title"] == "书"


class TestQAChain:
    """测试 QAChain 类"""

    def test_run_with_sources(self):
        """测试有来源的问答流程"""
        # Mock retriever
        mock_retriever = Mock()
        mock_retriever.get_sources.return_value = [
            {
                "content": "测试内容",
                "source": "test.pdf",
                "metadata": {"book_title": "测试书", "chapter_title": "第一章", "page": 1}
            }
        ]

        # Mock LLM manager
        mock_llm = Mock()
        mock_llm.generate.return_value = "这是 LLM 生成的答案"

        qa_chain = QAChain(retriever=mock_retriever, llm_manager=mock_llm)
        result = qa_chain.run("测试问题")

        assert "LLM 生成的答案" in result.answer
        assert len(result.sources) == 1
        assert result.sources[0]["source"] == "test.pdf"
        assert len(result.citations) == 1

    def test_run_no_sources(self):
        """测试无检索结果"""
        mock_retriever = Mock()
        mock_retriever.get_sources.return_value = []

        qa_chain = QAChain(retriever=mock_retriever)
        result = qa_chain.run("测试问题")

        assert "没有找到" in result.answer
        assert result.sources == []
        assert result.citations == []

    def test_build_context(self):
        """测试上下文构建 - 无标题元数据"""
        sources = [
            {
                "content": "内容1",
                "source": "doc1.pdf",
                "metadata": {"chunk_index": 0}
            },
            {
                "content": "内容2",
                "source": "doc2.pdf",
                "metadata": {"chunk_index": 1}
            }
        ]

        mock_retriever = Mock()
        qa_chain = QAChain(retriever=mock_retriever)
        context = qa_chain._build_context(sources)

        # 新格式：文档名、块号、标题信息
        assert "[文档: doc1 | 块: 1 | 标题: 无标题]" in context
        assert "[文档: doc2 | 块: 2 | 标题: 无标题]" in context
        assert "内容1" in context
        assert "内容2" in context
        # 分隔符
        assert "---" in context

    def test_build_context_with_markdown_headers(self):
        """测试上下文构建 - 包含 Markdown 标题元数据"""
        sources = [
            {
                "content": "Python 是一种高级编程语言。",
                "source": "编程语言介绍.md",
                "metadata": {
                    "chunk_index": 0,
                    "h1": "编程语言介绍",
                    "h2": "Python",
                    "h3": "特点"
                }
            },
            {
                "content": "JavaScript 是 Web 开发的核心语言。",
                "source": "编程语言介绍.md",
                "metadata": {
                    "chunk_index": 1,
                    "h1": "编程语言介绍",
                    "h2": "JavaScript"
                }
            },
            {
                "content": "应用领域包括数据科学、Web 开发。",
                "source": "编程语言介绍.md",
                "metadata": {
                    "chunk_index": 2,
                    "h1": "编程语言介绍",
                    "h2": "Python",
                    "h3": "应用领域"
                }
            }
        ]

        mock_retriever = Mock()
        qa_chain = QAChain(retriever=mock_retriever)
        context = qa_chain._build_context(sources)

        # 验证标题层级正确显示
        assert "标题: 编程语言介绍 > Python > 特点" in context
        assert "标题: 编程语言介绍 > JavaScript" in context
        assert "标题: 编程语言介绍 > Python > 应用领域" in context

        # 验证内容包含
        assert "Python 是一种高级编程语言" in context
        assert "JavaScript 是 Web 开发的核心语言" in context
        assert "应用领域包括数据科学" in context

        # 验证分隔符
        assert "\n\n---\n\n" in context

    def test_build_context_partial_headers(self):
        """测试上下文构建 - 部分标题元数据"""
        sources = [
            {
                "content": "只有 h2 标题的内容",
                "source": "test.md",
                "metadata": {
                    "chunk_index": 0,
                    "h2": "二级标题"
                    # 缺少 h1
                }
            }
        ]

        mock_retriever = Mock()
        qa_chain = QAChain(retriever=mock_retriever)
        context = qa_chain._build_context(sources)

        # 只有 h2，不应该显示 h1
        assert "标题: 二级标题" in context
        assert " > " not in context  # 不应该有层级分隔符

    def test_build_context_empty_headers(self):
        """测试上下文构建 - 空标题值"""
        sources = [
            {
                "content": "空标题值的内容",
                "source": "test.md",
                "metadata": {
                    "chunk_index": 0,
                    "h1": "",
                    "h2": "有效标题"
                }
            }
        ]

        mock_retriever = Mock()
        qa_chain = QAChain(retriever=mock_retriever)
        context = qa_chain._build_context(sources)

        # 空的 h1 应该被跳过，只显示有效的 h2
        assert "标题: 有效标题" in context
        # 不应该出现连续的 > 符号
        assert " >  > " not in context

    def test_generate_citations(self):
        """测试引用生成"""
        # 创建超过 100 字符的内容来测试截断
        long_content = "这是一段很长的测试内容，用于验证摘录功能是否正常工作。" * 5

        sources = [
            {
                "content": long_content,
                "source": "test.pdf",
                "metadata": {
                    "book_title": "测试书",
                    "chapter_title": "第一章",
                    "page": 10
                }
            }
        ]

        mock_retriever = Mock()
        qa_chain = QAChain(retriever=mock_retriever)
        citations = qa_chain._generate_citations(sources)

        assert len(citations) == 1
        assert citations[0].book_title == "测试书"
        assert citations[0].chapter_title == "第一章"
        assert citations[0].page_num == 10
        assert "..." in citations[0].excerpt  # 内容被截断

    def test_custom_retriever_and_llm(self):
        """测试自定义检索器和 LLM"""
        mock_retriever = Mock()
        mock_retriever.get_sources.return_value = []

        mock_llm = Mock()
        mock_llm.generate.return_value = "答案"

        qa_chain = QAChain(retriever=mock_retriever, llm_manager=mock_llm)

        assert qa_chain.retriever is mock_retriever
        assert qa_chain.llm_manager is mock_llm

    def test_run_without_llm_manager(self):
        """测试没有 LLM 管理器的情况"""
        mock_retriever = Mock()
        mock_retriever.get_sources.return_value = [
            {"content": "内容", "source": "test.pdf", "metadata": {}}
        ]

        qa_chain = QAChain(retriever=mock_retriever, llm_manager=None)
        result = qa_chain.run("问题")

        # 应该返回简单回答
        assert "相关文档" in result.answer

    def test_citation_to_dict(self):
        """测试 Citation 序列化"""
        citation = Citation(
            book_title="书",
            chapter_title="章",
            page_num=1,
            excerpt="摘录",
            full_content="完整内容"
        )

        result = citation.to_dict()

        assert result["book_title"] == "书"
        assert result["full_content"] == "完整内容"

    def test_qa_result_to_dict(self):
        """测试 QAResult 序列化"""
        citation = Citation("书", "章", 1, "摘录")
        result = QAResult(
            answer="答案",
            sources=[{"content": "内容"}],
            citations=[citation]
        )

        dict_result = result.to_dict()

        assert dict_result["answer"] == "答案"
        assert len(dict_result["sources"]) == 1
        assert len(dict_result["citations"]) == 1
