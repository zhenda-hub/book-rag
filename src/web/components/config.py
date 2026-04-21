"""配置面板组件"""
import streamlit as st


def get_available_models(api_key: str, provider: str = "openrouter") -> list:
    """获取可用模型列表（不缓存，确保实时获取）"""
    if not api_key:
        if provider == "siliconflow":
            return ["Qwen/Qwen2.5-7B-Instruct"]
        return ["deepseek/deepseek-chat"]
    try:
        from src.chains.llm_manager import LLMManager
        llm = LLMManager(api_key=api_key, provider=provider)
        models = llm.get_free_models()
        return models if models else ["deepseek/deepseek-chat"]
    except RuntimeError as e:
        # 模型获取失败时的具体错误
        if provider == "openrouter":
            st.warning(f"📋 OpenRouter 模型获取失败: {e}")
            st.caption("💡 将使用默认模型 deepseek/deepseek-chat")
        else:
            st.warning(f"📋 SiliconFlow 模型获取失败: {e}")
            st.caption("💡 将使用默认模型 Qwen/Qwen2.5-7B-Instruct")
        if provider == "siliconflow":
            return ["Qwen/Qwen2.5-7B-Instruct"]
        return ["deepseek/deepseek-chat"]
    except Exception as e:
        # 其他异常
        if provider == "openrouter":
            st.warning(f"📋 OpenRouter 连接失败: {e}")
            st.caption("💡 将使用默认模型 deepseek/deepseek-chat")
        else:
            st.warning(f"📋 SiliconFlow 连接失败: {e}")
            st.caption("💡 将使用默认模型 Qwen/Qwen2.5-7B-Instruct")
        if provider == "siliconflow":
            return ["Qwen/Qwen2.5-7B-Instruct"]
        return ["deepseek/deepseek-chat"]



def render_config_panel() -> tuple[str, str]:
    """渲染配置面板

    Returns:
        (api_key, model) 元组
    """
    from src.config import Config

    # --- API 配置（含 Provider 选择）---
    with st.expander("⚙️ API 配置"):
        provider = st.radio(
            "提供方",
            options=["openrouter", "siliconflow"],
            format_func=lambda x: {
                "openrouter": "🌐 OpenRouter",
                "siliconflow": "🇨🇳 SiliconFlow",
            }[x],
            index=["openrouter", "siliconflow"].index(
                st.session_state.get("llm_provider", "openrouter")
            ),
            horizontal=True,
        )
        st.session_state.llm_provider = provider

        if provider == "siliconflow":
            env_api_key = Config.SILICONFLOW_API_KEY
            key_label = "SiliconFlow API Key"
            key_help = "在 https://cloud.siliconflow.cn 获取"
        else:
            env_api_key = Config.OPENROUTER_API_KEY
            key_label = "OpenRouter API Key"
            key_help = "在 https://openrouter.ai/ 获取"

        provider_key = st.session_state.get(f"api_key_{provider}", env_api_key)
        api_key = st.text_input(
            key_label,
            type="password",
            value=provider_key,
            help=key_help,
        )

        st.session_state[f"api_key_{provider}"] = api_key
        st.session_state.api_key = api_key

        if api_key:
            if provider == "siliconflow" and api_key == Config.SILICONFLOW_API_KEY:
                st.caption("✅ API Key 从环境变量加载")
            elif provider == "openrouter" and api_key == Config.OPENROUTER_API_KEY:
                st.caption("✅ API Key 从环境变量加载")
            else:
                st.caption("✏️ 使用自定义 API Key")

        models = get_available_models(api_key, provider)
        model = st.selectbox(
            "模型",
            models,
            index=models.index(st.session_state.selected_model) if st.session_state.selected_model in models else 0
        )

        st.session_state.selected_model = model

    # --- 搜索配置 ---
    with st.expander("🔍 搜索配置"):
        mode_choice = st.radio(
            "检索模式",
            options=["local", "global", "lightrag"],
            format_func=lambda x: {
                "local": "🔍 局部模式",
                "global": "📑 全局模式",
                "lightrag": "🕸️ 图谱模式",
            }[x],
            index=["local", "global", "lightrag"].index(
                st.session_state.get("search_scope", "local")
            ),
            horizontal=True,
            label_visibility="collapsed"
        )

        st.session_state.search_scope = mode_choice

        if mode_choice == "lightrag":
            st.session_state.retriever_weights = {"semantic": 0.5, "fulltext": 0.5}
            lightrag_mode = st.selectbox(
                "图谱查询模式",
                options=["hybrid", "local", "global", "naive"],
                format_func=lambda x: {
                    "hybrid": "混合 (推荐)",
                    "local": "实体关系",
                    "global": "全局主题",
                    "naive": "朴素向量",
                }[x],
                index=0,
            )
            st.session_state.lightrag_query_mode = lightrag_mode
            mode_descriptions = {
                "hybrid": "结合实体关系 + 全局主题，适合大多数问题",
                "local": "基于实体和直接关系检索，适合具体问题",
                "global": "基于跨实体关系检索，适合主题性问题，不适合概括性提问",
                "naive": "直接向量搜索文本块，适合概括、总结类问题",
            }
            st.caption(mode_descriptions[lightrag_mode])

        elif mode_choice == "local":
            fulltext_percent = st.slider(
                "语义检索 ──────── 全文检索",
                min_value=0,
                max_value=100,
                value=80,
                step=5,
                format="%d%% 全文",
                key="retrieval_fulltext_percent",
                help="向右拖动增加全文检索比例，向左拖动增加语义检索比例"
            )

            fulltext_ratio = fulltext_percent / 100.0
            st.session_state.retriever_weights = {
                "semantic": 1.0 - fulltext_ratio,
                "fulltext": fulltext_ratio
            }

            if fulltext_percent == 100:
                mode_label = "全文检索"
            elif fulltext_percent == 0:
                mode_label = "语义检索"
            else:
                mode_label = f"混合检索 (全文 {fulltext_percent}% / 语义 {100 - fulltext_percent}%)"
            st.caption(f"当前模式：{mode_label}")

        else:
            st.session_state.retriever_weights = {
                "semantic": 0.5,
                "fulltext": 0.5
            }
            st.info("📖 基于文档目录结构回答问题（仅 Markdown、EPUB 支持）")

    return api_key, model
