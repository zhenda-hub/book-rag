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

    with st.expander("⚙️ API 配置", expanded=True):
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
