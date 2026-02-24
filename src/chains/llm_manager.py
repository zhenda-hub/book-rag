"""LLM 管理器 - 使用 OpenRouter 统一管理多个 LLM"""
import os
from typing import Optional
from openai import OpenAI

from src.logger import get_logger

logger = get_logger("llm_manager")


class LLMManager:
    """
    使用 OpenRouter 统一管理多个 LLM

    支持的模型格式: provider/model_name
    例如: anthropic/claude-3-opus, openai/gpt-4, deepseek/deepseek-chat
    """

    # OpenRouter API 端点
    BASE_URL = "https://openrouter.ai/api/v1"

    # 常用模型映射
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

    def __init__(
        self,
        api_key: str = None,
        default_model: str = None,
        temperature: float = 0.7,
    ):
        """
        初始化 LLM 管理器

        Args:
            api_key: OpenRouter API Key，默认从环境变量 OPENROUTER_API_KEY 读取
            default_model: 默认模型，可以是简写（如 "gpt-4"）或完整路径（如 "openai/gpt-4"）
            temperature: 温度参数
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 OPENROUTER_API_KEY 环境变量")

        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            timeout=60.0,  # 设置 60 秒超时
        )

        # 设置默认模型
        if default_model:
            self.default_model = self._resolve_model(default_model)
        else:
            # 从配置或环境变量获取
            env_model = os.getenv("DEFAULT_LLM_MODEL", "deepseek")
            self.default_model = self._resolve_model(env_model)

        self.temperature = temperature

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

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            result = response.choices[0].message.content
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
            # 直接使用传入的消息列表（已是标准 OpenAI 格式）
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            result = response.choices[0].message.content
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
        从 OpenRouter API 获取模型列表

        Returns:
            模型信息列表

        Raises:
            RuntimeError: API 请求失败或返回空列表
        """
        import requests

        logger.debug("开始获取 OpenRouter 模型列表")

        response = requests.get(
            f"{self.BASE_URL}/models",
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

        Returns:
            免费模型的 ID 列表

        Raises:
            RuntimeError: 未找到免费模型
        """
        models = self.fetch_models()
        free_models = []

        for model in models:
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})

            # 检查是否为免费模型
            # 方法1: 模型ID包含 :free 后缀
            # 方法2: prompt 价格为 "0" 或 0
            # 方法3: completion 价格为 "0" 或 0
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
