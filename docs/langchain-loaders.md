# LangChain Document Loaders 参考

## 概述

LangChain 提供了丰富的 Document Loaders，可以加载各种格式的文档。相比手写代码，使用 LangChain 的 Loaders 更可靠、功能更完善。

## 支持的格式

| 格式 | LangChain Loader | 安装依赖 |
|------|------------------|----------|
| PDF | `PyPDFLoader` | `pip install pypdf` |
| PDF (高级) | `UnstructuredLoader` | `pip install unstructured` |
| TXT | `TextLoader` | 内置 |
| Markdown | `UnstructuredMarkdownLoader` | `pip install unstructured` |
| EPUB | `UnstructuredEPubLoader` | `pip install unstructured` |
| Web | `WebLoader` | `pip install beautifulsoup4` |

## 使用示例

### PDF 加载

```python
from langchain_community.document_loaders import PyPDFLoader

# 基础用法
loader = PyPDFLoader("document.pdf")
pages = loader.load()

# 每页是一个 Document 对象
for page in pages:
    print(f"Page {page.metadata['page']}: {page.page_content[:100]}")
```

### TXT 加载

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("document.txt", encoding="utf-8")
documents = loader.load()
```

### Markdown 加载（推荐）

```python
from langchain_community.document_loaders import UnstructuredMarkdownLoader

# 自动识别标题层级，保留文档结构
loader = UnstructuredMarkdownLoader("README.md")
docs = loader.load()

# Elements 模式：按元素切分（标题、段落、列表等）
loader = UnstructuredMarkdownLoader("README.md", mode="elements")
docs = loader.load()
```

**优势**：
- ✅ 自动识别所有 6 级标题（`#` 到 `######`）
- ✅ 保留标题层级关系
- ✅ 不会把代码注释 `# 注释` 当作标题
- ✅ metadata 包含完整的标题路径

### EPUB 加载

```python
from langchain_community.document_loaders import UnstructuredEPubLoader

# 单文档模式
loader = UnstructuredEPubLoader("book.epub")
docs = loader.load()

# Elements 模式：按章节切分
loader = UnstructuredEPubLoader("book.epub", mode="elements")
docs = loader.load()
```

### Web 抓取

```python
from langchain_community.document_loaders import WebLoader

loader = WebLoader("https://example.com")
docs = loader.load()
```

## Loader 选择指南

| 场景 | 推荐的 Loader |
|------|---------------|
| 简单 PDF | `PyPDFLoader` |
| 复杂布局 PDF | `UnstructuredLoader` |
| 纯文本 | `TextLoader` |
| Markdown 文档 | `UnstructuredMarkdownLoader` |
| EPUB 电子书 | `UnstructuredEPubLoader` |
| 网页内容 | `WebLoader` |
