import os

from app.core.config import settings
from app.core.logger_handle import logger


def _get_prompts_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", settings.prompts.base_path)


def load_prompt(template_name: str) -> str:
    """从 prompts/ 目录加载提示词模板文件"""
    prompt_path = os.path.join(_get_prompts_dir(), template_name)
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("加载提示词失败: %s, error=%s", template_name, e)
        raise


def get_prompt(code: str) -> str:
    """根据模板代码获取提示词内容"""
    templates = settings.prompts.templates
    template_name = getattr(templates, code, None)
    if template_name is None:
        logger.warning("未找到提示词模板: code=%s", code)
        return ""
    return load_prompt(template_name)
