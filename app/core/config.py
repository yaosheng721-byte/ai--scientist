from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL",
    )
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    dashscope_model: str = Field(default="qwen3.8-max", alias="DASHSCOPE_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://ai_scientist:ai_scientist_password@localhost:5432/ai_scientist",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    output_dir: str = Field(default="outputs", alias="OUTPUT_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
