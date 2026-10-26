"""
Cinevora — Streamlit Application Entrypoint (Cinematic Streaming Edition)
Features:
- Narrow left vertical icon rail (Profile, Search, Home, Explore, For You, Watchlist, Likes, Monitoring, AI)
- Dark streaming visual aesthetic with electric cyan accents and Cinzel typography
- Edge-to-edge cinematic hero banner and Top 10 translucent ranking row
- Multi-signal user personalized recommendations (Likes, Watchlist, Views, Searches)
- Persistent demo account: test_id_1 / test123 with full SQLite session isolation
- Unobtrusive floating AI Movie Concierge modal dialog (Gemini 3.5 Flash Lite)
- Single source of truth: data/processed/Movies_Master_Cleaned.csv
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

print(">>> Streamlit run app.py: sys.path[0:5] =", sys.path[0:5])
print(">>> Streamlit run app.py: sys.modules['app'] =", sys.modules.get('app'))

import streamlit as st

# Configure page settings: expanded sidebar serves as the vertical icon rail
st.set_page_config(
    page_title="Cinevora — Cinema Discovery Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

from frontend.styles import inject_cinema_styles
from frontend.config import DEMO_ACCOUNTS
from frontend.api_client import api_client
from frontend.components import render_vertical_nav_rail, show_movie_details_dialog
from frontend.poster_service import get_movie_enrichment

# Import views
from frontend.views.home import render_home_page
from frontend.views.explore import render_explore_page
from frontend.views.recommendations import render_recommendations_page
from frontend.views.watchlist import render_watchlist_page
from frontend.views.liked_movies import render_liked_movies_page
from frontend.views.monitoring import render_monitoring_page
from frontend.views.about import render_about_page
from frontend.views.account import render_account_page

try:
    from frontend.views.assistant import render_assistant_page, render_assistant_dialog
except ImportError:
    import importlib
    import frontend.views.assistant as _assistant_mod
    importlib.reload(_assistant_mod)
    render_assistant_page = getattr(_assistant_mod, "render_assistant_page", None)
    render_assistant_dialog = getattr(_assistant_mod, "render_assistant_dialog", None)


def main():
    # Inject Cinematic Dark Streaming CSS
    inject_cinema_styles()

    # Initialize Authentication & Session State
    if "active_account" not in st.session_state:
        st.session_state["active_account"] = "test_id_1"
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = True
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = "Home"

    user_id = st.session_state["active_account"]
    current_page = st.session_state["nav_selection"]

    # -------------------------------------------------------------------------
    # 1. Left Vertical Icon Navigation Rail
    # -------------------------------------------------------------------------
    render_vertical_nav_rail(active_page=current_page, user_id=user_id)

    # -------------------------------------------------------------------------
    # 2. Sleek Minimal Top Bar (Brand Lockup, Quick Search, User Pill, Health)
    # -------------------------------------------------------------------------
    top_col1, top_col2, top_col3 = st.columns([3, 4, 3])

    with top_col1:
        st.markdown(
            """
            <div style="display: flex; align-items: baseline; gap: 8px; padding-top: 2px;">
                <span class="cinevora-brand" style="font-size: 1.85rem;">Cinevora</span>
                <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #00E5FF; box-shadow: 0 0 8px #00E5FF;"></span>
                <span class="cinevora-tagline" style="font-size: 0.76rem; letter-spacing: 0.15em;">STREAMING CINEMA</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with top_col2:
        # Quick Search Input
        with st.form("top_quick_search_form", clear_on_submit=False):
            s_col1, s_col2 = st.columns([5, 1])
            with s_col1:
                search_val = st.text_input(
                    "Search Catalog",
                    placeholder="Search 3,560 movies by title, cast, or director...",
                    label_visibility="collapsed",
                    key="top_search_input"
                )
            with s_col2:
                search_submitted = st.form_submit_button("🔍", help="Search Catalog", use_container_width=True)

            if search_submitted and search_val.strip():
                st.session_state["nav_selection"] = "Explore"
                st.session_state["explore_search_input"] = search_val.strip()
                st.rerun()

    with top_col3:
        user_col, status_col = st.columns([1.6, 1.2])
        with user_col:
            user_display = "Test Member" if user_id == "test_id_1" else user_id
            if st.button(f"👤 {user_display}", key="top_user_pill_btn", help="Manage Profile & Login", use_container_width=True):
                st.session_state["nav_selection"] = "Account"
                st.rerun()

        with status_col:
            health = api_client.get_health()
            if health and health.get("status") == "healthy":
                total_count = health.get("master_catalog_count", 3560)
                st.markdown(
                    f'<div style="color: #00E5FF; font-size: 0.74rem; font-weight: 700; text-align: right; padding-top: 8px;">● {total_count:,} Titles</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="color: #EF4444; font-size: 0.74rem; font-weight: 700; text-align: right; padding-top: 8px;">● Offline</div>',
                    unsafe_allow_html=True
                )

    st.markdown('<hr style="margin: 6px 0 16px 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.06);">', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 3. Floating AI Assistant Button (Bottom-Right Corner)
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div class="floating-assistant-btn-wrap">
            <a href="?action=open_ai_concierge" target="_self" class="floating-assistant-pill" title="Open AI Movie Concierge">
                <span>✨</span> <span>AI Concierge</span>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Handle direct movie details navigation (clicking movie poster or title anywhere)
    if st.query_params.get("action") == "movie_details" and st.query_params.get("m_id"):
        target_mid = str(st.query_params.get("m_id")).strip()
        m_meta = get_movie_enrichment(target_mid)
        if m_meta:
            st.session_state["selected_movie_id"] = target_mid
            st.session_state["selected_movie_data"] = m_meta
            if st.session_state.get("show_ai_dialog"):
                st.session_state["return_to_ai_dialog_after_details"] = True
                st.session_state["show_ai_dialog"] = False
            st.session_state["show_movie_details"] = True
        st.query_params.clear()
        st.rerun()

    if st.query_params.get("action") == "open_ai_concierge" or st.session_state.get("trigger_ai_dialog"):
        st.session_state["show_ai_dialog"] = True
        st.session_state["show_movie_details"] = False
        st.session_state["trigger_ai_dialog"] = False
        st.query_params.clear()

    # Mutually exclusive modal dialog management:
    # Streamlit prevents nesting dialogs within other dialogs. If movie details is triggered
    # from within the AI Concierge dialog, show_ai_dialog is temporarily cleared and show_movie_details
    # is set to True. Dismissing the movie details dialog cleanly returns to the AI Concierge.
    if st.session_state.get("show_movie_details", False) and st.session_state.get("selected_movie_data"):
        show_movie_details_dialog(st.session_state["selected_movie_data"], user_id)
    elif st.session_state.get("show_ai_dialog", False):
        if render_assistant_dialog:
            render_assistant_dialog(account_key=user_id)

    # -------------------------------------------------------------------------
    # 4. View Routing
    # -------------------------------------------------------------------------
    current_page = st.session_state["nav_selection"]

    if current_page == "Home":
        render_home_page(user_id=user_id)
    elif current_page in ["Explore", "Search"]:
        render_explore_page(user_id=user_id)
    elif current_page in ["Recommendations", "For You"]:
        render_recommendations_page(account_key=user_id)
    elif current_page in ["My Watchlist", "Watchlist"]:
        render_watchlist_page(account_key=user_id)
    elif current_page == "Liked Movies":
        render_liked_movies_page(account_key=user_id)
    elif current_page in ["Account", "Profile", "Login"]:
        render_account_page(current_user_id=user_id)
    elif current_page == "Monitoring":
        render_monitoring_page()
    elif current_page == "About":
        render_about_page()
    elif current_page == "AI Concierge":
        if render_assistant_page:
            render_assistant_page(account_key=user_id)
        elif render_assistant_dialog:
            render_assistant_dialog(account_key=user_id)
    else:
        render_home_page(user_id=user_id)


if __name__ == "__main__":
    main()
