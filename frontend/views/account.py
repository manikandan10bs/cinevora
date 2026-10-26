"""
Cinevora User Account & Authentication View
Provides:
- Secure login and registration powered by FastAPI / SQLite PBKDF2 hashing
- Persistent demo account: test_id_1 / test123
- Profile dashboard: User details, liked movies, watchlist, viewing history, taste breakdown
- Real-time session state management with isolation per user
"""

import html
from typing import Dict, Any, Optional
import streamlit as st

from frontend.api_client import api_client
from frontend.components import render_header, render_metric_card, render_empty_state, render_movie_card
from frontend.config import DEMO_ACCOUNTS


def render_account_page(current_user_id: str):
    """Renders the User Account / Login & Profile management page."""
    render_header("User Account & Profile")

    # Check if user is logged in
    is_authenticated = st.session_state.get("is_authenticated", True)
    active_user = st.session_state.get("active_account", current_user_id)
    profile_data = st.session_state.get("user_profile_data")

    if not profile_data:
        # Fetch profile from backend or use fallback
        backend_profile = api_client.get_user_profile(active_user)
        if backend_profile:
            st.session_state["user_profile_data"] = backend_profile
            profile_data = backend_profile
        else:
            profile_data = {
                "username": active_user,
                "display_name": "Test Member" if active_user == "test_id_1" else active_user,
                "created_at": "2026-10-24"
            }
            st.session_state["user_profile_data"] = profile_data

    # Layout: Profile View or Login/Register
    if is_authenticated:
        _render_authenticated_profile(active_user, profile_data)
    else:
        _render_login_register_form()


def _render_authenticated_profile(username: str, profile_data: Dict[str, Any]):
    """Renders the detailed user profile dashboard when logged in."""
    display_name = profile_data.get("display_name") or username

    # Header Card with Avatar and Logout
    c_prof1, c_prof2 = st.columns([4, 1.2])
    with c_prof1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #0E1622 0%, #131B26 100%);
                border: 1px solid rgba(0, 229, 255, 0.3);
                border-radius: 14px;
                padding: 22px 26px;
                display: flex;
                align-items: center;
                gap: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                margin-bottom: 24px;
            ">
                <div style="
                    width: 64px;
                    height: 64px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #00E5FF, #0284C7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.8rem;
                    font-weight: 800;
                    color: #06090E;
                    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
                ">
                    {display_name[:1].upper()}
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.45rem; font-weight: 800; color: #FFFFFF; font-family: 'Cinzel', serif;">
                            {html.escape(display_name)}
                        </span>
                        <span style="
                            background: rgba(0, 229, 255, 0.15);
                            border: 1px solid rgba(0, 229, 255, 0.4);
                            color: #00E5FF;
                            font-size: 0.72rem;
                            font-weight: 700;
                            padding: 2px 8px;
                            border-radius: 12px;
                            text-transform: uppercase;
                        ">Verified Member</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">
                        Username: <code style="color: #00E5FF; background: rgba(0, 229, 255, 0.08); padding: 2px 6px; border-radius: 4px;">{html.escape(username)}</code>
                        &nbsp;•&nbsp; Member since: {profile_data.get('created_at', '2026')[:10]}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c_prof2:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Log Out", key="account_logout_btn", use_container_width=True):
            st.session_state["is_authenticated"] = False
            st.session_state["active_account"] = "guest_user"
            st.session_state["user_profile_data"] = None
            st.toast("Logged out successfully.", icon="👋")
            st.rerun()

        with st.popover("🔄 Switch Persona", use_container_width=True):
            st.markdown("##### Quick Persona Switcher")
            for acc_key, info in DEMO_ACCOUNTS.items():
                if st.button(f"{info['avatar']} {info['label'].split('—')[0].strip()}", key=f"switch_to_{acc_key}", use_container_width=True):
                    st.session_state["active_account"] = acc_key
                    st.session_state["is_authenticated"] = (acc_key != "guest_user")
                    st.session_state["user_profile_data"] = None
                    st.toast(f"Switched persona to {acc_key}", icon="👤")
                    st.rerun()

    # Metrics Row: Liked, Watchlist, Views, Search
    likes = api_client.get_likes(username)
    favs = api_client.get_favorites(username)
    views = api_client.get_view_history(username, limit=100)
    searches = api_client.get_search_history(username, limit=50)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Liked Movies", len(likes), "Saved in profile", border_color="#E50914")
    with m2:
        render_metric_card("Watchlist Items", len(favs), "Queue to watch", border_color="#00E5FF")
    with m3:
        render_metric_card("Movies Viewed", len(views), "Details opened", border_color="#FFB800")
    with m4:
        render_metric_card("Searches Made", len(searches), "Exploration queries", border_color="#10B981")

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # Taste Breakdown Section
    st.markdown(
        """
        <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px;">
            📊 Personalized Taste Profile Breakdown
        </div>
        """,
        unsafe_allow_html=True
    )

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        # Genre frequency from interactions
        genre_counts: Dict[str, int] = {}
        for f in favs:
            for g in str(f.get("genres", "")).split(","):
                gc = g.strip()
                if gc and gc != "Cinema":
                    genre_counts[gc] = genre_counts.get(gc, 0) + 2
        for v in views:
            for g in str(v.get("genres", "")).split(","):
                gc = g.strip()
                if gc and gc != "Cinema":
                    genre_counts[gc] = genre_counts.get(gc, 0) + 1

        st.markdown("**Top Interacted Genres:**")
        if genre_counts:
            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for g_name, count in sorted_genres:
                pct = min(100, int((count / max(1, sum(genre_counts.values()))) * 100 * 2.5))
                st.markdown(
                    f"""
                    <div style="margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 3px; color: #CBD5E1;">
                            <span>{html.escape(g_name)}</span>
                            <span style="color: #00E5FF; font-weight: 700;">{count} interactions</span>
                        </div>
                        <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #00E5FF, #0284C7); border-radius: 4px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Start liking movies or opening details to see your genre preference distribution.")

    with t_col2:
        # Industry preference
        ind_counts: Dict[str, int] = {}
        for v in views:
            ind = v.get("industry")
            if ind and ind != "Cinema":
                ind_counts[ind] = ind_counts.get(ind, 0) + 1
        for f in favs:
            # We can infer or check
            ind_counts["Cinema"] = ind_counts.get("Cinema", 0) + 1

        st.markdown("**Film Industry Affinity:**")
        if ind_counts and any(k != "Cinema" for k in ind_counts):
            for ind_name, count in sorted(ind_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                if ind_name == "Cinema":
                    continue
                st.markdown(f"- **{ind_name}:** {count} views/saves")
        else:
            st.markdown(
                """
                <div style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6;">
                    Cinevora grounds your recommendations across:
                    <ul style="margin-top: 4px; padding-left: 18px;">
                        <li><strong style="color: #FFFFFF;">Indian Cinema:</strong> Bollywood, Tamil, Telugu, Malayalam, Kannada</li>
                        <li><strong style="color: #FFFFFF;">Hollywood:</strong> Blockbusters, Sci-Fi, Classics</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # Viewing History Section
    vh_head1, vh_head2 = st.columns([4, 1])
    with vh_head1:
        st.markdown(
            """
            <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF;">
                👁️ Recently Viewed & Opened Movies
            </div>
            """,
            unsafe_allow_html=True
        )
    with vh_head2:
        if views and st.button("🗑️ Clear History", key="clear_view_history_btn", use_container_width=True):
            api_client.clear_view_history(username)
            st.toast("Cleared viewing history", icon="🗑️")
            st.rerun()

    if views:
        for item in views[:8]:
            m_title = item.get("movie_title") or f"Movie #{item.get('movie_id')}"
            m_genres = item.get("genres") or "Cinema"
            m_time = item.get("viewed_at", "")[:19].replace("T", " ")
            m_ind = item.get("industry") or "Catalog"
            st.markdown(
                f"""
                <div style="
                    background: #111A24;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 8px;
                    padding: 10px 16px;
                    margin-bottom: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <span style="font-weight: 700; color: #F8FAFC;">{html.escape(m_title)}</span>
                        <span style="font-size: 0.78rem; color: #94A3B8; margin-left: 8px;">({html.escape(m_ind)} • {html.escape(m_genres)})</span>
                    </div>
                    <div style="font-size: 0.74rem; color: #64748B;">
                        {html.escape(m_time)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        render_empty_state("No Viewed Movies Yet", "Click 'Details' on any movie card or hero banner to record it here.", icon="👁️")


def _render_login_register_form():
    """Renders the Login and Registration tabs for switching or authenticating accounts."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-family: 'Cinzel', serif; font-size: 1.8rem; font-weight: 800; color: #FFFFFF;">
                Sign In to Cinevora
            </div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                Access your personalized movie stream, synced watchlist, and ratings
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    form_col, _ = st.columns([2, 1])
    with form_col:
        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with tab_login:
            # Quick Demo Login Shortcut
            st.info("💡 **Persistent Demo Account Available:** You can sign in immediately using `test_id_1` / `test123`.")
            if st.button("⚡ Fill Demo Credentials (test_id_1 / test123)", key="fill_demo_btn", use_container_width=True):
                st.session_state["login_user_input"] = "test_id_1"
                st.session_state["login_pass_input"] = "test123"
                st.rerun()

            with st.form("login_form"):
                u_in = st.text_input(
                    "Username",
                    value=st.session_state.get("login_user_input", "test_id_1"),
                    placeholder="Enter your username",
                    key="login_user_box"
                )
                p_in = st.text_input(
                    "Password",
                    value=st.session_state.get("login_pass_input", "test123"),
                    type="password",
                    placeholder="Enter your password",
                    key="login_pass_box"
                )
                submit_login = st.form_submit_button("Sign In 🎬", type="primary", use_container_width=True)

                if submit_login:
                    if not u_in.strip() or not p_in.strip():
                        st.error("Please enter both username and password.")
                    else:
                        res = api_client.login(username=u_in.strip(), password=p_in.strip())
                        if res and res.get("status") == "success":
                            st.session_state["is_authenticated"] = True
                            st.session_state["active_account"] = res.get("username", u_in.strip())
                            st.session_state["user_profile_data"] = res
                            st.toast(f"Welcome back, {res.get('display_name', u_in.strip())}!", icon="🎉")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Check your credentials and try again.")

        with tab_register:
            with st.form("register_form"):
                reg_u = st.text_input("New Username", placeholder="e.g. cinema_lover_42")
                reg_p = st.text_input("Password", type="password", placeholder="Choose a secure password")
                reg_d = st.text_input("Display Name", placeholder="e.g. Cinema Explorer")
                submit_reg = st.form_submit_button("Create Account 🚀", type="primary", use_container_width=True)

                if submit_reg:
                    if not reg_u.strip() or not reg_p.strip():
                        st.error("Username and password are required.")
                    else:
                        res = api_client.register(
                            username=reg_u.strip(),
                            password=reg_p.strip(),
                            display_name=reg_d.strip() or None
                        )
                        if res and res.get("status") == "success":
                            st.session_state["is_authenticated"] = True
                            st.session_state["active_account"] = res.get("username", reg_u.strip())
                            st.session_state["user_profile_data"] = res
                            st.success("Account created successfully! You are now logged in.")
                            st.rerun()
                        else:
                            st.error("Registration failed. The username may already be taken.")
