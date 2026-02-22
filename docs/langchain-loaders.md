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

## Document 对象结构

所有 Loader 返回的 Document 对象都包含：

```python
from langchain_core.documents import Document

doc = Document(
    page_content="文档内容",
    metadata={
        "source": "file.pdf",
        "page": 1,
        # 其他元数据...
    }
)
```

## 高级用法

### 批量加载目录

```python
from langchain_community.document_loaders import DirectoryLoader

# 加载所有 TXT 文件
loader = DirectoryLoader(
    "./docs",
    glob="**/*.txt",
    loader_cls=TextLoader,
    show_progress=True
)
docs = loader.load()

# 加载多种格式
from langchain_community.document_loaders import PyPDFLoader

txt_loader = DirectoryLoader("./docs", glob="**/*.txt", loader_cls=TextLoader)
pdf_loader = DirectoryLoader("./docs", glob="**/*.pdf", loader_cls=PyPDFLoader)

all_docs = txt_loader.load() + pdf_loader.load()
```

### 加载并自动切分

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

# 一步完成加载和切分
docs = loader.load_and_split(text_splitter=text_splitter)
```

### 异步加载

```python
# 异步加载（适合大文件）
docs = await loader.aload()
```

### 内存优化（懒加载）

```python
# 大文件逐个处理，不占用过多内存
for doc in loader.lazy_load():
    process(doc)
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

## 安装

```bash
# 核心包
pip install langchain langchain-community

# PDF 支持
pip install pypdf

# 高级文档处理（推荐）
pip install unstructured

# 网页抓取
pip install beautifulsoup4
```

## 与现有代码对比

### 当前手写代码

```python
# 需要自己写 Loader 类
class MarkdownLoader(BaseLoader):
    def load(self, path: str) -> List[Document]:
        # 自己实现解析逻辑
        ...
```

### 使用 LangChain

```python
# 直接使用，一行代码
from langchain_community.document_loaders import UnstructuredMarkdownLoader
docs = UnstructuredMarkdownLoader("README.md").load()
```

## 参考资料

- [LangChain Document Loaders 官方文档](https://python.langchain.com/docs/how_to/#document-loaders)
- [Unstructured 文档处理库](https://unstructured-io.github.io/unstructured/)
