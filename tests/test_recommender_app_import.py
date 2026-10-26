"""
Regression Test for Recommender 'app.db' Import Resolution
Tests that backend package 'app' and its submodules (app.db, app.config, etc.)
are cleanly resolvable by src/recommender.py even when Streamlit prepends
the 'frontend/' directory to sys.path during application launch.
"""

import sys
import uuid
from pathlib import Path
import pytest


def test_sys_path_and_app_package_resolution():
    """
    Simulates Streamlit's launch behavior where frontend/ is prepended to sys.path,
    and tests that 'app' resolves to the package directory, not frontend/app.py.
    """
    project_root = Path(__file__).resolve().parent.parent
    frontend_dir = project_root / "frontend"

    # Simulate Streamlit's _fix_sys_path
    sys.path.insert(0, str(frontend_dir))

    # Import and call _ensure_backend_app_package
    from src.recommender import _ensure_backend_app_package
    _ensure_backend_app_package()

    import app
    assert hasattr(app, "__path__"), f"Expected 'app' to be a package with __path__, got: {app}"
    from app.db import get_user_likes
    assert callable(get_user_likes)


def test_recommender_calls_under_frontend_syspath():
    """
    Simulates calling recommender methods (e.g. recommend_because_you_liked,
    recommend_for_user, recommend_from_watchlist, recommend_favorite_genres,
    recommend_discover_new) when frontend/ is at sys.path[0].
    """
    project_root = Path(__file__).resolve().parent.parent
    frontend_dir = project_root / "frontend"

    # Simulate Streamlit inserting frontend at index 0
    sys.path.insert(0, str(frontend_dir))

    from src.recommender import master_content_recommender
    from app.db import init_db, add_like, toggle_like, add_favorite, remove_favorite

    init_db()
    temp_user = f"test_user_{uuid.uuid4().hex[:8]}"

    # 1. Test when user has no interactions (should return graceful empty structure, no import error)
    rec_empty = master_content_recommender.recommend_because_you_liked(temp_user, limit=6)
    assert rec_empty["source_movie"] is None
    assert rec_empty["movies"] == []

    # 2. Add an explicit like and verify recommendations are generated
    test_movie_cid = "CINEVORA-0000001"
    add_like(temp_user, test_movie_cid)

    # Re-insert frontend to ensure safeguard handles repeat calls
    sys.path.insert(0, str(frontend_dir))

    rec_liked = master_content_recommender.recommend_because_you_liked(temp_user, limit=4)
    assert rec_liked["source_movie"] is not None
    assert rec_liked["source_movie"]["catalog_id"] == test_movie_cid
    assert len(rec_liked["movies"]) > 0

    # 3. Test watchlist recommendations
    add_favorite(temp_user, test_movie_cid, "Ksheera Sagara Madhanam", "Drama, Thriller")
    rec_watchlist = master_content_recommender.recommend_from_watchlist(temp_user, limit=4)
    assert rec_watchlist["source_movie"] is not None
    assert len(rec_watchlist["movies"]) > 0

    # 4. Test personalized user recommendations
    rec_user = master_content_recommender.recommend_for_user(temp_user, limit=5)
    assert len(rec_user) > 0

    # 5. Test favorite genres recommendations
    rec_genres = master_content_recommender.recommend_favorite_genres(temp_user, limit=4)
    assert rec_genres["favorite_genre"] is not None
    assert len(rec_genres["movies"]) > 0

    # 6. Test discover new recommendations
    rec_discover = master_content_recommender.recommend_discover_new(temp_user, limit=4)
    assert isinstance(rec_discover, list)

    # Cleanup
    toggle_like(temp_user, test_movie_cid)
    remove_favorite(temp_user, test_movie_cid)
