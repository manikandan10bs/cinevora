"""
Integration Tests for Cinevora FastAPI Endpoints
Tests cover:
1. Health and Assistant Status endpoints (verifying secrets are never exposed)
2. Core Movie Search and Recommendation endpoints (independent of Gemini)
3. Assistant Chat endpoint with mocked Gemini client and offline fallback
4. Input validation (bounds, invalid genres, edge cases)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient managing the application lifespan."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Health & Status Tests
# -----------------------------------------------------------------------------
def test_health_endpoint(client):
    """Verifies that /health returns 200 and accurate system state."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["catalog_movies_count"] == 3560
    assert "gemini_configured" in data


def test_assistant_status_never_exposes_secrets(client):
    """Verifies /assistant/status returns safe information without leaking API key."""
    response = client.get("/assistant/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert data["model"] == "gemini-3.5-flash-lite"
    assert "status" in data
    # Ensure no secret strings or key fragments appear in response
    assert "API_KEY" not in str(data)
    assert not any(k in str(data) for k in ["secret", "private_key", "bearer"])


# -----------------------------------------------------------------------------
# 2. Core Search & Recommender Endpoints (Gemini-Independent)
# -----------------------------------------------------------------------------
def test_catalog_search_title(client):
    """Verifies movie title substring search."""
    response = client.get("/movies/search?query=Leo")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    assert any("Leo" in m["movie_title"] for m in data["results"])


def test_catalog_search_genre_filter(client):
    """Verifies movie search with genre constraint."""
    response = client.get("/movies/search?genre=Animation&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 5
    for item in data["results"]:
        assert "Animation" in item["genres"]


def test_catalog_search_multi_genre_filter(client):
    """Verifies movie search with combined multi-genre constraint (e.g. Action and Comedy)."""
    response = client.get("/movies/search?genre=Action,Comedy&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    for item in data["results"]:
        # Each movie must satisfy at least one of the requested genres
        genres = [g.strip() for g in item["genres"].replace(",", "|").split("|")]
        assert "Action" in genres or "Comedy" in genres



def test_catalog_search_invalid_genre(client):
    """Verifies that querying an invalid genre returns 400 Bad Request."""
    response = client.get("/movies/search?genre=InvalidGenre123")
    assert response.status_code == 400
    assert "Invalid genre" in response.json()["detail"]


def test_recommendations_endpoint_hybrid(client):
    """Verifies /recommendations endpoint works without Gemini."""
    response = client.get("/recommendations?user_id=1&genre=Comedy&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5
    assert data["genre_filter"] == "Comedy"
    assert len(data["recommendations"]) == 5
    for m in data["recommendations"]:
        assert "Comedy" in m["genres"]
        assert 1.0 <= m["predicted_rating"] <= 10.0


def test_recommendations_invalid_model_type(client):
    """Verifies that an unsupported model type returns 400 Bad Request."""
    response = client.get("/recommendations?model_type=magic_neural_net")
    assert response.status_code == 400
    assert "Invalid model_type" in response.json()["detail"]


# -----------------------------------------------------------------------------
# 3. Assistant Chat Endpoint Tests (Mocked & Isolated)
# -----------------------------------------------------------------------------
def test_assistant_chat_with_mocked_gemini(client):
    """Verifies /assistant/chat endpoint with a mocked Gemini client."""
    with patch("app.assistant.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "Based on Cinevora's hybrid algorithm, these movies are great matches for you!"
        mock_client.models.generate_content.return_value = mock_response

        # Temporary assistant with mocked client
        from app.assistant import GeminiAssistant
        from app.main import app_state

        original_assistant = app_state["assistant"]
        app_state["assistant"] = GeminiAssistant(api_key="mock_test_key")

        try:
            payload = {
                "message": "I want an exciting thriller to watch tonight",
                "user_id": 1,
                "limit": 3
            }
            response = client.post("/assistant/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["assistant_mode"] == "gemini_flash"
            assert data["reply"] == mock_response.text
            assert data["detected_genre"] == "Thriller"
            assert len(data["recommendations"]) == 3
            for r in data["recommendations"]:
                assert "Thriller" in r["genres"]
        finally:
            app_state["assistant"] = original_assistant


def test_assistant_chat_input_validation(client):
    """Verifies Pydantic validation rejects out-of-bounds payloads."""
    # Empty message
    res1 = client.post("/assistant/chat", json={"message": "", "limit": 5})
    assert res1.status_code == 422

    # Limit > 20
    res2 = client.post("/assistant/chat", json={"message": "Good movies", "limit": 100})
    assert res2.status_code == 422

    # Negative user_id
    res3 = client.post("/assistant/chat", json={"message": "Good movies", "user_id": -5})
    assert res3.status_code == 422


def test_assistant_chat_genre_plus_decade_filtering(client):
    """
    Verifies /assistant/chat endpoint accurately extracts both genre and decade
    and enforces application-level filtering for recent action movies.
    """
    import re
    payload = {
        "message": "an exciting, fast-paced action movie from 2023",
        "limit": 3
    }
    response = client.post("/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_genre"] == "Action"
    assert data["detected_decade"] == "2023"
    assert len(data["recommendations"]) == 3
    for r in data["recommendations"]:
        assert "Action" in r["genres"]
        m_year = re.search(r"(\d{4})", r["release_date"] or r["movie_title"])
        assert m_year is not None
        assert int(m_year.group(1)) == 2023


def test_assistant_chat_no_match_satisfies_constraint(client):
    """
    Verifies that when criteria cannot be satisfied in catalog (e.g. 1920s Action),
    the endpoint returns 0 recommendations and a helpful explanation rather than
    substituting out-of-decade films.
    """
    payload = {
        "message": "Action movie from the 1920s",
        "limit": 3
    }
    response = client.post("/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_genre"] == "Action"
    assert data["detected_decade"] == "1920s"
    assert len(data["recommendations"]) == 0
    assert "No movies in Cinevora's catalog matched" in data["reply"]


# -----------------------------------------------------------------------------
# 4. Movie Details & Interaction Endpoints
# -----------------------------------------------------------------------------
def test_get_movie_details(client):
    """Verifies /movies/{movie_id} returns movie details or 404."""
    # Valid movie
    res = client.get("/movies/1")
    assert res.status_code == 200
    data = res.json()
    assert str(data["movie_id"]) in ["1", "CINEVORA-0000226"]
    assert "Hi Nanna" in data["movie_title"] or "title" in data
    assert "Drama" in data["genres"]

    # Non-existent movie
    res_404 = client.get("/movies/NON_EXISTENT_ID_999999")
    assert res_404.status_code == 404


def test_movie_search_with_year_range(client):
    """Verifies /movies/search honors start_year and end_year filters."""
    import re
    res = client.get("/movies/search?start_year=2022&end_year=2024&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    for m in data["results"]:
        m_year = re.search(r"\((\d{4})\)", m["movie_title"]) or re.search(r"(\d{4})", str(m.get("release_date", "")))
        assert m_year is not None
        assert 2022 <= int(m_year.group(1)) <= 2024


def test_favorites_api_lifecycle(client):
    """Verifies adding, listing, and removing a favorite via API."""
    user = "api_test_user_fav"
    fav_payload = {
        "user_id": user,
        "movie_id": 1,
        "movie_title": "Hi Nanna (2023)",
        "genres": "Drama,Family,Romance",
        "release_date": "2023",
        "rating": 8.3
    }

    # Add favorite
    res_add = client.post("/favorites", json=fav_payload)
    assert res_add.status_code == 200
    assert res_add.json()["status"] == "success"

    # List favorites
    res_list = client.get(f"/favorites?user_id={user}")
    assert res_list.status_code == 200
    fav_data = res_list.json()
    assert fav_data["count"] == 1
    assert str(fav_data["favorites"][0]["movie_id"]) == "1"

    # Delete favorite
    res_del = client.delete(f"/favorites/1?user_id={user}")
    assert res_del.status_code == 200

    # Confirm removed
    res_after = client.get(f"/favorites?user_id={user}")
    assert res_after.json()["count"] == 0


def test_likes_api_lifecycle(client):
    """Verifies toggling likes via API."""
    user = "api_test_user_like"
    like_payload = {"user_id": user, "movie_id": 50}

    # First toggle: liked = True
    res1 = client.post("/likes", json=like_payload)
    assert res1.status_code == 200
    assert res1.json()["liked"] is True

    # List likes
    res_list = client.get(f"/likes?user_id={user}")
    assert 50 in res_list.json()["liked_movie_ids"] or "50" in [str(x) for x in res_list.json()["liked_movie_ids"]]

    # Second toggle: liked = False
    res2 = client.post("/likes", json=like_payload)
    assert res2.status_code == 200
    assert res2.json()["liked"] is False


def test_catalog_search_newest_sort(client):
    """Verifies /movies/search supports sort_by=newest."""
    res = client.get("/movies/search?sort_by=newest&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    # First items should be recent releases
    first_title = data["results"][0]["movie_title"]
    first_rel = str(data["results"][0].get("release_date", ""))
    assert any(yr in first_title or yr in first_rel for yr in ["2025", "2024", "2023"])


def test_search_history_api_lifecycle(client):
    """Verifies posting, getting, and deleting user search history records via REST API."""
    user = "api_test_user_hist"

    # Initially clear
    client.delete(f"/history/search?user_id={user}")

    # 1. Post search history
    payload = {
        "user_id": user,
        "query": "star wars sci-fi",
        "matched_genres": "Action|Adventure|Sci-Fi",
        "matched_movie_id": 50,
        "matched_movie_title": "Star Wars (1977)"
    }
    res_post = client.post("/history/search", json=payload)
    assert res_post.status_code == 200
    assert res_post.json()["status"] == "success"

    # 2. Get search history
    res_get = client.get(f"/history/search?user_id={user}")
    assert res_get.status_code == 200
    hist_data = res_get.json()
    assert hist_data["user_id"] == user
    assert hist_data["count"] >= 1
    assert hist_data["history"][0]["query"] == "star wars sci-fi"
    assert hist_data["history"][0]["matched_genres"] == "Action|Adventure|Sci-Fi"

    # 3. Delete search history
    res_del = client.delete(f"/history/search?user_id={user}")
    assert res_del.status_code == 200

    # 4. Confirm empty
    res_empty = client.get(f"/history/search?user_id={user}")
    assert res_empty.json()["count"] == 0
