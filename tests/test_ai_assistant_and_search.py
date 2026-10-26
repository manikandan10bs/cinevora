"""
Phase 1 Foundation Tests:
1. Recommender import and invocation resilience
2. AI Movie Assistant (Gemini Flash & Catalog Fallback) request lifecycle and structured error handling
3. Consolidated search across title, cast, and director
4. Database integrity and session persistence
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from frontend.api_client import api_client
from app.db import init_db, verify_user_credentials, get_user_likes, get_favorites
from src.catalog_service import query_master_catalog
from src.recommender import master_content_recommender


def test_recommender_import_and_execution():
    """Verifies that the recommender imports and executes recommendations without 'app.db' import error."""
    init_db()
    # Test for demo account
    recs = master_content_recommender.recommend_for_user("test_id_1", limit=4)
    assert isinstance(recs, list)
    assert len(recs) > 0

    recs_liked = master_content_recommender.recommend_because_you_liked("test_id_1", limit=4)
    assert isinstance(recs_liked, dict)
    assert "source_movie" in recs_liked
    assert "movies" in recs_liked


def test_ai_assistant_request_lifecycle():
    """Verifies that assistant chat returns structured reply, grounded recommendations, and active mode."""
    res = api_client.chat_assistant(message="Recommend 3 gripping Tamil action movies", user_id="test_id_1", limit=3)
    assert res is not None
    assert res.get("success") is True
    assert len(res.get("reply", "")) > 10
    recs = res.get("recommendations", [])
    assert len(recs) > 0
    # Mode must be either gemini_flash or catalog_fallback
    assert res.get("assistant_mode") in ["gemini_flash", "catalog_fallback"]


def test_ai_assistant_error_handling_structure():
    """Verifies that chat_assistant returns readable error diagnostics instead of raw exceptions or None."""
    # Test with an invalid port/unreachable endpoint
    unreachable_client = type(api_client)("http://127.0.0.1:9999")
    res = unreachable_client.chat_assistant(message="test query")
    assert res.get("success") is False
    assert "error_detail" in res
    assert "Cannot reach" in res.get("error_detail") or "Unable to reach" in res.get("error_detail")


def test_consolidated_search_title_cast_director():
    """Verifies that catalog search functions across title, actor/cast, and director."""
    # 1. Title search
    res_title = api_client.search_movies(query="Avatar", limit=5)
    assert res_title.get("count", 0) > 0
    titles = [(m.get("movie_title") or m.get("title", "")).lower() for m in res_title.get("results", [])]
    assert any("avatar" in t for t in titles)

    # 2. Cast search (Shah Rukh Khan yields verified matches like Jawan, etc.)
    res_cast = api_client.search_movies(query="Shah Rukh Khan", limit=5)
    assert res_cast.get("count", 0) > 0
    assert len(res_cast.get("results", [])) > 0

    # 3. Director search (Nolan yields verified matches like Oppenheimer, etc.)
    res_dir = api_client.search_movies(query="Nolan", limit=5)
    assert res_dir.get("count", 0) > 0
    assert len(res_dir.get("results", [])) > 0


def test_database_records_intact():
    """Verifies that demo users and existing credentials remain completely intact."""
    user = verify_user_credentials("test_id_1", "test123")
    assert user is not None
    assert user["username"] == "test_id_1"
    assert "display_name" in user
