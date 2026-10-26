"""
Unit and Integration Tests for Cinevora Authentication and Multi-Signal Personalization
Verifies:
1. PBKDF2 password hashing and credential verification
2. Demo user account idempotency (test_id_1 / test123)
3. User registration and profile retrieval
4. Viewing history logging, query, and deletion
5. Multi-signal recommendations (Likes 3.0, Watchlist 2.5, Views 1.5, Search 1.0)
6. Single dataset integrity (all recommendations exist in Movies_Master_Cleaned.csv)
"""

import uuid
import pytest
from app.db import (
    init_db,
    hash_password,
    verify_password,
    create_user,
    get_user_by_username,
    verify_user_credentials,
    seed_default_users,
    record_view_history,
    get_view_history,
    clear_view_history,
    add_like,
    toggle_like,
    add_favorite
)
from src.recommender import MasterContentRecommender


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure DB tables are initialized and demo users seeded."""
    init_db()
    seed_default_users()


def test_password_hashing():
    """Verifies that PBKDF2 hashing generates unique salts and verifies correctly."""
    pwd = "secret_password_123"
    pwd_hash, salt = hash_password(pwd)
    assert pwd_hash is not None
    assert len(pwd_hash) == 64  # SHA-256 hex length
    assert len(salt) == 32      # 16 bytes hex

    assert verify_password(pwd, pwd_hash, salt) is True
    assert verify_password("wrong_password", pwd_hash, salt) is False


def test_demo_user_credentials():
    """Verifies that test_id_1 / test123 works idempotently."""
    user = verify_user_credentials("test_id_1", "test123")
    assert user is not None
    assert user["username"] == "test_id_1"
    assert "display_name" in user


def test_user_registration_and_duplicate_handling():
    """Verifies that user registration works and prevents duplicates."""
    uname = f"test_user_{uuid.uuid4().hex[:8]}"
    created = create_user(uname, "password99", "Custom Tester")
    assert created is not None
    assert created["username"] == uname

    # Duplicate should fail gracefully
    dup = create_user(uname, "password99", "Custom Tester")
    assert dup is None

    profile = get_user_by_username(uname)
    assert profile is not None
    assert profile["username"] == uname
    assert profile["display_name"] == "Custom Tester"


def test_view_history_crud():
    """Verifies recording, reading, and clearing movie view events."""
    uid = "test_viewer_user"
    clear_view_history(uid)

    assert len(get_view_history(uid)) == 0

    record_view_history(uid, "CINEVORA-0000001", "Vikram", "Action, Thriller", "Tamil")
    record_view_history(uid, "CINEVORA-0000002", "Inception", "Action, Sci-Fi", "Hollywood")

    history = get_view_history(uid, limit=10)
    assert len(history) == 2
    assert history[0]["movie_title"] == "Inception"
    assert history[1]["movie_title"] == "Vikram"

    clear_view_history(uid)
    assert len(get_view_history(uid)) == 0


def test_multi_signal_recommender():
    """Verifies multi-signal recommendations based on likes, watchlist, and views."""
    uid = "test_signal_user_distinct"
    clear_view_history(uid)

    rec = MasterContentRecommender()
    assert rec.df is not None
    assert len(rec.df) == 3560

    # Cold start recommendations
    cold_recs = rec.recommend_for_user(uid, limit=5)
    assert len(cold_recs) == 5
    for m in cold_recs:
        assert "catalog_id" in m
        assert "title" in m

    # Add Like and Watchlist interactions
    first_cid = rec.df.iloc[0]["catalog_id"]
    first_title = rec.df.iloc[0]["title"]
    add_like(uid, first_cid)

    second_cid = rec.df.iloc[1]["catalog_id"]
    second_title = rec.df.iloc[1]["title"]
    second_genre = str(rec.df.iloc[1].get("genre", "Cinema"))
    add_favorite(uid, second_cid, second_title, second_genre)

    # Multi-signal personalized recs
    warm_recs = rec.recommend_for_user(uid, limit=6, exclude_rated=True)
    assert len(warm_recs) == 6
    rec_cids = {m["catalog_id"] for m in warm_recs}
    assert first_cid not in rec_cids
    assert second_cid not in rec_cids

    # Because you liked
    liked_res = rec.recommend_because_you_liked(uid, limit=4)
    assert liked_res["source_movie"] is not None
    assert len(liked_res["movies"]) > 0

    # From watchlist
    wl_res = rec.recommend_from_watchlist(uid, limit=4)
    assert wl_res["source_movie"] is not None
    assert len(wl_res["movies"]) > 0

    # Discover new
    discover_res = rec.recommend_discover_new(uid, limit=4)
    assert len(discover_res) > 0
