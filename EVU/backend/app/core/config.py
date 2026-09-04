from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "EVU"
    DEBUG: bool = True

    # Safe local defaults make first startup possible even before .env exists.
    DATABASE_URL: str = "sqlite:///./app.db"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    XAI_API_KEY: str = ""
    XAI_MODEL: str = "grok-4.5"

    ZAI_API_KEY: str = ""
    ZAI_MODEL: str = "glm-5.1"
    ZAI_BASE_URL: str = "https://api.z.ai/api/paas/v4/"

    JWT_SECRET_KEY: str = "evu-development-secret-change-before-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    FRONTEND_URL: str = "http://localhost:3000"

    RAG_ENABLED: bool = True
    RAG_MAX_FILE_SIZE_MB: int = 20
    RAG_CHUNK_SIZE: int = 1200
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5
    RAG_MAX_CONTEXT_CHARS: int = 12000

    AGENT_ENABLED: bool = True
    AGENT_MAX_STEPS: int = 4
    AGENT_MAX_TOOL_OUTPUT_CHARS: int = 6000

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()