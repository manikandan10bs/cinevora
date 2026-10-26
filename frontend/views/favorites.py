"""
Cinevora Favorites / Watchlist Backward Compatibility Alias
Redirects to frontend.views.watchlist.
"""

from frontend.views.watchlist import render_watchlist_page

def render_favorites_page(account_key: str):
    """Wrapper forwarding to render_watchlist_page."""
    render_watchlist_page(account_key)
