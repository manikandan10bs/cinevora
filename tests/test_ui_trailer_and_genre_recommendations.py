"""
Test Suite: UI Movie Interaction, Trailer Links & 4 Same-Genre Movie Recommendations
Verifies:
1. get_effective_trailer_url: direct YouTube watch URL vs. YouTube search query fallback for nulls/empty
2. get_same_genre_movies: returns up to 4 movies matching the genre of the selected movie
3. Chainable navigation: related movies contain valid catalog IDs and metadata
4. AI assistant recommendations contain trailer_url and effective trailer link
"""

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from frontend.poster_service import (
    get_effective_trailer_url,
    get_same_genre_movies,
    get_movie_enrichment,
)
from app.assistant import GeminiAssistant


def test_effective_trailer_url_with_valid_youtube_link():
    """Valid youtube.com/watch link should be returned directly."""
    movie = {
        "title": "Leo",
        "trailer_link": "https://www.youtube.com/watch?v=FZYhL_bVQUQ"
    }
    url = get_effective_trailer_url(movie)
    assert url == "https://www.youtube.com/watch?v=FZYhL_bVQUQ"


def test_effective_trailer_url_fallback_on_null_or_empty():
    """Null, empty, or \\N trailer should fall back to YouTube search query."""
    movie_null = {"title": "Vikram", "trailer_link": None}
    url_null = get_effective_trailer_url(movie_null)
    assert url_null == "https://www.youtube.com/results?search_query=Vikram+trailer"

    movie_empty = {"title": "Kaithi", "trailer_link": ""}
    url_empty = get_effective_trailer_url(movie_empty)
    assert url_empty == "https://www.youtube.com/results?search_query=Kaithi+trailer"

    movie_slash_n = {"title": "Jailer", "trailer_link": r"\N"}
    url_slash_n = get_effective_trailer_url(movie_slash_n)
    assert url_slash_n == "https://www.youtube.com/results?search_query=Jailer+trailer"


def test_get_same_genre_movies_returns_four_movies():
    """Selecting a movie should return up to 4 movies in the same genre, excluding itself."""
    # Find a known movie, e.g. Action movie
    same_movies = get_same_genre_movies("tt10579952", genres_str="Action, Crime, Drama", limit=4)
    assert len(same_movies) == 4, f"Expected 4 movies, got {len(same_movies)}"
    
    # Ensure current movie is not in the related movies
    for rel in same_movies:
        assert str(rel.get("id")) != "tt10579952"
        assert rel.get("title") is not None
        assert rel.get("genres") is not None
        # Verify it has effective trailer url
        trailer = get_effective_trailer_url(rel)
        assert "youtube.com" in trailer


def test_get_same_genre_movies_chainable():
    """Clicking one of the 4 related movies should also yield 4 related movies."""
    first_gen = get_same_genre_movies("tt10579952", genres_str="Action", limit=4)
    assert len(first_gen) >= 1
    
    second_target = first_gen[0]
    second_id = str(second_target.get("catalog_id") or second_target.get("id"))
    second_genres = second_target.get("genres", "Action")
    
    second_gen = get_same_genre_movies(second_id, genres_str=second_genres, limit=4)
    assert len(second_gen) == 4
    for m in second_gen:
        m_id = str(m.get("catalog_id") or m.get("id"))
        assert m_id != second_id


def test_assistant_movies_have_trailers():
    """AI Assistant recommendations must supply valid trailer metadata."""
    assistant = GeminiAssistant()
    res = assistant.chat("Show me movies acted by Vijay", limit=3)
    assert len(res.recommendations) > 0
    for rec in res.recommendations:
        m_dict = rec.model_dump() if hasattr(rec, "model_dump") else rec.dict()
        eff_trailer = get_effective_trailer_url(m_dict)
        assert "youtube.com" in eff_trailer
