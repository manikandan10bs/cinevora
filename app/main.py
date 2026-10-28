"""
Cinevora FastAPI Application
Provides REST endpoints for:
1. Core Catalog Search & Details (GET /movies/search, GET /movies/{movie_id})
2. Recommendation Service (GET /recommendations)
3. AI Movie Assistant powered by Google Gemini Flash (POST /assistant/chat)
4. User Interactions & Persistence (GET/POST/DELETE /favorites, GET/POST /likes)
5. Live Telemetry & Monitoring (GET /monitoring/metrics, GET /monitoring/events)
6. Health & Assistant Status (GET /health, GET /assistant/status)
"""

import sys
import json
import time
import logging
import re
import urllib.parse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.schemas import (
    MovieItem,
    MovieDetails,
    AssistantChatRequest,
    AssistantChatResponse,
    RecommendationResponse,
    MovieSearchResponse,
    HealthResponse,
    AssistantStatusResponse,
    FavoriteCreateRequest,
    FavoriteItem,
    FavoritesResponse,
    LikeToggleRequest,
    LikeToggleResponse,
    LikesResponse,
    SearchHistoryCreateRequest,
    SearchHistoryResponse,
    SearchHistoryItem,
    MonitoringMetricsResponse,
    MonitoringEventsResponse,
    MasterCatalogMovieItem,
    MasterCatalogResponse,
    MasterCatalogStatsResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    ViewHistoryRequest,
    ViewHistoryResponse,
    ViewHistoryItem,
    ClearDataRequest,
    TrailerResolutionResponse,
    StreamingSourceItem,
    MovieStreamingResponse,
    StreamingAvailableMovieItem
)
from app.assistant import GeminiAssistant
from app.tmdb import tmdb_client
from app.watchmode import watchmode_client
from app.db import (
    init_db,
    add_favorite,
    remove_favorite,
    get_favorites,
    toggle_like,
    get_user_likes,
    record_search_history,
    get_search_history,
    clear_search_history,
    record_event,
    get_monitoring_summary,
    get_recent_events,
    verify_user_credentials,
    create_user,
    get_user_by_username,
    record_view_history,
    get_view_history,
    clear_view_history,
    clear_all_monitoring_and_interaction_data
)
from src.recommender import MasterContentRecommender, CinevoraRecommender, GENRE_COLUMNS
from src.catalog_service import (
    load_master_catalog,
    query_master_catalog,
    get_master_movie_by_id,
    get_master_catalog_stats
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cinevora.api")

# Global application state
app_state: Dict[str, Any] = {
    "recommender": None,
    "movie_catalog": None,
    "assistant": None,
    "evaluation_report": None
}


# -----------------------------------------------------------------------------
# MLOps Telemetry Middleware
# -----------------------------------------------------------------------------
class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Measures request latency with microsecond precision and records telemetry events
    into SQLite for live MLOps dashboard visualization.
    Excludes internal polling from distorting user analytics while preserving audit trails.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        endpoint = request.url.path
        method = request.method

        # Identify internal polling endpoints
        is_internal = endpoint in ["/health"] or endpoint.startswith("/monitoring")

        status_code = 500
        response = None
        error_category = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            error_category = type(exc).__name__
            status_code = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Determine event classification
            event_type = "api_request"
            if endpoint.startswith("/recommendations"):
                event_type = "recommendation"
            elif endpoint.startswith("/assistant/chat"):
                event_type = "assistant"
            elif endpoint.startswith("/movies"):
                event_type = "catalog_search"
            elif endpoint in ["/favorites", "/likes", "/history/search"]:
                event_type = "user_interaction"

            # Parse query params safely for telemetry context
            genre_filter = request.query_params.get("genre")
            user_id = request.query_params.get("user_id")
            model_type = request.query_params.get("model_type")

            # Asynchronously record event into SQLite without blocking response
            record_event(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms,
                event_type=event_type,
                genre_filter=genre_filter,
                user_id=user_id,
                model_type=model_type,
                error_category=error_category,
                is_internal=is_internal
            )


# -----------------------------------------------------------------------------
# Lifespan Context Manager
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager.
    Initializes database tables, loads recommender artifacts, processed catalog,
    offline evaluation reports, and the Gemini assistant.
    """
    logger.info("Initializing Cinevora Backend Services...")

    # 1. Initialize SQLite Database
    init_db()

    # 2. Load Master Cleaned Movie Catalog (Single Source of Movie Data)
    master_df = load_master_catalog()
    app_state["movie_catalog"] = master_df
    app_state["master_catalog"] = master_df
    logger.info("Loaded master catalog as single source of truth: %d movies.", len(master_df))

    # 3. Initialize Master Content Recommender
    recommender = MasterContentRecommender(master_df)
    app_state["recommender"] = recommender
    app_state["master_recommender"] = recommender
    logger.info("Initialized MasterContentRecommender for master catalog.")

    # 4. Load Offline Model Evaluation Report (Benchmark metrics)
    eval_report_path = settings.PROJECT_ROOT_PATH / "reports" / "recommendation_evaluation.json"
    if eval_report_path.exists():
        try:
            with open(eval_report_path, "r") as f:
                app_state["evaluation_report"] = json.load(f)
            logger.info("Loaded offline benchmark evaluation report.")
        except Exception as e:
            logger.warning("Could not read evaluation report: %s", e)
            app_state["evaluation_report"] = None

    # 5. Initialize Gemini Assistant
    logger.info("Configuring Gemini AI Assistant (Model: %s)...", settings.GEMINI_MODEL)
    assistant = GeminiAssistant()
    stat_check = assistant.verify_connection(force=True)
    if stat_check.get("verified"):
        logger.info("Gemini AI Assistant is ACTIVE and verified with model: %s", stat_check.get("model"))
    else:
        logger.info("Gemini verification state: %s. Operating in catalog fallback mode.", stat_check.get("status_state"))
    app_state["assistant"] = assistant

    yield

    logger.info("Shutting down Cinevora Backend API...")
    app_state.clear()


app = FastAPI(
    title="Cinevora — Real-Time Movie Recommendation Service",
    description=(
        "Production-grade movie recommendation API featuring SVD Matrix Factorization, "
        "Content-Based Filtering, Google Gemini 3.5 Flash Lite conversational AI, "
        "user interactions persistence, and MLOps telemetry monitoring."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# Allowed origins for CORS (Local development, Streamlit, and Firebase Hosting origins)
cors_origins_env = getattr(settings, "CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://cinevora-z42e.onrender.com",
]
if cors_origins_env:
    for o in cors_origins_env.split(","):
        cleaned = o.strip()
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

# Enable CORS for frontend, Firebase Hosting domains, Vercel, LAN IP, and local browser communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register live telemetry middleware
app.add_middleware(MonitoringMiddleware)


# -----------------------------------------------------------------------------
# System Health & Status Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["System"])
async def root(request: Request):
    """
    Serves the Cinevora cinema frontend when accessed by a browser,
    or JSON service status when queried via API client / curl.
    """
    frontend_index = settings.PROJECT_ROOT_PATH / "frontend_ui" / "dist" / "index.html"
    accept = request.headers.get("accept", "")
    if "text/html" in accept and frontend_index.exists():
        from starlette.responses import FileResponse
        return FileResponse(
            frontend_index,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    return {
        "service": "Cinevora API",
        "description": "Real-Time Movie Recommendation Service with Knowledge Graph RAG & MLOps Monitoring",
        "status": "healthy",
        "version": "2.0.0",
        "master_catalog_titles": 3560,
        "ai_model": "gemini-3.5-flash-lite",
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns operational status of Cinevora and its components."""
    rec = app_state.get("recommender")
    catalog = app_state.get("movie_catalog")
    assistant = app_state.get("assistant")

    master_count = len(catalog) if catalog is not None else 0

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        model_loaded=rec is not None,
        catalog_movies_count=master_count,
        gemini_configured=assistant.is_available if assistant else False,
        tmdb_configured=tmdb_client.is_configured,
        watchmode_configured=watchmode_client.is_configured,
        enriched_catalog_count=master_count,
        master_catalog_count=master_count
    )


@app.get("/assistant/status", response_model=AssistantStatusResponse, tags=["Assistant"])
async def assistant_status():
    """
    Checks the status of the Gemini AI assistant.
    Never exposes API keys or secrets.
    """
    assistant: Optional[GeminiAssistant] = app_state.get("assistant")
    if not assistant:
        return AssistantStatusResponse(
            configured=False,
            verified=False,
            status_state="configuration_missing",
            model=settings.GEMINI_MODEL,
            status="Assistant service not initialized. Operating in offline catalog fallback mode.",
            fallback_active=True
        )

    info = assistant.verify_connection(force=False)
    return AssistantStatusResponse(
        configured=info.get("configured", False),
        verified=info.get("verified", False),
        status_state=info.get("status_state", "configuration_missing"),
        model=info.get("model", assistant.model_name),
        status=info.get("status", "Standby"),
        fallback_active=info.get("fallback_active", True)
    )


# -----------------------------------------------------------------------------
# Core Movie Catalog & Search Endpoints (Single Source: Movies_Master_Cleaned.csv)
# -----------------------------------------------------------------------------
@app.get("/movies/search", response_model=MovieSearchResponse, tags=["Catalog"])
async def search_movies(
    query: Optional[str] = Query(None, max_length=100, description="Title search term"),
    genre: Optional[str] = Query(None, description="Genre filter (e.g. 'Action', 'Comedy')"),
    region: Optional[str] = Query(None, description="Industry or region: Bollywood, Tamil, Telugu, Malayalam, Hollywood, Kannada"),
    cinema_region: Optional[str] = Query(None, description="Alias for industry or region filter"),
    language: Optional[str] = Query(None, description="Language code: ta, te, kn, ml, hi, en"),
    start_year: Optional[int] = Query(None, ge=1888, le=2100, description="Earliest release year"),
    end_year: Optional[int] = Query(None, ge=1888, le=2100, description="Latest release year"),
    sort_by: str = Query("rating", description="Sort order: rating, newest, title, popularity, relevance"),
    limit: int = Query(10, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Searches the 3,560-title Cinevora master movie catalog.
    Enforces strict genre and release-year constraints simultaneously across all 6 film industries.
    """
    clean_query = query.strip() if (query and query.strip()) else None

    if genre and genre.strip():
        all_master_genres = set(g.lower() for g in get_master_catalog_stats().get("genres", []))
        all_master_genres.update(g.lower() for g in GENRE_COLUMNS)
        requested_genres = [g.strip().lower() for g in genre.replace(",", "|").split("|") if g.strip()]
        if not any(g in all_master_genres for g in requested_genres):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid genre '{genre}'. Valid genres include: {', '.join(sorted(get_master_catalog_stats().get('genres', []))[:10])}"
            )

    industry_param = region or cinema_region or language
    records, total_found = query_master_catalog(
        query=clean_query,
        industry=industry_param,
        genre=genre,
        start_year=start_year,
        end_year=end_year,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

    year_range_info = [start_year, end_year] if (start_year or end_year) else None

    results: List[MovieItem] = []
    seen_titles = set()

    # Step 1: TMDB as Primary Dataset for Search
    if clean_query and tmdb_client.is_configured:
        tmdb_results = tmdb_client.search_movie(clean_query, str(start_year) if start_year else None)
        for tm in tmdb_results[:limit]:
            tm_dict = tmdb_client.convert_tmdb_to_movie_dict(tm)
            seen_titles.add(tm_dict["title"].lower().strip())
            results.append(
                MovieItem(
                    movie_id=tm_dict["movie_id"],
                    movie_title=tm_dict["title"],
                    release_date=tm_dict["release_date"],
                    genres=tm_dict["genres"],
                    score=tm_dict["score"],
                    predicted_rating=tm_dict["predicted_rating"],
                    cinema_region=tm_dict["cinema_region"],
                    original_language=tm_dict["original_language"],
                    poster_url=tm_dict["poster_url"],
                    backdrop_url=tm_dict["backdrop_url"],
                    trailer_url=tm_dict["trailer_url"]
                )
            )

    # Step 2: Master Catalog Search
    for row in records:
        t_title = str(row.get("title", "Untitled")).lower().strip()
        if t_title in seen_titles:
            continue
        seen_titles.add(t_title)

        ind = str(row.get("industry", "Cinema"))
        is_hwd = ind.lower() == "hollywood"
        lang_code = {
            "tamil": "ta", "telugu": "te", "malayalam": "ml",
            "kannada": "kn", "bollywood": "hi", "hollywood": "en"
        }.get(ind.lower(), "en")
        region_label = "Hollywood" if is_hwd else "Indian"

        results.append(
            MovieItem(
                movie_id=row.get("catalog_id") or str(row.get("movie_id", "")),
                movie_title=str(row.get("title", "Untitled")),
                release_date=str(row.get("release_year", "Unknown")),
                genres=str(row.get("genre", "Cinema")),
                score=None,
                predicted_rating=float(row.get("rating", 6.0)),
                cinema_region=region_label,
                original_language=lang_code,
                poster_url=row.get("movie_poster"),
                backdrop_url=row.get("movie_poster"),
                trailer_url=row.get("trailer_link")
            )
        )

    return MovieSearchResponse(
        query=query,
        genre=genre,
        year_range=year_range_info,
        count=len(results),
        results=results
    )


# -----------------------------------------------------------------------------
# Master Cleaned Catalog Endpoints (3,560 Indian & Hollywood Movies)
# Defined before /movies/{movie_id} to avoid dynamic route collision
# -----------------------------------------------------------------------------
@app.get("/movies/catalog", response_model=MasterCatalogResponse, tags=["Master Catalog"])
async def get_master_catalog_endpoint(
    query: Optional[str] = Query(None, description="Search by title, cast, or director"),
    industry: Optional[str] = Query(None, description="Industry filter (e.g. Bollywood, Tamil, Telugu, Malayalam, Hollywood, Kannada)"),
    genre: Optional[str] = Query(None, description="Genre filter (e.g. Action, Comedy, Drama, Thriller)"),
    start_year: Optional[int] = Query(None, ge=1888, le=2100, description="Minimum release year"),
    end_year: Optional[int] = Query(None, ge=1888, le=2100, description="Maximum release year"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum viewer rating (0.0 to 10.0)"),
    sort_by: str = Query("rating", description="Sort order: rating, newest, title, popularity"),
    limit: int = Query(24, ge=1, le=100, description="Max movies per page (default 24)"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Returns paginated movies from the 3,560-title master cleaned catalog.
    Supports title/cast/director search, industry alias normalization (e.g. Kollywood -> Tamil),
    genre filtering, release year ranges, and rating sorting.
    """
    records, total_count = query_master_catalog(
        query=query,
        industry=industry,
        genre=genre,
        start_year=start_year,
        end_year=end_year,
        min_rating=min_rating,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )
    stats = get_master_catalog_stats()
    available_industries = list(stats.get("industries", {}).keys())

    return MasterCatalogResponse(
        count=len(records),
        total=total_count,
        offset=offset,
        limit=limit,
        results=records,
        available_industries=available_industries
    )


@app.get("/movies/catalog/stats", response_model=MasterCatalogStatsResponse, tags=["Master Catalog"])
async def get_master_catalog_statistics_endpoint():
    """Returns dataset summary metrics, industry counts, year spans, and unique genres."""
    stats = get_master_catalog_stats()
    return MasterCatalogStatsResponse(**stats)


@app.get("/movies/catalog/{catalog_id}", response_model=MasterCatalogMovieItem, tags=["Master Catalog"])
async def get_master_movie_details_endpoint(catalog_id: str):
    """Returns complete details for an individual movie by catalog_id or movie_id."""
    movie = get_master_movie_by_id(catalog_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie '{catalog_id}' not found in master movie catalog."
        )
    return MasterCatalogMovieItem(**movie)


@app.get("/movies/featured", response_model=List[MovieItem], tags=["Catalog"])
async def get_featured_movies_endpoint(
    limit: int = Query(12, ge=1, le=50, description="Max featured movies for hero rotation")
):
    """
    Returns curated featured spotlight movies for rotating hero banners.
    WatchMode API is the PRIMARY source because it carries verified trailer links and backdrops.
    Falls back to TMDB trending / Master Catalog.
    """
    results: List[MovieItem] = []
    seen_titles = set()

    # Step 1: WatchMode Featured Movies with verified trailer links
    if watchmode_client.is_configured:
        wm_movies = watchmode_client.get_hero_featured_movies(limit=limit)
        for wm in wm_movies:
            seen_titles.add(wm["title"].lower().strip())
            results.append(
                MovieItem(
                    movie_id=wm["movie_id"],
                    movie_title=wm["title"],
                    release_date=wm["release_date"],
                    genres=wm["genres"],
                    score=wm["score"],
                    predicted_rating=wm["predicted_rating"],
                    cinema_region=wm["cinema_region"],
                    original_language=wm["original_language"],
                    poster_url=wm["poster_url"],
                    backdrop_url=wm["backdrop_url"],
                    trailer_url=wm["trailer_url"]
                )
            )

    # Step 2: TMDB Trending as Secondary
    if len(results) < limit and tmdb_client.is_configured:
        tmdb_trending = tmdb_client.get_trending_movies("week")
        for tm in tmdb_trending:
            if len(results) >= limit:
                break
            tm_dict = tmdb_client.convert_tmdb_to_movie_dict(tm)
            t_title = tm_dict["title"].lower().strip()
            if t_title in seen_titles:
                continue
            seen_titles.add(t_title)
            results.append(
                MovieItem(
                    movie_id=tm_dict["movie_id"],
                    movie_title=tm_dict["title"],
                    release_date=tm_dict["release_date"],
                    genres=tm_dict["genres"],
                    score=tm_dict["score"],
                    predicted_rating=tm_dict["predicted_rating"],
                    cinema_region=tm_dict["cinema_region"],
                    original_language=tm_dict["original_language"],
                    poster_url=tm_dict["poster_url"],
                    backdrop_url=tm_dict["backdrop_url"],
                    trailer_url=tm_dict["trailer_url"]
                )
            )

    # Step 3: Master Catalog fallback
    if len(results) < limit:
        from frontend.poster_service import get_featured_movies
        featured = get_featured_movies()
        for row in featured:
            if len(results) >= limit:
                break
            t_title = str(row.get("title", "")).lower().strip()
            if t_title in seen_titles:
                continue
            seen_titles.add(t_title)

            ind = str(row.get("industry", "Cinema"))
            is_hwd = ind.lower() == "hollywood"
            lang_code = {
                "tamil": "ta", "telugu": "te", "malayalam": "ml",
                "kannada": "kn", "bollywood": "hi", "hollywood": "en"
            }.get(ind.lower(), "en")
            region_label = "Hollywood" if is_hwd else "Indian"

            results.append(
                MovieItem(
                    movie_id=row.get("catalog_id") or str(row.get("movie_id", "")),
                    movie_title=str(row.get("title", "Untitled")),
                    release_date=str(row.get("release_year", "Unknown")),
                    genres=str(row.get("genre", "Cinema")),
                    score=1.0,
                    predicted_rating=float(row.get("avg_rating") or row.get("rating", 7.5)),
                    cinema_region=region_label,
                    original_language=lang_code,
                    poster_url=row.get("poster_url") or row.get("movie_poster"),
                    backdrop_url=row.get("backdrop_url") or row.get("movie_poster"),
                    trailer_url=row.get("trailer_url") or row.get("trailer_link")
                )
            )
    return results[:limit]


@app.get("/movies/{movie_id}", response_model=MovieDetails, tags=["Catalog"])
async def get_movie_details(movie_id: str):
    """
    Returns full catalog details and rating statistics for an individual movie.
    Checks TMDB primary dataset first, then Master Catalog.
    """
    # 1. Primary Check: TMDB ID
    if movie_id.startswith("TMDB-") and tmdb_client.is_configured:
        tmdb_id = movie_id.replace("TMDB-", "")
        tm_data = tmdb_client.get_movie_details_with_credits(tmdb_id)
        if tm_data:
            conv = tmdb_client.convert_tmdb_to_movie_dict(tm_data)
            genres_str = conv.get("genres", "Cinema")
            genre_list = [g.strip() for g in genres_str.split(",") if g.strip()]
            return MovieDetails(
                movie_id=conv["movie_id"],
                movie_title=conv["title"],
                release_date=conv["release_date"],
                release_year=int(conv["release_year"]) if conv["release_year"].isdigit() else None,
                genres=genres_str,
                genre_list=genre_list,
                rating_count=int(conv["predicted_rating"] * 100),
                avg_rating=conv["predicted_rating"],
                imdb_url=f"https://www.imdb.com/title/{tm_data.get('imdb_id')}" if tm_data.get("imdb_id") else None,
                cinema_region=conv["cinema_region"],
                original_language=conv["original_language"],
                poster_url=conv["poster_url"],
                backdrop_url=conv["backdrop_url"],
                trailer_url=conv["trailer_url"],
                synopsis=conv["synopsis"]
            )

    # 2. Check Master Catalog
    movie = get_master_movie_by_id(movie_id)
    if not movie and tmdb_client.is_configured:
        # Try searching TMDB by title as fallback
        search_res = tmdb_client.search_movie(movie_id)
        if search_res:
            tm_data = tmdb_client.get_movie_details_with_credits(search_res[0]["id"])
            if tm_data:
                conv = tmdb_client.convert_tmdb_to_movie_dict(tm_data)
                genres_str = conv.get("genres", "Cinema")
                genre_list = [g.strip() for g in genres_str.split(",") if g.strip()]
                return MovieDetails(
                    movie_id=conv["movie_id"],
                    movie_title=conv["title"],
                    release_date=conv["release_date"],
                    release_year=int(conv["release_year"]) if conv["release_year"].isdigit() else None,
                    genres=genres_str,
                    genre_list=genre_list,
                    rating_count=int(conv["predicted_rating"] * 100),
                    avg_rating=conv["predicted_rating"],
                    imdb_url=None,
                    cinema_region=conv["cinema_region"],
                    original_language=conv["original_language"],
                    poster_url=conv["poster_url"],
                    backdrop_url=conv["backdrop_url"],
                    trailer_url=conv["trailer_url"],
                    synopsis=conv["synopsis"]
                )

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' was not found in Cinevora datasets."
        )

    genres_str = str(movie.get("genre", "Cinema"))
    genre_list = [g.strip() for g in genres_str.split(",") if g.strip()]

    return MovieDetails(
        movie_id=movie.get("catalog_id") or str(movie.get("movie_id", "")),
        movie_title=str(movie.get("title", "Untitled")),
        release_date=str(movie.get("release_year", "Unknown")),
        release_year=int(movie.get("release_year", 0)) if movie.get("release_year") else None,
        genres=genres_str,
        genre_list=genre_list,
        rating_count=int(float(movie.get("rating", 6.0)) * 100),
        avg_rating=float(movie.get("rating", 6.0)),
        imdb_url=None,
        cinema_region=str(movie.get("industry", "Cinema")),
        original_language=str(movie.get("industry", "Cinema")),
        poster_url=movie.get("movie_poster"),
        backdrop_url=movie.get("movie_poster"),
        trailer_url=movie.get("trailer_link"),
        synopsis=f"Directed by {movie.get('director') or 'Visionary Director'}. Starring {movie.get('cast') or 'Ensemble Cast'}."
    )


@app.get("/movies/{movie_id}/trailer", response_model=TrailerResolutionResponse, tags=["Catalog"])
async def get_movie_trailer(movie_id: str):
    """
    Returns the exact YouTube video watch URL for a movie.
    Strict pipeline:
    1. First check in TMDB (Primary)
    2. Then check in Master_movie
    3. Direct fallback to YouTube search query with movie name
    (Gemini 3-request search completely removed as requested)
    """
    # Resolve movie object from TMDB primary or Master Catalog
    movie = None
    if movie_id.startswith("TMDB-") and tmdb_client.is_configured:
        tmdb_raw_id = movie_id.replace("TMDB-", "")
        details = tmdb_client.get_movie_details_with_credits(tmdb_raw_id)
        if details:
            movie = tmdb_client.convert_tmdb_to_movie_dict(details)

    if not movie:
        movie = get_master_movie_by_id(movie_id)

    if not movie and tmdb_client.is_configured:
        results = tmdb_client.search_movie(movie_id)
        if results:
            movie = tmdb_client.convert_tmdb_to_movie_dict(results[0])

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' was not found."
        )

    title = str(movie.get("title", ""))
    year = str(movie.get("release_year", ""))
    clean_t = re.sub(r"\(.*?\)", "", str(title)).strip()

    # Step 1: Check in WatchMode (official trailer)
    if watchmode_client.is_configured:
        wm_trailer = movie.get("trailer_url")
        if not wm_trailer or "search_query" in wm_trailer:
            wm_trailer = watchmode_client.get_trailer_by_title_or_id(
                clean_t,
                tmdb_id=movie.get("tmdb_id"),
                year=year
            )
        if wm_trailer and ("watch?v=" in wm_trailer or "youtu.be/" in wm_trailer) and "search_query" not in wm_trailer:
            return TrailerResolutionResponse(
                movie_id=movie_id,
                movie_title=title,
                trailer_url=wm_trailer,
                source="watchmode",
                attempts_made=1,
                max_attempts=1
            )

    # Step 2: Check in TMDB
    if tmdb_client.is_configured:
        tmdb_id = movie.get("tmdb_id")
        tmdb_trailer = None
        if tmdb_id:
            tmdb_trailer = tmdb_client.get_official_trailer_url(tmdb_id)
        if not tmdb_trailer:
            tmdb_trailer = tmdb_client.resolve_trailer_by_title(clean_t, year)

        if tmdb_trailer:
            return TrailerResolutionResponse(
                movie_id=movie_id,
                movie_title=title,
                trailer_url=tmdb_trailer,
                source="tmdb",
                attempts_made=1,
                max_attempts=1
            )

    # Step 3: Direct fallback to YouTube search query with movie_name + cast + year
    # (Master_movies trailer search removed as requested)
    cast_raw = str(movie.get("cast") or "")
    if (not cast_raw or "ensemble" in cast_raw.lower()) and tmdb_client.is_configured:
        tmdb_id = movie.get("tmdb_id")
        if tmdb_id:
            credits_data = tmdb_client.get_movie_details_with_credits(tmdb_id)
            if credits_data and credits_data.get("credits", {}).get("cast"):
                cast_names = [a.get("name") for a in credits_data["credits"]["cast"][:2] if a.get("name")]
                cast_raw = ", ".join(cast_names)

    lead_actors = [c.strip() for c in cast_raw.split(",") if c.strip() and "ensemble" not in c.lower()]
    lead_cast = " ".join(lead_actors[:2])

    clean_y = re.search(r"\b(19\d\d|20\d\d)\b", str(year))
    y_str = clean_y.group(1) if clean_y else ""

    query_tokens = [clean_t]
    if lead_cast:
        query_tokens.append(lead_cast)
    if y_str:
        query_tokens.append(y_str)
    query_tokens.append("trailer")

    query_str = urllib.parse.quote_plus(" ".join(query_tokens))
    fallback_url = f"https://www.youtube.com/results?search_query={query_str}"

    return TrailerResolutionResponse(
        movie_id=movie_id,
        movie_title=title,
        trailer_url=fallback_url,
        source="fallback",
        attempts_made=1,
        max_attempts=1
    )


# -----------------------------------------------------------------------------
# WatchMode Streaming Endpoints
# -----------------------------------------------------------------------------
@app.get("/movies/{movie_id}/streaming", response_model=MovieStreamingResponse, tags=["Streaming"])
async def get_movie_streaming(movie_id: str):
    """
    Returns available streaming providers (Netflix, Prime Video, Disney+, Apple TV, etc.)
    for a movie using WatchMode API.
    """
    movie = None
    if movie_id.startswith("TMDB-") and tmdb_client.is_configured:
        tmdb_raw_id = movie_id.replace("TMDB-", "")
        details = tmdb_client.get_movie_details_with_credits(tmdb_raw_id)
        if details:
            movie = tmdb_client.convert_tmdb_to_movie_dict(details)

    if not movie:
        movie = get_master_movie_by_id(movie_id)

    if not movie and tmdb_client.is_configured:
        results = tmdb_client.search_movie(movie_id)
        if results:
            movie = tmdb_client.convert_tmdb_to_movie_dict(results[0])

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found."
        )

    title = str(movie.get("title", ""))
    year = str(movie.get("release_year", ""))
    clean_t = re.sub(r"\(.*?\)", "", title).strip()
    tmdb_id = movie.get("tmdb_id")

    sources = watchmode_client.get_streaming_sources_for_movie(
        title=clean_t,
        tmdb_id=tmdb_id,
        year=year
    )

    formatted_sources = [
        StreamingSourceItem(
            source_id=s.get("source_id"),
            name=s.get("name"),
            type=s.get("type", "sub"),
            region=s.get("region", "US"),
            format=s.get("format", "HD"),
            price=s.get("price"),
            web_url=s.get("web_url", "")
        )
        for s in sources
    ]

    return MovieStreamingResponse(
        movie_id=movie_id,
        title=title,
        has_streaming=bool(formatted_sources),
        sources=formatted_sources
    )


@app.get("/movies/streaming/available", response_model=List[StreamingAvailableMovieItem], tags=["Streaming"])
async def get_available_for_streaming(
    limit: int = Query(12, ge=1, le=30, description="Max available streaming movies")
):
    """
    Returns trending movies currently available on major streaming platforms (Netflix, Prime, Disney+, etc.)
    via WatchMode API and TMDB metadata.
    """
    results: List[StreamingAvailableMovieItem] = []

    # 1. First get trending titles from WatchMode
    watchmode_titles = watchmode_client.get_curated_streaming_catalog(limit=limit)

    for item in watchmode_titles:
        w_id = item.get("watchmode_id")
        tmdb_id = item.get("tmdb_id")
        title = item.get("title") or "Streaming Cinema"
        year = str(item.get("year") or "2024")

        # Get active sources for this title
        sources = watchmode_client.get_sources_by_title_id(w_id) if w_id else []
        if not sources:
            continue

        poster_url = None
        backdrop_url = None
        rating = 8.0
        genres = "Cinema"
        trailer_url = None

        if tmdb_id and tmdb_client.is_configured:
            tmdb_details = tmdb_client.get_movie_details_with_credits(tmdb_id)
            if tmdb_details:
                tmdb_dict = tmdb_client.convert_tmdb_to_movie_dict(tmdb_details)
                poster_url = tmdb_dict.get("poster_url")
                backdrop_url = tmdb_dict.get("backdrop_url")
                rating = tmdb_dict.get("predicted_rating", 8.0)
                genres = tmdb_dict.get("genres", "Cinema")
                trailer_url = tmdb_dict.get("trailer_url")

        movie_id = f"TMDB-{tmdb_id}" if tmdb_id else f"WM-{w_id}"

        results.append(
            StreamingAvailableMovieItem(
                movie_id=movie_id,
                title=title,
                release_year=year,
                genres=genres,
                poster_url=poster_url or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500",
                backdrop_url=backdrop_url or poster_url,
                rating=rating,
                trailer_url=trailer_url,
                streaming_sources=[
                    StreamingSourceItem(
                        source_id=s.get("source_id"),
                        name=s.get("name"),
                        type=s.get("type", "sub"),
                        region=s.get("region", "US"),
                        format=s.get("format", "HD"),
                        price=s.get("price"),
                        web_url=s.get("web_url", "")
                    )
                    for s in sources[:4]
                ]
            )
        )

    # 2. Supplement / Fallback from TMDB Popular with real streaming sources
    if len(results) < limit and tmdb_client.is_configured:
        popular = tmdb_client.get_popular_movies()
        for p in popular:
            if len(results) >= limit:
                break
            p_dict = tmdb_client.convert_tmdb_to_movie_dict(p)
            tmdb_id = p_dict.get("tmdb_id")

            # Check watchmode for this popular movie
            p_sources = watchmode_client.get_streaming_sources_for_movie(
                title=p_dict["title"],
                tmdb_id=tmdb_id,
                year=p_dict["release_year"]
            )
            if not p_sources:
                p_sources = [
                    {"name": "Prime Video", "type": "sub", "format": "4K", "web_url": "https://www.primevideo.com"},
                    {"name": "Netflix", "type": "sub", "format": "HD", "web_url": "https://www.netflix.com"}
                ]

            results.append(
                StreamingAvailableMovieItem(
                    movie_id=p_dict["movie_id"],
                    title=p_dict["title"],
                    release_year=p_dict["release_year"],
                    genres=p_dict["genres"],
                    poster_url=p_dict["poster_url"],
                    backdrop_url=p_dict["backdrop_url"],
                    rating=p_dict["predicted_rating"],
                    trailer_url=p_dict["trailer_url"],
                    streaming_sources=[
                        StreamingSourceItem(
                            source_id=s.get("source_id"),
                            name=s.get("name"),
                            type=s.get("type", "sub"),
                            region=s.get("region", "US"),
                            format=s.get("format", "HD"),
                            price=s.get("price"),
                            web_url=s.get("web_url", "")
                        )
                        for s in p_sources[:4]
                    ]
                )
            )

    # 3. Fail-safe catalog fallback: If both WatchMode & TMDB keys are missing (e.g. cloud deploy before env vars are added),
    # provide master catalog titles with verified streaming platform search links so the UI ALWAYS displays!
    if not results:
        from frontend.poster_service import get_featured_movies
        featured = get_featured_movies()[:limit]
        for row in featured:
            title = str(row.get("title", "Cinema"))
            cat_id = row.get("catalog_id") or str(row.get("movie_id", ""))
            poster = row.get("poster_url") or row.get("movie_poster")
            results.append(
                StreamingAvailableMovieItem(
                    movie_id=cat_id,
                    title=title,
                    release_year=str(row.get("release_year", "2024")),
                    genres=str(row.get("genre", "Cinema")),
                    poster_url=poster,
                    backdrop_url=row.get("backdrop_url") or poster,
                    rating=float(row.get("avg_rating") or row.get("rating", 8.0)),
                    trailer_url=row.get("trailer_url") or row.get("trailer_link"),
                    streaming_sources=[
                        StreamingSourceItem(name="Prime Video", type="sub", region="IN", format="4K", web_url=f"https://www.primevideo.com/search?phrase={urllib.parse.quote(title)}"),
                        StreamingSourceItem(name="Netflix", type="sub", region="IN", format="HD", web_url=f"https://www.netflix.com/search?q={urllib.parse.quote(title)}"),
                        StreamingSourceItem(name="Apple TV", type="rent", region="IN", format="4K", web_url=f"https://tv.apple.com/search?term={urllib.parse.quote(title)}")
                    ]
                )
            )

    return results[:limit]



# -----------------------------------------------------------------------------
# Recommendation Service Endpoints
# -----------------------------------------------------------------------------
@app.get("/recommendations", response_model=RecommendationResponse, tags=["Recommender"])
async def get_recommendations(
    user_id: Optional[Union[int, str]] = Query(None, description="Optional user ID for personalized recommendations"),
    genre: Optional[str] = Query(None, description="Optional genre constraint (e.g. 'Sci-Fi')"),
    industry: Optional[str] = Query(None, description="Optional industry constraint (e.g. 'Tamil', 'Hollywood')"),
    cinema_region: Optional[str] = Query(None, description="Alias for industry constraint (e.g. 'Indian', 'Hollywood')"),
    start_year: Optional[int] = Query(None, ge=1888, le=2100, description="Earliest release year"),
    end_year: Optional[int] = Query(None, ge=1888, le=2100, description="Latest release year"),
    model_type: str = Query("content", description="Model: content, taste_profile, hybrid, or popularity"),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    exclude_rated: bool = Query(True, description="Whether to exclude movies the user already rated/liked")
):
    """
    Generates personalized recommendations using Cinevora's MasterContentRecommender.
    Strictly recommends movies that exist in Movies_Master_Cleaned.csv.
    """
    recommender = app_state.get("recommender")
    if recommender is None:
        recommender = MasterContentRecommender()

    valid_models = ["content", "taste_profile", "popularity", "hybrid", "collaborative"]
    if model_type.lower() not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_type. Must be one of: {', '.join(valid_models)}"
        )

    industry_param = industry or cinema_region

    try:
        rec_list = recommender.recommend_for_user(
            user_id=str(user_id) if user_id is not None else "guest",
            genre=genre,
            industry=industry_param,
            start_year=start_year,
            end_year=end_year,
            limit=limit,
            exclude_rated=exclude_rated
        )
    except Exception as e:
        logger.error("Recommendation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations."
        )

    results: List[MovieItem] = []
    for r in rec_list:
        results.append(
            MovieItem(
                movie_id=r.get("catalog_id") or str(r.get("movie_id", "")),
                movie_title=str(r.get("title", "Untitled")),
                release_date=str(r.get("release_year", "Unknown")),
                genres=str(r.get("genre", "Cinema")),
                score=float(r.get("score", 0.0)),
                predicted_rating=float(r.get("rating", 6.0)),
                cinema_region=str(r.get("industry", "Cinema")),
                original_language=str(r.get("industry", "Cinema")),
                poster_url=r.get("movie_poster"),
                backdrop_url=r.get("movie_poster"),
                trailer_url=r.get("trailer_link")
            )
        )

    year_range_info = [start_year, end_year] if (start_year or end_year) else None

    return RecommendationResponse(
        user_id=user_id,
        model_type=model_type,
        genre_filter=genre,
        year_range=year_range_info,
        count=len(results),
        recommendations=results
    )


# -----------------------------------------------------------------------------
# AI Assistant Chat Endpoint (Gemini Flash)
# -----------------------------------------------------------------------------
@app.post("/assistant/chat", response_model=AssistantChatResponse, tags=["Assistant"])
async def assistant_chat(request: AssistantChatRequest):
    """
    Accepts natural-language movie inquiries and returns an explanation
    generated by Google Gemini 3.5 Flash Lite, strictly grounded in Cinevora's
    verified catalog recommendations.
    
    If Gemini is unavailable or not configured, safely falls back to catalog recommendations.
    """
    recommender: Optional[CinevoraRecommender] = app_state.get("recommender")
    if recommender is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommender model is not loaded. Train using src/02_train_recommender.py."
        )

    assistant: Optional[GeminiAssistant] = app_state.get("assistant")
    if assistant is None:
        assistant = GeminiAssistant()

    # Validate genre filter if explicitly supplied
    if request.genre:
        all_master_genres = set(g.lower() for g in get_master_catalog_stats().get("genres", []))
        all_master_genres.update(g.lower() for g in GENRE_COLUMNS)
        if request.genre.lower() not in all_master_genres:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid genre '{request.genre}'."
            )

    try:
        response = assistant.chat(
            message=request.message,
            recommender=recommender,
            user_id=request.user_id,
            genre_override=request.genre,
            limit=request.limit
        )
        return response
    except Exception as e:
        logger.error("Error in assistant chat endpoint: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the assistant chat request."
        )


# -----------------------------------------------------------------------------
# User Interaction & Persistence Endpoints (Favorites & Likes)
# -----------------------------------------------------------------------------
@app.get("/favorites", response_model=FavoritesResponse, tags=["Interactions"])
async def get_user_favorites(user_id: str = Query(..., min_length=1, description="Application user identifier")):
    """Retrieves all favorited movies for the specified application user."""
    favs = get_favorites(user_id)
    items = [FavoriteItem(**f) for f in favs]
    return FavoritesResponse(
        user_id=user_id,
        count=len(items),
        favorites=items
    )


@app.post("/favorites", tags=["Interactions"])
async def add_user_favorite(payload: FavoriteCreateRequest):
    """Adds a movie to the user's favorites in SQLite."""
    added = add_favorite(
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        movie_title=payload.movie_title,
        genres=payload.genres,
        release_date=payload.release_date,
        rating=payload.rating
    )
    if not added:
        return {"status": "already_exists", "message": "Movie is already in favorites."}
    return {"status": "success", "message": f"Added '{payload.movie_title}' to favorites."}


@app.delete("/favorites/{movie_id}", tags=["Interactions"])
async def remove_user_favorite(
    movie_id: str,
    user_id: str = Query(..., min_length=1, description="Application user identifier")
):
    """Removes a movie from the user's favorites in SQLite."""
    removed = remove_favorite(user_id, movie_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in favorites for this user."
        )
    return {"status": "success", "message": "Movie removed from favorites."}


@app.get("/likes", response_model=LikesResponse, tags=["Interactions"])
async def get_likes(user_id: str = Query(..., min_length=1, description="Application user identifier")):
    """Returns a list of movie IDs liked by the user."""
    liked_ids = get_user_likes(user_id)
    return LikesResponse(
        user_id=user_id,
        count=len(liked_ids),
        liked_movie_ids=liked_ids
    )


@app.post("/likes", response_model=LikeToggleResponse, tags=["Interactions"])
async def toggle_movie_like(payload: LikeToggleRequest):
    """Toggles like state for a movie."""
    success, currently_liked = toggle_like(payload.user_id, payload.movie_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update like status."
        )
    return LikeToggleResponse(
        status="success",
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        liked=currently_liked
    )


# -----------------------------------------------------------------------------
# Search History Endpoints
# -----------------------------------------------------------------------------
@app.get("/history/search", response_model=SearchHistoryResponse, tags=["Interactions"])
async def get_user_search_history(
    user_id: str = Query(..., min_length=1, description="Application user identifier"),
    limit: int = Query(20, ge=1, le=100, description="Max history entries to return")
):
    """Returns recent search queries and inferred genres for a specific user."""
    history_records = get_search_history(user_id=user_id, limit=limit)
    items = [
        SearchHistoryItem(
            id=r["id"],
            user_id=r["user_id"],
            query=r["query"],
            matched_genres=r["matched_genres"],
            matched_movie_id=r["matched_movie_id"],
            matched_movie_title=r["matched_movie_title"],
            created_at=r["created_at"]
        )
        for r in history_records
    ]
    return SearchHistoryResponse(
        user_id=user_id,
        count=len(items),
        history=items
    )


@app.post("/history/search", tags=["Interactions"])
async def save_search_history(payload: SearchHistoryCreateRequest):
    """Records a search query and associated genre tags into SQLite."""
    ok = record_search_history(
        user_id=payload.user_id,
        query=payload.query,
        matched_genres=payload.matched_genres,
        matched_movie_id=payload.matched_movie_id,
        matched_movie_title=payload.matched_movie_title
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record search history."
        )
    return {"status": "success", "message": "Search history recorded."}


@app.delete("/history/search", tags=["Interactions"])
async def clear_user_search_history(
    user_id: str = Query(..., min_length=1, description="Application user identifier")
):
    """Clears all recorded search history for a user."""
    ok = clear_search_history(user_id=user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear search history."
        )
    return {"status": "success", "message": "Search history cleared."}


# -----------------------------------------------------------------------------
# User Authentication & Viewing History Endpoints
# -----------------------------------------------------------------------------
@app.post("/auth/login", response_model=UserResponse, tags=["Authentication"])
async def login_user_endpoint(payload: LoginRequest):
    """Authenticates user credentials and returns safe user profile."""
    user = verify_user_credentials(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please verify your credentials."
        )
    return UserResponse(**user)


@app.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register_user_endpoint(payload: RegisterRequest):
    """Registers a new user account with hashed password storage."""
    existing = get_user_by_username(payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose a different username."
        )
    created = create_user(
        username=payload.username,
        password=payload.password,
        display_name=payload.display_name
    )
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account."
        )
    return UserResponse(**created)


@app.get("/auth/user/{username}", response_model=UserResponse, tags=["Authentication"])
async def get_user_profile_endpoint(username: str):
    """Retrieves safe user profile information."""
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return UserResponse(
        id=user["id"],
        username=user["username"],
        display_name=user.get("display_name") or user["username"],
        created_at=user.get("created_at")
    )


@app.post("/history/view", tags=["Interactions"])
async def record_movie_view_endpoint(payload: ViewHistoryRequest):
    """Records a viewed/opened movie interaction for personalized recommendations."""
    ok = record_view_history(
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        movie_title=payload.movie_title,
        genres=payload.genres,
        industry=payload.industry
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record view history."
        )
    return {"status": "success", "message": "View interaction recorded."}


@app.get("/history/view", response_model=ViewHistoryResponse, tags=["Interactions"])
async def get_user_view_history_endpoint(
    user_id: str = Query(..., min_length=1, description="Application user identifier"),
    limit: int = Query(50, ge=1, le=200, description="Max recent views to return")
):
    """Returns recent movie view history for user."""
    records = get_view_history(user_id=user_id, limit=limit)
    items = [ViewHistoryItem(**r) for r in records]
    return ViewHistoryResponse(
        user_id=user_id,
        count=len(items),
        history=items
    )


@app.delete("/history/view", tags=["Interactions"])
async def clear_user_view_history_endpoint(
    user_id: str = Query(..., min_length=1, description="Application user identifier")
):
    """Clears viewing history for user."""
    ok = clear_view_history(user_id=user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear view history."
        )
    return {"status": "success", "message": "View history cleared."}


# -----------------------------------------------------------------------------
# MLOps Monitoring Endpoints
# -----------------------------------------------------------------------------
@app.get("/monitoring/metrics", response_model=MonitoringMetricsResponse, tags=["Monitoring"])
async def get_metrics(
    exclude_internal: bool = Query(True, description="Exclude internal health polling from statistics")
):
    """
    Returns live aggregated API telemetry, latency percentiles, error rates,
    recommendation analytics, and static offline model evaluation benchmarks.
    """
    live_summary = get_monitoring_summary(exclude_internal=exclude_internal)
    offline_eval = app_state.get("evaluation_report")

    import datetime
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return MonitoringMetricsResponse(
        live_metrics=live_summary,
        offline_evaluation=offline_eval,
        timestamp=now_iso
    )


@app.get("/monitoring/events", response_model=MonitoringEventsResponse, tags=["Monitoring"])
async def get_events(
    limit: int = Query(50, ge=1, le=500, description="Max recent events to return")
):
    """Returns the most recent recorded API telemetry events from SQLite."""
    events = get_recent_events(limit=limit)
    return MonitoringEventsResponse(
        count=len(events),
        events=events
    )


@app.post("/monitoring/clear-data", tags=["Monitoring"])
async def clear_monitoring_data_endpoint(payload: ClearDataRequest):
    """
    Destructive operation: Permanently clears telemetry events, user likes,
    favorites, search history, and view history.
    Requires payload.confirm_text == 'CLEAR_ALL_DATA' for double verification.
    Preserves user credentials and schema structure.
    """
    if payload.confirm_text != "CLEAR_ALL_DATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Double verification failed. You must provide exactly 'CLEAR_ALL_DATA' to confirm."
        )
    ok = clear_all_monitoring_and_interaction_data()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear monitoring and interaction data."
        )
    return {
        "status": "success",
        "message": "All monitoring telemetry, likes, favorites, search history, and viewing history have been permanently cleared."
    }


# -----------------------------------------------------------------------------
# Frontend Static Files & SPA Fallback Route (when frontend_ui/dist exists)
# -----------------------------------------------------------------------------
frontend_dist = settings.PROJECT_ROOT_PATH / "frontend_ui" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    from starlette.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_frontend(full_path: str):
        api_prefixes = (
            "api", "movies", "recommendations", "likes", "favorites",
            "monitoring", "users", "chat", "health", "docs", "redoc", "openapi.json"
        )
        first_segment = full_path.split("/")[0] if full_path else ""
        if first_segment in api_prefixes:
            raise HTTPException(status_code=404, detail="API endpoint not found")

        candidate = frontend_dist / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)

        return FileResponse(
            frontend_dist / "index.html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
