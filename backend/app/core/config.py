from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Determine env file location (check project root first, then backend dir)
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_ROOT_ENV = os.path.join(_ROOT_DIR, ".env")
_BACKEND_ENV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_ENV_FILE = _ROOT_ENV if os.path.exists(_ROOT_ENV) else _BACKEND_ENV

class Settings(BaseSettings):
    PROJECT_NAME: str = "ClimateTwin API"
    DEBUG: bool = True
    API_V1_STR: str = "/api"
    
    # CORS Origins (Allow frontend dev server by default)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # Fallback 1
        "http://127.0.0.1:5174",
        "http://localhost:5175",  # Fallback 2
        "http://127.0.0.1:5175",
        "http://localhost:3000",
    ]
    
    # Security
    JWT_SECRET_KEY: str = "b3a562ef75f284f6d3e91b5c490a147820a4b3d7c58e19198642a8b9f6d7e012"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Demo User Credentials (optional via env)
    DEMO_ADMIN_PASSWORD: Optional[str] = None
    DEMO_OPERATOR_PASSWORD: Optional[str] = None
    DEMO_VIEWER_PASSWORD: Optional[str] = None
    
    # External APIs & Services
    FIREBASE_DB_URL: Optional[str] = None
    MQTT_BROKER_URL: str = "localhost"
    MQTT_PORT: int = 1883
    
    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "climatetwin"
    DATABASE_URL: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Validate critical security configurations on startup
if not settings.DEBUG and settings.JWT_SECRET_KEY == "b3a562ef75f284f6d3e91b5c490a147820a4b3d7c58e19198642a8b9f6d7e012":
    logger.critical("PRODUCTION WARNING: Running with default insecure JWT_SECRET_KEY! Set JWT_SECRET_KEY in .env immediately.")

