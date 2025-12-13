"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "pizzabot"
    POSTGRES_PASSWORD: str = "pizzabot_password_123"
    POSTGRES_DB: str = "pizza_delivery"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-70b-8192"

    # CORS - comma-separated string that will be split
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Application
    ENVIRONMENT: str = "development"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
