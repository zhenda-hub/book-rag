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



def _detect_language(text: str) -> str:
    """根据中文字符占比判断语言"""
    if not text:
        return "English"
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return "Chinese" if chinese_chars / len(text) > 0.15 else "English"


def _meta_path(source: str) -> Path:
    """获取 workspace 元数据文件路径"""
    return _get_workspace_dir(source) / "_meta.json"


def _save_meta(source: str, data: dict) -> None:
    """保存 workspace 元数据"""
    meta_file = _meta_path(source)
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    import json
    meta_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_meta(source: str) -> dict:
    """读取 workspace 元数据"""
    meta_file = _meta_path(source)
    if not meta_file.exists():
        return {}
    import json
    return json.loads(meta_file.read_text(encoding="utf-8"))


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


def get_graph_info(source: str) -> dict:
    """获取图谱信息（是否存在、LLM 调用次数）"""
    exists = has_graph(source)
    if not exists:
        return {"has_graph": False, "llm_calls": 0}
    meta = _load_meta(source)
    return {
        "has_graph": True,
        "llm_calls": meta.get("llm_calls", 0),
    }


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


def _get_rag(api_key: str, model: str, base_url: str, workspace_dir: str, language: str = "English", call_counter: list = None, last_error: list = None) -> LightRAG:
    """创建 LightRAG 实例（指定 workspace）

    Args:
        call_counter: 可选的计数器 [0]，llm_func 每次调用后自增
        last_error: 可选的 [""], llm_func 捕获异常时记录错误信息
    """
    async def llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        try:
            result = await openai_complete_if_cache(
                model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=api_key,
                base_url=base_url,
            )
        except Exception as e:
            if last_error is not None:
                last_error[0] = str(e)
            raise
        if call_counter is not None:
            call_counter[0] += 1
        return result

    rag = LightRAG(
        working_dir=workspace_dir,
        llm_model_func=llm_func,
        embedding_func=embedding_func,
        addon_params={"language": language},
        cosine_better_than_threshold=0.4,
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
        return False, 0

    resolved_key, base_url = _resolve_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"未配置 {provider} API Key")

    if not model:
        raise ValueError("未指定模型，请在界面选择模型后重试")

    language = _detect_language(text)
    workspace_dir = str(_get_workspace_dir(source))
    call_counter = [0]
    rag = _get_rag(resolved_key, model, base_url, workspace_dir, language=language, call_counter=call_counter)
    await rag.initialize_storages()
    try:
        await rag.ainsert(text)
    except Exception:
        # 构建失败，清理 workspace 避免缓存半成品
        await rag.finalize_storages()
        delete_graph(source)
        raise
    await rag.finalize_storages()

    # 保存语言设置和 LLM 调用次数
    _save_meta(source, {"language": language, "llm_calls": call_counter[0]})

    return True, call_counter[0]


def _query_cache_path(source: str) -> Path:
    """获取查询缓存文件路径"""
    return _get_workspace_dir(source) / "_query_cache.json"


def _load_query_cache(source: str) -> dict:
    """加载查询缓存"""
    cache_file = _query_cache_path(source)
    if not cache_file.exists():
        return {}
    import json
    return json.loads(cache_file.read_text(encoding="utf-8"))


def _save_query_cache(source: str, cache: dict) -> None:
    """保存查询缓存"""
    cache_file = _query_cache_path(source)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    import json
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


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
    errors = []
    for source in active_sources:
        # 检查查询缓存
        cache = _load_query_cache(source)
        cache_key = f"{mode}:{question}"
        if cache_key in cache:
            results.append(cache[cache_key])
            continue

        meta = _load_meta(source)
        language = meta.get("language", "English")
        workspace_dir = str(_get_workspace_dir(source))
        last_error = [""]
        rag = _get_rag(resolved_key, model, base_url, workspace_dir, language=language, last_error=last_error)
        await rag.initialize_storages()
        try:
            answer = await rag.aquery(question, param=QueryParam(mode=mode))
            if answer:
                results.append(answer)
                # 缓存成功的结果
                cache[cache_key] = answer
                _save_query_cache(source, cache)
            elif last_error[0]:
                # LightRAG 吞掉了错误，但从 last_error 捕获到了
                err = last_error[0]
                if "429" in err:
                    errors.append(f"{source}: API 限流（429），请稍后重试")
                elif "1301" in err or "sensitive" in err.lower() or "unsafe" in err.lower():
                    errors.append(f"{source}: API 内容审核拦截")
                else:
                    errors.append(f"{source}: {err}")
            else:
                errors.append(f"{source}: 未找到相关内容")
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                errors.append(f"{source}: API 限流（429），请稍后重试")
            elif "1301" in error_msg or "sensitive" in error_msg.lower() or "unsafe" in error_msg.lower():
                errors.append(f"{source}: API 内容审核拦截")
            else:
                errors.append(f"{source}: {error_msg}")
        finally:
            await rag.finalize_storages()

    if not results:
        if errors:
            return f"图谱查询失败：\n" + "\n".join(f"- {e}" for e in errors)
        return "未找到相关图谱信息。"

    return "\n\n---\n\n".join(results)
