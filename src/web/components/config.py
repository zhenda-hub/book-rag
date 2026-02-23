"""配置面板组件"""
import streamlit as st


@st.cache_data
def get_available_models(api_key: str) -> list:
    """获取可用模型列表（带缓存）"""
    if not api_key:
        return ["deepseek"]
    try:
        from src.chains.llm_manager import LLMManager
        llm = LLMManager(api_key=api_key)
        models = llm.get_free_models()
        return models if models else ["deepseek"]
    except Exception:
        return ["deepseek"]


def render_config_panel() -> tuple[str, str]:
    """渲染配置面板

    Returns:
        (api_key, model) 元组
    """
    from src.config import Config

    with st.expander("⚙️ API 配置"):
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=st.session_state.api_key,
            help="在 https://openrouter.ai/ 获取"
        )

        # 显示 API Key 来源指示器
        if api_key:
            if api_key == Config.OPENROUTER_API_KEY:
                st.caption("✅ API Key 从环境变量加载")
            else:
                st.caption("✏️ 使用自定义 API Key")

        models = get_available_models(api_key)
        model = st.selectbox(
            "模型",
            models,
            index=models.index(st.session_state.selected_model) if st.session_state.selected_model in models else 0
        )

        # 更新会话状态
        st.session_state.api_key = api_key
        st.session_state.selected_model = model

    with st.expander("🔍 搜索配置"):
        # 搜索模式选择
        search_mode = st.selectbox(
            "搜索模式",
            options=["语义检索", "全文检索", "混合检索"],
            index=["语义检索", "全文检索", "混合检索"].index(st.session_state.search_mode) if st.session_state.search_mode in ["语义检索", "全文检索", "混合检索"] else 0,
            help="""
            - **语义检索**: 基于向量相似度，适合理解语义
            - **全文检索**: 基于 BM25 关键词匹配，适合精确匹配
            - **混合检索**: 结合两者优势，自动融合结果
            """
        )
        st.session_state.search_mode = search_mode

        # 混合检索权重配置
        if search_mode == "混合检索":
            st.markdown("**检索权重配置**")
            col1, col2 = st.columns(2)

            with col1:
                semantic_weight = st.slider(
                    "语义权重",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.retriever_weights.get("semantic", 0.7),
                    step=0.1,
                    help="语义检索的权重"
                )

            with col2:
                fulltext_weight = st.slider(
                    "全文权重",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.retriever_weights.get("fulltext", 0.3),
                    step=0.1,
                    help="全文检索的权重"
                )

            # 权重归一化提示
            total = semantic_weight + fulltext_weight
            if abs(total - 1.0) > 0.01:
                st.caption(f"⚠️ 权重之和为 {total:.1f}，将自动归一化")

            st.session_state.retriever_weights = {
                "semantic": semantic_weight,
                "fulltext": fulltext_weight
            }

    return api_key, model
