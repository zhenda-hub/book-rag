"""Streamlit 会话状态管理"""
import streamlit as st


def init_session_state() -> None:
    """初始化会话状态"""
    from src.config import Config

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'api_key' not in st.session_state:
        st.session_state.api_key = Config.OPENROUTER_API_KEY
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'deepseek'
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = None
    if 'selected_sources' not in st.session_state:
        st.session_state.selected_sources = []
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False
    if '_vector_store' not in st.session_state:
        st.session_state._vector_store = None
    if '_embeddings' not in st.session_state:
        st.session_state._embeddings = None
    if 'suggested_questions' not in st.session_state:
        st.session_state.suggested_questions = []
    if 'search_mode' not in st.session_state:
        st.session_state.search_mode = '语义检索'  # 默认语义检索
    if 'retriever_weights' not in st.session_state:
        st.session_state.retriever_weights = {
            'semantic': 0.7,
            'fulltext': 0.3
        }


def get_vector_store():
    """获取向量存储实例（延迟加载）"""
    if st.session_state._vector_store is None:
        from src.vector_store import get_vector_store as _get_vector_store
        st.session_state._vector_store = _get_vector_store()
    return st.session_state._vector_store


def get_embeddings():
    """获取嵌入模型实例（延迟加载）"""
    if st.session_state._embeddings is None:
        from src.embeddings import get_embeddings as _get_embeddings
        st.session_state._embeddings = _get_embeddings()
    return st.session_state._embeddings
