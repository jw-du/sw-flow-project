from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SW-flow-project"
    app_env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    flow_dir: str = Field(default="flows", env="FLOW_DIR")
    default_topk: int = Field(default=3, env="DEFAULT_TOPK")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    llm_provider: str = Field(default="deepseek", env="LLM_PROVIDER")
    llm_api_key: str = Field(default="", env="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.deepseek.com", env="LLM_BASE_URL")
    llm_model: str = Field(default="deepseek-chat", env="LLM_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
