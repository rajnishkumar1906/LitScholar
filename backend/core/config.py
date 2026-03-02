from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DB_URL_NEON: str

    # JWT Settings
    JWT_SECRET: str = "dev-secret-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Added this

    # OAuth / Session
    SESSION_SECRET_KEY: str = "dev-session-secret-change-this-in-production"  # Added this
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [  # Added this
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # API Keys
    GEMINI_API_KEY: str = ""

    # Environment
    ENVIRONMENT: str = "development"  # Added this

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()