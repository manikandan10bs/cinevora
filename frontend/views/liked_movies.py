"""
Cinevora Liked Movies View (Cinematic Dark Edition)
Dedicated page for movies liked by the user:
- Shows all liked movies persisted in SQLite
- Displays taste summary (top liked genres that drive recommendations)
- Option to unlike individual titles
- Empty state with quick discovery suggestions
"""

from collections import Counter
from typing import Dict, Any, List
import streamlit as st
import plotly.graph_objects as go

from frontend.api_client import api_client
from frontend.components import render_header, render_movie_card, render_empty_state, render_metric_card
from frontend.config import DEMO_ACCOUNTS


def render_liked_movies_page(account_key: str):
    """Renders the dedicated Liked Movies view."""
    account_info = DEMO_ACCOUNTS.get(account_key, DEMO_ACCOUNTS["demo_user_1"])
    persona_label = account_info.get("label", "Movie Enthusiast")
    avatar = account_info.get("avatar", "🎬")

    render_header(f"Liked Movies & Taste Signals — {avatar} {persona_label}")

    # Fetch liked movie IDs from SQLite backend
    liked_ids = api_client.get_likes(account_key)
    total_likes = len(liked_ids)

    # Fetch movie metadata for liked IDs
    meta_cache = st.session_state.setdefault("liked_meta_cache", {})
    liked_movies: List[Dict[str, Any]] = []
    all_liked_genres: List[str] = []

    for movie_id in liked_ids:
        if movie_id in meta_cache:
            m = meta_cache[movie_id]
        else:
            details = api_client.get_movie_details(movie_id)
            if details:
                m = {
                    "movie_id": movie_id,
                    "movie_title": details.get("movie_title", f"Movie #{movie_id}"),
                    "genres": details.get("genres", ""),
                    "release_date": details.get("release_date", ""),
                    "predicted_rating": details.get("avg_rating", 4.0)
                }
                meta_cache[movie_id] = m
            else:
                m = {"movie_id": movie_id, "movie_title": f"Movie #{movie_id}", "genres": ""}

        liked_movies.append(m)
        g_str = m.get("genres", "")
        if g_str:
            all_liked_genres.extend([g.strip() for g in g_str.split("|") if g.strip()])

    genre_counts = Counter(all_liked_genres)
    top_genres = [g for g, _ in genre_counts.most_common(3)]
    top_genres_str = ", ".join(top_genres) if top_genres else "None yet"

    # KPI Summary Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Liked Movies", f"{total_likes} titles", "Active Taste Signals", border_color="#E50914")
    with m2:
        render_metric_card("Top Taste Genres", top_genres_str, "Driving Recommendations", border_color="#F59E0B")
    with m3:
        render_metric_card("Taste Diversity", f"{len(genre_counts)} genres", "Breadth of Preferences", border_color="#3B82F6")
    with m4:
        rec_status = "Active" if total_likes > 0 else "Cold Start"
        render_metric_card("Engine State", rec_status, "Recommender Alignment", border_color="#10B981")

    st.write("")

    if not liked_movies:
        render_empty_state(
            title="No Liked Movies Yet",
            message="You haven't liked any movies yet. Click '❤️ Like' on any movie in Home, Discover, or For You to teach Cinevora your cinematic tastes.",
            icon="❤️"
        )
        return

    # Actions Bar
    act_col1, act_col2 = st.columns([4, 1.2])
    with act_col1:
        st.markdown(f"### ❤️ Movies You Liked ({total_likes})")
        st.caption("These movies directly shape your 'Recommended for You' carousel.")
    with act_col2:
        if st.button("🗑️ Reset All Likes", key="clear_all_likes", use_container_width=True):
            for m in liked_movies:
                api_client.toggle_like(account_key, m["movie_id"])
            likes_cache_key = f"likes_set_{account_key}"
            if likes_cache_key in st.session_state:
                st.session_state[likes_cache_key].clear()
            st.session_state.pop("liked_meta_cache", None)
            st.toast("Reset all likes!", icon="🗑️")
            st.rerun()

    # Visual Taste Signals (Plotly Bar Chart)
    if genre_counts and total_likes >= 2:
        with st.expander("📊 Liked Genres Taste Profile", expanded=False):
            genres_list = [g for g, _ in genre_counts.most_common(8)]
            counts_list = [genre_counts[g] for g in genres_list]

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=genres_list,
                        y=counts_list,
                        marker=dict(
                            color=["#E50914", "#F59E0B", "#3B82F6", "#10B981", "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"][:len(genres_list)],
                            line=dict(color="#FFFFFF", width=1.5)
                        )
                    )
                ]
            )
            fig.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color="#171923", family="sans-serif"),
                xaxis=dict(gridcolor="#F2F4F7"),
                yaxis=dict(gridcolor="#F2F4F7"),
                margin=dict(t=10, b=10, l=10, r=10),
                height=240
            )
            st.plotly_chart(fig, use_container_width=True)

    # Grid of Liked Movies
    cols = st.columns(4)
    for i, m in enumerate(liked_movies):
        with cols[i % 4]:
            render_movie_card(m, user_id=account_key, key_prefix=f"liked_grid_{i}")
