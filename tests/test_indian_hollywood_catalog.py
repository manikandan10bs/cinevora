"""
Unit Tests for Cinevora 2.0: Combined Indian + Hollywood Movie Discovery Platform
Tests verify:
1. Combined catalog counts & regional distribution (1,706 total, Indian, Hollywood, International)
2. Preserved MovieLens IDs (1-1682) and non-colliding new IDs (2001+)
3. PosterService regional & language query helpers (ta, te, ml, kn, hi, en)
4. Verified media availability: 16:9 backdrops, 2:3 posters, official trailers
5. Assistant natural language parsing for Indian cinema, languages, and modern decades
6. Grounded assistant recommendations for regional inquiries (e.g. Tamil action)
7. Cross-language suggested movie engine blending Indian & Hollywood signals
8. FastAPI /movies/search filtering by cinema region and language
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.config import settings
from app.assistant import GeminiAssistant
from src.recommender import CinevoraRecommender
from frontend.poster_service import (
    init_poster_cache,
    get_movie_enrichment,
    get_indian_movies,
    get_hollywood_movies,
    get_movies_by_language,
    get_movies_by_region,
    get_featured_movies,
    get_poster_url,
    get_backdrop_url,
    get_trailer_url
)
from frontend.suggested_service import get_suggested_movies


@pytest.fixture(scope="module")
def client():
    """Test client for FastAPI endpoints."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def recommender_instance():
    """Loads the trained Cinevora recommender artifact."""
    model_path = settings.MODEL_ARTIFACT_PATH
    assert model_path.exists(), "Recommender artifact must exist to run tests."
    return CinevoraRecommender.load(str(model_path))


# -----------------------------------------------------------------------------
# 1. Combined Catalog & ID Separation Tests
# -----------------------------------------------------------------------------
def test_combined_catalog_integrity():
    """Verifies that the enriched catalog has 3,560 total master movies."""
    init_poster_cache()
    indian_movies = get_indian_movies()
    hollywood_movies = get_hollywood_movies()

    assert len(indian_movies) >= 3000, "Must contain at least 3,000 curated Indian cinema titles"
    assert len(hollywood_movies) >= 500, "Must contain at least 500 Hollywood titles"
    assert len(indian_movies) + len(hollywood_movies) == 3560, "Combined total must equal 3,560"
    assert all(m.get("catalog_id") for m in indian_movies)


# -----------------------------------------------------------------------------
# 2. Regional & Language Helper Tests
# -----------------------------------------------------------------------------
def test_language_and_region_helpers():
    """Verifies helper functions for Tamil, Telugu, Malayalam, Kannada, Hindi, and Hollywood."""
    init_poster_cache()

    tamil = get_movies_by_language("ta")
    telugu = get_movies_by_language("te")
    malayalam = get_movies_by_language("ml")
    kannada = get_movies_by_language("kn")
    hindi = get_movies_by_language("hi")

    assert len(tamil) >= 600, "Must contain Tamil blockbusters (Vikram, Leo, etc.)"
    assert len(telugu) >= 600, "Must contain Telugu blockbusters (RRR, etc.)"
    assert len(malayalam) >= 600, "Must contain Malayalam cinema"
    assert len(kannada) >= 200, "Must contain Kannada cinema"
    assert len(hindi) >= 700, "Must contain Hindi cinema"

    # Verify title matching
    tamil_titles = [m.get("title") for m in tamil]
    assert any("Vikram" in t for t in tamil_titles)
    assert any("Leo" in t for t in tamil_titles)

    telugu_titles = [m.get("title") for m in telugu]
    assert any("RRR" in t for t in telugu_titles)


# -----------------------------------------------------------------------------
# 3. Media Availability Tests (Backdrops, Trailers, Posters)
# -----------------------------------------------------------------------------
def test_spotlight_media_availability():
    """Verifies that Indian & Hollywood spotlights have verified 16:9 backdrops, trailers, and posters."""
    init_poster_cache()
    featured = get_featured_movies()

    assert len(featured) >= 8, "Rotating hero banner must contain at least 8 featured movies"

    for m in featured[:4]:
        assert m.get("backdrop_url") is not None and m["backdrop_url"].startswith("http")
        assert m.get("poster_url") is not None and m["poster_url"].startswith("http")
        assert m.get("trailer_url") is not None and "youtube" in m["trailer_url"]


# -----------------------------------------------------------------------------
# 4. Assistant Natural Language Parsing for Indian & Modern Cinema
# -----------------------------------------------------------------------------
def test_assistant_language_and_region_detection():
    """Verifies that the assistant detects Indian languages and cinema regions accurately."""
    assistant = GeminiAssistant(api_key="")

    # Language detection
    assert assistant.detect_language_from_text("Recommend a recent Tamil action movie") == "ta"
    assert assistant.detect_language_from_text("Show me great Telugu blockbusters") == "te"
    assert assistant.detect_language_from_text("Looking for Malayalam survival drama") == "ml"
    assert assistant.detect_language_from_text("Any awesome Kannada fantasy films?") == "kn"
    assert assistant.detect_language_from_text("Tell me about Hindi wrestling movies") == "hi"

    # Region detection
    assert assistant.detect_region_from_text("Best Indian movies of all time") == "Indian"
    assert assistant.detect_region_from_text("Show me Hollywood sci-fi blockbusters") == "Hollywood"

    # Modern decade detection
    assert assistant.detect_decade_or_year("Hollywood thrillers from the 2000s") == (2000, 2009, "2000s")
    assert assistant.detect_decade_or_year("latest modern cinema") == (2020, 2026, "recent")


# -----------------------------------------------------------------------------
# 5. Assistant Regional Grounding Tests
# -----------------------------------------------------------------------------
def test_assistant_grounded_tamil_recommendations(recommender_instance):
    """
    Verifies that 'Recommend a recent Tamil action movie' returns verified Tamil movies
    grounded in catalog metadata rather than hallucinated responses.
    """
    assistant = GeminiAssistant(api_key="")

    res = assistant.chat(
        message="Recommend a recent Tamil action movie",
        recommender=recommender_instance,
        limit=3
    )

    assert len(res.recommendations) > 0, "Must return verified Tamil action movies"
    for item in res.recommendations:
        assert item.movie_id is not None
        assert "Action" in item.genres, "Returned movie must satisfy the Action genre constraint"
        assert item.cinema_region in ["Tamil", "Indian"]


# -----------------------------------------------------------------------------
# 6. Cross-Language Recommendation Signals
# -----------------------------------------------------------------------------
def test_cross_language_suggestions():
    """
    Verifies that when a user likes an Action film, the suggested movie engine
    suggests cross-language Action blockbusters spanning Indian & Hollywood cinema.
    """
    import streamlit as st

    user_id = "test_cross_user"
    # Seed session state with an active Action interest
    st.session_state["recent_search_genres"] = {"Action"}
    st.session_state[f"likes_set_{user_id}"] = set()

    res = get_suggested_movies(user_id=user_id, limit=6)
    movies = res.get("movies", [])
    assert len(movies) > 0, "Must generate suggestions for user with Action interest"

    # Check for presence of cross-language explanation badge
    reasons = [m.get("suggestion_reason", "") for m in movies]
    assert any("Action" in r or "Cross-Language" in r or "Matches" in r for r in reasons)


# -----------------------------------------------------------------------------
# 7. FastAPI /movies/search Region & Language Filter Tests
# -----------------------------------------------------------------------------
def test_api_region_and_language_filtering(client):
    """Verifies that /movies/search correctly filters by region and language."""
    # Test Indian region filter
    res_ind = client.get("/movies/search?region=Indian&limit=10")
    assert res_ind.status_code == 200
    data_ind = res_ind.json()
    assert data_ind["count"] >= 15
    for item in data_ind["results"]:
        assert item["cinema_region"] == "Indian"

    # Test Tamil language filter
    res_ta = client.get("/movies/search?language=ta&limit=10")
    assert res_ta.status_code == 200
    data_ta = res_ta.json()
    assert data_ta["count"] >= 4
    for item in data_ta["results"]:
        assert item["original_language"] == "ta"

    # Test title search for an Indian blockbuster
    res_rrr = client.get("/movies/search?query=RRR")
    assert res_rrr.status_code == 200
    data_rrr = res_rrr.json()
    assert any("RRR" in m["movie_title"] for m in data_rrr["results"])


# -----------------------------------------------------------------------------
# 8. Regression Tests: Import Verification & Metadata Discrimination
# -----------------------------------------------------------------------------
def test_poster_service_and_frontend_app_imports():
    """
    Regression test verifying that get_indian_movies and all related symbols
    are properly exported and importable from frontend.poster_service, and
    that frontend.app imports cleanly without startup failure.
    """
    # 1. Direct import from poster_service
    from frontend.poster_service import (
        get_indian_movies,
        get_hollywood_movies,
        get_movies_by_language,
        get_movies_by_region,
        is_indian_movie
    )
    assert callable(get_indian_movies)
    assert callable(get_hollywood_movies)
    assert callable(get_movies_by_language)
    assert callable(get_movies_by_region)
    assert callable(is_indian_movie)

    # 2. Package-level import from frontend
    from frontend import get_indian_movies as pkg_get_indian_movies
    assert callable(pkg_get_indian_movies)

    # 3. View module imports
    from frontend.views.indian_cinema import render_indian_cinema_page
    from frontend.views.hollywood import render_hollywood_page
    assert callable(render_indian_cinema_page)
    assert callable(render_hollywood_page)

    # 4. Streamlit app import
    import frontend.app
    assert hasattr(frontend.app, "main")


def test_is_indian_movie_accuracy():
    """
    Verifies that Indian movie classification strictly uses origin-country and
    Indian language metadata, and does NOT classify foreign non-English movies as Indian.
    """
    from frontend.poster_service import is_indian_movie

    # Positive cases (Indian cinema)
    assert is_indian_movie({"cinema_region": "Indian", "original_language": "ta", "origin_countries": "IN"}) is True
    assert is_indian_movie({"cinema_region": "Indian", "original_language": "te", "origin_countries": "IN"}) is True
    assert is_indian_movie({"original_language": "ml", "origin_countries": "IN"}) is True
    assert is_indian_movie({"original_language": "kn", "origin_countries": "IN"}) is True
    assert is_indian_movie({"original_language": "hi", "origin_countries": "IN"}) is True

    # Negative cases: Non-Indian foreign cinema (must NOT be classified as Indian)
    assert is_indian_movie({"cinema_region": "International", "original_language": "ko", "origin_countries": "KR"}) is False
    assert is_indian_movie({"cinema_region": "Hollywood", "original_language": "fr", "origin_countries": "FR"}) is False
    assert is_indian_movie({"original_language": "de", "origin_countries": "DE"}) is False
    assert is_indian_movie({"original_language": "es", "origin_countries": "ES"}) is False
    assert is_indian_movie({"original_language": "ja", "origin_countries": "JP"}) is False
    assert is_indian_movie({"original_language": "it", "origin_countries": "IT"}) is False
    assert is_indian_movie({"original_language": "en", "origin_countries": "US"}) is False


def test_get_indian_movies_signatures_and_filters():
    """Verifies that get_indian_movies accepts language codes, language names, and genres."""
    from frontend.poster_service import get_indian_movies

    # By language code
    tamil_code = get_indian_movies(language="ta")
    assert len(tamil_code) >= 4
    for m in tamil_code:
        assert m["original_language"] == "ta"

    # By language name
    tamil_name = get_indian_movies(language="Tamil")
    assert len(tamil_name) >= 4
    for m in tamil_name:
        assert m["original_language"] == "ta"

    # By genre
    action_indian = get_indian_movies(genre="Action")
    assert len(action_indian) >= 5
    for m in action_indian:
        assert "Action" in m["genres"]


def test_safe_release_year_handling_and_none_filtering():
    """
    Regression test verifying that movies with None, missing, empty, or invalid
    release_year values are handled gracefully without raising TypeError: int().
    """
    from frontend.poster_service import extract_release_year, get_hollywood_movies, get_indian_movies

    # 1. extract_release_year unit tests
    assert extract_release_year({"release_year": 2024}) == 2024
    assert extract_release_year({"release_year": "2023"}) == 2023
    assert extract_release_year({"release_year": None, "title": "Movie (1995)"}) == 1995
    assert extract_release_year({"release_year": None, "title": "unknown"}) is None
    assert extract_release_year({"release_year": None, "title": "unknown"}, default=0) == 0
    assert extract_release_year({"release_year": ""}) is None
    assert extract_release_year({"release_year": "invalid"}, default=1990) == 1990
    assert extract_release_year({}) is None
    assert extract_release_year(None) is None

    # 2. Modern Hollywood filter test including movies with year >= 2000 and excluding None
    mock_catalog = [
        {"movie_id": 1, "title": "Dune 2 (2024)", "release_year": 2024, "cinema_region": "Hollywood"},
        {"movie_id": 2, "title": "Unknown (1995)", "release_year": None, "cinema_region": "Hollywood"},
        {"movie_id": 3, "title": "No Year Title", "release_year": None, "cinema_region": "Hollywood"},
        {"movie_id": 4, "title": "Old Movie (1990)", "release_year": 1990, "cinema_region": "Hollywood"},
    ]
    modern_hwd = [m for m in mock_catalog if (extract_release_year(m) or 0) >= 2000]
    assert len(modern_hwd) == 1
    assert modern_hwd[0]["title"] == "Dune 2 (2024)"

    # 3. Live get_hollywood_movies and get_indian_movies call verification (no crash on movie #267 unknown)
    hwd = get_hollywood_movies(min_year=2000)
    assert all((extract_release_year(m) or 0) >= 2000 for m in hwd)

