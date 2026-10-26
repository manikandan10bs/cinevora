"""
Cinevora Frontend Configuration
Centralizes API settings, color constants, and demo accounts.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Ensure .env is reliably loaded from project root
FRONTEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FRONTEND_DIR.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)

# Backend FastAPI URL (can be customized via environment variable)
API_BASE_URL = os.getenv("CINEVORA_API_URL", "http://127.0.0.1:8000").rstrip("/")

# Standard MovieLens 100K Genres
ALL_GENRES: List[str] = [
    "Action",
    "Adventure",
    "Animation",
    "Children's",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western"
]

# Demo Accounts for easy exploration in the UI
DEMO_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "demo_user_1": {
        "label": "Demo User #1 — Classic & Blockbuster Enthusiast (272 ratings)",
        "movielens_id": 1,
        "avatar": "🎬",
        "description": "Active MovieLens reviewer who loves Star Wars, Toy Story, and Fargo."
    },
    "demo_user_2": {
        "label": "Demo User #2 — Drama & Thriller Aficionado (62 ratings)",
        "movielens_id": 2,
        "avatar": "🎭",
        "description": "Appreciates tense thrillers, gritty crime, and deep character dramas."
    },
    "demo_user_42": {
        "label": "Demo User #42 — Action & Sci-Fi Explorer (183 ratings)",
        "movielens_id": 42,
        "avatar": "🚀",
        "description": "High affinity for fast-paced 90s action, sci-fi epics, and adventure."
    },
    "demo_user_100": {
        "label": "Demo User #100 — Eclectic Cinephile (74 ratings)",
        "movielens_id": 100,
        "avatar": "🍿",
        "description": "Explores varied genres including foreign films, animation, and indie comedy."
    },
    "guest_user": {
        "label": "Guest Account — Brand New User (Cold-Start Experience)",
        "movielens_id": None,
        "avatar": "✨",
        "description": "No prior watch history. Uses popularity fallback and ad-hoc genre onboarding."
    }
}

# Cinema Theme Color Palette (Apple TV / Modern Streaming Inspired Light Mode)
COLORS = {
    "bg_main": "#F7F8FC",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F8FAFC",
    "border": "#E5E7EB",
    "accent_red": "#E50914",
    "accent_amber": "#D97706",
    "accent_emerald": "#059669",
    "accent_blue": "#2563EB",
    "text_primary": "#171923",
    "text_secondary": "#667085",
    "text_muted": "#98A2B3",
    "text_dark": "#344054"
}
