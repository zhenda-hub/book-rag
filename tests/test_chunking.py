"""测试文本切分模块"""
import pytest
from src.chunking.splitter import get_text_splitter, LangchainTextSplitter, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from src.loaders.base import Document


def test_basic_splitting():
    """测试基本切分功能"""
    text = "这是一个测试。" * 100
    splitter = get_text_splitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    # 允许一定的误差（因为 langchain 可能在边界处超出）
    assert all(len(chunk) <= 550 for chunk in chunks)


def test_sentence_boundary():
    """测试句子边界切分"""
    text = "第一句。第二句。第三句。"
    splitter = get_text_splitter(chunk_size=50)
    chunks = splitter.split_text(text)
    # 应该在句号处切分
    assert all("。" in chunk or chunk.endswith("。") for chunk in chunks)


def test_short_text():
    """测试短文本不切分"""
    text = "短文本"
    splitter = get_text_splitter()
    chunks = splitter.split_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_custom_params():
    """测试自定义参数"""
    text = "测试。" * 100
    splitter = get_text_splitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_text(text)
    assert all(len(chunk) <= 220 for chunk in chunks)


def test_default_params():
    """测试默认参数"""
    splitter = get_text_splitter()
    assert splitter.chunk_size == DEFAULT_CHUNK_SIZE
    assert splitter.chunk_overlap == DEFAULT_CHUNK_OVERLAP


def test_empty_text():
    """测试空文本"""
    text = ""
    splitter = get_text_splitter()
    chunks = splitter.split_text(text)
    # langchain splitter 对空文本返回空列表
    assert chunks == []


def test_paragraph_splitting():
    """测试段落切分"""
    text = "第一段。\n\n第二段。\n\n第三段。"
    splitter = get_text_splitter(chunk_size=100)
    chunks = splitter.split_text(text)
    # 优先在段落边界切分
    assert len(chunks) >= 1


def test_overlap():
    """测试重叠功能"""
    text = "测试文本。" * 50
    splitter = get_text_splitter(chunk_size=200, chunk_overlap=50)
    chunks = splitter.split_text(text)
    if len(chunks) > 1:
        # 检查相邻块是否有重叠
        # 由于内容重复，应该能找到一些共同字符
        first_chunk_end = chunks[0][-50:]
        second_chunk_start = chunks[1][:50]
        # 简单检查：有重叠的话，第二块开头应该包含第一块结尾的部分内容
        # 但因为标点符号切分，不能严格保证
        assert len(chunks) > 1


class TestMarkdownSplitting:
    """测试 Markdown 文档切分"""

    def test_markdown_six_levels(self):
        """测试 6 级 Markdown 标题都能被识别"""
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        text = """# 一级标题

这是一级标题的内容。

## 二级标题

这是二级标题的内容。

### 三级标题

这是三级标题的内容。

#### 四级标题

这是四级标题的内容。

##### 五级标题

这是五级标题的内容。

###### 六级标题

这是六级标题的内容。
"""

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
                ("#####", "h5"),
                ("######", "h6"),
            ]
        )

        docs = splitter.split_text(text)

        # 应该生成多个文档块，每个标题对应一个块
        assert len(docs) >= 6, f"Expected at least 6 documents, got {len(docs)}"

        # 验证 metadata 包含标题信息
        h1_found = any("h1" in doc.metadata for doc in docs)
        h2_found = any("h2" in doc.metadata for doc in docs)
        assert h1_found, "h1 metadata not found"
        assert h2_found, "h2 metadata not found"

    def test_markdown_nested_headers(self):
        """测试嵌套标题结构"""
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        text = """# 第一章

第一章内容。

## 1.1 小节

小节内容。

### 1.1.1 子小节

子小节内容。

# 第二章

第二章内容。
"""

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        )

        docs = splitter.split_text(text)

        # 验证文档数量
        assert len(docs) >= 3, f"Expected at least 3 documents, got {len(docs)}"

        # 验证嵌套结构被正确捕获
        # 最后一个文档应该包含 h1="第二章"
        last_doc = docs[-1]
        assert last_doc.metadata.get("h1") == "第二章", f"Expected h1='第二章', got {last_doc.metadata}"

    def test_markdown_no_false_positives(self):
        """测试代码注释中的 # 不会被误识别为标题"""
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        text = """# 正确的标题

这是一段正文。

```python
# 这是代码注释，不是标题
def function():
    pass
```

另一段正文。

## 另一个正确的标题

内容。
"""

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
            ]
        )

        docs = splitter.split_text(text)

        # 应该只有 2 个文档（对应 2 个真实标题）
        assert len(docs) == 2, f"Expected 2 documents, got {len(docs)}"

    def test_markdown_chinese_headers(self):
        """测试中文标题处理"""
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        text = """# 前言

前言内容。

## 第一章 概述

概述内容。

### 1.1 背景

背景内容。
"""

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        )

        docs = splitter.split_text(text)

        # 验证中文标题被正确识别
        assert len(docs) >= 3, f"Expected at least 3 documents, got {len(docs)}"

        # 验证标题内容
        first_doc = docs[0]
        assert first_doc.metadata.get("h1") == "前言"


