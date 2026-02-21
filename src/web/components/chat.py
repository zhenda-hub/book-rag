"""聊天界面组件"""
import streamlit as st
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.vector_store import VectorStore


# 初始示例问题
EXAMPLE_QUESTIONS = [
    "文档的主要内容是什么？",
    "总结一下核心观点",
    "有什么关键结论？",
]


def generate_followup_questions(question: str, answer: str, vector_store: "VectorStore") -> list:
    """生成后续问题建议

    Args:
        question: 用户的问题
        answer: 助手的回答
        vector_store: 向量存储实例

    Returns:
        后续问题列表
    """
    # 验证 API Key
    if not st.session_state.api_key:
        return []

    # 验证文档
    has_documents = len(vector_store.get_all_sources()) > 0
    if not has_documents:
        return []

    try:
        from src.chains.qa_chain import QAChain
        from src.retriever.base import Retriever

        # 创建 QA Chain（与 generate_response 保持一致）
        filter_dict = None
        if st.session_state.selected_sources:
            filter_dict = {"source": {"$in": st.session_state.selected_sources}}

        retriever = Retriever(vector_store=vector_store, filter_metadata=filter_dict)
        qa_chain = QAChain(retriever=retriever, llm_manager=st.session_state.llm_manager)

        return qa_chain.generate_followup_questions(question, answer)
    except Exception:
        return []


def generate_response(prompt: str, vector_store: "VectorStore") -> dict:
    """生成回复

    Args:
        prompt: 用户问题
        vector_store: 向量存储实例

    Returns:
        {"answer": str, "citations": list} 格式的回复
    """
    # 验证 API Key
    if not st.session_state.api_key:
        return {"answer": "⚠️ 请先在侧边栏配置 API Key", "citations": []}

    # 验证文档（检查向量存储中是否有文档）
    has_documents = len(vector_store.get_all_sources()) > 0
    if not has_documents:
        return {"answer": "⚠️ 请先上传文档", "citations": []}

    # 更新 LLM 管理器（每次都检查模型是否变化）
    from src.chains.llm_manager import LLMManager
    if st.session_state.llm_manager is None or st.session_state.llm_manager.default_model != st.session_state.selected_model:
        st.session_state.llm_manager = LLMManager(
            api_key=st.session_state.api_key,
            default_model=st.session_state.selected_model
        )

    try:
        from src.chains.qa_chain import QAChain
        from src.retriever.base import Retriever

        # 创建检索器（带过滤）
        filter_dict = None
        if st.session_state.selected_sources:
            filter_dict = {"source": {"$in": st.session_state.selected_sources}}

        retriever = Retriever(vector_store=vector_store, filter_metadata=filter_dict)
        qa_chain = QAChain(retriever=retriever, llm_manager=st.session_state.llm_manager)

        # 执行问答
        result = qa_chain.run(prompt)

        return {
            "answer": result.answer,
            "citations": result.citations
        }

    except Exception as e:
        return {
            "answer": f"❌ 出错了：{e}",
            "citations": []
        }


def _add_user_message(question: str) -> None:
    """添加用户消息到历史

    Args:
        question: 用户问题
    """
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)


def _add_assistant_message(response: dict) -> str:
    """添加助手消息到历史

    Args:
        response: 响应字典

    Returns:
        助手的回答内容
    """
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            st.markdown(response["answer"])

            if response.get("citations"):
                with st.expander("📚 查看引用"):
                    for citation in response["citations"]:
                        st.caption(f"- {citation}")
                        with st.expander("查看原文", expanded=True):
                            st.markdown(citation.format_full())

    # 添加到历史
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response["answer"],
        "citations": response.get("citations", [])
    })

    return response["answer"]


def render_chat_interface(vector_store: "VectorStore") -> None:
    """渲染聊天界面

    Args:
        vector_store: 向量存储实例
    """
    st.header("💬 问答")

    # 显示聊天历史
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("citations"):
                    with st.expander("📚 查看引用"):
                        for citation in msg["citations"]:
                            st.caption(f"- {citation}")
                            with st.expander("查看原文", expanded=True):
                                st.markdown(citation.format_full())

    # 清空对话按钮
    if st.session_state.chat_history:
        if st.button("清空对话", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.suggested_questions = []
            st.rerun()

    # 建议问题区域
    suggested_questions = st.session_state.get("suggested_questions", [])
    questions_to_show = suggested_questions if suggested_questions else EXAMPLE_QUESTIONS

    st.markdown("**💡 试试这些问题：**")
    for question in questions_to_show:
        if st.button(question, key=f"suggested_{question}"):
                # 清空之前的建议问题
                st.session_state.suggested_questions = []

                # 添加用户消息
                _add_user_message(question)

                # 生成助手回复
                response = generate_response(question, vector_store)
                answer = _add_assistant_message(response)

                # 生成后续问题建议
                followup_questions = generate_followup_questions(question, answer, vector_store)
                st.session_state.suggested_questions = followup_questions

                st.rerun()

    # 聊天输入
    if prompt := st.chat_input("输入你的问题..."):
        # 清空之前的建议问题
        st.session_state.suggested_questions = []

        # 添加用户消息
        _add_user_message(prompt)

        # 生成助手回复
        response = generate_response(prompt, vector_store)
        answer = _add_assistant_message(response)

        # 生成后续问题建议
        followup_questions = generate_followup_questions(prompt, answer, vector_store)
        st.session_state.suggested_questions = followup_questions

        st.rerun()
