from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "VendorFlow API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security (Read securely from .env)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAGIC_LINK_BASE_URL: str = "http://localhost:8000"
    
    # Database URL (Read securely from .env)
    DATABASE_URL: str
    
    # Pydantic v2 Settings configuration to bind the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()