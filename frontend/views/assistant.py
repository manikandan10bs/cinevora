"""
Cinevora AI Movie Concierge View (Modern Streaming Chatbot Edition)
Provides an intelligent conversational cinema assistant powered by Google Gemini (gemini-3.5-flash-lite).
All recommendations are strictly grounded against Cinevora's 3,560-title Master Catalog
(Bollywood, Kollywood, Tollywood, Mollywood, Sandalwood, and Hollywood).

Features:
- Chatbot Header with glowing avatar, real-time Gemini connectivity indicator, and catalog count pill
- Quick Suggestion Chips categorized by mood, industry, director, and genre
- HTML5 Web Speech API Voice Dictation button
- Streamlit native chat messages with custom streaming aesthetics
- Interactive movie recommendation cards with poster artwork, ratings, like, watchlist, and details
- Follow-up query suggestion chips for continuous conversational exploration
- Graceful error handling and instant retry actions
"""

from typing import Dict, Any, List, Optional, Union
import html
import re
import streamlit as st
import streamlit.components.v1 as components

from frontend.api_client import api_client
from frontend.components import render_header, render_movie_card, render_empty_state
from frontend.config import DEMO_ACCOUNTS


def _render_voice_dictation_widget():
    """
    Renders an HTML5 Web Speech API voice dictation button.
    Only triggers microphone listening when the user explicitly clicks the button.
    """
    voice_html = """
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(0,229,255,0.18); border-radius: 12px; padding: 10px 16px; margin: 8px 0 14px 0; display: flex; align-items: center; justify-content: space-between; font-family: 'Inter', sans-serif;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <button id="micBtn" onclick="toggleDictation()" style="background: linear-gradient(135deg, #00E5FF, #0077B6); color: #06090E; border: none; border-radius: 20px; padding: 6px 14px; font-weight: 700; font-size: 0.82rem; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 8px rgba(0,229,255,0.3); transition: all 0.2s ease;">
                <span id="micIcon">🎤</span> <span id="micText">Voice Input</span>
            </button>
            <span id="speechStatus" style="font-size: 0.82rem; color: #94A3B8;">Click to speak your movie request...</span>
        </div>
        <div id="transcriptWrap" style="display: none; align-items: center; gap: 8px;">
            <span id="transcriptText" style="font-size: 0.84rem; font-weight: 600; color: #00E5FF; max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"></span>
            <button onclick="copyTranscript()" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; padding: 4px 8px; font-size: 0.75rem; cursor: pointer; color: #FFFFFF;">📋 Copy</button>
        </div>
    </div>

    <script>
    let recognition = null;
    let isListening = false;

    function toggleDictation() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            document.getElementById('speechStatus').innerText = "Web Speech API not supported in this browser. Please type below.";
            return;
        }

        if (!recognition) {
            recognition = new SpeechRec();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = function() {
                isListening = true;
                document.getElementById('micBtn').style.background = "#E50914";
                document.getElementById('micBtn').style.color = "#FFFFFF";
                document.getElementById('micText').innerText = "Listening...";
                document.getElementById('speechStatus').innerText = "Listening now — speak your movie request...";
            };

            recognition.onresult = function(event) {
                const text = event.results[0][0].transcript;
                document.getElementById('speechStatus').innerText = "Heard clearly!";
                document.getElementById('transcriptWrap').style.display = "inline-flex";
                document.getElementById('transcriptText').innerText = '"' + text + '"';
                window.lastTranscript = text;
                navigator.clipboard.writeText(text).catch(function(){});
            };

            recognition.onerror = function(event) {
                isListening = false;
                document.getElementById('micBtn').style.background = "linear-gradient(135deg, #00E5FF, #0077B6)";
                document.getElementById('micBtn').style.color = "#06090E";
                document.getElementById('micText').innerText = "Voice Input";
                document.getElementById('speechStatus').innerText = "Speech recognition error: " + event.error;
            };

            recognition.onend = function() {
                isListening = false;
                document.getElementById('micBtn').style.background = "linear-gradient(135deg, #00E5FF, #0077B6)";
                document.getElementById('micBtn').style.color = "#06090E";
                document.getElementById('micText').innerText = "Voice Input";
            };
        }

        if (!isListening) {
            try {
                recognition.start();
            } catch (err) {
                console.error(err);
            }
        } else {
            recognition.stop();
        }
    }

    function copyTranscript() {
        if (window.lastTranscript) {
            navigator.clipboard.writeText(window.lastTranscript).then(function() {
                alert("Copied to clipboard: " + window.lastTranscript + "\\nPaste into the chat box below!");
            });
        }
    }
    </script>
    """
    components.html(voice_html, height=58)


def _render_chatbot_header(status_info: Optional[Dict[str, Any]], in_dialog: bool):
    """Renders the sleek streaming chatbot header bar with real-time indicators and controls."""
    is_verified = bool(status_info and status_info.get("verified", False))
    status_state = status_info.get("status_state", "configuration_missing") if status_info else "disconnected"
    model_name = status_info.get("model", "gemini-3.5-flash-lite") if status_info else "gemini-3.5-flash-lite"
    catalog_count = status_info.get("master_catalog_count", 3560) if status_info else 3560

    if is_verified or status_state == "connected":
        status_badge_html = f'<span class="chat-status-pill"><span class="chat-pulse-dot"></span> ✨ {html.escape(model_name)} Active</span>'
    elif status_state == "quota_or_network_error":
        status_badge_html = '<span class="chat-status-pill" style="color: #FFB800; border-color: rgba(255,184,0,0.4); background: rgba(255,184,0,0.1);"><span class="chat-pulse-dot" style="background: #FFB800; box-shadow: 0 0 8px #FFB800;"></span> ⏳ Quota Limit — Catalog Mode</span>'
    else:
        status_badge_html = '<span class="chat-status-pill" style="color: #FFB800; border-color: rgba(255,184,0,0.4); background: rgba(255,184,0,0.1);"><span class="chat-pulse-dot" style="background: #FFB800; box-shadow: 0 0 8px #FFB800;"></span> 🍿 Catalog Grounded Mode</span>'

    header_html = f"""
    <div class="chat-header-card">
        <div class="chat-bot-brand">
            <div class="chat-avatar-glow">✨</div>
            <div class="chat-bot-title-box">
                <div class="chat-bot-title">
                    Cinevora AI Concierge
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #00E5FF; box-shadow: 0 0 8px #00E5FF;"></span>
                </div>
                <div class="chat-bot-subtitle">Personalized Cinema Curator • Grounded in 3,560 Verified Master Catalog Titles</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            {status_badge_html}
            <span class="chat-catalog-count-pill">📚 {catalog_count:,} Movies</span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def _render_assistant_message(msg: Dict[str, Any], idx: int, account_key: str, in_dialog: bool):
    """Renders a single message from the chat history with appropriate styling and cards."""
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    recs = msg.get("recommendations", [])
    constraints = msg.get("constraints", {})
    source = msg.get("source", "catalog")
    is_error = msg.get("error", False)
    failed_query = msg.get("failed_query")

    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<div style="font-size: 0.94rem; color: #FFFFFF; font-weight: 500;">{html.escape(content)}</div>', unsafe_allow_html=True)
    elif is_error:
        with st.chat_message("assistant", avatar="⚠️"):
            st.error(content)
            if failed_query:
                retry_key = f"retry_btn_{idx}_{in_dialog}"
                if st.button(f"🔄 Retry: \"{failed_query[:40]}\"", key=retry_key, type="secondary"):
                    st.session_state["assistant_retry_query"] = failed_query
                    st.rerun()
    else:
        with st.chat_message("assistant", avatar="✨"):
            # Badges row for detected constraints & model
            detected_badges = []
            if constraints.get("actor"):
                detected_badges.append(
                    f'<span style="background: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 700;">'
                    f'⭐ Star: {html.escape(str(constraints["actor"]))}</span>'
                )
            if constraints.get("director"):
                detected_badges.append(
                    f'<span style="background: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 700;">'
                    f'🎬 Director: {html.escape(str(constraints["director"]))}</span>'
                )
            if constraints.get("genre"):
                detected_badges.append(
                    f'<span style="background: rgba(255, 255, 255, 0.08); color: #CBD5E1; border: 1px solid rgba(255, 255, 255, 0.16); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 600;">'
                    f'🎭 Genre: {html.escape(str(constraints["genre"]))}</span>'
                )
            if constraints.get("industry") or constraints.get("region"):
                ind = constraints.get("industry") or constraints.get("region")
                detected_badges.append(
                    f'<span style="background: rgba(255, 255, 255, 0.08); color: #CBD5E1; border: 1px solid rgba(255, 255, 255, 0.16); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 600;">'
                    f'🌍 Industry: {html.escape(str(ind))}</span>'
                )
            if constraints.get("decade"):
                detected_badges.append(
                    f'<span style="background: rgba(255, 255, 255, 0.08); color: #CBD5E1; border: 1px solid rgba(255, 255, 255, 0.16); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 600;">'
                    f'📅 Period: {html.escape(str(constraints["decade"]))}</span>'
                )

            if source in ["gemini", "gemini_flash"]:
                detected_badges.append(
                    '<span style="background: rgba(0, 229, 255, 0.18); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.45); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 800;">'
                    '✨ Gemini 3.5 Flash Lite</span>'
                )
            elif source == "greeting":
                pass
            else:
                detected_badges.append(
                    '<span style="background: rgba(255, 184, 0, 0.15); color: #FFB800; border: 1px solid rgba(255, 184, 0, 0.4); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 800;">'
                    '🍿 Master Catalog Grounded</span>'
                )

            if detected_badges:
                st.markdown(
                    f'<div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">{"".join(detected_badges)}</div>',
                    unsafe_allow_html=True
                )

            # Markdown Content from Assistant
            st.markdown(content)

            # Grounded Catalog Movie Recommendations
            if recs:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 18px; margin-bottom: 12px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px;">
                        <span style="font-family: 'Cinzel', serif; font-size: 1.05rem; font-weight: 700; color: #FFFFFF;">
                            🍿 Verified Catalog Recommendations ({len(recs)})
                        </span>
                        <span style="font-size: 0.74rem; color: #00E5FF; font-weight: 700;">Click ℹ️ for details & trailer</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                num_cols = min(len(recs), 3)
                rec_cols = st.columns(num_cols)
                for r_idx, rec in enumerate(recs):
                    with rec_cols[r_idx % num_cols]:
                        render_movie_card(
                            movie=rec,
                            user_id=account_key,
                            key_prefix=f"chat_card_{in_dialog}_{idx}_{r_idx}",
                            show_score=True,
                            in_dialog=in_dialog
                        )


def render_assistant_chat_interface(account_key: str, in_dialog: bool = False):
    """
    Renders the modern AI Movie Concierge chatbot interface.
    Features:
    - Chatbot Header with real-time backend status and clear controls
    - Quick Suggestion Chips categorized by mood, region, and star
    - Web Speech API Voice Dictation integration
    - Streamlit native chat messages with streaming dark aesthetics
    - Grounded movie cards with rating stars, Like, Watchlist, and Trailer/Details
    - Bottom chat input dock that handles submissions smoothly
    """
    if not in_dialog:
        render_header("AI Movie Concierge — Powered by Gemini 3.5 Flash Lite")

    # 1. Dialog Header Bar & Controls
    status_info = api_client.get_assistant_status()

    # Render Modern Chatbot Header Bar
    _render_chatbot_header(status_info=status_info, in_dialog=in_dialog)

    # 2. Action Controls Row: Clear Chat & Dialog Close
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([4, 1.2, 1.2] if in_dialog else [5, 1.3, 0.1])
    with ctrl_col1:
        st.markdown(
            '<div style="font-size: 0.8rem; color: #64748B; font-weight: 600; padding-top: 4px;">'
            'Ask in natural language for movies, actors, directors, genres, decades, or themes.'
            '</div>',
            unsafe_allow_html=True
        )
    with ctrl_col2:
        if st.button("🧹 Clear Chat", key=f"asst_clear_{in_dialog}", use_container_width=True):
            st.session_state["assistant_chat_history"] = []
            st.rerun()
    if in_dialog:
        with ctrl_col3:
            if st.button("✕ Close", key=f"asst_close_dialog_{in_dialog}", use_container_width=True):
                st.session_state["show_ai_dialog"] = False
                st.rerun()

    # 3. Chat History State Initialization
    if "assistant_chat_history" not in st.session_state or not st.session_state["assistant_chat_history"]:
        st.session_state["assistant_chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "👋 **Welcome to Cinevora AI Concierge!**\n\n"
                    "I am your personal cinema curator powered by **Google Gemini 3.5 Flash Lite**, "
                    "strictly grounded in our **3,560-title master catalog** across Bollywood, Tamil, Telugu, "
                    "Malayalam, Kannada, and Hollywood.\n\n"
                    "What kind of movie are you looking to watch tonight? Pick a prompt below or type your taste!"
                ),
                "recommendations": [],
                "source": "greeting",
                "constraints": {}
            }
        ]

    # 4. Web Speech API Voice Dictation Widget
    _render_voice_dictation_widget()

    # 5. Quick Suggestion Chips (Prompt Starters)
    st.markdown(
        """
        <div style="font-size: 0.82rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
            💡 Quick Cinema Prompts
        </div>
        """,
        unsafe_allow_html=True
    )

    preset_prompts = [
        ("🎬 Best Tamil Masterpieces", "What is the best Tamil movie?"),
        ("🔥 High-Stakes Action", "Recommend exciting Tamil and Bollywood action thrillers"),
        ("🚀 Nolan Sci-Fi", "Christopher Nolan sci-fi movies"),
        ("🍿 Vijay Hits", "Show me movies acted by Vijay"),
        ("😂 Heartwarming Comedy", "I want to watch something funny"),
        ("❤️ Bollywood Romance", "suggest a romantic Bollywood film"),
    ]

    selected_prompt = None
    chip_cols = st.columns(len(preset_prompts))
    for idx, (p_col, (label, query)) in enumerate(zip(chip_cols, preset_prompts)):
        with p_col:
            if st.button(label, key=f"chip_prompt_{in_dialog}_{idx}", use_container_width=True):
                selected_prompt = query

    st.write("")

    # 6. Render Message Thread
    for idx, msg in enumerate(st.session_state["assistant_chat_history"]):
        _render_assistant_message(msg=msg, idx=idx, account_key=account_key, in_dialog=in_dialog)

    # 7. Check for Pending Retry Query or Quick Prompt
    retry_query = st.session_state.pop("assistant_retry_query", None)
    active_input = retry_query or selected_prompt

    # 8. Render Input Area (Chat Dock)
    if not active_input:
        if not in_dialog and hasattr(st, "chat_input"):
            # On standalone page, use native sticky bottom chat_input
            typed_chat = st.chat_input("Ask Cinevora AI... (e.g. 'Best Tamil action films' or 'Sci-Fi directed by Nolan')")
            if typed_chat and typed_chat.strip():
                active_input = typed_chat.strip()
        else:
            # Inside dialog or fallback: streamlined input form with Enter key submission
            with st.form(f"assistant_input_form_{in_dialog}", clear_on_submit=True):
                in_col1, in_col2 = st.columns([5, 1.2])
                with in_col1:
                    typed_query = st.text_input(
                        "Ask Cinevora AI",
                        placeholder="e.g. 'What is the best Tamil movie?' or 'Recommend Nolan sci-fi'...",
                        label_visibility="collapsed",
                        key=f"typed_chat_input_{in_dialog}"
                    )
                with in_col2:
                    send_clicked = st.form_submit_button("Send 🚀", type="primary", use_container_width=True)

                if send_clicked and typed_query and typed_query.strip():
                    active_input = typed_query.strip()

    # 9. Execute Query when Active Input is Present
    if active_input:
        # Prevent rapid duplicate submissions
        last_msg = st.session_state["assistant_chat_history"][-1] if st.session_state["assistant_chat_history"] else None
        is_duplicate = bool(last_msg and last_msg.get("role") == "user" and last_msg.get("content") == active_input)

        if not is_duplicate:
            # Append User Message to History
            st.session_state["assistant_chat_history"].append({
                "role": "user",
                "content": active_input
            })

            # Render user message immediately
            with st.chat_message("user", avatar="👤"):
                st.markdown(f'<div style="font-size: 0.94rem; color: #FFFFFF; font-weight: 500;">{html.escape(active_input)}</div>', unsafe_allow_html=True)

            # Query Backend API with visible loading spinner
            with st.chat_message("assistant", avatar="✨"):
                with st.spinner("✨ Cinevora AI is consulting the 3,560-title catalog & Gemini 3.5 Flash Lite..."):
                    response = api_client.chat_assistant(
                        message=active_input,
                        user_id=account_key,
                        limit=3
                    )

                if response and response.get("success", True):
                    reply = response.get("reply", "Here are movie recommendations grounded in our master catalog.")
                    recs = response.get("recommendations", [])
                    source = response.get("assistant_mode") or response.get("source", "catalog_fallback")
                    meta = response.get("metadata", {})
                    constraints = {
                        "actor": response.get("detected_actor") or meta.get("detected_actor"),
                        "director": response.get("detected_director") or meta.get("detected_director"),
                        "genre": response.get("detected_genre") or meta.get("detected_genre"),
                        "industry": response.get("detected_region") or meta.get("detected_industry"),
                        "region": response.get("detected_region") or meta.get("detected_region"),
                        "decade": response.get("detected_decade") or meta.get("detected_decade"),
                        "start_year": meta.get("detected_start_year"),
                        "end_year": meta.get("detected_end_year")
                    }

                    new_msg = {
                        "role": "assistant",
                        "content": reply,
                        "recommendations": recs,
                        "source": source,
                        "constraints": constraints,
                        "error": False
                    }
                    st.session_state["assistant_chat_history"].append(new_msg)

                    # Render badges, reply text, and recommendations immediately
                    detected_badges = []
                    if constraints.get("actor"):
                        detected_badges.append(
                            f'<span style="background: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 700;">'
                            f'⭐ Star: {html.escape(str(constraints["actor"]))}</span>'
                        )
                    if constraints.get("director"):
                        detected_badges.append(
                            f'<span style="background: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 700;">'
                            f'🎬 Director: {html.escape(str(constraints["director"]))}</span>'
                        )
                    if constraints.get("genre"):
                        detected_badges.append(
                            f'<span style="background: rgba(255, 255, 255, 0.08); color: #CBD5E1; border: 1px solid rgba(255, 255, 255, 0.16); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 600;">'
                            f'🎭 Genre: {html.escape(str(constraints["genre"]))}</span>'
                        )
                    if constraints.get("industry") or constraints.get("region"):
                        ind = constraints.get("industry") or constraints.get("region")
                        detected_badges.append(
                            f'<span style="background: rgba(255, 255, 255, 0.08); color: #CBD5E1; border: 1px solid rgba(255, 255, 255, 0.16); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 600;">'
                            f'🌍 Industry: {html.escape(str(ind))}</span>'
                        )
                    if source in ["gemini", "gemini_flash"]:
                        detected_badges.append(
                            '<span style="background: rgba(0, 229, 255, 0.18); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.45); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 800;">'
                            '✨ Gemini 3.5 Flash Lite</span>'
                        )
                    else:
                        detected_badges.append(
                            '<span style="background: rgba(255, 184, 0, 0.15); color: #FFB800; border: 1px solid rgba(255, 184, 0, 0.4); padding: 3px 10px; border-radius: 12px; font-size: 0.74rem; font-weight: 800;">'
                            '🍿 Master Catalog Grounded</span>'
                        )

                    if detected_badges:
                        st.markdown(
                            f'<div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">{"".join(detected_badges)}</div>',
                            unsafe_allow_html=True
                        )

                    st.markdown(reply)

                    if recs:
                        st.markdown(
                            f"""
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 18px; margin-bottom: 12px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px;">
                                <span style="font-family: 'Cinzel', serif; font-size: 1.05rem; font-weight: 700; color: #FFFFFF;">
                                    🍿 Verified Catalog Recommendations ({len(recs)})
                                </span>
                                <span style="font-size: 0.74rem; color: #00E5FF; font-weight: 700;">Click ℹ️ for details & trailer</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        num_cols = min(len(recs), 3)
                        rec_cols = st.columns(num_cols)
                        for r_idx, rec in enumerate(recs):
                            with rec_cols[r_idx % num_cols]:
                                render_movie_card(
                                    movie=rec,
                                    user_id=account_key,
                                    key_prefix=f"live_card_{in_dialog}_{r_idx}",
                                    show_score=True,
                                    in_dialog=in_dialog
                                )
                else:
                    err_msg = (
                        response.get("error_detail")
                        if response
                        else "Unable to connect to the Cinevora recommendation service. Please ensure the backend is running."
                    )
                    error_entry = {
                        "role": "assistant",
                        "content": f"⚠️ **Connection Notice:** {err_msg}",
                        "recommendations": [],
                        "source": "error",
                        "error": True,
                        "failed_query": active_input,
                        "constraints": {}
                    }
                    st.session_state["assistant_chat_history"].append(error_entry)
                    st.error(f"⚠️ {err_msg}")
                    if st.button("🔄 Retry Query", key=f"immediate_retry_{in_dialog}"):
                        st.session_state["assistant_retry_query"] = active_input
                        st.rerun()


def _on_ai_dialog_dismiss():
    """Callback triggered by Streamlit when the user closes the modal dialog."""
    st.session_state["show_ai_dialog"] = False


if hasattr(st, "dialog"):
    @st.dialog("🎬 Cinevora AI Movie Concierge", width="large", on_dismiss=_on_ai_dialog_dismiss)
    def render_assistant_dialog(account_key: str):
        """Renders the modal AI Movie Concierge dialog on top of the current view."""
        render_assistant_chat_interface(account_key=account_key, in_dialog=True)
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("🎬 Cinevora AI Movie Concierge", width="large", on_dismiss=_on_ai_dialog_dismiss)
    def render_assistant_dialog(account_key: str):
        """Renders the modal AI Movie Concierge dialog on top of the current view."""
        render_assistant_chat_interface(account_key=account_key, in_dialog=True)
else:
    def render_assistant_dialog(account_key: str):
        """Fallback when st.dialog is not supported."""
        with st.expander("🎬 Cinevora AI Movie Concierge", expanded=True):
            render_assistant_chat_interface(account_key=account_key, in_dialog=True)


def render_assistant_page(account_key: str):
    """Renders the standalone AI Concierge page."""
    render_assistant_chat_interface(account_key=account_key, in_dialog=False)


__all__ = [
    "render_assistant_chat_interface",
    "render_assistant_dialog",
    "render_assistant_page"
]
