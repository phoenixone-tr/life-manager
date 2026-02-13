from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://lifemanager:changeme@postgres:5432/lifemanager"
    REDIS_URL: str = "redis://redis:6379/0"
    TELEGRAM_BOT_TOKEN: str
    ENVIRONMENT: str = "development"


settings = Settings()
