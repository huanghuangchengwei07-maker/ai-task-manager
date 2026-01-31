from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path

# 确保从项目根目录加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """应用配置"""
    openai_api_key: str = ""
    google_ai_api_key: str = ""
    ai_provider: str = "auto"  # "openai", "google", "auto" (auto = 优先 OpenAI，失败时用 Google)
    database_url: str = "sqlite:///./tasks.db"
    chroma_persist_dir: str = "./chroma_data"
    
    class Config:
        env_file = str(env_path) if env_path.exists() else ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
