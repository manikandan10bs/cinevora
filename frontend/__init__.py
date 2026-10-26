"""Cinevora Frontend Package."""

from frontend.poster_service import (
    extract_release_year,
    get_indian_movies,
    get_hollywood_movies,
    get_movies_by_language,
    get_movies_by_region,
    get_all_enriched_movies,
    get_poster_url,
    get_backdrop_url,
    get_trailer_url,
    get_movie_enrichment,
)

__all__ = [
    "extract_release_year",
    "get_indian_movies",
    "get_hollywood_movies",
    "get_movies_by_language",
    "get_movies_by_region",
    "get_all_enriched_movies",
    "get_poster_url",
    "get_backdrop_url",
    "get_trailer_url",
    "get_movie_enrichment",
]
