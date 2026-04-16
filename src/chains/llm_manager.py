"""LLM 管理器 - 使用 OpenRouter 统一管理多个 LLM"""
import os
from typing import Optional
from openai import OpenAI

from src.logger import get_logger

logger = get_logger("llm_manager")


class LLMManager:
    """
    统一管理多个 LLM 提供方（OpenRouter / SiliconFlow）

    支持的模型格式: provider/model_name
    例如: anthropic/claude-3-opus, openai/gpt-4, deepseek/deepseek-chat
    """

    # 常用模型映射（OpenRouter 简写）
    MODELS = {
        "deepseek": "deepseek/deepseek-chat",
        "deepseek-reasoner": "deepseek/deepseek-r1",
        "gpt-4": "openai/gpt-4-turbo",
        "gpt-3.5": "openai/gpt-3.5-turbo",
        "claude-opus": "anthropic/claude-3-opus",
        "claude-sonnet": "anthropic/claude-3-sonnet",
        "gemini": "google/gemini-pro",
        "llama": "meta-llama/llama-3-70b",
    }

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

    def __init__(
        self,
        api_key: str = None,
        default_model: str = None,
        temperature: float = None,
        top_p: float = None,
        provider: str = None,
        base_url: str = None,
    ):
        """
        初始化 LLM 管理器

        Args:
            api_key: API Key，默认从环境变量读取
            default_model: 默认模型
            temperature: 温度参数
            top_p: 核采样参数
            provider: 提供方名称 ("openrouter" / "siliconflow")
            base_url: 自定义 API 端点（覆盖 provider 默认值）
        """
        # 确定 provider
        if provider and provider in self.PROVIDERS:
            self.provider = provider
        else:
            self.provider = "openrouter"

        provider_config = self.PROVIDERS[self.provider]

        # 确定 API Key
        self.api_key = api_key or os.getenv(provider_config["env_key"])
        if not self.api_key:
            raise ValueError(f"请设置 {provider_config['env_key']} 环境变量")

        # 确定 base_url
        self.base_url = base_url or provider_config["base_url"]

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=60.0,
        )

        # 设置默认模型
        if default_model:
            self.default_model = self._resolve_model(default_model)
        else:
            # 从配置或环境变量获取
            env_model = os.getenv("DEFAULT_LLM_MODEL", "deepseek")
            self.default_model = self._resolve_model(env_model)

        # 从配置读取默认值（如果未提供参数）
        from src.config import Config
        if temperature is None:
            temperature = Config.LLM_TEMPERATURE
        if top_p is None:
            top_p = Config.LLM_TOP_P

        self.temperature = temperature
        self.top_p = top_p

    def _resolve_model(self, model: str) -> str:
        """
        解析模型名称

        Args:
            model: 模型名称（简写或完整路径）

        Returns:
            完整的模型路径
        """
        # 如果已经是完整路径（包含 /），直接返回
        if "/" in model:
            return model

        # 否则从映射表查找
        return self.MODELS.get(model, model)

    def _call_llm(self, model: str, messages: list, temperature: float) -> str:
        """
        调用 LLM API 的通用方法（复用代码）

        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数

        Returns:
            生成的文本
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=self.top_p,
        )
        return response.choices[0].message.content

    def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
    ) -> str:
        """
        生成回答

        Args:
            prompt: 提示词
            model: 模型名称，默认使用 default_model
            temperature: 温度参数，默认使用初始化时的值

        Returns:
            生成的文本
        """
        model = self._resolve_model(model) if model else self.default_model
        temperature = temperature if temperature is not None else self.temperature

        logger.info(f"调用 LLM 生成 | 模型: {model} | 输入长度: {len(prompt)} 字符")

        try:
            # 确保 prompt 是字符串类型
            if not isinstance(prompt, str):
                prompt = str(prompt)

            # 构造标准 OpenAI 消息格式
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            result = self._call_llm(model, messages, temperature)
            logger.info(f"LLM 生成成功 | 输出长度: {len(result)} 字符")
            return result
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            raise RuntimeError(f"LLM 调用失败: {e}")

    def chat(
        self,
        messages: list,
        model: str = None,
        temperature: float = None,
    ) -> str:
        """
        多轮对话

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            model: 模型名称
            temperature: 温度参数

        Returns:
            生成的文本
        """
        model = self._resolve_model(model) if model else self.default_model
        temperature = temperature if temperature is not None else self.temperature

        logger.info(f"调用 LLM 对话 | 模型: {model} | 对话轮数: {len(messages)}")

        try:
            result = self._call_llm(model, messages, temperature)
            logger.info(f"LLM 对话成功 | 输出长度: {len(result)} 字符")
            return result
        except Exception as e:
            logger.error(f"LLM 对话失败: {e}")
            raise RuntimeError(f"LLM 调用失败: {e}")

    async def agenerate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
    ) -> str:
        """
        异步生成回答

        Args:
            prompt: 提示词
            model: 模型名称
            temperature: 温度参数

        Returns:
            生成的文本
        """
        # OpenAI SDK 不直接支持异步，使用同步版本
        # 如需真正的异步，可以使用 httpx 异步客户端
        return self.generate(prompt, model, temperature)

    def list_available_models(self) -> dict:
        """
        获取可用的模型列表

        Returns:
            模型映射字典
        """
        return self.MODELS.copy()

    def fetch_models(self) -> list:
        """
        从当前 provider API 获取模型列表

        Returns:
            模型信息列表

        Raises:
            RuntimeError: API 请求失败或返回空列表
        """
        import requests

        logger.debug(f"开始获取 {self.provider} 模型列表")

        response = requests.get(
            f"{self.base_url}/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        models = response.json().get("data", [])

        if not models:
            logger.error("API 返回空模型列表")
            raise RuntimeError("API 返回空模型列表，请检查 API Key 或网络连接")

        logger.info(f"成功获取 {len(models)} 个模型")
        return models

    def get_free_models(self) -> list:
        """
        获取免费模型列表

        - OpenRouter: :free 后缀或定价为 0
        - SiliconFlow: 非 Pro/ 前缀的模型

        Returns:
            免费模型的 ID 列表

        Raises:
            RuntimeError: 未找到免费模型
        """
        models = self.fetch_models()
        free_models = []

        if self.provider == "siliconflow":
            # SiliconFlow: 非 Pro/ 前缀的都是免费模型
            for model in models:
                model_id = model.get("id", "")
                if not model_id.startswith("Pro/"):
                    free_models.append(model_id)
        else:
            # OpenRouter: :free 后缀或定价为 0
            for model in models:
                model_id = model.get("id", "")
                pricing = model.get("pricing", {})

                prompt_price = pricing.get("prompt", "0")
                completion_price = pricing.get("completion", "0")

                is_free = (
                    ":free" in model_id or
                    prompt_price == "0" or prompt_price == 0 or
                    completion_price == "0" or completion_price == 0
                )

                if is_free:
                    free_models.append(model_id)

        if not free_models:
            logger.error("未找到免费模型")
            raise RuntimeError("未找到免费模型")

        logger.info(f"找到 {len(free_models)} 个免费模型")
        return free_models
