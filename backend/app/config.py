import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "TN SecureVote"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "tn-securevote-secret-key-change-in-production-2026"
    DATABASE_URL: str = "sqlite:///./tn_securevote.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    DEMO_MODE: bool = True
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    RSA_KEY_SIZE: int = 2048
    ELGAMAL_KEY_SIZE: int = 256
    VOTES_PER_BLOCK: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
