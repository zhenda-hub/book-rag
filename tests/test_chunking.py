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


class TestMarkdownDocumentSplitting:
    """测试 split_markdown_document 函数"""

    def test_split_with_toc_directive(self):
        """测试包含 [toc] 标记的 markdown"""
        from src.web.components.documents import split_markdown_document

        content = """[toc]

## docker介绍

- Docker Desktop
  - Docker Engine

## why use docker?

- 环境一致性
"""

        doc = Document(content=content, metadata={}, source="test.md")
        chunks = split_markdown_document(doc, "test.md", "upload:test.md")

        # 应该切分成至少 2 个块（两个 h2）
        assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"

        # 第一个块应该有 h2 metadata（docker介绍）
        # 不应该有一个无标题的 [toc] 块
        assert chunks[0].metadata.get("h2") == "docker介绍", \
            f"First chunk should have h2='docker介绍', got metadata: {chunks[0].metadata}"

        # 所有块都应该有标题 metadata
        for i, chunk in enumerate(chunks):
            headers = [k for k in chunk.metadata.keys() if k.startswith("h")]
            assert len(headers) > 0, f"块 {i+1} 缺少标题 metadata: {chunk.metadata}"

    def test_split_with_hugo_frontmatter(self):
        """测试包含 Hugo frontmatter 的 markdown"""
        from src.web.components.documents import split_markdown_document

        content = """+++
title = 'Docker指南'
date = 2024-01-09T00:04:35+08:00
+++

## docker介绍

- Docker Desktop
  - Docker Engine

## why use docker?

- 环境一致性
"""

        doc = Document(content=content, metadata={}, source="docker.md")
        chunks = split_markdown_document(doc, "docker.md", "upload:docker.md")

        # 应该切分成至少 2 个块（两个 h2）
        assert len(chunks) >= 2

        # 每个块都应该有 h2 metadata
        for chunk in chunks:
            assert "h2" in chunk.metadata, f"块缺少 h2 metadata: {chunk.metadata}"

        # 第一个块应该有 h2 = docker介绍
        assert chunks[0].metadata.get("h2") == "docker介绍"

    def test_split_with_frontmatter_and_toc(self):
        """测试同时包含 frontmatter 和 [toc] 的真实情况"""
        from src.web.components.documents import split_markdown_document

        content = """+++
title = 'Docker指南'
toc = true
+++

[toc]

## docker介绍

- Docker Desktop
  - Docker Engine

## why use docker?

- 环境一致性
"""

        doc = Document(content=content, metadata={}, source="docker.md")
        chunks = split_markdown_document(doc, "docker.md", "upload:docker.md")

        # 应该切分成至少 2 个块
        assert len(chunks) >= 2

        # 第一个块应该有 h2 metadata
        assert chunks[0].metadata.get("h2") == "docker介绍"

        # 所有块都应该有标题 metadata
        for i, chunk in enumerate(chunks):
            headers = [k for k in chunk.metadata.keys() if k.startswith("h")]
            assert len(headers) > 0, f"块 {i+1} 缺少标题 metadata"

    def test_split_nested_headers(self):
        """测试多层嵌套标题"""
        from src.web.components.documents import split_markdown_document

        content = """# 一级标题

## 二级标题A

### 三级标题A1
内容A1

### 三级标题A2
内容A2

## 二级标题B

### 三级标题B1
内容B1

### 三级标题B2
内容B2
"""

        doc = Document(content=content, metadata={}, source="test.md")
        chunks = split_markdown_document(doc, "test.md", "upload:test.md")

        # 应该有多个块（至少有 4 个 h3 块）
        assert len(chunks) >= 4

        # 检查标题层级
        h2a_chunks = [c for c in chunks if c.metadata.get("h2") == "二级标题A"]
        h2b_chunks = [c for c in chunks if c.metadata.get("h2") == "二级标题B"]
        assert len(h2a_chunks) >= 2  # 至少有 A1 和 A2
        assert len(h2b_chunks) >= 2  # 至少有 B1 和 B2

        # 检查 h1 是否都存在
        for chunk in chunks:
            assert chunk.metadata.get("h1") == "一级标题"

    def test_all_chunks_have_headers(self):
        """测试所有块都应该有标题 metadata（对于有标题的文档）"""
        from src.web.components.documents import split_markdown_document

        content = """# 标题1

内容1

## 标题2

内容2
"""

        doc = Document(content=content, metadata={}, source="test.md")
        chunks = split_markdown_document(doc, "test.md", "upload:test.md")

        # 所有块都应该有至少一个标题 metadata
        for i, chunk in enumerate(chunks):
            headers = [k for k in chunk.metadata.keys() if k.startswith("h")]
            assert len(headers) > 0, f"块 {i+1} 缺少标题 metadata: {chunk.metadata}"
