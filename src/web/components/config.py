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

    with st.expander("🔍 搜索配置", expanded=True):
        st.markdown("**检索模式**")

        # 始终显示检索范围选择
        search_scope = st.radio(
            "检索范围",
            ["局部模式", "全局模式"],
            index=0,  # 默认选中第一项（局部模式）
            horizontal=True,
            help="局部模式：搜索相关内容 | 全局模式：基于文档目录结构回答（仅 Markdown、EPUB 支持）"
        )
        st.session_state.search_scope = "local" if search_scope == "局部模式" else "global"

        # 只在局部模式下显示语义/全文滑块
        if st.session_state.search_scope == "local":
            fulltext_percent = st.slider(
                "语义检索 ──────── 全文检索",
                min_value=0,
                max_value=100,
                value=80,  # 初始默认值（80% 全文 / 20% 语义）
                step=5,
                format="%d%% 全文",
                key="retrieval_fulltext_percent",  # 使用 key 让 Streamlit 管理状态
                help="向右拖动增加全文检索比例，向左拖动增加语义检索比例"
            )

            # 转换为 0-1 范围存储
            fulltext_ratio = fulltext_percent / 100.0
            st.session_state.retriever_weights = {
                "semantic": 1.0 - fulltext_ratio,
                "fulltext": fulltext_ratio
            }

            # 显示当前模式标签
            if fulltext_percent == 100:
                mode_label = "全文检索"
            elif fulltext_percent == 0:
                mode_label = "语义检索"
            else:
                mode_label = f"混合检索 (全文 {fulltext_percent}% / 语义 {100 - fulltext_percent}%)"
            st.caption(f"当前模式：{mode_label}")

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

    return api_key, model
