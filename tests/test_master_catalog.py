"""
Unit Tests for Cinevora Master Cleaned Catalog (Movies_Master_Cleaned.csv)
Tests cover:
1. Safe CSV loading relative to project root
2. Missing files, zero-byte empty files, and empty datasets
3. Missing values, invalid ratings, string year parsing, and malformed URL handling
4. Multi-industry filtering with alias normalization (Kollywood, Tollywood, Sandalwood, Mollywood, Bollywood, Hollywood)
5. Search by title, cast, and director
6. Release year bounds, rating thresholds, and multi-genre filtering
7. Sorting (rating, newest, alphabetical) and pagination consistency
8. REST API endpoints (GET /movies/catalog, /movies/catalog/stats, /movies/catalog/{catalog_id})
9. Safe persistence of favorites and likes with catalog_id strings (e.g. 'CINEVORA-0000001')
"""

import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from src.catalog_service import (
    load_master_catalog,
    query_master_catalog,
    get_master_catalog_stats,
    get_master_movie_by_id,
    normalize_industry_filter,
    is_valid_url,
    get_similar_catalog_movies_by_genre
)
from app.main import app
from app.db import (
    init_db,
    add_favorite,
    remove_favorite,
    get_favorites,
    is_favorite,
    toggle_like,
    get_user_likes
)


@pytest.fixture(scope="module")
def api_client():
    """Initializes FastAPI test client."""
    init_db()
    with TestClient(app) as client:
        yield client


# -----------------------------------------------------------------------------
# 1. Dataset Loading & File Handling Tests
# -----------------------------------------------------------------------------
def test_load_real_master_dataset():
    """Verifies that the actual Movies_Master_Cleaned.csv loads properly with 3,560 titles."""
    df = load_master_catalog(force_reload=True)
    assert not df.empty, "Master catalog DataFrame must not be empty."
    assert len(df) == 3560, f"Expected 3,560 rows in master dataset, got {len(df)}"
    assert "catalog_id" in df.columns
    assert "industry" in df.columns
    assert "title" in df.columns
    assert "release_year" in df.columns
    assert "rating" in df.columns
    assert "movie_poster" in df.columns


def test_load_master_catalog_missing_file():
    """Verifies graceful handling when the master CSV file does not exist."""
    fake_path = PROJECT_ROOT / "data" / "nonexistent_catalog_file_12345.csv"
    df = load_master_catalog(csv_path=fake_path, force_reload=True)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert "catalog_id" in df.columns


def test_load_master_catalog_empty_file():
    """Verifies graceful handling of zero-byte or header-only empty files."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tf:
        tf.write("")  # 0 bytes
        temp_path = Path(tf.name)

    try:
        df = load_master_catalog(csv_path=temp_path, force_reload=True)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_load_master_catalog_dirty_data_resilience():
    """Verifies that missing values, string-year floats, invalid ratings, and malformed URLs are cleaned."""
    dirty_content = """catalog_id,movie_id,industry,title,release_year,genre,rating,cast,director,movie_poster,trailer_link
CINEVORA-0000001,101,Telugu,Narappa,2021.0,Action,7.6,Venkatesh,Srikanth,https://image.tmdb.org/valid.jpg,https://youtube.com/watch?v=123
CINEVORA-0000002,102,Tamil,Vikram,2022,Action,14.5,Kamal Haasan,Lokesh,not_a_valid_url,N/A
,103,,Fallback Title,invalid_year,,NaN,\\N,\\N,http://image.tmdb.org/poster.jpg,
"""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", encoding="utf-8", delete=False) as tf:
        tf.write(dirty_content)
        temp_path = Path(tf.name)

    try:
        df = load_master_catalog(csv_path=temp_path, force_reload=True)
        assert len(df) == 3

        # Row 1: Valid
        r1 = df.iloc[0]
        assert r1["release_year"] == 2021
        assert r1["rating"] == 7.6
        assert r1["movie_poster"] == "https://image.tmdb.org/valid.jpg"
        assert r1["trailer_link"] == "https://youtube.com/watch?v=123"

        # Row 2: Clipped rating from 14.5 to 10.0, malformed poster/trailer converted to None
        r2 = df.iloc[1]
        assert r2["rating"] == 10.0
        assert pd.isna(r2["movie_poster"]) or r2["movie_poster"] is None
        assert pd.isna(r2["trailer_link"]) or r2["trailer_link"] is None

        # Row 3: Generated catalog_id, invalid_year parsed to 0, rating NaN parsed to 0.0, \N cleaned
        r3 = df.iloc[2]
        assert str(r3["catalog_id"]).startswith("CINEVORA-")
        assert r3["release_year"] == 0
        assert r3["rating"] == 0.0
        assert r3["cast"] == ""
        assert r3["movie_poster"] == "http://image.tmdb.org/poster.jpg"
        assert pd.isna(r3["trailer_link"]) or r3["trailer_link"] is None

    finally:
        if temp_path.exists():
            temp_path.unlink()
        # Restore real cache
        load_master_catalog(force_reload=True)


# -----------------------------------------------------------------------------
# 2. Industry Alias Normalization & Filtering Tests
# -----------------------------------------------------------------------------
def test_normalize_industry_aliases():
    """Verifies that colloquial aliases normalize to canonical dataset industries."""
    assert normalize_industry_filter("Kollywood") == "Tamil"
    assert normalize_industry_filter("Kollywood/Tamil") == "Tamil"
    assert normalize_industry_filter("Kollywood (Tamil)") == "Tamil"
    assert normalize_industry_filter("Tollywood") == "Telugu"
    assert normalize_industry_filter("Tollywood/Telugu") == "Telugu"
    assert normalize_industry_filter("Mollywood") == "Malayalam"
    assert normalize_industry_filter("Sandalwood") == "Kannada"
    assert normalize_industry_filter("Kannada/Sandalwood") == "Kannada"
    assert normalize_industry_filter("Hindi") == "Bollywood"
    assert normalize_industry_filter("Bollywood") == "Bollywood"
    assert normalize_industry_filter("American") == "Hollywood"
    assert normalize_industry_filter("Hollywood") == "Hollywood"
    assert normalize_industry_filter("All") is None
    assert normalize_industry_filter("All Industries") is None
    assert normalize_industry_filter("") is None


def test_industry_filtering_results():
    """Verifies that query_master_catalog filters by industry accurately."""
    df = load_master_catalog()

    # Kollywood / Tamil
    kolly_movies, kolly_count = query_master_catalog(df=df, industry="Kollywood", limit=20)
    assert kolly_count == 699
    assert len(kolly_movies) == 20
    for m in kolly_movies:
        assert m["industry"] == "Tamil"

    # Sandalwood / Kannada
    kannada_movies, kannada_count = query_master_catalog(df=df, industry="Sandalwood", limit=15)
    assert kannada_count == 286
    assert len(kannada_movies) == 15
    for m in kannada_movies:
        assert m["industry"] == "Kannada"

    # Bollywood
    bolly_movies, bolly_count = query_master_catalog(df=df, industry="Bollywood", limit=10)
    assert bolly_count == 780
    assert len(bolly_movies) == 10
    for m in bolly_movies:
        assert m["industry"] == "Bollywood"

    # Hollywood
    hwd_movies, hwd_count = query_master_catalog(df=df, industry="Hollywood", limit=10)
    assert hwd_count == 503
    for m in hwd_movies:
        assert m["industry"] == "Hollywood"


# -----------------------------------------------------------------------------
# 3. Search, Genre, Year & Rating Filtering Tests
# -----------------------------------------------------------------------------
def test_title_and_cast_search():
    """Verifies case-insensitive search by title and cast."""
    df = load_master_catalog()

    # Search known title
    res, count = query_master_catalog(df=df, query="narappa")
    assert count >= 1
    assert any("Narappa" in m["title"] for m in res)

    # Search by cast member (e.g. Kamal Haasan)
    res_cast, count_cast = query_master_catalog(df=df, query="Kamal Haasan")
    assert count_cast >= 1
    assert any("Kamal Haasan" in m.get("cast", "") for m in res_cast)


def test_genre_and_year_bounds_filtering():
    """Verifies filtering by genre, release year bounds, and minimum rating."""
    df = load_master_catalog()

    # Action movies in 2023 with rating >= 7.0
    res, count = query_master_catalog(
        df=df,
        genre="Action",
        start_year=2023,
        end_year=2023,
        min_rating=7.0,
        limit=20
    )
    assert count > 0
    for m in res:
        assert "Action" in m["genre"]
        assert m["release_year"] == 2023
        assert m["rating"] >= 7.0


def test_sorting_and_pagination():
    """Verifies sorting modes and page slicing."""
    df = load_master_catalog()

    # 1. Rating sort (descending)
    p1, _ = query_master_catalog(df=df, sort_by="rating", limit=10, offset=0)
    for i in range(len(p1) - 1):
        assert p1[i]["rating"] >= p1[i + 1]["rating"]

    # 2. Alphabetical sort (A-Z)
    p_alpha, _ = query_master_catalog(df=df, sort_by="title", limit=10, offset=0)
    for i in range(len(p_alpha) - 1):
        assert p_alpha[i]["title"].lower() <= p_alpha[i + 1]["title"].lower()

    # 3. Pagination offset check: Page 1 and Page 2 must not have overlapping IDs
    page1, _ = query_master_catalog(df=df, limit=10, offset=0)
    page2, _ = query_master_catalog(df=df, limit=10, offset=10)
    p1_ids = {m["catalog_id"] for m in page1}
    p2_ids = {m["catalog_id"] for m in page2}
    assert len(p1_ids.intersection(p2_ids)) == 0


def test_get_master_movie_by_id():
    """Verifies retrieving an individual movie by catalog_id."""
    movie = get_master_movie_by_id("CINEVORA-0000001")
    assert movie is not None
    assert movie["catalog_id"] == "CINEVORA-0000001"
    assert "title" in movie
    assert "industry" in movie
    assert is_valid_url(movie.get("movie_poster"))

    # Invalid ID
    assert get_master_movie_by_id("CINEVORA-NONEXISTENT") is None


def test_master_catalog_stats():
    """Verifies statistical summary calculation."""
    stats = get_master_catalog_stats()
    assert stats["total_movies"] == 3560
    assert "Tamil" in stats["industries"]
    assert "Bollywood" in stats["industries"]
    assert stats["trailers_count"] > 1000
    assert stats["year_min"] >= 2021
    assert stats["year_max"] <= 2026


def test_similar_catalog_movies():
    """Verifies content-based genre recommendations within master catalog."""
    sims = get_similar_catalog_movies_by_genre("CINEVORA-0000001", n=5)
    assert len(sims) == 5
    for s in sims:
        assert s["catalog_id"] != "CINEVORA-0000001"


# -----------------------------------------------------------------------------
# 4. REST API Endpoint Tests
# -----------------------------------------------------------------------------
def test_api_get_master_catalog_endpoint(api_client):
    """Verifies GET /movies/catalog returns 200 with paginated master movies."""
    resp = api_client.get("/movies/catalog?limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 10
    assert data["total"] == 3560
    assert len(data["results"]) == 10
    assert "available_industries" in data


def test_api_master_catalog_industry_filter(api_client):
    """Verifies GET /movies/catalog?industry=Kollywood returns only Tamil movies."""
    resp = api_client.get("/movies/catalog?industry=Kollywood&limit=15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 699
    for m in data["results"]:
        assert m["industry"] == "Tamil"


def test_api_master_catalog_stats_endpoint(api_client):
    """Verifies GET /movies/catalog/stats returns summary metrics."""
    resp = api_client.get("/movies/catalog/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_movies"] == 3560
    assert "industries" in data
    assert "genres" in data


def test_api_master_catalog_movie_details(api_client):
    """Verifies GET /movies/catalog/{catalog_id} returns movie details."""
    resp = api_client.get("/movies/catalog/CINEVORA-0000001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["catalog_id"] == "CINEVORA-0000001"
    assert "title" in data

    # 404 for invalid ID
    resp_404 = api_client.get("/movies/catalog/CINEVORA-9999999")
    assert resp_404.status_code == 404


def test_api_health_includes_master_catalog(api_client):
    """Verifies GET /health includes master_catalog_count."""
    resp = api_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("master_catalog_count") == 3560


# -----------------------------------------------------------------------------
# 5. SQLite Persistence of Catalog Movies (Watchlist & Likes)
# -----------------------------------------------------------------------------
def test_favorites_and_likes_with_catalog_id():
    """Verifies that string catalog_id can be favorited and liked without errors."""
    test_user = "test_catalog_user_99"
    cat_id = "CINEVORA-0000001"

    # Reset any existing test state
    remove_favorite(test_user, cat_id)
    if cat_id in [str(l) for l in get_user_likes(test_user)]:
        toggle_like(test_user, cat_id)

    # 1. Add to favorites
    ok = add_favorite(
        user_id=test_user,
        movie_id=cat_id,
        movie_title="Narappa",
        genres="Action,Drama",
        release_date="2021",
        rating=7.6
    )
    assert ok is True
    assert is_favorite(test_user, cat_id) is True

    # Check favorites list
    favs = get_favorites(test_user)
    fav_ids = [str(f["movie_id"]) for f in favs]
    assert cat_id in fav_ids

    # 2. Toggle like
    ok_like, is_liked = toggle_like(test_user, cat_id)
    assert ok_like is True
    assert is_liked is True

    user_likes = [str(l) for l in get_user_likes(test_user)]
    assert cat_id in user_likes

    # Clean up
    remove_favorite(test_user, cat_id)
    assert is_favorite(test_user, cat_id) is False

