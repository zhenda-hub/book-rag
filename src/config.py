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

    # DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_TEMPERATURE: float = float(os.getenv("DEEPSEEK_TEMPERATURE", "0"))

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
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))  # 相似度阈值(0-1)

    # Reranker
    RERANKER_ENABLED: bool = os.getenv("RERANKER_ENABLED", "false").lower() == "true"
    RERANKER_TOP_K: int = int(os.getenv("RERANKER_TOP_K", "5"))
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "")  # 空字符串使用 FlashRank 默认模型

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    @classmethod
    def ensure_dirs(cls) -> None:
        """确保必要的目录存在"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# 初始化时创建目录
Config.ensure_dirs()


config = Config()
