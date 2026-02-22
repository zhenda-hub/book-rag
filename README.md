# Book RAG - 知识库问答系统

基于 RAG（检索增强生成）的知识库问答系统，支持多格式文档解析和引用溯源。

## 功能特性

- **多格式文档解析**：支持 PDF、Word、Markdown、EPUB 格式
- **引用溯源**：显示答案参考来源，支持原文链接跳转
- **语义检索**：基于 Chroma 向量数据库的语义搜索
- **Web 界面**：Streamlit 提供的可视化问答界面
- **多云 LLM**：通过 OpenRouter 支持多种模型（DeepSeek、GPT-4、Claude 等）

## 环境准备

```bash
# 使用 uv 安装依赖（推荐）
uv venv
uv sync
source .venv/bin/activate
```

## 使用方法

### 1. 配置环境变量

复制 `.env_example` 为 `.env` 并配置：

```bash
cp .env_example .env
```

编辑 `.env` 文件，填入你的 OpenRouter API Key：

```
OPENROUTER_API_KEY=sk-or-v1-你的密钥
```

### 2. 启动 Web 界面

```bash
uv run streamlit run src/web/streamlit_app.py
```

启动后访问 http://127.0.0.1:8501

### 3. 使用步骤

1. 输入 OpenRouter API Key
2. 选择 LLM 模型（deepseek、gpt-4、claude-opus 等）
3. 上传文档文件（PDF、DOCX、MD、EPUB）
4. 开始问答

### 4. 查看文档分块信息

使用提供的工具查看已上传文档的 chunk 详情：

```bash
# 列出所有已上传的文档
uv run python scripts/view_chunks.py

# 查看指定文档的 chunks
uv run python scripts/view_chunks.py docker.md

# 只查看前 N 个块
uv run python scripts/view_chunks.py docker.md --limit 5

# 显示完整内容
uv run python scripts/view_chunks.py docker.md --full
```

这个工具可以帮你：
- 查看每个文档被切分成了多少块
- 检查每个块的内容和大小
- 验证切分策略是否合理
- 调试分块问题

## 支持的模型

通过 OpenRouter 支持：

- DeepSeek (deepseek, deepseek-reasoner)
- OpenAI (gpt-4, gpt-3.5)
- Anthropic (claude-opus, claude-sonnet)
- Google (gemini)
- Meta (llama)

## 项目结构

```
book-rag/
├── src/
│   ├── config.py          # 配置管理
│   ├── embeddings.py      # Embedding 封装
│   ├── vector_store.py    # Chroma 向量存储
│   ├── loaders/           # 文档加载器
│   ├── retriever/         # 检索器
│   ├── chains/            # 问答链
│   └── web/               # Streamlit Web 界面
├── data/
│   ├── documents/         # 待处理文档
│   └── chroma/            # 向量数据库
├── pyproject.toml
├── .env_example
└── README.md
```
