"""测试 TXT 加载器 - 针对长/短文本的场景"""
import pytest
from pathlib import Path
from src.loaders.txt_loader import TXTLoader
from src.chunking.splitter import get_text_splitter


class TestTXTLoader:
    """测试 TXTLoader 基础功能"""

    def test_load_short_text(self, tmp_path):
        """测试加载短文本（少于 chunk_size）"""
        test_file = tmp_path / "short.txt"
        content = "这是一个短文本。"
        test_file.write_text(content, encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        assert len(documents) == 1
        assert documents[0].content == content
        assert documents[0].metadata["type"] == "txt"
        assert documents[0].source == str(test_file)

    def test_load_long_text(self, tmp_path):
        """测试加载长文本（超过 chunk_size）"""
        test_file = tmp_path / "long.txt"
        # 生成一个 1000 字的长文本（超过默认 chunk_size=500）
        content = "这是一段很长的文本。" * 100  # 约 1000 字
        test_file.write_text(content, encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        # 验证长文本被切分成多个 Document
        assert len(documents) > 1

        # 验证所有块的内容总和接近原长度
        total_content = sum(len(doc.content) for doc in documents)
        assert total_content >= len(content) * 0.9  # 考虑 overlap，至少 90%

    def test_load_text_with_special_chars(self, tmp_path):
        """测试包含特殊字符的文本"""
        test_file = tmp_path / "special.txt"
        content = "包含特殊字符：\n换行符\t制表符\"引号\"'单引号'"
        test_file.write_text(content, encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        assert len(documents) == 1
        assert documents[0].content == content

    def test_load_empty_file(self, tmp_path):
        """测试空文件"""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        # 空文件返回空列表（因为没有内容可以切分）
        assert len(documents) == 0

    def test_file_not_found(self):
        """测试文件不存在"""
        loader = TXTLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/file.txt")

    def test_get_loader_mapping(self, tmp_path):
        """测试通过 get_loader 正确获取 TXTLoader"""
        from src.loaders import get_loader

        test_file = tmp_path / "test.txt"
        test_file.write_text("测试内容", encoding="utf-8")

        loader = get_loader(str(test_file))
        assert isinstance(loader, TXTLoader)

        # 验证能正确加载
        documents = loader.load(str(test_file))
        assert len(documents) == 1


class TestTXTWithRAGFlow:
    """测试 TXT 文件在 RAG 流程中的表现"""

    def test_short_text_rag_scenario(self, tmp_path):
        """测试短文本在 RAG 场景下的表现"""
        test_file = tmp_path / "short_rag.txt"
        # 模拟一个短的知识片段
        content = "Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。"
        test_file.write_text(content, encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        # 短文本应该只有一个 chunk
        chunks = get_text_splitter(chunk_size=500, chunk_overlap=50).split_text(documents[0].content)
        assert len(chunks) == 1
        assert content in chunks[0]

    def test_long_text_rag_scenario(self, tmp_path):
        """测试长文本在 RAG 场景下的表现"""
        test_file = tmp_path / "long_rag.txt"
        # 模拟一个长文档（多段落）
        content = """
        第一章：概述
        本项目是一个基于 RAG（检索增强生成）的智能问答系统。

        第二章：架构
        系统使用 LangChain 作为框架，支持多种文档格式。

        第三章：功能
        支持文档上传、向量化存储、语义检索等功能。
        """ * 20  # 重复 20 次模拟长文本

        test_file.write_text(content.strip(), encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        # 验证文档被正确加载并切分
        assert len(documents) >= 5  # 应该有多个 chunk

        # 验证每个 chunk 的大小合理
        for i, doc in enumerate(documents):
            assert len(doc.content) <= 600  # 允许一些超出 chunk_size 的余量
            # 验证 chunk 不为空
            assert len(doc.content.strip()) > 0

    def test_metadata_preservation(self, tmp_path):
        """测试元数据是否正确保存"""
        test_file = tmp_path / "metadata_test.txt"
        content = "测试元数据"
        test_file.write_text(content, encoding="utf-8")

        loader = TXTLoader()
        documents = loader.load(str(test_file))

        metadata = documents[0].metadata
        assert "type" in metadata
        assert metadata["type"] == "txt"
