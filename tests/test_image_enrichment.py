"""
Tests for Movie Catalog Image Enrichment & Media Service
Validates:
1. Master movie catalog structure and coverage (3,560 titles)
2. Presence and validity of 16:9 landscape backdrops for spotlight movies
3. Fallback behavior when external APIs or images are absent
4. poster_service helper functions (get_poster_url, get_backdrop_url, get_featured_movies)
5. Zero-indent HTML rendering preventing Markdown code-fence bugs
"""

import pandas as pd
from pathlib import Path
import pytest

from frontend.poster_service import (
    init_poster_cache,
    get_poster_url,
    get_backdrop_url,
    get_movie_synopsis,
    get_trailer_url,
    get_featured_movies,
    get_movie_enrichment,
    render_poster_html
)
from src.catalog_service import load_master_catalog


@pytest.fixture(autouse=True)
def setup_poster_cache():
    init_poster_cache()


def test_enrichment_manifest_exists_and_contains_catalog():
    """Verifies that Movies_Master_Cleaned.csv exists and contains 3,560 catalog movies."""
    manifest_path = Path("data/processed/Movies_Master_Cleaned.csv")
    assert manifest_path.exists(), "Movies_Master_Cleaned.csv should exist as single source of truth"

    df = pd.read_csv(manifest_path)
    assert len(df) == 3560, "Master catalog must contain exactly 3,560 movies"

    # Verify Leo (CINEVORA-0000001) or high-rated spotlight title
    first_movie = df.iloc[0]
    assert first_movie["catalog_id"] == "CINEVORA-0000001"
    assert first_movie["movie_poster"] is not None
    assert str(first_movie["movie_poster"]).startswith("http")


def test_featured_movies_have_required_streaming_fields():
    """Ensures spotlight featured movies have backdrops, synopses, and ratings for hero banner."""
    featured = get_featured_movies()
    assert len(featured) >= 5, "At least 5 featured movies should be configured for the rotating banner"

    for movie in featured:
        assert "catalog_id" in movie or "movie_id" in movie
        assert "title" in movie
        assert movie.get("backdrop_url") is not None
        assert movie["backdrop_url"].startswith("http")
        assert movie.get("synopsis") is not None
        assert len(movie["synopsis"]) > 10
        assert movie.get("avg_rating", 0.0) > 0.0


def test_poster_service_retrieval_functions():
    """Tests retrieval functions across poster, backdrop, synopsis, and trailer."""
    featured = get_featured_movies()
    assert len(featured) > 0
    test_movie = featured[0]
    mid = test_movie["catalog_id"]

    p_url = get_poster_url(mid)
    assert p_url is not None
    assert p_url.startswith("http")

    b_url = get_backdrop_url(mid)
    assert b_url is not None
    assert b_url.startswith("http")

    syn = get_movie_synopsis(mid)
    assert syn is not None
    assert len(syn) > 5

    tr = get_trailer_url(mid)
    assert tr is not None
    assert "youtube" in tr.lower()


def test_render_poster_html_has_no_leading_indentation_or_newlines():
    """
    CRITICAL TEST for Bug Fix (Section 5):
    Verifies that render_poster_html outputs single-line or dedented HTML
    so that CommonMark/markdown-it never treats the HTML block as an indented code block.
    """
    html_out = render_poster_html("CINEVORA-0000001", "Leo (2023)", "2023", "Action|Crime")
    assert "<div class=\"movie-poster-container\">" in html_out
    assert "</div>" in html_out
    # Must not contain newlines with 4+ leading spaces that trigger markdown code fences
    lines = html_out.split("\n")
    for line in lines:
        if line.strip():
            assert not line.startswith("    "), "HTML lines must not have 4 leading spaces (code fence bug)"


def test_unmapped_movie_graceful_fallback():
    """Verifies that an unmapped movie ID falls back to styled cinema fallback without crashing."""
    html_fallback = render_poster_html(99999, "Imaginary Nonexistent Film (1990)")
    assert "movie-poster-fallback" in html_fallback
    assert "Imaginary Nonexistent Film" in html_fallback
    assert "🎬" in html_fallback


def test_build_enrichment_manifest_limit_mode():
    """Verifies that load_master_catalog loads correctly and returns DataFrame with 3,560 titles."""
    df = load_master_catalog()
    assert len(df) == 3560
    assert "catalog_id" in df.columns
    assert "industry" in df.columns
