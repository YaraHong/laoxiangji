import os
from functools import lru_cache
from typing import List

import yaml
from pydantic import BaseModel, Field


class DbSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    name: str = "laoxiangji"
    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/laoxiangji"


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    url: str = "redis://localhost:6379/0"


class ModelSettings(BaseModel):
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    chat_name: str = "qwen-plus"
    embedding_name: str = "text-embedding-v3"
    request_timeout: int = 120


class MilvusSettings(BaseModel):
    host: str = "localhost"
    port: int = 19530
    collection: str = "laoxiangji_knowledge"
    dim: int = 1024


class MinioSettings(BaseModel):
    endpoint: str = "localhost:19000"
    access_key: str = "admin"
    secret_key: str = "admin123456"
    bucket: str = "knowledge"
    secure: bool = False


class CelerySettings(BaseModel):
    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/2"


class TextSplitterSettings(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 100
    separators: List[str] = Field(default_factory=lambda: ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""])


class PromptTemplates(BaseModel):
    chat_system: str = "chat_system_prompt.txt"
    rag_system: str = "rag_system_prompt.txt"
    lead_hint: str = "lead_hint_prompt.txt"
    intent_recognition: str = "intent_recognition_prompt.txt"


class PromptSettings(BaseModel):
    base_path: str = "prompts/"
    templates: PromptTemplates = Field(default_factory=PromptTemplates)


class AppConfig(BaseModel):
    app_name: str = "laoxiangji"
    debug: bool = False
    db: DbSettings = Field(default_factory=DbSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    milvus: MilvusSettings = Field(default_factory=MilvusSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    text_splitter: TextSplitterSettings = Field(default_factory=TextSplitterSettings)
    prompts: PromptSettings = Field(default_factory=PromptSettings)

    @classmethod
    def from_yaml(cls, config_path: str = None):
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "..", "settings.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
        return cls(
            app_name=config_data.get("app", {}).get("name", "laoxiangji"),
            debug=config_data.get("app", {}).get("debug", False),
            db=DbSettings(**config_data.get("database", {})),
            redis=RedisSettings(**config_data.get("redis", {})),
            model=ModelSettings(**config_data.get("model", {})),
            milvus=MilvusSettings(**config_data.get("milvus", {})),
            minio=MinioSettings(**config_data.get("minio", {})),
            celery=CelerySettings(**config_data.get("celery", {})),
            text_splitter=TextSplitterSettings(**config_data.get("text_splitter", {})),
            prompts=PromptSettings(
                base_path=config_data.get("prompts", {}).get("base_path", "prompts/"),
                templates=PromptTemplates(**config_data.get("prompts", {}).get("templates", {})),
            ),
        )


@lru_cache()
def get_settings() -> AppConfig:
    return AppConfig.from_yaml()


settings = get_settings()
