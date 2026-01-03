from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Creator Monetization API"
    ENV: str = "dev"

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24 * 7  # 7 days

    TOKEN_ENCRYPTION_KEY: str  # Fernet key (base64)
    BASE_URL: str = "http://localhost:8000"

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_PATH: str = "/oauth/youtube/callback"

    class Config:
        env_file = ".env"

settings = Settings()
