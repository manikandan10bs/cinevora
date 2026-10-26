import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.recommender import MasterContentRecommender
from src.catalog_service import load_master_catalog
from app.db import toggle_like, get_db_connection

def test_taste_shift_action_horror_to_drama():
    df = load_master_catalog()
    rec = MasterContentRecommender(df)

    user_test = "test_taste_shift_user"
    with get_db_connection() as conn:
        conn.cursor().execute("DELETE FROM likes WHERE user_id = ?;", (user_test,))
        conn.commit()

    try:
        # 1. Like Action and Horror movies
        action_m = df[df["genre"].str.lower().str.contains("action", na=False)].iloc[0]
        horror_m = df[df["genre"].str.lower().str.contains("horror", na=False)].iloc[0]
        toggle_like(user_test, action_m["catalog_id"])
        toggle_like(user_test, horror_m["catalog_id"])

        recs_ah = rec.recommend_for_user(user_test, limit=6)
        assert len(recs_ah) > 0
        ah_genres = " ".join([r["genre"].lower() for r in recs_ah])
        assert "action" in ah_genres or "horror" in ah_genres

        # 2. Clear likes and pivot to Drama
        with get_db_connection() as conn:
            conn.cursor().execute("DELETE FROM likes WHERE user_id = ?;", (user_test,))
            conn.commit()

        drama_m = df[df["genre"].str.lower().str.contains("drama", na=False)].iloc[0]
        toggle_like(user_test, drama_m["catalog_id"])

        recs_d = rec.recommend_for_user(user_test, limit=6)
        assert len(recs_d) > 0
        d_genres = [r["genre"].lower() for r in recs_d]
        assert any("drama" in g for g in d_genres)

        # 3. Test Indian industry isolation (never returns Hollywood)
        recs_ind = rec.recommend_for_user(user_test, industry="Indian", limit=8)
        assert len(recs_ind) > 0
        for r in recs_ind:
            assert r["industry"].lower() != "hollywood"
            assert r["industry"].lower() in ["bollywood", "tamil", "telugu", "malayalam", "kannada"]
    finally:
        with get_db_connection() as conn:
            conn.cursor().execute("DELETE FROM likes WHERE user_id = ?;", (user_test,))
            conn.commit()
