"""
Cinevora Application Configuration
Safely loads environment variables using python-dotenv.
Ensures secrets like GEMINI_API_KEY are never logged, printed, or exposed.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base directory paths
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

# Load .env file from project root
ENV_FILE_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)


class Settings:
    """Application configuration and secrets management."""

    # Project Paths
    PROJECT_ROOT_PATH: Path = PROJECT_ROOT
    MODEL_ARTIFACT_PATH: Path = PROJECT_ROOT / "models" / "recommender_model.joblib"
    MOVIE_METADATA_PATH: Path = PROJECT_ROOT / "data" / "processed" / "movie_metadata.csv"

    # Server Configuration
    HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("APP_PORT", "8000"))

    # Google Gemini Configuration
    # Official cost-effective Flash model: 'gemini-3.5-flash-lite'
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    @classmethod
    def get_gemini_api_key(cls) -> Optional[str]:
        """
        Retrieves the Gemini API key from environment.
        Returns None or empty string if not configured.
        """
        key = os.getenv("GEMINI_API_KEY")
        if key and key.strip():
            return key.strip()
        return None

    @classmethod
    def is_gemini_configured(cls) -> bool:
        """Checks if a non-empty Gemini API key is configured."""
        key = cls.get_gemini_api_key()
        return bool(key and len(key) > 5)


settings = Settings()
