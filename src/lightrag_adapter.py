"""LightRAG 适配器 - 支持多 provider"""
import os
import numpy as np
from pathlib import Path
from functools import lru_cache

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.utils import wrap_embedding_func_with_attrs

WORKING_DIR = str(Path(__file__).parent.parent / "data" / "lightrag")

# Provider 配置
PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "env_key": "SILICONFLOW_API_KEY",
    },
}

# LightRAG insert 推荐模型（SiliconFlow，高 RPM）
DEFAULT_INSERT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


@wrap_embedding_func_with_attrs(embedding_dim=384, max_token_size=8192)
async def embedding_func(texts: list[str]) -> np.ndarray:
    """复用项目已有的 sentence-transformers 模型"""
    embeddings = _get_embeddings()
    return np.array(embeddings.embed_documents(texts))


@lru_cache(maxsize=1)
def _get_embeddings():
    """缓存 embeddings 实例"""
    from src.config import get_embeddings
    return get_embeddings()


def _get_rag(api_key: str, model: str, base_url: str) -> LightRAG:
    """创建 LightRAG 实例"""
    async def llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return await openai_complete_if_cache(
            model,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=api_key,
            base_url=base_url,
        )

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_func,
        embedding_func=embedding_func,
    )
    return rag


def _resolve_provider(provider: str, api_key: str = None) -> tuple[str, str]:
    """解析 provider，返回 (api_key, base_url)"""
    if provider not in PROVIDERS:
        provider = "openrouter"

    config = PROVIDERS[provider]
    key = api_key or os.getenv(config["env_key"])
    return key, config["base_url"]


async def insert_text(
    text: str,
    api_key: str = None,
    model: str = None,
    provider: str = "siliconflow",
) -> None:
    """插入文本到 LightRAG（默认用 SiliconFlow，高 RPM）

    Args:
        text: 文本内容
        api_key: API Key（默认从环境变量读取）
        model: 模型名称（默认用 SiliconFlow 推荐模型）
        provider: 提供方（默认 siliconflow）
    """
    resolved_key, base_url = _resolve_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"未配置 {provider} API Key")

    if not model:
        model = DEFAULT_INSERT_MODEL

    rag = _get_rag(resolved_key, model, base_url)
    await rag.initialize_storages()
    try:
        await rag.ainsert(text)
    finally:
        await rag.finalize_storages()


async def query(
    question: str,
    api_key: str,
    model: str,
    mode: str = "hybrid",
    provider: str = "openrouter",
) -> str:
    """查询 LightRAG

    Args:
        question: 问题
        api_key: API Key
        model: 模型名称
        mode: 查询模式 (hybrid/local/global/naive)
        provider: 提供方
    """
    resolved_key, base_url = _resolve_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"未配置 {provider} API Key")

    rag = _get_rag(resolved_key, model, base_url)
    await rag.initialize_storages()
    try:
        return await rag.aquery(question, param=QueryParam(mode=mode))
    finally:
        await rag.finalize_storages()
