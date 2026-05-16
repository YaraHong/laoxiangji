import logging
import os
from datetime import datetime
from logging import Logger

from app.utils.path_tool import get_abs_path

LOG_ROOT = get_abs_path("logs")
os.makedirs(LOG_ROOT, exist_ok=True)

DEFAULT_LOG_FORMAT = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s",
)


def get_logger(
        name: str = "hr-assistant",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file=None,
) -> logging.Logger:
    logger: Logger = logging.getLogger(name)

    # 1. 防止重复添加 Handler
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 2. 控制台处理器
    console_handle = logging.StreamHandler()
    console_handle.setLevel(console_level)
    console_handle.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handle)

    # 3. 文件处理器
    if log_file is None:
        log_file = os.path.join(
            LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        )

    file_handle = logging.FileHandler(log_file, encoding="utf-8")
    file_handle.setLevel(file_level)
    file_handle.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handle)

    return logger


# 初始化
logger = get_logger()
