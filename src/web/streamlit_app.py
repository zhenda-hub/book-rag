"""Streamlit Web 界面 - Book RAG"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.web.components.state import init_session_state, get_vector_store
from src.web.components.config import render_config_panel
from src.web.components.documents import render_document_panel, render_web_scraping, render_file_management
from src.web.components.chat import render_chat_interface


def main():
    # 页面配置
    st.set_page_config(
        page_title="Book RAG",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 初始化状态
    init_session_state()

    # 侧边栏
    with st.sidebar:
        st.title("📚 Book RAG")
        st.markdown("---")

        render_config_panel()
        st.markdown("---")

        # 获取向量存储（在需要时才加载）
        vector_store = get_vector_store()

        render_document_panel(vector_store)
        st.markdown("")

        render_web_scraping(vector_store)
        st.markdown("---")

        render_file_management(vector_store)

    # 主内容区：Tab 切换聊天和图谱
    vector_store = get_vector_store()
    tab_chat, tab_graph = st.tabs(["💬 问答", "🕸️ 图谱可视化"])

    with tab_chat:
        render_chat_interface(vector_store)

    with tab_graph:
        from src.web.components.graph_viewer import render_graph_viewer
        render_graph_viewer()


if __name__ == "__main__":
    main()
