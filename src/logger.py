"""日志配置模块 - 使用 loguru"""
from loguru import logger
import sys
from pathlib import Path


def setup_logger():
    """设置 loguru logger"""
    # 移除默认 handler
    logger.remove()

    # 控制台 handler - INFO 级别
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 文件 handler - DEBUG 级别（轮换）
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "book-rag.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )


def get_logger(name: str = __name__):
    """获取 logger 实例的便捷函数"""
    return logger.bind(name=name)


# 初始化
setup_logger()
