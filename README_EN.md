# 📚 Book RAG

English | [简体中文](./README.md)

<div align="center">
  <h3>Intelligent Document Q&A System · Precise Citation · Multi-modal Retrieval</h3>
  <p>A RAG-based knowledge base Q&A system supporting multiple document formats and web content, with semantic, full-text, and hybrid retrieval modes</p>
</div>

## 🎯 Demo

![ui](./imgs/index.png)

## ✨ Core Features

### 🔍 Three Retrieval Modes

- **Semantic Search**: Intelligent matching based on vector similarity, understands semantic associations
- **Full-text Search**: BM25 algorithm for precise keyword matching, ideal for finding specific content
- **Hybrid Search**: Combines both advantages with customizable weights (default: semantic 0.7 + full-text 0.3)

### 📄 Multi-format Document Support

- **File Upload**: PDF, Word (DOCX), Markdown, TXT, EPUB
- **Web Scraping**: Extract main content directly by entering URL
- **Smart Chunking**: Automatic chapter detection for Markdown, page number extraction for PDF

### 🎯 Precise Citation Tracking

- Display answer sources: book title, chapter, page number
- Similarity scores
- One-click view of original content

### 💬 Intelligent Chat Experience

- Auto-generated follow-up question suggestions
- Chat history
- Example question recommendations

### 🤖 Multi-cloud LLM Support

Via OpenRouter:

- DeepSeek (deepseek-chat, deepseek-r1)
- OpenAI (gpt-4-turbo, gpt-3.5-turbo)
- Anthropic (claude-3-opus, claude-3-sonnet)
- Google (gemini-pro)
- Meta (llama-3-70b)

### 📁 File Management

- File enable/disable control
- Batch upload
- Duplicate detection
- On-demand deletion

## 🚀 Quick Start

### Environment Setup

```bash
# Clone project
git clone https://github.com/yourusername/book-rag.git
cd book-rag

# Install dependencies (uv recommended)
uv venv
uv sync
source .venv/bin/activate
```

### Configure API Key

```bash
# Copy environment variable template
cp .env_example .env

# Edit .env file, add OpenRouter API Key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Launch Web Interface

```bash
uv run streamlit run src/web/streamlit_app.py
```

Visit http://127.0.0.1:8501 to get started!

## 📖 User Guide

### 1. Configuration Panel

Set API Key and LLM model in the sidebar

### 2. Add Documents

- **Upload Files**: Supports PDF, DOCX, MD, TXT, EPUB
- **Web Scraping**: Enter URL to automatically extract content

### 3. Select Retrieval Mode

Choose the best retrieval method based on your question type:

- Semantic questions → Semantic Search
- Exact lookup → Full-text Search
- Comprehensive queries → Hybrid Search

### 4. Start Q&A

Enter your question and get precise answers with citations

## 🛠️ Development Tools

### View Document Chunks

```bash
# List all documents
uv run python scripts/view_chunks.py

# View chunks for specific document
uv run python scripts/view_chunks.py docker.md

# View only first N chunks
uv run python scripts/view_chunks.py docker.md --limit 5

# Display full content
uv run python scripts/view_chunks.py docker.md --full
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_pdf_loader.py -v

# View coverage
uv run pytest --cov=src --cov-report=html
```

## 📁 Project Structure

```
book-rag/
├── src/
│   ├── config.py              # Configuration management
│   ├── embeddings.py          # Embedding wrapper
│   ├── vector_store.py        # Chroma vector storage
│   ├── loaders/               # Document loaders
│   │   ├── base.py           # Base classes
│   │   ├── pdf_loader.py     # PDF loader
│   │   ├── docx_loader.py    # Word loader
│   │   ├── markdown_loader.py # Markdown loader (with chapter detection)
│   │   ├── epub_loader.py    # EPUB loader
│   │   └── web_loader.py     # Web scraper
│   ├── retriever/             # Retrievers
│   │   ├── base.py           # Base retriever
│   │   └── ensemble.py       # Hybrid retriever (semantic + full-text)
│   ├── chains/                # Q&A chains
│   │   ├── llm_manager.py    # LLM manager
│   │   └── qa_chain.py       # QA chain
│   └── web/                   # Streamlit Web interface
│       ├── streamlit_app.py  # Main application
│       └── components/
│           ├── state.py      # Session state
│           ├── config.py     # Configuration panel
│           ├── documents.py  # Document management
│           └── chat.py       # Chat interface
├── data/
│   ├── documents/            # Document storage
│   └── chroma/              # Vector database
├── tests/                    # Test cases
├── scripts/                  # Development tools
│   └── view_chunks.py       # Chunk viewing tool
├── pyproject.toml           # Project configuration
├── .env_example             # Environment variable template
└── README.md
```

## 🔧 Tech Stack

- **Python**: >= 3.12
- **LangChain**: RAG framework
- **ChromaDB**: Vector database
- **sentence-transformers**: Text embeddings
- **Streamlit**: Web interface
- **OpenRouter**: Multi-cloud LLM access
- **rank-bm25**: Full-text search

## 📄 License

MIT License

## 🤝 Contributing

Issues and Pull Requests are welcome!
