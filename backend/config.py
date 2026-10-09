"""
Loads environment variables once, so every other module just does:
    from backend.config import settings
    settings.AI_API_KEY
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.0-flash")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./eco_energy.db")
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")


settings = Settings()
