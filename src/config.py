"""配置管理模块"""
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    """应用配置"""

    # 项目路径
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DOCUMENTS_DIR = DATA_DIR / "documents"
    CHROMA_DIR = DATA_DIR / "chroma"

    # OpenRouter API
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # SiliconFlow API
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"

    # Embedding
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")

    # Chroma
    CHROMA_PERSIST_DIR: str = str(CHROMA_DIR)
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_base")

    # 检索
    TOP_K_RETRIEVALS: int = int(os.getenv("TOP_K_RETRIEVALS", "10"))  # 增加默认检索数量

    # Reranker
    RERANKER_ENABLED: bool = os.getenv("RERANKER_ENABLED", "false").lower() == "true"
    RERANKER_TOP_K: int = int(os.getenv("RERANKER_TOP_K", "5"))
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "")  # 空字符串使用 FlashRank 默认模型

    # LLM 生成参数
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "1.0"))

    # 全局检索 - 有结构的文档类型（支持全局模式）
    STRUCTURED_DOC_TYPES: list = ["md", "markdown", "epub"]

    @classmethod
    def ensure_dirs(cls) -> None:
        """确保必要的目录存在"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# 初始化时创建目录
Config.ensure_dirs()


config = Config()


def get_embeddings() -> "HuggingFaceEmbeddings":
    """获取统一的 LangChain Embeddings 实例

    不手动指定 device，让 sentence-transformers 自动选择（避免 NotImplementedError）

    Returns:
        HuggingFaceEmbeddings: 配置好的 embeddings 实例
    """
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=Config.EMBEDDING_MODEL,
        encode_kwargs={
            'batch_size': 32,
            'normalize_embeddings': True,
        },
        show_progress=False,
    )
