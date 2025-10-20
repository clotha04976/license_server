import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # App settings
    PROJECT_NAME: str = "License Server"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days

    # License generation settings
    LICENSE_AES_KEY: str = os.getenv("LICENSE_AES_KEY", "0123456789abcdef0123456789abcdef") # 32 bytes key
    LICENSE_PRIVATE_KEY: str = os.getenv("LICENSE_PRIVATE_KEY", "")

    class Config:
        case_sensitive = True

settings = Settings()