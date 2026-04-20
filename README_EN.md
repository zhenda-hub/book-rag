# 📚 Book RAG

[English](./README_EN.md) | [简体中文](./README.md)

<div align="center">
  <h3>Intelligent Document Q&A System · Hybrid Retrieval · Knowledge Graph · Mind Map</h3>
  <p>Fusing semantic search, full-text search, and graph retrieval for precise document Q&A with visualization capabilities</p>
</div>

## 🎯 Demo

![ui](./imgs/index.png)

## ✨ Key Features

### 🔍 Three Retrieval Modes

- **Semantic Search**: Vector-based similarity matching (sentence-transformers) for understanding semantic associations
- **Full-Text Search**: BM25 algorithm for precise keyword matching, ideal for finding specific content
- **Hybrid Search**: Combines both advantages with customizable weight balance (default semantic 0.7 + full-text 0.3), 30%+ recall improvement

### 🕸️ Knowledge Graph Enhancement (LightRAG)

- **Automatic Graph Construction**: Extract entities and relationships from documents to build a queryable knowledge graph
- **Three Graph Retrieval Modes**:
  - `local` - Local retrieval based on entity neighbors
  - `global` - Global retrieval across entities based on relationship chains
  - `hybrid` - Comprehensive retrieval combining local and global
- **Graph Visualization**: Use pyvis to display entity relationship networks
- **Entity Merging**: Support manual merging of alias entities to resolve knowledge fragmentation

### 🗺️ Mind Map Generation

- **Automatic Chapter Detection**: Automatically identify chapter hierarchy in Markdown documents
- **Tree Visualization**: Render mind maps with ECharts for intuitive document structure display
- **Performance Optimization**: File caching mechanism, large documents (100K+ words) render in < 1s

### 📄 Multi-Format Document Support

- **File Upload**: PDF, Word (DOCX), Markdown, TXT, EPUB
- **Web Scraping**: Extract web content by simply entering a URL
- **Smart Chunking**: Automatic chapter detection for Markdown, page number extraction for PDF

### 🎯 Precise Citation Tracking

- Display answer sources: book title, chapter, page number
- Similarity scores
- One-click original content viewing

### 💬 Intelligent Chat Experience

- Auto-generated follow-up question suggestions
- Chat history
- Example question recommendations

### 🤖 Multi-Cloud LLM Support

Via OpenRouter / SiliconFlow:

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

# Edit .env file, fill in API Key
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Launch Web Interface

```bash
uv run streamlit run src/web/streamlit_app.py
```

Visit http://127.0.0.1:8501 to get started!

## 📖 User Guide

### 1. Configuration Panel

Set API Key, LLM model, and retrieval mode in the sidebar

### 2. Add Documents

- **Upload Files**: Support PDF, DOCX, MD, TXT, EPUB
- **Web Scraping**: Enter URL to automatically extract content

### 3. Choose Retrieval Mode

Select the best retrieval method based on your question type:

| Question Type | Recommended Mode | Description |
|---------------|------------------|-------------|
| Semantic Understanding | Semantic Search | Understand concepts, meanings |
| Exact Lookup | Full-Text Search | Find specific keywords |
| Comprehensive Query | Hybrid Search | Balance semantics and keywords |
| Cross-Entity Relationships | Graph-Global | Global retrieval across relationship chains |
| Local Context | Graph-Local | Local retrieval based on entity neighbors |
| Full Scope | Graph-Hybrid | Combine local and global |

### 4. View Visualizations

- **Mind Map**: View document chapter structure
- **Knowledge Graph**: View entity relationship networks

### 5. Start Q&A

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

# Show full content
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
│   ├── lightrag/              # LightRAG integration
│   │   ├── __init__.py
│   │   └── manager.py         # LightRAG manager
│   ├── loaders/               # Document loaders
│   │   ├── base.py           # Base classes
│   │   ├── pdf_loader.py     # PDF loader
│   │   ├── docx_loader.py    # Word loader
│   │   ├── markdown_loader.py # Markdown loader (with chapter detection)
│   │   ├── epub_loader.py    # EPUB loader
│   │   └── web_loader.py     # Web scraper
│   ├── retriever/             # Retrievers
│   │   ├── base.py           # Base retriever
│   │   └── ensemble.py       # Hybrid retrieval (semantic + full-text)
│   ├── chains/                # Q&A chains
│   │   ├── llm_manager.py    # LLM manager
│   │   └── qa_chain.py       # QA chain
│   └── web/                   # Streamlit web interface
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
│   └── view_chunks.py       # View chunks tool
├── docs/                     # Documentation
│   └── lightrag-parameters.md # LightRAG parameters guide
├── pyproject.toml           # Project configuration
├── .env_example             # Environment variable template
└── README.md
```

## 🔧 Tech Stack

- **Python**: >= 3.12
- **LangChain**: RAG framework
- **LightRAG**: Knowledge graph construction and retrieval
- **ChromaDB**: Vector database
- **sentence-transformers**: Text embedding
- **rank-bm25**: Full-text search
- **ECharts**: Mind map rendering
- **pyvis**: Graph visualization
- **Streamlit**: Web interface
- **OpenRouter**: Multi-cloud LLM access

## 📄 License

MIT License

## 🤝 Contributing

Issues and Pull Requests are welcome!
