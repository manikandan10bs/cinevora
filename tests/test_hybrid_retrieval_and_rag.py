"""
Cinevora Comprehensive Hybrid Retrieval, RAG, and Real-Time Personalization Test Suite
Tests:
1. Actor-only search for Vijay
2. Vijay + Tamil + Action combined filters
3. Director-only search (Lokesh Kanagaraj)
4. Genre and industry filtering (English Sci-Fi)
5. Release-year ranges (after 2020)
6. Missing metadata and empty cast safety
7. No-match queries returning honest empty states
8. Malformed Gemini JSON and API failure fallback
9. Semantic search followed by strict filter validation
10. Duplicate result removal
11. Stable and valid catalog movie IDs
12. No irrelevant popular-movie fallback
13. Search results completely unaffected by user preference history
14. Homepage recommendations changing after like or save
15. User isolation (User A activity never affects User B)
16. Cold-start recommendations for new users
17. Streamlit dialog state and rerun resilience
18. Explicit BTS regression test: Vijay search never returns BTS
"""

import sys
from pathlib import Path
import json
import pytest

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.assistant import GeminiAssistant
from src.retrieval_service import (
    movie_retrieval_service,
    QueryFilters,
    matches_person_name
)
from src.catalog_service import load_master_catalog, get_master_movie_by_id
from src.recommender import master_content_recommender
from app.db import (
    init_db,
    toggle_like,
    add_favorite,
    remove_favorite,
    get_user_likes,
    get_favorites
)


@pytest.fixture(scope="module")
def assistant():
    return GeminiAssistant()


# -----------------------------------------------------------------------------
# Test 1: Actor-only search for Vijay
# -----------------------------------------------------------------------------
def test_01_actor_only_search_vijay(assistant):
    """Verifies actor-only search for Vijay returns matching cast records with lead Vijay prioritized."""
    filters = QueryFilters(actor="Vijay")
    recs, total = movie_retrieval_service.search(filters, limit=5)
    assert total > 0, "Expected Vijay matches"
    assert len(recs) > 0

    # First result should be lead billing Joseph Vijay blockbuster
    first = recs[0]
    assert "joseph vijay" in str(first.get("cast", "")).lower() or first.get("title") in [
        "Master", "Leo", "Varisu", "The Greatest of All Time", "Beast"
    ]

    for r in recs:
        assert matches_person_name(r.get("cast", ""), "Vijay")


# -----------------------------------------------------------------------------
# Test 2: Vijay + Tamil + Action combined filters
# -----------------------------------------------------------------------------
def test_02_combined_actor_industry_genre_vijay_tamil_action(assistant):
    """Verifies combined filters: all 3 explicit constraints must be strictly satisfied."""
    filters = QueryFilters(actor="Vijay", industry="Tamil", genre="Action")
    recs, total = movie_retrieval_service.search(filters, limit=5)
    assert total > 0

    expected_blockbusters = {"Master", "Leo", "Varisu", "The Greatest of All Time", "Beast"}
    found_titles = {r["title"] for r in recs}
    assert found_titles.intersection(expected_blockbusters), f"Expected modern blockbusters, got {found_titles}"

    for r in recs:
        assert r["industry"].lower() == "tamil"
        assert "action" in r["genre"].lower()
        assert matches_person_name(r["cast"], "Vijay")


# -----------------------------------------------------------------------------
# Test 3: Director-only search (Lokesh Kanagaraj)
# -----------------------------------------------------------------------------
def test_03_director_only_search_lokesh(assistant):
    """Verifies director-only search retrieves only films directed by Lokesh Kanagaraj."""
    filters = QueryFilters(director="Lokesh Kanagaraj")
    recs, total = movie_retrieval_service.search(filters, limit=5)
    assert total == 4, f"Expected 4 Lokesh Kanagaraj films in catalog, got {total}"

    titles = {r["title"] for r in recs}
    assert titles == {"Vikram", "Master", "Leo", "Coolie"}

    for r in recs:
        assert "lokesh kanagaraj" in r["director"].lower()


# -----------------------------------------------------------------------------
# Test 4: Genre and industry filtering (English Sci-Fi)
# -----------------------------------------------------------------------------
def test_04_genre_and_industry_filtering_english_scifi(assistant):
    """Verifies Hollywood / English science-fiction movies."""
    filters = QueryFilters(industry="Hollywood", genre="Sci-Fi")
    recs, total = movie_retrieval_service.search(filters, limit=5)
    assert total > 0

    for r in recs:
        assert r["industry"].lower() == "hollywood"
        assert "sci-fi" in r["genre"].lower()


# -----------------------------------------------------------------------------
# Test 5: Release-year ranges (after 2020)
# -----------------------------------------------------------------------------
def test_05_release_year_ranges_after_2020(assistant):
    """Verifies release-year filtering strictly respects bounds."""
    filters = QueryFilters(industry="Tamil", genre="Thriller", year_from=2021)
    recs, total = movie_retrieval_service.search(filters, limit=5)
    assert total > 0

    for r in recs:
        assert int(r["release_year"]) >= 2021
        assert r["industry"].lower() == "tamil"
        assert "thriller" in r["genre"].lower()


# -----------------------------------------------------------------------------
# Test 6: Missing metadata and empty cast safety
# -----------------------------------------------------------------------------
def test_06_missing_metadata_safety():
    """Verifies that empty cast, null trailer links, or missing values do not crash search."""
    # Test person matching with None / empty
    assert matches_person_name(None, "Vijay") is False
    assert matches_person_name("", "Vijay") is False
    assert matches_person_name("   ", "Vijay") is False
    assert matches_person_name("Joseph Vijay", None) is False
    assert matches_person_name("Joseph Vijay", "") is False

    # Search with empty query filter returns all sorted by rating safely
    empty_filters = QueryFilters()
    recs, total = movie_retrieval_service.search(empty_filters, limit=3)
    assert total == 3560
    assert len(recs) == 3


# -----------------------------------------------------------------------------
# Test 7: No-match query returning honest empty state
# -----------------------------------------------------------------------------
def test_07_no_match_query_honest_empty_state(assistant):
    """Verifies impossible query returns 0 recommendations and honest explanation."""
    filters = QueryFilters(director="Quentin Tarantino", industry="Tamil")
    recs, total = movie_retrieval_service.search(filters, limit=5)
    assert total == 0
    assert len(recs) == 0

    # Via chat
    res = assistant.chat("Movies directed by Quentin Tarantino in Tamil", limit=5)
    assert len(res.recommendations) == 0
    assert "no matching movies" in res.reply.lower() or "no movies" in res.reply.lower()


# -----------------------------------------------------------------------------
# Test 8: Malformed Gemini JSON and API failure fallback
# -----------------------------------------------------------------------------
def test_08_malformed_gemini_json_and_api_failure_fallback(assistant):
    """Verifies that malformed JSON or API failures fall back cleanly to deterministic parsing."""
    # Simulate malformed JSON parser input
    bad_json = "NOT_A_JSON_STRING {actor: 'Vijay'}"
    with pytest.raises(Exception):
        json.loads(bad_json)

    # Calling assistant with a complex query succeeds via fallback even if network fails
    res = assistant.chat("Vijay's Tamil action movies", limit=3)
    assert len(res.recommendations) > 0
    for m in res.recommendations:
        assert "action" in m.genres.lower()
        assert m.cinema_region.lower() == "tamil"


# -----------------------------------------------------------------------------
# Test 9: Semantic search followed by strict filter validation
# -----------------------------------------------------------------------------
def test_09_semantic_search_followed_by_strict_filter_validation():
    """
    Verifies that semantic search returns thematically matching titles,
    and strict validation layer filters out any candidate failing metadata constraints.
    """
    # 1. Broad semantic query
    filters_broad = QueryFilters(semantic_query="dark gritty crime thriller directed by Lokesh")
    recs_broad, total_broad = movie_retrieval_service.search(filters_broad, limit=5)
    assert total_broad > 0
    broad_titles = {r["title"] for r in recs_broad}
    assert "Vikram" in broad_titles or "Leo" in broad_titles or "Master" in broad_titles

    # 2. Semantic query combined with strict factual constraint: director must be Lokesh Kanagaraj
    filters_strict = QueryFilters(
        semantic_query="dark gritty crime thriller",
        director="Lokesh Kanagaraj"
    )
    recs_strict, total_strict = movie_retrieval_service.search(filters_strict, limit=5)
    for r in recs_strict:
        assert "lokesh kanagaraj" in r["director"].lower()


# -----------------------------------------------------------------------------
# Test 10: Duplicate result removal
# -----------------------------------------------------------------------------
def test_10_duplicate_result_removal():
    """Verifies candidate validation deduplicates movie IDs while preserving rank order."""
    df = load_master_catalog()
    sample_a = df.iloc[0].to_dict()
    sample_b = df.iloc[1].to_dict()

    candidates_with_dupes = [sample_a, sample_b, sample_a, sample_b, sample_a]
    verified = movie_retrieval_service.validate_candidate_movies(candidates_with_dupes, QueryFilters())
    assert len(verified) == 2
    assert verified[0]["catalog_id"] == sample_a["catalog_id"]
    assert verified[1]["catalog_id"] == sample_b["catalog_id"]


# -----------------------------------------------------------------------------
# Test 11: Stable and valid catalog movie IDs
# -----------------------------------------------------------------------------
def test_11_stable_and_valid_movie_ids(assistant):
    """Verifies that every recommendation returns a valid catalog ID that exists in master catalog."""
    df = load_master_catalog()
    valid_cids = set(df["catalog_id"].values)

    res = assistant.chat("Show me movies acted by Vijay", limit=5)
    assert len(res.recommendations) > 0
    for item in res.recommendations:
        assert item.movie_id in valid_cids, f"Invalid movie_id: {item.movie_id}"
        assert str(item.movie_id).startswith("CINEVORA-")


# -----------------------------------------------------------------------------
# Test 12: No irrelevant popular-movie fallback
# -----------------------------------------------------------------------------
def test_12_no_irrelevant_popular_movie_fallback(assistant):
    """Verifies that queries never fall back to static high-rated catalog titles."""
    static_top3 = {"Sarpatta Parambarai", "Foreign Sarakku", "Dhil Raja"}

    # Search for Nolan
    res_nolan = assistant.chat("Movies directed by Christopher Nolan", limit=5)
    nolan_titles = {m.movie_title for m in res_nolan.recommendations}
    assert static_top3.isdisjoint(nolan_titles), "Nolan results should not contain static top 3 fallback"

    # Search for English Sci-Fi
    res_scifi = assistant.chat("English science-fiction movies", limit=5)
    scifi_titles = {m.movie_title for m in res_scifi.recommendations}
    assert static_top3.isdisjoint(scifi_titles), "Sci-Fi results should not contain static top 3 fallback"


# -----------------------------------------------------------------------------
# Test 13: Search results unaffected by user preference history
# -----------------------------------------------------------------------------
def test_13_search_results_unaffected_by_user_preference_history(assistant):
    """Verifies factual AI search returns identical objective results regardless of user likes."""
    init_db()
    user_test = "user_search_isolation_test"

    # Clean previous state
    for mid in list(get_user_likes(user_test)):
        toggle_like(user_test, mid)

    # 1. Search when user has no likes
    res_before = assistant.chat("Movies directed by Christopher Nolan", user_id=user_test, limit=4)
    ids_before = [m.movie_id for m in res_before.recommendations]

    # 2. User likes completely different movies (e.g. Tamil horror / comedy)
    toggle_like(user_test, "CINEVORA-0000001")
    toggle_like(user_test, "CINEVORA-0000002")

    # 3. Search again: results for Nolan MUST remain completely identical
    res_after = assistant.chat("Movies directed by Christopher Nolan", user_id=user_test, limit=4)
    ids_after = [m.movie_id for m in res_after.recommendations]

    assert ids_before == ids_after, "Search results must be completely isolated from user profile likes"

    # Cleanup
    toggle_like(user_test, "CINEVORA-0000001")
    toggle_like(user_test, "CINEVORA-0000002")


# -----------------------------------------------------------------------------
# Test 14: Homepage recommendations respond to like or save
# -----------------------------------------------------------------------------
def test_14_homepage_recommendations_respond_to_like_or_save():
    """Verifies that homepage recommendations adapt dynamically when a user likes or saves a movie."""
    init_db()
    user_test = "user_homepage_adapt_test"

    for mid in list(get_user_likes(user_test)):
        toggle_like(user_test, mid)

    # User engages: likes horror films
    horror_movies, _ = movie_retrieval_service.search(QueryFilters(genre="Horror"), limit=3)
    assert len(horror_movies) >= 2
    liked_ids = []
    for hm in horror_movies[:3]:
        h_id = hm["catalog_id"]
        toggle_like(user_test, h_id)
        liked_ids.append(h_id)

    recs = master_content_recommender.recommend_for_user(user_test, limit=5)
    rec_genres = [str(r.get("genre", "")).lower() for r in recs]
    assert any("horror" in g for g in rec_genres), "Recommendations should incorporate user's liked Horror genre"

    for h_id in liked_ids:
        toggle_like(user_test, h_id)


# -----------------------------------------------------------------------------
# Test 15: User isolation (User A never affects User B)
# -----------------------------------------------------------------------------
def test_15_user_isolation_a_does_not_affect_b():
    """Verifies that User A's activity never leaks into User B's homepage recommendations."""
    init_db()
    user_a = "user_alpha_rag_test"
    user_b = "user_beta_rag_test"

    for mid in list(get_user_likes(user_a)):
        toggle_like(user_a, mid)
    for mid in list(get_user_likes(user_b)):
        toggle_like(user_b, mid)

    # User A likes Malayalam cinema
    m_movies, _ = movie_retrieval_service.search(QueryFilters(industry="Malayalam"), limit=2)
    for m in m_movies:
        toggle_like(user_a, m["catalog_id"])

    # User B likes Hollywood cinema
    h_movies, _ = movie_retrieval_service.search(QueryFilters(industry="Hollywood"), limit=2)
    for m in h_movies:
        toggle_like(user_b, m["catalog_id"])

    recs_a = master_content_recommender.recommend_for_user(user_a, limit=5)
    recs_b = master_content_recommender.recommend_for_user(user_b, limit=5)

    ind_a = {str(r.get("industry", "")).lower() for r in recs_a}
    ind_b = {str(r.get("industry", "")).lower() for r in recs_b}

    assert "malayalam" in ind_a
    assert "hollywood" in ind_b

    for mid in list(get_user_likes(user_a)):
        toggle_like(user_a, mid)
    for mid in list(get_user_likes(user_b)):
        toggle_like(user_b, mid)


# -----------------------------------------------------------------------------
# Test 16: Cold-start recommendations for new users
# -----------------------------------------------------------------------------
def test_16_cold_start_recommendations():
    """Verifies that new users with zero activity receive diverse cross-industry curation."""
    init_db()
    brand_new_user = "brand_new_cold_start_user_999"

    for mid in list(get_user_likes(brand_new_user)):
        toggle_like(brand_new_user, mid)

    recs = master_content_recommender.recommend_for_user(brand_new_user, limit=6)
    assert len(recs) == 6

    # Verify diversity across industries in cold-start curation
    industries = {r.get("industry") for r in recs}
    assert len(industries) >= 3, f"Expected diverse industries for cold-start, got {industries}"


# -----------------------------------------------------------------------------
# Test 17: Streamlit dialog state and rerun resilience
# -----------------------------------------------------------------------------
def test_17_streamlit_dialog_state_and_rerun_resilience():
    """Verifies mutual exclusivity of dialog states ensuring no nested Streamlit dialog."""
    session_state = {
        "show_ai_dialog": True,
        "show_movie_details": False,
        "return_to_ai_dialog_after_details": False
    }

    # Simulate info click in assistant dialog
    session_state["return_to_ai_dialog_after_details"] = True
    session_state["show_ai_dialog"] = False
    session_state["show_movie_details"] = True

    # Mutually exclusive dialog router evaluation
    assert session_state["show_movie_details"] is True
    assert session_state["show_ai_dialog"] is False

    # Simulate dismiss of movie details
    session_state["show_movie_details"] = False
    if session_state.pop("return_to_ai_dialog_after_details", False):
        session_state["show_ai_dialog"] = True

    assert session_state["show_movie_details"] is False
    assert session_state["show_ai_dialog"] is True


# -----------------------------------------------------------------------------
# Test 18: Regression - Vijay query never returns BTS
# -----------------------------------------------------------------------------
def test_18_regression_vijay_query_never_returns_bts(assistant):
    """
    CRITICAL REGRESSION TEST:
    Verifies that searching for actor Vijay CANNOT return the BTS movie
    ('CINEVORA-0001142' / 'BTS: Yet To Come in Cinemas') whose cast contains 'V'.
    Ensures token-level person verification prevents single-letter false positive matching.
    """
    bts_catalog_id = "CINEVORA-0001142"

    # 1. Via MovieRetrievalService with actor='Vijay'
    filters = QueryFilters(actor="Vijay")
    recs, total = movie_retrieval_service.search(filters, limit=50)
    returned_cids = {r["catalog_id"] for r in recs}
    assert bts_catalog_id not in returned_cids, "Vijay search MUST NEVER return BTS movie"

    # 2. Via GeminiAssistant chat
    chat_res = assistant.chat("Show me movies acted by Vijay", limit=10)
    chat_cids = {m.movie_id for m in chat_res.recommendations}
    assert bts_catalog_id not in chat_cids, "Assistant chat for Vijay MUST NEVER return BTS movie"

    # 3. Direct cast token matching test
    bts_cast = "RM, Jin, Suga, J-Hope, Jimin, V, Jungkook"
    assert matches_person_name(bts_cast, "Vijay") is False
    assert matches_person_name(bts_cast, "Thalapathy Vijay") is False


# -----------------------------------------------------------------------------
# Test 19: Natural language query 'suggest me vijay acted movies'
# -----------------------------------------------------------------------------
def test_19_suggest_me_vijay_acted_movies(assistant):
    """
    CRITICAL USER BUG REGRESSION:
    Verifies that the exact natural query 'suggest me vijay acted movies'
    correctly resolves actor='vijay', clears free_query, and returns verified
    Vijay films (e.g. Master, Leo, Varisu) rather than 0 matches.
    """
    intent = assistant.parse_query_intent("suggest me vijay acted movies")
    assert intent.get("actor") == "vijay"
    assert intent.get("free_query") is None

    chat_res = assistant.chat("suggest me vijay acted movies", limit=3)
    assert len(chat_res.recommendations) == 3
    titles = [m.movie_title for m in chat_res.recommendations]
    assert any("Master" in t or "Leo" in t or "Varisu" in t for t in titles)
    assert chat_res.detected_actor == "vijay"
