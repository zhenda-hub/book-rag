"""文档管理组件"""
import streamlit as st
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.vector_store import VectorStore

from src.chunking.splitter import get_text_splitter
from src.loaders.base import Document


def split_markdown_document(doc: Document, original_filename: str, original_source: str) -> List[Document]:
    """使用 MarkdownHeaderTextSplitter 切分 Markdown 文档

    两阶段切分：
    1. 先按标题切分，保留结构信息
    2. 对过长的块用 RecursiveCharacterTextSplitter 二次切分

    Args:
        doc: 原始文档
        original_filename: 原始文件名
        original_source: 原始 source 标识

    Returns:
        切分后的文档列表
    """
    from langchain_text_splitters import MarkdownHeaderTextSplitter
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # 预处理：移除 front matter（Hugo 格式：+++...+++ 或 ---...---）
    content = doc.content
    if content.startswith("+++"):
        # 跳过第一个 +++ 之间的内容
        end_idx = content.find("+++", 3)
        if end_idx != -1:
            content = content[end_idx + 3:].lstrip()
    elif content.startswith("---"):
        # 跳过第一个 --- 之间的内容
        end_idx = content.find("---", 3)
        if end_idx != -1:
            content = content[end_idx + 3:].lstrip()

    # 预处理：移除常见的 TOC 标记（它们不是标题，会导致第一个块没有标题 metadata）
    import re
    # 移除 [toc]、[TOC]、{{< toc >}} 等 TOC 标记
    content = re.sub(r'^\[(toc|TOC)\]\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^{{<\s*toc\s*>}}\s*$', '', content, flags=re.MULTILINE)
    # 清理多余的空行
    content = re.sub(r'\n{3,}', '\n\n', content.strip())

    # 配置所有 6 级标题
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
            ("####", "h4"),
            ("#####", "h5"),
            ("######", "h6"),
        ]
    )

    # 第二阶段：对过长的块进行切分（改进的分隔符，保护 Markdown 特殊结构）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # 从 500 提高到 1000，减少切分频率
        chunk_overlap=100,  # 从 50 提高到 100，增加上下文
        separators=[
            "\n\n\n",  # 多个空行（安全）
            "\n## ",   # 二级标题（安全）
            "\n### ",  # 三级标题（安全）
            "\n#### ", # 四级标题（安全）
            "\n##### ",# 五级标题（安全）
            "\n###### ",# 六级标题（安全）
            "\n\n",    # 段落间空行（相对安全）
            "。", "！", "？",  # 中文标点
            ". ",      # 英文句号
            " ",       # 空格
            "",        # 字符级切分（最后手段）
        ],
    )

    # 第一阶段：按标题切分
    langchain_docs = md_splitter.split_text(content)

    # 第二阶段：对每个块进行大小控制
    chunked_docs = []
    chunk_index = 0

    for lc_doc in langchain_docs:
        page_content = lc_doc.page_content

        # 如果内容超过阈值，进行二次切分
        if len(page_content) > 1000:  # 从 500 提高到 1000
            sub_chunks = text_splitter.split_text(page_content)
            for sub_chunk in sub_chunks:
                chunked_doc = Document(
                    content=sub_chunk,
                    metadata={
                        **doc.metadata,
                        **lc_doc.metadata,  # 包含 h1, h2 等标题信息
                        "chunk_index": chunk_index,
                        "original_filename": original_filename,
                    },
                    source=original_source,
                )
                chunked_docs.append(chunked_doc)
                chunk_index += 1
        else:
            # 内容较短，直接作为一个块
            chunked_doc = Document(
                content=page_content,
                metadata={
                    **doc.metadata,
                    **lc_doc.metadata,
                    "chunk_index": chunk_index,
                    "original_filename": original_filename,
                },
                source=original_source,
            )
            chunked_docs.append(chunked_doc)
            chunk_index += 1

    # 更新 total_chunks
    for chunk_doc in chunked_docs:
        chunk_doc.metadata["total_chunks"] = len(chunked_docs)

    return chunked_docs


def split_regular_document(doc: Document, original_filename: str, original_source: str) -> List[Document]:
    """使用常规文本切分器切分文档

    Args:
        doc: 原始文档
        original_filename: 原始文件名
        original_source: 原始 source 标识

    Returns:
        切分后的文档列表
    """
    chunked_docs = []
    chunks = get_text_splitter().split_text(doc.content)

    for j, chunk in enumerate(chunks):
        chunked_doc = Document(
            content=chunk,
            metadata={
                **doc.metadata,
                "chunk_index": j,
                "total_chunks": len(chunks),
                "original_filename": original_filename,
            },
            source=original_source,
        )
        chunked_docs.append(chunked_doc)

    return chunked_docs


def render_document_panel(vector_store: "VectorStore") -> None:
    """渲染文档上传面板

    Args:
        vector_store: 向量存储实例
    """
    with st.expander("📄 上传文档"):
        uploaded_files = st.file_uploader(
            "选择文件",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'md', 'epub'],
            help="支持：PDF, DOCX, TXT, MD, EPUB"
        )

        if uploaded_files and st.button("上传", type="primary", use_container_width=True):
            with st.status("正在处理...", expanded=True) as status:
                from src.loaders import get_loader

                total = len(uploaded_files)
                for i, file in enumerate(uploaded_files):
                    status.update(label=f"处理 {file.name} ({i+1}/{total})")

                    # 使用原始文件名作为 source（加上前缀避免冲突）
                    original_source = f"upload:{file.name}"

                    # 检查是否已存在
                    if vector_store.source_exists(original_source):
                        st.info(f"⏭️ {file.name} 已存在，跳过")
                        continue

                    # 保存临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix) as f:
                        f.write(file.getvalue())
                        temp_path = f.name

                    try:
                        path = Path(temp_path)

                        # 加载文档
                        loader = get_loader(str(path))
                        documents = loader.load(str(path))

                        # 切分文档
                        chunked_docs = []
                        is_markdown = path.suffix.lower() in ['.md', '.markdown']

                        for doc in documents:
                            if is_markdown:
                                # 使用 Markdown 专用切分器
                                chunks = split_markdown_document(doc, file.name, original_source)
                            else:
                                # 使用常规切分器
                                chunks = split_regular_document(doc, file.name, original_source)
                            chunked_docs.extend(chunks)

                        # 清除旧数据（如果存在）
                        vector_store.delete_by_source(original_source)

                        # 存储到向量库
                        vector_store.add_documents(chunked_docs)
                        st.success(f"✅ {file.name}: {len(chunked_docs)} 个块")

                    except Exception as e:
                        st.error(f"❌ {file.name}: {e}")
                    finally:
                        # 清理临时文件
                        try:
                            Path(temp_path).unlink(missing_ok=True)
                        except:
                            pass

                status.update(label="完成！", state="complete")
                st.session_state.documents_loaded = True
                st.rerun()


def render_web_scraping(vector_store: "VectorStore") -> None:
    """渲染网页抓取面板

    Args:
        vector_store: 向量存储实例
    """
    with st.expander("🔗 网页抓取"):
        url = st.text_input("网页 URL", placeholder="https://example.com", key="web_url")

        if st.button("抓取", use_container_width=True, key="scrape_btn"):
            if url and url.strip():
                url = url.strip()

                # 检查是否已存在
                if vector_store.source_exists(url):
                    st.warning(f"⏭️ URL 已存在: {url}")
                    return

                with st.spinner("正在抓取..."):
                    try:
                        from src.loaders.web_loader import WebLoader
                        from src.loaders.base import Document

                        # 抓取网页
                        loader = WebLoader()
                        documents = loader.load(url)

                        # 切分文档
                        chunked_docs = []
                        for doc in documents:
                            chunks = get_text_splitter().split_text(doc.content)
                            for i, chunk in enumerate(chunks):
                                chunked_doc = Document(
                                    content=chunk,
                                    metadata={
                                        **doc.metadata,
                                        "chunk_index": i,
                                        "total_chunks": len(chunks),
                                    },
                                    source=doc.source,
                                )
                                chunked_docs.append(chunked_doc)

                        # 存储到向量库
                        vector_store.add_documents(chunked_docs)

                        st.success(f"✅ 成功抓取：{url}\n📊 共 {len(chunked_docs)} 个文档块")
                        st.session_state.documents_loaded = True
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 抓取失败：{e}")


def render_file_management(vector_store: "VectorStore") -> None:
    """渲染文件管理面板

    Args:
        vector_store: 向量存储实例
    """
    with st.expander("📁 文件管理", expanded=True):
        all_sources = vector_store.get_all_sources()
        source_counts = vector_store.get_all_sources_with_counts()

        # 分组显示：上传的文件和网页
        upload_files = [s for s in all_sources if s.startswith("upload:")]
        web_files = [s for s in all_sources if s.startswith("http")]
        old_files = [s for s in all_sources if s not in upload_files + web_files]

        # 初始化禁用文件集合
        if 'disabled_sources' not in st.session_state:
            st.session_state.disabled_sources = set()

        if upload_files or web_files:
            # 创建显示名称映射
            source_to_display = {}
            for source in all_sources:
                if source.startswith("upload:"):
                    source_to_display[source] = source.replace("upload:", "")
                elif source.startswith("http"):
                    source_to_display[source] = source[:50] + "..." if len(source) > 50 else source
                else:
                    source_to_display[source] = Path(source).name

            # 表头（只显示一次）
            header_col1, header_col2, header_col3, header_col4 = st.columns([1, 5, 2, 2])
            with header_col1:
                st.markdown("**启用**")
            with header_col2:
                st.markdown("**文件名**")
            with header_col3:
                st.markdown("**Chunks**")
            with header_col4:
                st.markdown("**操作**")

            st.divider()  # 添加分隔线

            # 数据行：[复选框] [文件名] [chunk数量] [删除按钮]
            for source in all_sources:
                display_name = source_to_display[source]
                col1, col2, col3, col4 = st.columns([1, 5, 2, 2])

                with col1:
                    # 复选框：控制是否参与 RAG
                    is_checked = st.checkbox(
                        "启用",
                        value=source not in st.session_state.disabled_sources,
                        key=f"check_{source}",
                        label_visibility="hidden"
                    )
                    # 根据复选框状态更新 disabled_sources
                    if is_checked and source in st.session_state.disabled_sources:
                        st.session_state.disabled_sources.remove(source)
                    elif not is_checked and source not in st.session_state.disabled_sources:
                        st.session_state.disabled_sources.add(source)

                with col2:
                    # 文件名
                    st.text(display_name)

                with col3:
                    # chunk 数量（只显示数值）
                    chunk_count = source_counts.get(source, 0)
                    st.write(f"**{chunk_count}**")

                with col4:
                    # 删除按钮
                    if st.button("删除", key=f"delete_{source}"):
                        vector_store.delete_by_source(source)
                        # 同时从禁用集合中移除
                        st.session_state.disabled_sources.discard(source)
                        st.rerun()

            # 更新选中的文件（保持与其他模块的兼容性）
            st.session_state.selected_sources = [
                s for s in all_sources if s not in st.session_state.disabled_sources
            ]
        else:
            st.info("暂无文件，请先上传文档或抓取网页")
