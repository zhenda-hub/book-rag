# 文本切分 (Chunking) 策略

## 概述

本项目采用**章节感知的文本切分策略**（Chapter-Aware Chunking），相比固定大小切分，能够：
- 保持语义完整性，避免跨章节切分
- 为每个 chunk 保留章节上下文信息
- 提升检索精准度

---

## 核心组件

### 1. 章节检测器 (`ChapterDetector`)

**位置**: `src/chunking/chapter_detector.py`

**功能**: 从文档中识别章节结构

**支持格式**:
| 格式 | 检测方式 | 说明 |
|------|----------|------|
| TXT | 正则匹配 | 按行扫描匹配章节标题模式 |
| EPUB | 目录解析 | 读取 EPUB 内置目录结构 |
| PDF | 正则 + 页面 | 扫描前10页匹配章节模式 |

**章节标题模式**:
```python
# 英文章节
Chapter\s+\d+[:\.\s]*
\d+\.\s+[\w\s]+

# 中文章节
第[一二三...]章[：:\s]*
第[一二三...]节[：:\s]*
\d+、[\w\u4e00-\u9fff]+

# Markdown 标题
^#{1,3}\s+.+
```

**输出结构**:
```python
@dataclass
class ChapterInfo:
    chapter_id: str      # 章节ID
    title: str           # 章节标题
    level: int           # 层级 (1=主章节, 2=子节, 3=小节)
    page_num: int        # 页码 (PDF)
    line_start: int      # 起始行号
    line_end: int        # 结束行号
```

---

### 2. 文本切分器 (`TextSplitters`)

**位置**: `src/chunking/splitter.py`

#### 2.1 LangchainTextSplitter (遗留)

基础的递归字符切分器，按固定大小切分。

```python
from src.chunking.splitter import get_text_splitter

splitter = get_text_splitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(text)
```

#### 2.2 ChapterAwareSplitter (默认) ⭐

**两层切分策略**:

```
原文档
   ↓
【第一层】章节检测
   ↓
┌─────────┬─────────┬─────────┐
│ 第1章   │ 第2章   │ 第3章   │
└─────────┴─────────┴─────────┘
   ↓
【第二层】大小切分
   ↓ (仅对过长章节)
┌────┬────┬────┬────┬────┬────┐
│1.1 │1.2 │2.1 │2.2 │3.1 │3.2 │
└────┴────┴────┴────┴────┴────┘
```

**切分逻辑**:
```python
1. 使用 ChapterDetector 检测章节
2. 对每个章节：
   - 如果长度 <= min_chapter_size (默认100字符)
     → 保持完整 (chunk_type: "full_chapter")
   - 如果长度 > min_chapter_size
     → 递归切分 (chunk_type: "chapter_part")
3. 如果未检测到章节
     → 全局递归切分 (chunk_type: "no_chapter")
```

**使用方法**:
```python
from src.chunking import get_chapter_aware_splitter

splitter = get_chapter_aware_splitter(
    chunk_size=500,        # 最大 chunk 大小
    chunk_overlap=50,      # 重叠大小
    min_chapter_size=100   # 小章节阈值
)

chunks = splitter.split_text(
    document_content,
    metadata={"source": "book.pdf"}
)
```

**返回格式**:
```python
[
    {
        "content": "章节内容...",
        "metadata": {
            "chapter": "第一章 Python基础",
            "chapter_level": 1,
            "chapter_index": 0,
            "chunk_type": "full_chapter",  # or "chapter_part", "no_chapter"
            "chunk_index": 0,               # 仅 chapter_part
            "total_sub_chunks": 1           # 仅 chapter_part
        }
    },
    ...
]
```

---

## 元数据说明

### chunk_type 类型

| 类型 | 说明 | 元数据字段 |
|------|------|------------|
| `full_chapter` | 整章作为一个 chunk | `chapter`, `chapter_level`, `chapter_index` |
| `chapter_part` | 章节被切分为多个 | 额外包含 `chunk_index`, `total_sub_chunks` |
| `no_chapter` | 未检测到章节 | 仅包含 `chunk_index`, `total_chunks` |

### 元数据用途

```python
# 检索时可按章节过滤
results = vector_store.search(
    query="Python变量",
    filter={"chapter": "第一章 Python基础"}
)

# 生成答案时显示来源
answer = f"{content}\n\n来源: {metadata['chapter']}"
```

---

## 参数调优建议

| 参数 | 默认值 | 推荐范围 | 说明 |
|------|--------|----------|------|
| `chunk_size` | 500 | 300-1000 | 根据文档类型调整 |
| `chunk_overlap` | 50 | 10%-15% of chunk_size | 保持上下文连贯 |
| `min_chapter_size` | 100 | 50-200 | 小于此值的章节不切分 |

---

## 开发指南

### 修改章节检测模式

编辑 `src/chunking/chapter_detector.py`:

```python
class ChapterDetector:
    PATTERNS = [
        # 添加你的自定义模式
        (r"^你的正则模式", level),
    ]
```

### 自定义切分逻辑

创建自定义切分器类：

```python
from src.chunking.splitter import TextSplitter

class MyCustomSplitter:
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        # 你的切分逻辑
        pass
```

### 测试切分效果

```bash
# 运行测试
uv run pytest tests/test_chunking.py -v

# 测试特定功能
uv run pytest tests/test_chunking.py::test_chapter_aware_small_chapter -v
```

---

## 参考资料

- [LangChain Text Splitters](https://python.langchain.com/docs/how_to/#text-splitters)
- [RAG Chunking 最佳实践](https://juejin.cn/post/7607358297457098752)
- [2025年 RAG 分块策略](https://m.blog.csdn.net/qiwsir/article/details/155039091)
