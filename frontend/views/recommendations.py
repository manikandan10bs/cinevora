"""
Cinevora Recommendations View
Provides interactive, model-switchable movie recommendations for the Master Catalog:
- Master Content-Based Engine (TF-IDF similarity across Industry, Genre, Director, Cast)
- User Taste Profile (Personalized vector built from real-time SQLite Likes, Watchlist, and Searches)
- Popularity Prior Baseline (Bayesian-weighted quality ranking across 3,560 titles)
- Hard industry, genre, and release year constraints
- "Exclude already interacted movies" toggle
- Cold-start handling for guest accounts
- Transparent scoring and recommendation rationales
"""

from typing import Dict, Any, Optional
import re
import streamlit as st

from frontend.api_client import api_client
from frontend.components import render_header, render_movie_card, render_empty_state, render_metric_card, render_movie_carousel
from frontend.config import DEMO_ACCOUNTS
from src.catalog_service import get_master_catalog_stats
from src.recommender import master_content_recommender

INDUSTRY_OPTIONS = [
    "All Industries",
    "Bollywood",
    "Tamil",
    "Telugu",
    "Malayalam",
    "Kannada",
    "Hollywood"
]


def render_recommendations_page(account_key: str):
    """Renders the 'Recommendations / For You' page for the selected account."""
    account_info = DEMO_ACCOUNTS.get(
        account_key,
        {
            "label": f"Verified Member ({account_key})",
            "description": "Active Cinevora member with synced likes and watchlist.",
            "avatar": "👤"
        }
    )
    persona_label = account_info.get("label", "Movie Enthusiast")
    persona_desc = account_info.get("description", "")
    avatar = account_info.get("avatar", "🎬")

    render_header("Personalized Cinema Recommendations")

    # Persona banner (Dark Theme)
    st.markdown(
        f"""
        <div style="
            background: #0E1622;
            border: 1px solid rgba(0, 229, 255, 0.25);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        ">
            <div style="font-size: 2.2rem;">{avatar}</div>
            <div>
                <div style="color: #FFFFFF; font-weight: 700; font-size: 1.05rem; font-family: 'Cinzel', serif;">
                    {persona_label}
                </div>
                <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 3px;">
                    {persona_desc}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    stats = get_master_catalog_stats()
    catalog_genres = ["All Genres"] + stats.get("genres", ["Action", "Drama", "Comedy", "Thriller", "Romance", "Sci-Fi"])

    # Controls Bar
    with st.container():
        c1, c2, c3, c4 = st.columns([1.8, 1.4, 1.2, 1.0])

        with c1:
            model_options = {
                "content": "Master Content Engine (TF-IDF Cast, Director, Genre)",
                "taste_profile": "User Taste Profile (SQLite Likes & Watchlist)",
                "popularity": "Top Rated Baseline (Bayesian Quality Priors)"
            }
            model_type = st.selectbox(
                "Recommendation Engine",
                options=list(model_options.keys()),
                format_func=lambda k: model_options[k],
                index=0,
                help="Switch between Cinevora's master catalog recommendation algorithms."
            )

        with c2:
            selected_industry = st.selectbox(
                "Industry Filter",
                options=INDUSTRY_OPTIONS,
                index=0,
                help="Constrain recommendations strictly to a specific film industry."
            )

        with c3:
            selected_genre = st.selectbox(
                "Genre Constraint",
                options=catalog_genres,
                index=0,
                help="Filters recommendations strictly to this genre."
            )

        with c4:
            num_recs = st.slider("Results Limit", min_value=4, max_value=24, value=12, step=4)

    # Optional Year Range Filter & Interaction exclusions
    exp_col1, exp_col2 = st.columns([3, 1])
    with exp_col1:
        with st.expander("📅 Release Year Filter (1950 – 2025)", expanded=False):
            year_range = st.slider(
                "Release Year Window",
                min_value=1950,
                max_value=2025,
                value=(1950, 2025),
                step=1,
                help="Constrain recommendations strictly to movies released within this year range."
            )
    with exp_col2:
        exclude_interacted = st.checkbox(
            "Exclude Interacted",
            value=True,
            help="Hides movies you have already liked or saved to your watchlist."
        )

    start_year = year_range[0] if 'year_range' in locals() and year_range != (1950, 2025) else None
    end_year = year_range[1] if 'year_range' in locals() and year_range != (1950, 2025) else None

    # Fetch recommendations from FastAPI backend
    with st.spinner("Generating tailored cinema recommendations from master catalog"):
        response = api_client.get_recommendations(
            user_id=account_key,
            genre=selected_genre if selected_genre != "All Genres" else None,
            industry=selected_industry if selected_industry != "All Industries" else None,
            start_year=start_year,
            end_year=end_year,
            model_type=model_type,
            limit=num_recs,
            exclude_rated=exclude_interacted
        )

    recs = response.get("recommendations", [])
    model_used = response.get("model_type", model_type)
    total_returned = len(recs)

    # Summary Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Algorithm Active", model_used.upper(), "Master Recommender")
    with m2:
        render_metric_card("Recommendations", f"{total_returned} titles", f"Requested: {num_recs}")
    with m3:
        top_score = f"{recs[0].get('score', 0):.2f}" if recs and recs[0].get('score') is not None else "N/A"
        render_metric_card("Top Match Score", top_score, "Normalized similarity [0, 1]")
    with m4:
        top_rating = f"★ {recs[0].get('predicted_rating', 0):.1f}/10" if recs and recs[0].get('predicted_rating') is not None else "N/A"
        render_metric_card("Top Rating", top_rating, "Master Catalog Score")

    st.write("")

    # Display Movie Cards
    if not recs:
        render_empty_state(
            title="No Matching Recommendations",
            message="No movies matched your current combination of industry, genre, and year constraints. "
                    "Try broadening your release year window or selecting 'All Industries'.",
            icon="🔍"
        )
    else:
        num_cols = 4
        for i in range(0, len(recs), num_cols):
            cols = st.columns(num_cols)
            batch = recs[i:i + num_cols]
            for col_idx, movie in enumerate(batch):
                with cols[col_idx]:
                    render_movie_card(
                        movie=movie,
                        user_id=account_key,
                        key_prefix=f"rec_{model_type}_{i}_{col_idx}",
                        show_score=True
                    )

    # Dynamic Multi-Signal Recommendation Rows
    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # 1. "Because You Liked [Movie Title]"
    liked_signal = master_content_recommender.recommend_because_you_liked(user_id=account_key, limit=6)
    if liked_signal.get("source_movie") and liked_signal.get("movies"):
        src_movie_title = re.sub(r"\s*\(\d{4}\)", "", liked_signal["source_movie"].get("title", "")).strip()
        render_movie_carousel(
            title=f"Because You Liked '{src_movie_title}'",
            subtitle="Recommendations powered by content and metadata similarity to your liked titles",
            movies=liked_signal["movies"],
            user_id=account_key,
            section_id="rec_page_because_liked",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # 2. "More Like Movies in Your Watchlist"
    wl_signal = master_content_recommender.recommend_from_watchlist(user_id=account_key, limit=6)
    if wl_signal.get("source_movie") and wl_signal.get("movies"):
        wl_movie_title = re.sub(r"\s*\(\d{4}\)", "", wl_signal["source_movie"].get("title", "")).strip()
        render_movie_carousel(
            title=f"More Like '{wl_movie_title}' in Your Watchlist",
            subtitle="Similar acclaimed films matching titles saved in your watchlist",
            movies=wl_signal["movies"],
            user_id=account_key,
            section_id="rec_page_from_watchlist",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # 3. "Your Favourite Genres"
    fav_genre_data = master_content_recommender.recommend_favorite_genres(user_id=account_key, limit=6)
    if fav_genre_data.get("favorite_genre") and fav_genre_data.get("movies"):
        fav_g = fav_genre_data["favorite_genre"]
        render_movie_carousel(
            title=f"Your Favourite Genre: {fav_g}",
            subtitle=f"Top-rated {fav_g} films from across Indian Cinema and Hollywood",
            movies=fav_genre_data["movies"],
            user_id=account_key,
            section_id="rec_page_fav_genre",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # 4. "Discover Something New"
    discover_recs = master_content_recommender.recommend_discover_new(user_id=account_key, limit=6)
    if discover_recs:
        render_movie_carousel(
            title="Discover Something New",
            subtitle="Expand your cinematic palette with high-rated films from unexplored industries",
            movies=discover_recs,
            user_id=account_key,
            section_id="rec_page_discover_new",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # Methodology Explainer
    with st.expander("🔬 How are Cinevora master recommendations calculated?", expanded=False):
        st.markdown(
            """
            ### Master Catalog Recommendation Architecture
            Cinevora's recommendation pipeline is grounded strictly in `data/processed/Movies_Master_Cleaned.csv` (3,560 titles):
            - **TF-IDF Semantic Representation**: Each movie is vectorized over its **industry**, **genres**, **director**, and **ensemble cast**, assigning higher semantic weights to cinematic industry and genre alignments.
            - **User Preference Profile**: Real-time interaction signals (likes, watchlist additions, and search history saved in SQLite) are aggregated to construct a personalized user taste vector in the TF-IDF feature space.
            - **Cosine Similarity & Quality Prior**: Candidate titles are scored via cosine similarity between the user profile vector and catalog items, blended with a Bayesian rating multiplier ($0.8 + 0.4 \\cdot \\frac{\\text{rating}}{10}$) to prioritize acclaimed cinematic works.
            - **Cold-Start Resilience**: When a new user or guest explores without prior history, the engine automatically recommends top-rated benchmark titles across Indian Cinema (Bollywood, Tamil, Telugu, Malayalam, Kannada) and Hollywood.
            - **Strict Filtering**: Industry, genre, and release-year bounds are applied as rigorous pre-filters before scoring.
            """
        )
