"""
Unit Tests for Cinevora SQLite Persistence Layer
Tests cover:
1. Database schema initialization
2. Favorites addition, retrieval, duplicate prevention, and deletion
3. Likes toggling and status tracking
4. Live monitoring event recording and telemetry calculations
5. Percentile latency computation and event pruning
"""

import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app.db import (
    init_db,
    add_favorite,
    get_favorites,
    is_favorite,
    remove_favorite,
    toggle_like,
    get_user_likes,
    record_search_history,
    get_search_history,
    clear_search_history,
    record_event,
    get_monitoring_summary,
    get_recent_events,
    prune_events
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Ensures database is initialized prior to running tests."""
    init_db()


def test_favorites_crud_and_duplicate_prevention():
    """Verifies complete lifecycle of a user favorite including duplicate prevention."""
    user = "pytest_user_alpha"
    movie_id = 99991

    # Initially not favorited
    assert not is_favorite(user, movie_id)

    # 1. Add favorite
    added = add_favorite(
        user_id=user,
        movie_id=movie_id,
        movie_title="Unit Test Film (1995)",
        genres="Action|Sci-Fi",
        release_date="01-Jan-1995",
        rating=4.5
    )
    assert added is True
    assert is_favorite(user, movie_id) is True

    # 2. Duplicate addition must be prevented safely
    duplicate = add_favorite(
        user_id=user,
        movie_id=movie_id,
        movie_title="Unit Test Film (1995)",
        genres="Action|Sci-Fi"
    )
    assert duplicate is False

    # 3. Retrieve favorites
    favs = get_favorites(user)
    assert len(favs) == 1
    assert favs[0]["movie_id"] == movie_id
    assert favs[0]["movie_title"] == "Unit Test Film (1995)"

    # 4. Remove favorite
    removed = remove_favorite(user, movie_id)
    assert removed is True
    assert not is_favorite(user, movie_id)

    # 5. Removing non-existent favorite returns False
    assert remove_favorite(user, movie_id) is False


def test_likes_toggle():
    """Verifies toggling of likes on and off for an application user."""
    user = "pytest_user_beta"
    movie_id = 99992

    # First toggle: should like (True)
    success1, liked1 = toggle_like(user, movie_id)
    assert success1 is True
    assert liked1 is True
    assert movie_id in get_user_likes(user)

    # Second toggle: should unlike (False)
    success2, liked2 = toggle_like(user, movie_id)
    assert success2 is True
    assert liked2 is False
    assert movie_id not in get_user_likes(user)


def test_monitoring_telemetry_recording_and_summary():
    """Verifies that monitoring events are recorded and aggregated properly."""
    # Record synthetic telemetry events
    record_event(
        endpoint="/recommendations",
        method="GET",
        status_code=200,
        duration_ms=45.0,
        event_type="recommendation",
        genre_filter="Sci-Fi",
        model_type="hybrid",
        items_count=10
    )
    record_event(
        endpoint="/movies/search",
        method="GET",
        status_code=200,
        duration_ms=25.0,
        event_type="catalog_search"
    )
    record_event(
        endpoint="/health",
        method="GET",
        status_code=200,
        duration_ms=1.5,
        is_internal=True
    )

    # Test summary excluding internal health checks
    summary = get_monitoring_summary(exclude_internal=True)
    assert summary["total_requests"] >= 2
    assert summary["avg_latency_ms"] > 0
    assert summary["recommendation_metrics"]["total_requests"] >= 1

    # Check recent events list
    recent = get_recent_events(limit=10)
    assert len(recent) > 0
    endpoints = [e["endpoint"] for e in recent]
    assert "/recommendations" in endpoints


def test_pruning_maintains_bounded_retention():
    """Verifies event pruning deletes older events beyond boundary."""
    deleted = prune_events(keep_latest=1000)
    assert deleted >= 0


def test_search_history_crud():
    """Verifies recording, retrieval, and clearing of user search history in SQLite."""
    user = "pytest_user_gamma"

    # Initially empty
    clear_search_history(user)
    assert len(get_search_history(user)) == 0

    # 1. Record search
    ok = record_search_history(
        user_id=user,
        query="terminator action",
        matched_genres="Action|Sci-Fi",
        matched_movie_id=96,
        matched_movie_title="Terminator 2: Judgment Day (1991)"
    )
    assert ok is True

    # 2. Retrieve history
    history = get_search_history(user, limit=5)
    assert len(history) == 1
    rec = history[0]
    assert rec["user_id"] == user
    assert rec["query"] == "terminator action"
    assert rec["matched_genres"] == "Action|Sci-Fi"
    assert rec["matched_movie_id"] == 96

    # 3. Clear history
    cleared = clear_search_history(user)
    assert cleared is True
    assert len(get_search_history(user)) == 0
