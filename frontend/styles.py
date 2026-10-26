"""
Cinevora Cinematic Dark Streaming Theme CSS
Directly inspired by modern cinematic streaming platforms (Prime Video, Apple TV, Netflix):
- Background: Deep Dark Void (#090D14 / #0B1118)
- Left Vertical Icon Rail: Slim, fixed (#06090E) with bright cyan (#00E5FF) active indicators
- High-contrast typography: Pure White (#F8FAFC) & Slate (#94A3B8)
- Hero section: Edge-to-edge landscape backdrop with smooth gradient masking and stylized titles
- Top 10 Ranking row: Huge translucent ranking numbers behind cards (1, 2, 3, 4, ...)
- Consistent 2:3 portrait cards with object-fit: cover and zero distortion
- Gold rating stars (★★★★★ #FFB800) and electric cyan/red accents
- Floating AI Movie Concierge trigger in bottom-right corner
- Fully responsive across desktop, tablet, and mobile
"""

import streamlit as st

CINEMA_DARK_CSS = """
<style>
/* -------------------------------------------------------------------------
   Google Fonts Import
   ------------------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* -------------------------------------------------------------------------
   Global Variables & Palette (Cinematic Dark Streaming Theme)
   ------------------------------------------------------------------------- */
:root {
    --bg-app: #090D14;
    --bg-surface: #0E1622;
    --bg-card: #131B26;
    --bg-card-hover: #1A2536;
    --bg-rail: #06090E;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(0, 229, 255, 0.4);
    --accent-cyan: #00E5FF;
    --accent-cyan-glow: rgba(0, 229, 255, 0.25);
    --accent-red: #E50914;
    --accent-red-hover: #DC2626;
    --accent-gold: #FFB800;
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --card-radius: 10px;
    --card-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    --card-shadow-hover: 0 14px 32px rgba(0, 0, 0, 0.7), 0 0 20px rgba(0, 229, 255, 0.2);
}

/* -------------------------------------------------------------------------
   Global Page Settings
   ------------------------------------------------------------------------- */
.stApp {
    background-color: var(--bg-app) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Main Container: padded for left rail */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 5rem !important;
    padding-left: 2rem !important;
    padding-right: 2.5rem !important;
    max-width: 1560px !important;
}

/* -------------------------------------------------------------------------
   LEFT VERTICAL ICON NAVIGATION RAIL
   ------------------------------------------------------------------------- */
section[data-testid="stSidebar"] {
    width: 76px !important;
    min-width: 76px !important;
    max-width: 76px !important;
    background-color: var(--bg-rail) !important;
    border-right: 1px solid var(--border-subtle) !important;
    padding: 0 !important;
    z-index: 99999 !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] > div:first-child {
    width: 76px !important;
    padding: 18px 8px !important;
}

/* Hide default sidebar collapse arrow */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* Sidebar navigation buttons styling */
section[data-testid="stSidebar"] .stButton {
    margin-bottom: 6px !important;
    display: flex !important;
    justify-content: center !important;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 52px !important;
    height: 48px !important;
    min-height: 48px !important;
    padding: 0 !important;
    border-radius: 12px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--text-secondary) !important;
    font-size: 1.35rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    color: #FFFFFF !important;
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    transform: scale(1.06) !important;
}

section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    color: #FFFFFF !important;
    background: rgba(0, 229, 255, 0.16) !important;
    border: 1px solid rgba(0, 229, 255, 0.5) !important;
    box-shadow: 0 0 16px rgba(0, 229, 255, 0.35) !important;
}

/* Sidebar navigation buttons */
.nav-rail-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 58px;
    height: 52px;
    border-radius: 12px;
    margin: 6px auto;
    color: var(--text-secondary);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    text-decoration: none;
    position: relative;
}

.nav-rail-item:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.06);
    transform: scale(1.05);
}

.nav-rail-item.active {
    color: #FFFFFF;
    background: rgba(0, 229, 255, 0.12);
    border: 1px solid rgba(0, 229, 255, 0.4);
    box-shadow: 0 0 15px var(--accent-cyan-glow);
}

.nav-rail-icon {
    font-size: 1.35rem;
    line-height: 1;
}

.nav-rail-label {
    font-size: 0.62rem;
    font-weight: 700;
    margin-top: 3px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.9;
}

/* Rail User Avatar Circle */
.rail-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, #E50914, #B91C1C);
    border: 2px solid rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1rem;
    color: #FFFFFF;
    margin: 0 auto 18px auto;
    box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);
    cursor: pointer;
}

/* -------------------------------------------------------------------------
   CINEMATIC FULL-SCREEN HERO SECTION (Matching Reference Screenshot)
   ------------------------------------------------------------------------- */
.hero-streaming-container {
    position: relative;
    width: 100%;
    min-height: 460px;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 28px;
    background-color: #070B10;
    border: 1px solid var(--border-subtle);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
}

.hero-backdrop-img {
    position: absolute;
    top: 0;
    right: 0;
    width: 70%;
    height: 100%;
    object-fit: cover;
    object-position: center top;
    z-index: 1;
    mask-image: linear-gradient(to right, transparent 0%, rgba(0,0,0,0.6) 25%, rgba(0,0,0,1) 60%),
                linear-gradient(to bottom, rgba(0,0,0,1) 75%, transparent 100%);
    -webkit-mask-image: linear-gradient(to right, transparent 0%, rgba(0,0,0,0.6) 20%, rgba(0,0,0,1) 55%),
                        linear-gradient(to bottom, rgba(0,0,0,1) 75%, transparent 100%);
}

.hero-content-overlay {
    position: relative;
    z-index: 2;
    padding: 36px 42px;
    max-width: 580px;
    background: linear-gradient(to right, rgba(9, 13, 20, 0.98) 45%, rgba(9, 13, 20, 0.82) 75%, transparent 100%);
    min-height: 460px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.hero-rank-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--accent-cyan);
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.hero-brand-subtitle {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    color: #94A3B8;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.hero-title-text {
    font-family: 'Cinzel', 'Inter', serif;
    font-size: 2.6rem;
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: 0.06em;
    color: #FFFFFF;
    text-transform: uppercase;
    text-shadow: 0 4px 16px rgba(0, 0, 0, 0.8);
    margin-bottom: 12px;
}

.hero-meta-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 0.84rem;
    color: #CBD5E1;
    margin-bottom: 12px;
}

.hero-stars {
    color: var(--accent-gold);
    letter-spacing: 2px;
    font-size: 0.96rem;
}

.hero-age-badge {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #F8FAFC;
}

.hero-synopsis-text {
    font-size: 0.90rem;
    line-height: 1.55;
    color: #94A3B8;
    margin-bottom: 18px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.hero-included-tag {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    color: var(--accent-cyan);
    font-weight: 700;
    margin-bottom: 18px;
}

/* -------------------------------------------------------------------------
   TOP 10 RANKING CAROUSEL WITH LARGE TRANSLUCENT NUMBERS
   ------------------------------------------------------------------------- */
.ranked-card-container {
    position: relative;
    display: flex;
    align-items: flex-end;
    margin-bottom: 12px;
    overflow: visible;
}

.ranked-card-number {
    font-family: 'Cinzel', 'Impact', sans-serif;
    font-size: 6.8rem;
    font-weight: 900;
    line-height: 0.8;
    color: rgba(255, 255, 255, 0.16);
    -webkit-text-stroke: 1.5px rgba(255, 255, 255, 0.38);
    position: absolute;
    left: -12px;
    bottom: 2px;
    z-index: 1;
    pointer-events: none;
    user-select: none;
}

.ranked-card-content {
    position: relative;
    z-index: 2;
    margin-left: 38px;
    width: calc(100% - 38px);
}

/* -------------------------------------------------------------------------
   MOVIE CARDS & CAROUSELS (Consistent 2:3 Aspect Ratio)
   ------------------------------------------------------------------------- */
.movie-card-dark {
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--card-radius);
    overflow: hidden;
    transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--card-shadow);
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    position: relative;
}

.movie-card-dark:hover {
    transform: translateY(-6px) scale(1.02);
    background-color: var(--bg-card-hover);
    border-color: var(--border-hover);
    box-shadow: var(--card-shadow-hover);
    z-index: 5;
}

/* Poster Container: strictly 2:3 portrait aspect ratio */
.poster-wrap-2-3 {
    position: relative;
    width: 100%;
    aspect-ratio: 2 / 3;
    overflow: hidden;
    background-color: #0E1622;
}

.poster-wrap-2-3 img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    transition: transform 0.35s ease;
    display: block;
}

.movie-card-dark:hover .poster-wrap-2-3 img {
    transform: scale(1.05);
}

.poster-fallback-dark {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(145deg, #131B26, #090D14);
    color: #64748B;
    text-align: center;
    padding: 16px;
}

/* Movie Card Body */
.movie-card-body-dark {
    padding: 12px 14px 10px 14px;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.movie-title-dark {
    font-size: 0.92rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.3;
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.movie-meta-dark {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin-bottom: 6px;
}

.movie-stars-dark {
    color: var(--accent-gold);
    font-size: 0.85rem;
    letter-spacing: 1px;
}

/* -------------------------------------------------------------------------
   STREAMING CAROUSEL HEADERS & NAVIGATION BUTTONS
   ------------------------------------------------------------------------- */
.carousel-header-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-top: 24px;
    margin-bottom: 12px;
}

.carousel-title-text {
    font-family: 'Inter', sans-serif;
    font-size: 1.28rem;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: 0.01em;
}

.carousel-title-cyan {
    color: var(--accent-cyan);
    font-weight: 800;
}

.carousel-subtitle-text {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-top: 2px;
}

/* -------------------------------------------------------------------------
   BADGES & CHIPS (Lite High-Contrast Colors on Dark)
   ------------------------------------------------------------------------- */
.badge-ind-dark {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #E2E8F0;
}

.badge-ind-dark.tamil { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.4); color: #FCA5A5; }
.badge-ind-dark.telugu { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.4); color: #FCD34D; }
.badge-ind-dark.bollywood { background: rgba(168, 85, 247, 0.15); border-color: rgba(168, 85, 247, 0.4); color: #D8B4FE; }
.badge-ind-dark.hollywood { background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.4); color: #93C5FD; }
.badge-ind-dark.malayalam { background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.4); color: #6EE7B7; }
.badge-ind-dark.kannada { background: rgba(236, 72, 153, 0.15); border-color: rgba(236, 72, 153, 0.4); color: #F472B6; }

/* -------------------------------------------------------------------------
   FLOATING AI CONCIERGE BUTTON (Bottom-Right)
   ------------------------------------------------------------------------- */
.floating-assistant-btn-wrap {
    position: fixed;
    bottom: 24px;
    right: 28px;
    z-index: 999999;
}

.floating-assistant-pill {
    background: linear-gradient(135deg, #00E5FF, #0091EA);
    color: #06090E !important;
    font-family: 'Inter', sans-serif;
    font-size: 0.90rem;
    font-weight: 800;
    padding: 10px 18px;
    border-radius: 30px;
    border: none;
    cursor: pointer;
    box-shadow: 0 6px 20px rgba(0, 229, 255, 0.45);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    transition: all 0.25s ease;
}

.floating-assistant-pill:hover {
    transform: translateY(-3px) scale(1.04);
    box-shadow: 0 10px 28px rgba(0, 229, 255, 0.65);
    color: #000000 !important;
}

/* -------------------------------------------------------------------------
   STREAMLIT BUTTON & INPUT OVERRIDES FOR CINEMATIC DARK THEME
   ------------------------------------------------------------------------- */
.stButton > button, div[data-testid="stLinkButton"] > a {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stLinkButton"] > a {
    background-color: #111A24 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #00E5FF !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.25rem 0.5rem !important;
    text-decoration: none !important;
    min-height: 38px !important;
}

div[data-testid="stLinkButton"] > a:hover {
    background-color: #1A2536 !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 10px rgba(0, 229, 255, 0.3) !important;
}

.stButton > button[kind="primary"], div[data-testid="stLinkButton"] > a[kind="primary"] {
    background: var(--accent-red) !important;
    border-color: var(--accent-red) !important;
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover, div[data-testid="stLinkButton"] > a[kind="primary"]:hover {
    background: var(--accent-red-hover) !important;
    box-shadow: 0 4px 14px rgba(229, 9, 20, 0.4) !important;
}

/* Clickable Movie Poster Hover & Transition */
.movie-card a {
    text-decoration: none !important;
    color: inherit !important;
}

.movie-card a .movie-poster-container {
    cursor: pointer !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease !important;
}

.movie-card a:hover .movie-poster-container {
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 10px 24px rgba(0, 229, 255, 0.25) !important;
}

.movie-card a:hover .movie-title-text {
    color: #00E5FF !important;
}

.stTextInput > div > div > input {
    background-color: #111A24 !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 8px !important;
}

.stSelectbox > div > div {
    background-color: #111A24 !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 8px !important;
}

/* -------------------------------------------------------------------------
   AI CONCIERGE CHATBOT UI/UX (Streaming Theme)
   ------------------------------------------------------------------------- */
.chat-header-card {
    background: linear-gradient(135deg, rgba(14, 22, 34, 0.95), rgba(19, 27, 38, 0.85));
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 229, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
}

.chat-bot-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.chat-avatar-glow {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #00E5FF 0%, #0077B6 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.chat-bot-title {
    font-family: 'Cinzel', serif;
    font-size: 1.28rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 0.03em;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.chat-bot-subtitle {
    font-size: 0.78rem;
    color: #94A3B8;
    margin: 2px 0 0 0;
}

.chat-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 229, 255, 0.12);
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #00E5FF;
}

.chat-pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00E5FF;
    box-shadow: 0 0 8px #00E5FF;
}

.chat-catalog-count-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: #CBD5E1;
    font-weight: 600;
}

.chat-pills-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0 16px 0;
}

/* Styling Streamlit Chat Messages */
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    padding: 10px 4px !important;
    margin-bottom: 12px !important;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(0, 229, 255, 0.08), rgba(0, 145, 234, 0.12)) !important;
    border: 1px solid rgba(0, 229, 255, 0.25) !important;
    border-radius: 16px 16px 4px 16px !important;
    padding: 12px 18px !important;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(14, 22, 34, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-left: 3px solid #00E5FF !important;
    border-radius: 16px 16px 16px 4px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
}

/* Chat Input Bar (Modern Floating Dock) */
.chat-input-bar-wrap {
    background: rgba(14, 22, 34, 0.95);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 16px;
    padding: 8px 12px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 229, 255, 0.1);
    margin-top: 16px;
}

/* Divider */
.cinevora-section-divider {
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.12) 30%, rgba(255, 255, 255, 0.12) 70%, transparent);
    margin: 28px 0;
}
</style>
"""


def inject_cinema_styles():
    """Injects the Cinevora streaming-style dark theme CSS into the current Streamlit app."""
    st.markdown(CINEMA_DARK_CSS, unsafe_allow_html=True)
