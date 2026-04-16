"""LightRAG 适配器 - 每文档独立 workspace + 同名缓存"""
import os
import re
import shutil
import numpy as np
from pathlib import Path
from functools import lru_cache

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.utils import wrap_embedding_func_with_attrs

BASE_DIR = Path(__file__).parent.parent / "data" / "lightrag"

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


def _safe_dirname(source: str) -> str:
    """将 source 转为安全的目录名"""
    name = re.sub(r'[^\w\-]', '_', source)
    return name[:200]


def _get_workspace_dir(source: str) -> Path:
    """获取文档对应的 workspace 目录"""
    return BASE_DIR / _safe_dirname(source)


def has_graph(source: str) -> bool:
    """检查 source 是否已有图谱（同名缓存判断）"""
    workspace = _get_workspace_dir(source)
    return workspace.exists() and any(workspace.iterdir())


def delete_graph(source: str) -> None:
    """删除 source 对应的图谱 workspace"""
    workspace = _get_workspace_dir(source)
    if workspace.exists():
        shutil.rmtree(workspace)


def get_graph_sources() -> list[str]:
    """列出所有已有图谱的 source 名称"""
    if not BASE_DIR.exists():
        return []
    return [
        d.name for d in BASE_DIR.iterdir()
        if d.is_dir() and any(d.iterdir())
    ]


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


def _get_rag(api_key: str, model: str, base_url: str, workspace_dir: str) -> LightRAG:
    """创建 LightRAG 实例（指定 workspace）"""
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
        working_dir=workspace_dir,
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
    source: str,
    api_key: str = None,
    model: str = None,
    provider: str = "siliconflow",
) -> bool:
    """插入文本到 LightRAG（每文档独立 workspace，同名缓存）

    Args:
        text: 文本内容
        source: 文档 source 标识（如 upload:file.md）
        api_key: API Key
        model: 模型名称
        provider: 提供方

    Returns:
        True 表示新建图谱，False 表示缓存命中跳过
    """
    # 同名缓存：workspace 已存在且非空则跳过
    if has_graph(source):
        return False

    resolved_key, base_url = _resolve_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"未配置 {provider} API Key")

    if not model:
        model = DEFAULT_INSERT_MODEL

    workspace_dir = str(_get_workspace_dir(source))
    rag = _get_rag(resolved_key, model, base_url, workspace_dir)
    await rag.initialize_storages()
    try:
        await rag.ainsert(text)
    finally:
        await rag.finalize_storages()

    return True


async def query(
    question: str,
    api_key: str,
    model: str,
    sources: list[str] = None,
    mode: str = "hybrid",
    provider: str = "openrouter",
) -> str:
    """查询 LightRAG（遍历所有启用文档的 workspace）

    Args:
        question: 问题
        api_key: API Key
        model: 模型名称
        sources: 启用的文档 source 列表（None 则查所有）
        mode: 查询模式
        provider: 提供方
    """
    resolved_key, base_url = _resolve_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"未配置 {provider} API Key")

    # 确定要查询的 source 列表
    if sources is None:
        sources = get_graph_sources()

    # 过滤出有图谱的 source
    active_sources = [s for s in sources if has_graph(s)]

    if not active_sources:
        return "暂无知识图谱数据，请先上传文档并构建图谱。"

    # 逐个 workspace 查询
    results = []
    for source in active_sources:
        workspace_dir = str(_get_workspace_dir(source))
        rag = _get_rag(resolved_key, model, base_url, workspace_dir)
        await rag.initialize_storages()
        try:
            answer = await rag.aquery(question, param=QueryParam(mode=mode))
            if answer:
                results.append(answer)
        finally:
            await rag.finalize_storages()

    if not results:
        return "未找到相关图谱信息。"

    return "\n\n---\n\n".join(results)
