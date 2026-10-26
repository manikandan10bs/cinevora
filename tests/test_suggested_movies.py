"""
Tests for Cinevora Suggested Movies Engine (frontend/suggested_service.py).
Verifies:
1. Genre detection from search queries (e.g. 'action', 'comedy', 'sci-fi').
2. Liked movies genre extraction.
3. Multi-genre taste aggregation (e.g. liking Action and searching Comedy yields both).
4. Suggested movies retrieval with cross-genre matching and exclusion of liked movies.
"""

from unittest.mock import patch, MagicMock
import pytest
import streamlit as st

from frontend.suggested_service import (
    record_search,
    record_genre_filter,
    clear_search_signals,
    get_active_taste_profile,
    get_suggested_movies
)


@pytest.fixture(autouse=True)
def clean_session_state():
    """Resets session state before each test."""
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_record_search_detects_genres_from_query_text():
    """Searching for 'action' or 'comedy' adds Action and Comedy to active genres."""
    record_search("action")
    assert "Action" in st.session_state["recent_search_genres"]

    record_search("classic comedy and romance")
    assert "Comedy" in st.session_state["recent_search_genres"]
    assert "Romance" in st.session_state["recent_search_genres"]


def test_record_search_infers_genres_from_results():
    """Searching for a title like 'Toy Story' extracts genres from returned movies."""
    mock_results = [
        {"movie_id": 1, "movie_title": "Toy Story", "genres": "Animation|Children's|Comedy"}
    ]
    record_search("Toy Story", results=mock_results)
    assert "Animation" in st.session_state["recent_search_genres"]
    assert "Comedy" in st.session_state["recent_search_genres"]


def test_record_genre_filter():
    """Explicit genre filter from UI is tracked."""
    record_genre_filter("Sci-Fi")
    assert "Sci-Fi" in st.session_state["recent_search_genres"]


def test_taste_profile_combines_liked_and_searched_genres():
    """
    If a user likes Action movies and searches Comedy,
    the active taste profile must contain BOTH Action and Comedy.
    """
    user_id = "test_user_1"
    # User liked movie #50 (Star Wars: Action|Adventure|Sci-Fi)
    st.session_state["liked_meta_cache"] = {
        50: {"movie_id": 50, "movie_title": "Star Wars (1977)", "genres": "Action|Adventure|Sci-Fi"}
    }
    st.session_state[f"likes_set_{user_id}"] = {50}

    # User searched for comedy
    record_search("hilarious comedy")

    profile = get_active_taste_profile(user_id)
    combined = set(profile["combined_genres"])

    assert "Action" in combined
    assert "Comedy" in combined
    assert "❤️ Liked" in profile["breakdown"]["Action"]
    assert "🔍 Searched" in profile["breakdown"]["Comedy"]


def test_suggested_movies_returns_matches_and_excludes_liked():
    """
    When user likes Action (movie 50) and searches Comedy,
    suggested movies queries for Action and Comedy, prioritizes crossovers,
    and excludes movie 50.
    """
    user_id = "test_user_1"
    st.session_state["liked_meta_cache"] = {
        50: {"movie_id": 50, "movie_title": "Star Wars", "genres": "Action|Adventure|Sci-Fi"}
    }
    st.session_state[f"likes_set_{user_id}"] = {50}
    record_search("comedy")

    mock_catalog_response = {
        "count": 3,
        "results": [
            {"movie_id": 50, "movie_title": "Star Wars", "genres": "Action|Adventure|Sci-Fi"},
            {"movie_id": 100, "movie_title": "Men in Black", "genres": "Action|Adventure|Comedy|Sci-Fi"},
            {"movie_id": 200, "movie_title": "Liar Liar", "genres": "Comedy"}
        ]
    }

    with patch("frontend.suggested_service.api_client.search_movies", return_value=mock_catalog_response) as mock_search:
        result = get_suggested_movies(user_id, limit=5)
        movies = result["movies"]

        # Movie 50 must be excluded because it is already liked
        suggested_ids = [m["movie_id"] for m in movies]
        assert 50 not in suggested_ids
        assert 100 in suggested_ids
        assert 200 in suggested_ids

        # Men in Black matches both Action and Comedy!
        mib = next(m for m in movies if m["movie_id"] == 100)
        assert "Action" in mib["suggestion_reason"]
        assert "Matches your taste" in mib["suggestion_reason"]


def test_clear_search_signals():
    """Clearing signals removes search queries and search genres."""
    record_search("thriller")
    assert len(st.session_state["recent_search_genres"]) > 0
    clear_search_signals()
    assert len(st.session_state["recent_search_genres"]) == 0
    assert len(st.session_state["recent_search_queries"]) == 0
