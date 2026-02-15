# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) based knowledge base Q&A system with multi-format document parsing support and citation tracking.

## Core Features

- **Multi-format Document Parsing**: Supports PDF, Word, Markdown, EPUB formats
- **Web Scraping**: Extract content from URLs
- **Semantic Search**: Chroma-based vector database semantic search
- **Citation Tracking**: Display answer references with book title, chapter, and page number
- **Web Interface**: Gradio-based visual Q&A interface
- **Multi-cloud LLM**: Support multiple models (DeepSeek, GPT-4, Claude, etc.) via OpenRouter

## Common Commands

```bash
# Install dependencies using uv (recommended)
uv venv          # Create virtual environment
uv sync          # Sync dependencies
source .venv/bin/activate  # Activate environment

# Run Web interface
uv run streamlit run src/web/streamlit_app.py
# Or after activating environment
streamlit run src/web/streamlit_app.py
```

## Project Structure

```
book-rag/
├── src/
│   ├── config.py          # Configuration management
│   ├── embeddings.py      # Embedding wrapper (sentence-transformers)
│   ├── vector_store.py    # Chroma vector storage
│   ├── loaders/           # Document loaders
│   │   ├── base.py        # Document base class and loader base class
│   │   ├── pdf_loader.py  # PDF loader (pypdf + pdfplumber)
│   │   ├── docx_loader.py # Word loader
│   │   ├── markdown_loader.py # Markdown loader
│   │   ├── epub_loader.py # EPUB loader
│   │   └── web_loader.py  # Web scraper (trafilatura)
│   ├── chunking/          # Text chunking
│   │   └── chapter_detector.py # Chapter detection
│   ├── retriever/         # Retrieval
│   │   └── base.py        # Similarity-based retriever
│   ├── chains/            # Q&A chains
│   │   ├── llm_manager.py # LLM manager (OpenRouter)
│   │   └── qa_chain.py    # QA chain
│   └── web/               # Gradio Web interface
│       └── app.py         # Main application entry
├── data/
│   ├── documents/         # Documents to process
│   └── chroma/            # Vector database storage
├── pyproject.toml         # Project configuration and dependencies
├── .env_example           # Environment variable template
└── README.md
```

## Core Components

### 1. Document Loaders (`src/loaders/`)

All loaders inherit from `BaseLoader`, returning a list of `Document` objects:

```python
class Document:
    content: str      # Document content
    metadata: dict    # Metadata (book title, chapter, page number, etc.)
    source: str       # Source (file path or URL)
```

### 2. Vector Store (`src/vector_store.py`)

Uses Chroma as the vector database. Core methods:
- `add_documents(documents)` - Add documents
- `search(query, k=4)` - Semantic search
- `delete_by_source(source)` - Delete by source
- `source_exists(source)` - Check if source exists

### 3. Retriever (`src/retriever/base.py`)

Similarity-based retriever that returns the most relevant document chunks.

### 4. LLM Manager (`src/chains/llm_manager.py`)

- Supports OpenRouter API
- Dynamically fetches free model list
- Supports multiple models (deepseek, gpt-4, claude, etc.)

### 5. QA Chain (`src/chains/qa_chain.py`)

Combines retriever and LLM to generate answers with citations, returning:
- `answer`: Answer text
- `citations`: List of citations (book title, chapter, page number)

### 6. Web Interface (`src/web/app.py`)

Gradio application with features:
- Batch document upload
- Web URL scraping
- Interactive Q&A
- Model selection
- Progress display

## Environment Configuration

Project uses `.env` file for API keys:

```bash
# OpenRouter API Key (required)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Reference `.env_example` template.

## Dependency Management

- Uses `uv` + `pyproject.toml` for dependency management
- Python version requirement: >= 3.12
- Main dependencies:
  - `langchain` / `langchain-community` / `langchain-core`
  - `chromadb` - Vector database
  - `sentence-transformers` - Embeddings
  - `gradio` - Web interface
  - `openai` - OpenRouter API
  - Document parsing: `pypdf`, `pdfplumber`, `python-docx`, `ebooklib`, `trafilatura`

## Data Flow

1. **Document Loading**: Parse documents using appropriate loaders, extract text and metadata
2. **Text Chunking**: Split text into chunks by chapter or fixed size
3. **Vectorization**: Generate embeddings using sentence-transformers
4. **Storage**: Store in Chroma vector database
5. **Retrieval**: Semantic search based on questions
6. **Generation**: LLM generates answers with citations based on retrieved results

## Development Workflow

### Testing Standards

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_pdf_loader.py -v

# Run specific test function
uv run pytest tests/test_pdf_loader.py::test_load_document -v

# View coverage
uv run pytest --cov=src --cov-report=html
```

Test file structure:
```
tests/
├── test_loaders/      # Loader tests
├── test_chains/       # Q&A chain tests
├── test_retriever/    # Retriever tests
└── fixtures/          # Test data
```

## Development Notes

1. **Add new document format**: Create new loader in `src/loaders/`, inheriting from `BaseLoader`
2. **Modify chunking strategy**: Modify `split_text` function in `src/web/app.py`
3. **Change Embedding model**: Modify `src/embeddings.py`
4. **Change vector database**: Modify `src/vector_store.py`
5. **Customize prompt**: Modify `src/chains/qa_chain.py`
