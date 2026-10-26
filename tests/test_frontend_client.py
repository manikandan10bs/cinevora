"""
Tests for Cinevora Frontend API Client (frontend/api_client.py).
Verifies error handling, timeouts, fallbacks when backend is unreachable,
and proper query parameter construction.
"""

from unittest.mock import patch, MagicMock
import requests
import pytest

from frontend.api_client import CinevoraAPIClient


@pytest.fixture
def client():
    return CinevoraAPIClient(base_url="http://testserver:8000")


def test_client_handles_connection_error_gracefully(client):
    """When the backend is down, client methods return safe fallbacks rather than crashing."""
    with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")):
        assert client.get_health() is None
        assert client.get_assistant_status() is None

        search_res = client.search_movies(query="Alien")
        assert search_res == {"count": 0, "results": []}

        rec_res = client.get_recommendations(user_id=1)
        assert rec_res == {"count": 0, "recommendations": []}

        favs = client.get_favorites("demo_user_1")
        assert favs == []

        likes = client.get_likes("demo_user_1")
        assert likes == []

        metrics = client.get_monitoring_metrics()
        assert metrics is None

        events = client.get_monitoring_events()
        assert events == []


def test_client_handles_http_errors_gracefully(client):
    """When the backend returns 404 or 500, methods return None / empty lists."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch("requests.get", return_value=mock_resp):
        assert client.get_movie_details(9999) is None
        assert client.get_monitoring_metrics() is None


def test_client_search_params_construction(client):
    """search_movies formats genre, year range, and sorting query parameters properly."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"count": 1, "results": [{"movie_id": 1, "movie_title": "Toy Story"}]}
        mock_get.return_value = mock_resp

        res = client.search_movies(
            query="Toy",
            genre="Animation",
            start_year=1990,
            end_year=1999,
            sort_by="rating",
            limit=10,
            offset=0
        )

        assert res["count"] == 1
        mock_get.assert_called_once()
        called_args, called_kwargs = mock_get.call_args
        params = called_kwargs["params"]
        assert params["query"] == "Toy"
        assert params["genre"] == "Animation"
        assert params["start_year"] == 1990
        assert params["end_year"] == 1999
        assert params["sort_by"] == "rating"


def test_client_recommendations_params_construction(client):
    """get_recommendations formats user_id, genre, model_type, and exclude_rated."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"count": 2, "recommendations": []}
        mock_get.return_value = mock_resp

        res = client.get_recommendations(
            user_id=42,
            genre="Sci-Fi",
            start_year=1980,
            end_year=1989,
            model_type="collaborative",
            limit=5,
            exclude_rated=True
        )

        assert res["count"] == 2
        mock_get.assert_called_once()
        params = mock_get.call_args[1]["params"]
        assert params["user_id"] == 42
        assert params["genre"] == "Sci-Fi"
        assert params["start_year"] == 1980
        assert params["end_year"] == 1989
        assert params["model_type"] == "collaborative"
        assert params["exclude_rated"] == "true"


def test_client_chat_assistant(client):
    """chat_assistant posts properly and returns response payload."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "reply": "Here are 90s action picks.",
            "recommendations": [{"movie_id": 50, "movie_title": "Star Wars (1977)"}],
            "source": "gemini"
        }
        mock_post.return_value = mock_resp

        res = client.chat_assistant("Exciting action", user_id=1, genre="Action", limit=3)
        assert res is not None
        assert res["source"] == "gemini"
        assert len(res["recommendations"]) == 1

        payload = mock_post.call_args[1]["json"]
        assert payload["message"] == "Exciting action"
        assert payload["user_id"] == 1
        assert payload["genre"] == "Action"
        assert payload["limit"] == 3


def test_client_favorites_and_likes_lifecycle(client):
    """Verifies add_favorite, remove_favorite, and toggle_like."""
    # Test add_favorite
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "id": 1}
        mock_post.return_value = mock_resp

        added = client.add_favorite(
            user_id="demo_user_1",
            movie_id=1,
            movie_title="Toy Story (1995)",
            genres="Animation|Children's|Comedy"
        )
        assert added is True

    # Test remove_favorite
    with patch("requests.delete") as mock_del:
        mock_del_resp = MagicMock()
        mock_del_resp.status_code = 200
        mock_del.return_value = mock_del_resp

        removed = client.remove_favorite(user_id="demo_user_1", movie_id=1)
        assert removed is True

    # Test toggle_like
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"movie_id": 1, "liked": True}
        mock_post.return_value = mock_resp

        liked = client.toggle_like("demo_user_1", 1)
        assert liked is True


def test_client_search_history_methods(client):
    """Verifies search history record, get, and clear methods."""
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success"}
        mock_post.return_value = mock_resp

        ok = client.record_search_history(
            user_id="demo_user_1",
            query="action",
            matched_genres="Action"
        )
        assert ok is True

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"count": 1, "history": [{"query": "action"}]}
        mock_get.return_value = mock_resp

        history = client.get_search_history("demo_user_1")
        assert len(history) == 1
        assert history[0]["query"] == "action"

    with patch("requests.delete") as mock_del:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_del.return_value = mock_resp

        cleared = client.clear_search_history("demo_user_1")
        assert cleared is True
