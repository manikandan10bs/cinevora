"""
Cinevora My Watchlist View (Cinematic Dark Edition)
Dedicated page for movies saved to user's Watchlist:
- Shows all saved movies persisted in SQLite
- Displays title, release year, genres, rating, and date added
- Instant removal button per movie
- Option to clear the entire watchlist
- Genre distribution visualization
"""

from collections import Counter
from typing import Dict, Any, List
import streamlit as st
import plotly.graph_objects as go

from frontend.api_client import api_client
from frontend.components import render_header, render_movie_card, render_empty_state, render_metric_card
from frontend.config import DEMO_ACCOUNTS


def render_watchlist_page(account_key: str):
    """Renders the dedicated My Watchlist view."""
    account_info = DEMO_ACCOUNTS.get(account_key, DEMO_ACCOUNTS["demo_user_1"])
    persona_label = account_info.get("label", "Movie Enthusiast")
    avatar = account_info.get("avatar", "🎬")

    render_header(f"My Watchlist — {avatar} {persona_label}")

    # Fetch fresh watchlist from SQLite
    favorites = api_client.get_favorites(account_key)
    total_favs = len(favorites)

    # Genre calculation
    all_fav_genres: List[str] = []
    for item in favorites:
        g_str = item.get("genres", "")
        if g_str:
            all_fav_genres.extend([g.strip() for g in g_str.split("|") if g.strip()])
    genre_counts = Counter(all_fav_genres)
    top_genre = genre_counts.most_common(1)[0][0] if genre_counts else "None yet"

    # KPI Summary Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Saved to Watchlist", f"{total_favs} titles", "Stored in SQLite", border_color="#E50914")
    with m2:
        render_metric_card("Top Genre", top_genre, "Most saved category", border_color="#F59E0B")
    with m3:
        diversity = f"{len(genre_counts)} genres" if genre_counts else "0 genres"
        render_metric_card("Catalog Breadth", diversity, "Genre coverage", border_color="#3B82F6")
    with m4:
        avg_rating_val = sum(float(f.get("rating") or 0) for f in favorites) / max(1, total_favs)
        render_metric_card("Avg Quality", f"★ {avg_rating_val:.2f}" if total_favs else "N/A", "Saved titles", border_color="#10B981")

    st.write("")

    if not favorites:
        render_empty_state(
            title="Your Watchlist is Empty",
            message="You haven't saved any movies yet. Explore the catalog or personalized recommendations and click '⭐ Save' to build your watchlist.",
            icon="⭐"
        )
        return

    # Watchlist Actions Bar
    act_col1, act_col2 = st.columns([4, 1.2])
    with act_col1:
        st.markdown(f"### 📋 Saved Movies ({total_favs})")
    with act_col2:
        if st.button("🗑️ Clear Watchlist", key="clear_all_watchlist", use_container_width=True):
            for f in favorites:
                api_client.remove_favorite(account_key, f["movie_id"])
            fav_cache_key = f"fav_set_{account_key}"
            if fav_cache_key in st.session_state:
                st.session_state[fav_cache_key].clear()
            st.toast("Watchlist cleared!", icon="🗑️")
            st.rerun()

    # Visual Genre Distribution
    if genre_counts and total_favs >= 2:
        with st.expander("📊 Watchlist Genre Breakdown", expanded=False):
            labels = list(genre_counts.keys())
            values = list(genre_counts.values())

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.55,
                        textinfo="label+percent",
                        marker=dict(
                            colors=[
                                "#E50914", "#F59E0B", "#3B82F6", "#10B981",
                                "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"
                            ],
                            line=dict(color="#FFFFFF", width=2)
                        )
                    )
                ]
            )
            fig.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color="#171923", family="sans-serif"),
                showlegend=True,
                margin=dict(t=10, b=10, l=10, r=10),
                height=260
            )
            st.plotly_chart(fig, use_container_width=True)

    # Grid of Saved Movies
    cols = st.columns(4)
    for i, fav in enumerate(favorites):
        movie_dict = {
            "movie_id": fav.get("movie_id"),
            "movie_title": fav.get("movie_title"),
            "genres": fav.get("genres"),
            "release_date": fav.get("release_date"),
            "predicted_rating": fav.get("rating")
        }
        with cols[i % 4]:
            render_movie_card(movie_dict, user_id=account_key, key_prefix=f"watchlist_grid_{i}")
