"""文档管理组件"""
import streamlit as st
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.vector_store import VectorStore

from src.loaders.base import Document, CHUNKING_STRATEGY, STRATEGY_NONE


def _add_source_metadata(documents: List[Document], source: str, original_filename: str) -> List[Document]:
    """为文档添加 source 和 original_filename metadata

    Args:
        documents: 文档列表
        source: 原始 source 标识
        original_filename: 原始文件名

    Returns:
        添加了 metadata 的文档列表
    """
    result = []
    for doc in documents:
        new_doc = Document(
            content=doc.content,
            metadata={
                **doc.metadata,
                "original_filename": original_filename,
            },
            source=source,
        )
        result.append(new_doc)
    return result


@st.fragment
def render_document_panel(vector_store: "VectorStore") -> None:
    """渲染文档上传面板

    Args:
        vector_store: 向量存储实例
    """
    # 初始化 file_uploader key（用于上传成功后清除显示）
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = "file_uploader"

    with st.expander("📄 上传文档"):
        uploaded_files = st.file_uploader(
            "选择文件",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'md', 'epub', 'csv'],
            help="支持：PDF, DOCX, TXT, MD, EPUB, CSV",
            key=st.session_state.file_uploader_key
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
                        # 加载文档（Loader 已完成切分）
                        loader = get_loader(temp_path)
                        documents = loader.load(temp_path)

                        # 添加 source 和 original_filename metadata
                        documents = _add_source_metadata(documents, original_source, file.name)

                        # 清除旧数据（如果存在）
                        vector_store.delete_by_source(original_source)

                        # 存储到向量库
                        vector_store.add_documents(documents)
                        st.success(f"✅ {file.name}: {len(documents)} 个块")

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
                # 重置 file_uploader key 以清除显示
                st.session_state.file_uploader_key = f"file_uploader_{st.session_state.documents_loaded}"
                st.rerun()


@st.fragment
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

                        # 抓取网页（Loader 已完成切分）
                        loader = WebLoader()
                        documents = loader.load(url)

                        # 存储到向量库
                        vector_store.add_documents(documents)

                        st.success(f"✅ 成功抓取：{url}\n📊 共 {len(documents)} 个文档块")
                        st.session_state.documents_loaded = True
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 抓取失败：{e}")


@st.fragment
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

        # 初始化禁用文件集合（默认禁用所有文件）
        if 'disabled_sources' not in st.session_state:
            st.session_state.disabled_sources = set(all_sources)

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
