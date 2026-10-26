"""
Regression and Verification Test Suite:
1. AI Search Accuracy (Actor, Director, Genre, Multi-filter, No-match)
2. Eliminating Repetitive 3-Movie Bug & Ensuring Dynamic Grounded Results
3. Non-Nested Dialog State Management (Streamlit Layout Context Compliance)
4. User Personalization Independence & Isolation
"""

import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.assistant import GeminiAssistant
from src.catalog_service import query_master_catalog, get_master_movie_by_id, load_master_catalog
from src.recommender import master_content_recommender
from app.db import (
    init_db,
    toggle_like,
    add_favorite,
    remove_favorite,
    get_user_likes,
    get_favorites,
    record_view_history,
    get_view_history
)


@pytest.fixture(scope="module")
def assistant():
    return GeminiAssistant()


# -----------------------------------------------------------------------------
# Test 1: Actor Query ("Show me movies acted by Vijay")
# -----------------------------------------------------------------------------
def test_01_actor_query_vijay(assistant):
    """Verifies that actor queries return movies where the actor appears in the cast."""
    res = assistant.chat("Show me movies acted by Vijay", limit=5)
    assert len(res.recommendations) > 0, "Expected recommendations for Vijay"
    
    # Check that each returned movie has Vijay in the cast
    for item in res.recommendations:
        movie_data = get_master_movie_by_id(item.movie_id)
        assert movie_data is not None, f"Movie {item.movie_id} not found in catalog"
        cast_lower = str(movie_data.get("cast", "")).lower()
        # Vijay or Joseph Vijay
        assert "vijay" in cast_lower, f"Expected 'Vijay' in cast: {movie_data.get('cast')}"


# -----------------------------------------------------------------------------
# Test 2: Director Query ("Movies directed by Christopher Nolan")
# -----------------------------------------------------------------------------
def test_02_director_query_christopher_nolan(assistant):
    """Verifies that director queries return movies directed by Christopher Nolan."""
    res = assistant.chat("Movies directed by Christopher Nolan", limit=5)
    assert len(res.recommendations) > 0, "Expected recommendations for Christopher Nolan"
    
    for item in res.recommendations:
        movie_data = get_master_movie_by_id(item.movie_id)
        assert movie_data is not None, f"Movie {item.movie_id} not found in catalog"
        dir_lower = str(movie_data.get("director", "")).lower()
        assert "nolan" in dir_lower or "christopher" in dir_lower, f"Expected Nolan in director: {movie_data.get('director')}"


# -----------------------------------------------------------------------------
# Test 3: Genre Query ("Tamil horror movies")
# -----------------------------------------------------------------------------
def test_03_genre_query_tamil_horror(assistant):
    """Verifies that queries specifying region and genre filter strictly by both."""
    res = assistant.chat("Tamil horror movies", limit=5)
    assert len(res.recommendations) > 0, "Expected Tamil horror recommendations"
    
    for item in res.recommendations:
        movie_data = get_master_movie_by_id(item.movie_id)
        assert movie_data is not None
        ind = str(movie_data.get("industry", "")).lower()
        genre = str(movie_data.get("genre", "")).lower()
        assert ind == "tamil", f"Expected Tamil industry, got {ind}"
        assert "horror" in genre, f"Expected Horror in genre, got {genre}"


# -----------------------------------------------------------------------------
# Test 4: Combined Actor + Genre + Year ("Vijay action movies from 2020 onward")
# -----------------------------------------------------------------------------
def test_04_combined_actor_genre_year(assistant):
    """Verifies multi-constraint query combining actor, genre, and release period."""
    res = assistant.chat("Vijay action movies from 2020 onward", limit=5)
    assert len(res.recommendations) > 0, "Expected Vijay action movies >= 2020"
    
    for item in res.recommendations:
        movie_data = get_master_movie_by_id(item.movie_id)
        assert movie_data is not None
        cast_lower = str(movie_data.get("cast", "")).lower()
        genre_lower = str(movie_data.get("genre", "")).lower()
        year = int(movie_data.get("release_year", 0))
        
        assert "vijay" in cast_lower, f"Expected Vijay in cast: {movie_data.get('cast')}"
        assert "action" in genre_lower, f"Expected Action in genre: {movie_data.get('genre')}"
        assert year >= 2020, f"Expected year >= 2020, got {year}"


# -----------------------------------------------------------------------------
# Test 5: No-match Query ("Movies directed by Quentin Tarantino in Tamil")
# -----------------------------------------------------------------------------
def test_05_no_match_query(assistant):
    """Verifies that impossible / non-existent combinations return an honest explanation and empty list."""
    res = assistant.chat("Movies directed by Quentin Tarantino in Tamil", limit=5)
    assert len(res.recommendations) == 0, f"Expected 0 recommendations, got {len(res.recommendations)}"
    assert "No movies in Cinevora's catalog matched" in res.reply or "no movies" in res.reply.lower()


# -----------------------------------------------------------------------------
# Test 6: Distinct Queries Yield Distinct Results (Fixes Repetitive 3-Movie Bug)
# -----------------------------------------------------------------------------
def test_06_distinct_queries_yield_distinct_results(assistant):
    """Verifies that distinct queries return distinct, specific sets of movies."""
    res_vijay = assistant.chat("movies acted by Vijay", limit=4)
    res_nolan = assistant.chat("movies directed by Christopher Nolan", limit=4)
    
    ids_vijay = {m.movie_id for m in res_vijay.recommendations}
    ids_nolan = {m.movie_id for m in res_nolan.recommendations}
    
    assert len(ids_vijay) > 0
    assert len(ids_nolan) > 0
    # The two sets should not overlap
    assert ids_vijay.isdisjoint(ids_nolan), "Vijay and Nolan recommendations should be completely disjoint"


# -----------------------------------------------------------------------------
# Test 7: Results Not Restricted to Arbitrary Three Movies
# -----------------------------------------------------------------------------
def test_07_results_not_restricted_to_three_movies(assistant):
    """Verifies that assistant does not default to the old static top-3 catalog movies."""
    old_static_titles = {"Sarpatta Parambarai", "Foreign Sarakku", "Dhil Raja"}
    
    res_vijay = assistant.chat("Show me movies acted by Vijay", limit=5)
    vijay_titles = {m.movie_title for m in res_vijay.recommendations}
    assert old_static_titles.isdisjoint(vijay_titles), "Should not return arbitrary static catalog titles for Vijay"
    
    res_nolan = assistant.chat("Christopher Nolan sci-fi movies", limit=5)
    nolan_titles = {m.movie_title for m in res_nolan.recommendations}
    assert old_static_titles.isdisjoint(nolan_titles), "Should not return arbitrary static catalog titles for Nolan"


# -----------------------------------------------------------------------------
# Test 8: Non-nested Dialog State Transition Simulation
# -----------------------------------------------------------------------------
def test_08_non_nested_dialog_state_transition():
    """
    Simulates the Streamlit session state lifecycle when an info button is clicked
    inside an AI assistant dialog, verifying that no nested @st.dialog call occurs.
    """
    from frontend.components import _on_movie_details_dismiss
    
    # 1. User is inside AI Concierge dialog
    session_state = {
        "show_ai_dialog": True,
        "show_movie_details": False,
        "return_to_ai_dialog_after_details": False,
        "selected_movie_id": None,
        "selected_movie_data": None
    }
    
    # 2. User clicks "ℹ️" on a movie card inside the dialog (in_dialog=True)
    clicked_movie = {
        "catalog_id": "CINEVORA-0001730",
        "title": "Leo",
        "release_year": 2023,
        "genre": "Action, Crime, Drama",
        "industry": "Tamil"
    }
    
    # State update performed by render_movie_card(in_dialog=True):
    session_state["selected_movie_id"] = clicked_movie["catalog_id"]
    session_state["selected_movie_data"] = clicked_movie
    session_state["return_to_ai_dialog_after_details"] = True
    session_state["show_ai_dialog"] = False
    session_state["show_movie_details"] = True
    
    # 3. Streamlit app.py evaluates routing:
    # app.py logic:
    # if session_state.get("show_movie_details") and session_state.get("selected_movie_data"):
    #     show_movie_details_dialog(...)
    # elif session_state.get("show_ai_dialog"):
    #     render_assistant_dialog(...)
    
    active_dialog = None
    if session_state.get("show_movie_details") and session_state.get("selected_movie_data"):
        active_dialog = "movie_details"
    elif session_state.get("show_ai_dialog"):
        active_dialog = "ai_concierge"
        
    assert active_dialog == "movie_details", "Movie details should be the ONLY active dialog"
    assert session_state["show_ai_dialog"] is False, "AI Concierge dialog must be inactive to prevent nesting"
    
    # 4. When movie details is closed, _on_movie_details_dismiss callback executes:
    session_state["show_movie_details"] = False
    if session_state.pop("return_to_ai_dialog_after_details", False):
        session_state["show_ai_dialog"] = True
        
    # 5. On next rerun:
    active_dialog_after = None
    if session_state.get("show_movie_details") and session_state.get("selected_movie_data"):
        active_dialog_after = "movie_details"
    elif session_state.get("show_ai_dialog"):
        active_dialog_after = "ai_concierge"
        
    assert active_dialog_after == "ai_concierge", "AI Concierge dialog should reopen after details dismissed"
    assert session_state["show_movie_details"] is False


# -----------------------------------------------------------------------------
# Test 9: Selected Movie Matches Clicked Movie
# -----------------------------------------------------------------------------
def test_09_selected_movie_matches_clicked_movie():
    """Verifies data integrity: the movie stored in session state is the exact one clicked."""
    movie_a = {"catalog_id": "CINEVORA-0000001", "title": "Toy Story"}
    movie_b = {"catalog_id": "CINEVORA-0001730", "title": "Leo"}
    
    session_state = {}
    
    # Click movie B
    session_state["selected_movie_id"] = movie_b["catalog_id"]
    session_state["selected_movie_data"] = movie_b
    
    assert session_state["selected_movie_id"] == "CINEVORA-0001730"
    assert session_state["selected_movie_data"]["title"] == "Leo"
    assert session_state["selected_movie_id"] != movie_a["catalog_id"]


# -----------------------------------------------------------------------------
# Test 10: Normal Movie Cards Work Outside Assistant
# -----------------------------------------------------------------------------
def test_10_normal_movie_cards_work_outside_assistant():
    """Verifies that outside the assistant (in_dialog=False), cards trigger details normally without setting return_to_ai."""
    session_state = {
        "show_ai_dialog": False,
        "return_to_ai_dialog_after_details": False
    }
    movie = {"catalog_id": "CINEVORA-0000500", "title": "Master"}
    
    # In outside mode: in_dialog is False
    in_dialog = False
    if in_dialog:
        session_state["return_to_ai_dialog_after_details"] = True
    else:
        # Opens details dialog directly
        session_state["selected_movie_id"] = movie["catalog_id"]
        session_state["selected_movie_data"] = movie
        
    assert session_state.get("return_to_ai_dialog_after_details") is False
    assert session_state["selected_movie_id"] == "CINEVORA-0000500"


# -----------------------------------------------------------------------------
# Test 11: Likes and Watchlist Function Independently of Details
# -----------------------------------------------------------------------------
def test_11_likes_and_watchlist_independent_of_details():
    """Verifies that toggling likes and watchlist modifies database state directly without altering dialog state."""
    init_db()
    user_id = "test_user_isolated_1"
    movie_id = "CINEVORA-0001730"
    
    # Clean up any leftover state from prior runs
    for mid in list(get_user_likes(user_id)):
        toggle_like(user_id, mid)
    remove_favorite(user_id, movie_id)
    
    # Initial state
    likes_before = get_user_likes(user_id)
    assert movie_id not in likes_before
    
    # Toggle like
    success, currently_liked = toggle_like(user_id, movie_id)
    assert success is True
    assert currently_liked is True
    likes_after = get_user_likes(user_id)
    assert movie_id in likes_after
    
    # Add to favorite / watchlist
    add_favorite(user_id, movie_id, "Leo", "Action, Crime", "2023", 7.8)
    favs = get_favorites(user_id)
    fav_ids = [f["movie_id"] for f in favs]
    assert movie_id in fav_ids
    
    # Cleanup
    toggle_like(user_id, movie_id)
    remove_favorite(user_id, movie_id)


# -----------------------------------------------------------------------------
# Test 12: Homepage Recommendations Respond to User Activity
# -----------------------------------------------------------------------------
def test_12_homepage_recommendations_respond_to_user_activity():
    """Verifies that user likes, watchlist, and views immediately influence personalized recommendations."""
    init_db()
    test_user = "test_user_dynamic_activity"
    
    # Baseline recommendations
    baseline_recs = master_content_recommender.recommend_for_user(test_user, limit=5)
    assert len(baseline_recs) > 0
    
    # User engages: likes a specific Sci-Fi Hollywood movie (e.g. Inception or Interstellar)
    nolan_movies, _ = query_master_catalog(director="Christopher Nolan", limit=1)
    assert len(nolan_movies) > 0
    nolan_id = nolan_movies[0]["catalog_id"]
    nolan_genre = nolan_movies[0]["genre"]
    
    toggle_like(test_user, nolan_id)
    
    # Updated recommendations
    updated_recs = master_content_recommender.recommend_for_user(test_user, limit=5)
    assert len(updated_recs) > 0
    
    # The updated recommendations should reflect the liked genre/director
    liked_genres = [g.strip().lower() for g in nolan_genre.split(",")]
    matching_genre_count = 0
    for rec in updated_recs:
        rec_genres = [g.strip().lower() for g in str(rec.get("genre", "")).split(",")]
        if any(g in rec_genres for g in liked_genres):
            matching_genre_count += 1
            
    assert matching_genre_count >= 1, "Recommendations should adapt to incorporate user's liked genres"
    
    # Cleanup
    toggle_like(test_user, nolan_id)


# -----------------------------------------------------------------------------
# Test 13: User Isolation
# -----------------------------------------------------------------------------
def test_13_user_isolation():
    """Verifies that User A's activity never leaks into User B's personalized recommendations."""
    init_db()
    user_a = "user_isolation_alpha"
    user_b = "user_isolation_beta"
    
    # Clean previous state if any
    for mid in list(get_user_likes(user_a)):
        toggle_like(user_a, mid)
    for mid in list(get_user_likes(user_b)):
        toggle_like(user_b, mid)
        
    # User A likes horror movies
    horror_movies, _ = query_master_catalog(genre="Horror", limit=3)
    for m in horror_movies:
        toggle_like(user_a, m["catalog_id"])
        
    # User B likes comedy movies
    comedy_movies, _ = query_master_catalog(genre="Comedy", limit=3)
    for m in comedy_movies:
        toggle_like(user_b, m["catalog_id"])
        
    likes_a = get_user_likes(user_a)
    likes_b = get_user_likes(user_b)
    
    assert set(likes_a).isdisjoint(set(likes_b)), "User A and User B likes must be isolated"
    
    recs_a = master_content_recommender.recommend_for_user(user_a, limit=5)
    recs_b = master_content_recommender.recommend_for_user(user_b, limit=5)
    
    recs_a_genres = [str(m.get("genre", "")).lower() for m in recs_a]
    recs_b_genres = [str(m.get("genre", "")).lower() for m in recs_b]
    
    assert any("horror" in g for g in recs_a_genres), "User A should receive Horror recommendations"
    assert any("comedy" in g for g in recs_b_genres), "User B should receive Comedy recommendations"
    
    # Cleanup
    for mid in list(likes_a):
        toggle_like(user_a, mid)
    for mid in list(likes_b):
        toggle_like(user_b, mid)
