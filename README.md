# 📚 Book RAG

<div align="center">
  <h3>智能文档问答系统 · 精确引用溯源 · 多模态检索</h3>
  <p>基于 RAG 的知识库问答系统，支持多种文档格式和网页内容，提供语义、全文、混合三种检索模式</p>
</div>

## 🎯 示例

![ui](./imgs/index.png)

## ✨ 核心特性

### 🔍 三种检索模式

- **语义检索**：基于向量相似度的智能匹配，理解语义关联
- **全文检索**：BM25 算法精确匹配关键词，适合查找特定内容
- **混合检索**：结合两者优势，可自定义权重平衡（默认语义 0.7 + 全文 0.3）

### 📄 多格式文档支持

- **文件上传**：PDF、Word (DOCX)、Markdown、TXT、EPUB
- **网页抓取**：直接输入 URL 即可提取网页正文内容
- **智能分块**：Markdown 自动章节检测，PDF 提取页码信息

### 🎯 精确引用溯源

- 显示答案来源：书名、章节、页码
- 相似度评分
- 一键查看原文内容

### 💬 智能对话体验

- 自动生成后续问题建议
- 聊天历史记录
- 示例问题推荐

### 🤖 多云 LLM 支持

通过 OpenRouter 支持：

- DeepSeek (deepseek-chat, deepseek-r1)
- OpenAI (gpt-4-turbo, gpt-3.5-turbo)
- Anthropic (claude-3-opus, claude-3-sonnet)
- Google (gemini-pro)
- Meta (llama-3-70b)

### 📁 文件管理

- 文件启用/禁用控制
- 批量上传
- 重复检测
- 按需删除

## 🚀 快速开始

### 环境准备

```bash
# 克隆项目
git clone https://github.com/yourusername/book-rag.git
cd book-rag

# 安装依赖（推荐使用 uv）
uv venv
uv sync
source .venv/bin/activate
```

### 配置 API Key

```bash
# 复制环境变量模板
cp .env_example .env

# 编辑 .env 文件，填入 OpenRouter API Key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 启动 Web 界面

```bash
uv run streamlit run src/web/streamlit_app.py
```

访问 http://127.0.0.1:8501 开始使用！

## 📖 使用指南

### 1. 配置面板

在侧边栏设置 API Key 和 LLM 模型

### 2. 添加文档

- **上传文件**：支持 PDF、DOCX、MD、TXT、EPUB
- **网页抓取**：输入 URL 自动提取内容

### 3. 选择检索模式

根据问题类型选择最佳检索方式：

- 语义问题 → 语义检索
- 精确查找 → 全文检索
- 综合查询 → 混合检索

### 4. 开始问答

输入问题，获取带引用的精准答案

## 🛠️ 开发工具

### 查看文档分块

```bash
# 列出所有文档
uv run python scripts/view_chunks.py

# 查看指定文档的 chunks
uv run python scripts/view_chunks.py docker.md

# 只查看前 N 个块
uv run python scripts/view_chunks.py docker.md --limit 5

# 显示完整内容
uv run python scripts/view_chunks.py docker.md --full
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_pdf_loader.py -v

# 查看覆盖率
uv run pytest --cov=src --cov-report=html
```

## 📁 项目结构

```
book-rag/
├── src/
│   ├── config.py              # 配置管理
│   ├── embeddings.py          # Embedding 封装
│   ├── vector_store.py        # Chroma 向量存储
│   ├── loaders/               # 文档加载器
│   │   ├── base.py           # 基础类
│   │   ├── pdf_loader.py     # PDF 加载
│   │   ├── docx_loader.py    # Word 加载
│   │   ├── markdown_loader.py # Markdown 加载（含章节检测）
│   │   ├── epub_loader.py    # EPUB 加载
│   │   └── web_loader.py     # 网页抓取
│   ├── retriever/             # 检索器
│   │   ├── base.py           # 基础检索器
│   │   └── ensemble.py       # 混合检索（语义+全文）
│   ├── chains/                # 问答链
│   │   ├── llm_manager.py    # LLM 管理
│   │   └── qa_chain.py       # QA 链
│   └── web/                   # Streamlit Web 界面
│       ├── streamlit_app.py  # 主应用
│       └── components/
│           ├── state.py      # 会话状态
│           ├── config.py     # 配置面板
│           ├── documents.py  # 文档管理
│           └── chat.py       # 聊天界面
├── data/
│   ├── documents/            # 文档存储
│   └── chroma/              # 向量数据库
├── tests/                    # 测试用例
├── scripts/                  # 开发工具
│   └── view_chunks.py       # 查看分块工具
├── pyproject.toml           # 项目配置
├── .env_example             # 环境变量模板
└── README.md
```

## 🔧 技术栈

- **Python**: >= 3.12
- **LangChain**: RAG 框架
- **ChromaDB**: 向量数据库
- **sentence-transformers**: 文本嵌入
- **Streamlit**: Web 界面
- **OpenRouter**: 多云 LLM 接入
- **rank-bm25**: 全文检索

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
