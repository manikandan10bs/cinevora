"""
Cinevora Master Movie Catalog Service
Safely loads, caches, and filters the combined Indian + Hollywood master dataset:
'data/processed/Movies_Master_Cleaned.csv' (3,560 titles).

Features:
- Relative path resolution from project root
- Safe handling of missing files, empty CSVs, missing values, and malformed URLs
- In-memory DataFrame caching
- Multi-industry filtering with normalization for aliases (Kollywood, Tollywood, Mollywood, Sandalwood, Bollywood, Hollywood)
- Fast substring search, genre matching, release year bounds, and rating thresholds
- Pagination and robust sorting (rating, newest, alphabetical title)
- Safe unique identifier support ('catalog_id' like 'CINEVORA-0000001')
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import logging

logger = logging.getLogger("cinevora.catalog")

# Project Root Resolution
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DEFAULT_MASTER_CSV = PROJECT_ROOT / "data" / "processed" / "Movies_Master_Cleaned.csv"

# Global In-Memory Cache
_MASTER_CATALOG_CACHE: Optional[pd.DataFrame] = None

# Normalized Industry Aliases
INDUSTRY_NORMALIZATION_MAP: Dict[str, str] = {
    # Pan-Indian
    "indian": "Indian",
    "india": "Indian",
    # Bollywood / Hindi
    "bollywood": "Bollywood",
    "hindi": "Bollywood",
    "hi": "Bollywood",
    "bollywood/hindi": "Bollywood",
    "bollywood (hindi)": "Bollywood",
    # Kollywood / Tamil
    "tamil": "Tamil",
    "kollywood": "Tamil",
    "ta": "Tamil",
    "kollywood/tamil": "Tamil",
    "kollywood (tamil)": "Tamil",
    # Tollywood / Telugu
    "telugu": "Telugu",
    "tollywood": "Telugu",
    "te": "Telugu",
    "tollywood/telugu": "Telugu",
    "tollywood (telugu)": "Telugu",
    # Mollywood / Malayalam
    "malayalam": "Malayalam",
    "mollywood": "Malayalam",
    "ml": "Malayalam",
    "mollywood/malayalam": "Malayalam",
    "mollywood (malayalam)": "Malayalam",
    # Sandalwood / Kannada
    "kannada": "Kannada",
    "sandalwood": "Kannada",
    "kn": "Kannada",
    "kannada/sandalwood": "Kannada",
    "sandalwood (kannada)": "Kannada",
    # Hollywood / American
    "hollywood": "Hollywood",
    "american": "Hollywood",
    "english": "Hollywood",
    "en": "Hollywood",
    "hollywood (english)": "Hollywood",
    # Bengali
    "bengali": "Bengali",
    "tollywood (bengali)": "Bengali",
    "bengali cinema": "Bengali",
}

EXPECTED_COLUMNS = [
    "catalog_id",
    "movie_id",
    "industry",
    "title",
    "release_year",
    "genre",
    "rating",
    "cast",
    "director",
    "movie_poster",
    "trailer_link",
    "metadata_source",
    "poster_source",
    "trailer_source",
    "collection_method"
]


def get_master_catalog_path() -> Path:
    """Returns the absolute path to the master cleaned movie dataset."""
    return DEFAULT_MASTER_CSV


def normalize_industry_filter(user_input: Optional[str]) -> Optional[str]:
    """
    Normalizes industry filter aliases into canonical names in the dataset.
    Returns None if 'All' or empty.
    """
    if not user_input or not str(user_input).strip():
        return None

    cleaned = str(user_input).strip().lower()
    if cleaned in ["all", "all industries", "all regions", "any"]:
        return None

    # Exact alias match
    if cleaned in INDUSTRY_NORMALIZATION_MAP:
        return INDUSTRY_NORMALIZATION_MAP[cleaned]

    # Keyword check
    for alias_key, canonical in INDUSTRY_NORMALIZATION_MAP.items():
        if alias_key in cleaned:
            return canonical

    return str(user_input).strip()


def is_valid_url(url: Any) -> bool:
    """Checks whether a string is a non-empty, well-formed HTTP/HTTPS URL."""
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    return u.startswith("http://") or u.startswith("https://")


def load_master_catalog(
    csv_path: Optional[Path] = None,
    force_reload: bool = False
) -> pd.DataFrame:
    """
    Safely loads and caches the master cleaned movie dataset.
    Handles missing files, empty files, missing values, and invalid data gracefully.
    """
    global _MASTER_CATALOG_CACHE

    if _MASTER_CATALOG_CACHE is not None and not force_reload:
        return _MASTER_CATALOG_CACHE

    target_path = Path(csv_path) if csv_path else get_master_catalog_path()

    if not target_path.exists():
        logger.warning("Master movie dataset not found at %s. Returning empty DataFrame.", target_path)
        empty_df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        if not force_reload:
            _MASTER_CATALOG_CACHE = empty_df
        return empty_df

    try:
        # Check for zero-byte or empty file
        if target_path.stat().st_size == 0:
            logger.warning("Master movie dataset at %s is empty (0 bytes).", target_path)
            empty_df = pd.DataFrame(columns=EXPECTED_COLUMNS)
            if not force_reload:
                _MASTER_CATALOG_CACHE = empty_df
            return empty_df

        df = pd.read_csv(target_path, encoding="utf-8", dtype=str)
        if df.empty:
            empty_df = pd.DataFrame(columns=EXPECTED_COLUMNS)
            if not force_reload:
                _MASTER_CATALOG_CACHE = empty_df
            return empty_df

        # Ensure all expected columns are present
        for col in EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Clean catalog_id: Ensure non-empty string fallback
        df["catalog_id"] = df["catalog_id"].fillna("").astype(str).str.strip()
        mask_missing_cat = df["catalog_id"] == ""
        if mask_missing_cat.any():
            df.loc[mask_missing_cat, "catalog_id"] = [
                f"CINEVORA-{i+1:07d}" for i in range(mask_missing_cat.sum())
            ]

        # Clean title
        df["title"] = df["title"].fillna("Untitled Movie").astype(str).str.strip()

        # Clean industry
        df["industry"] = df["industry"].fillna("Cinema").astype(str).str.strip()

        # Clean release_year safely to integer
        def parse_year(val):
            if pd.isna(val):
                return 0
            try:
                # Handle possible float string like '2023.0' or '2023'
                return int(float(val))
            except (ValueError, TypeError):
                # Regex search for 4-digit year
                m = re.search(r"(\d{4})", str(val))
                return int(m.group(1)) if m else 0

        df["release_year"] = df["release_year"].apply(parse_year)

        # Clean rating safely to float [0.0, 10.0]
        def parse_rating(val):
            if pd.isna(val):
                return 0.0
            try:
                r = float(val)
                if r < 0.0:
                    return 0.0
                if r > 10.0:
                    return 10.0
                return round(r, 2)
            except (ValueError, TypeError):
                return 0.0

        df["rating"] = df["rating"].apply(parse_rating)

        # Clean genre
        df["genre"] = df["genre"].fillna("Cinema").astype(str).str.strip()
        df["genre"] = df["genre"].replace(r"\\N", "Cinema", regex=True)

        # Clean cast & director
        df["cast"] = df["cast"].fillna("").astype(str).str.strip()
        df["cast"] = df["cast"].replace(r"\\N", "", regex=True)
        df["director"] = df["director"].fillna("").astype(str).str.strip()
        df["director"] = df["director"].replace(r"\\N", "", regex=True)

        # Validate URLs: Set malformed or non-http URLs to None
        df["movie_poster"] = df["movie_poster"].apply(lambda u: u.strip() if is_valid_url(u) else None)
        df["trailer_link"] = df["trailer_link"].apply(lambda u: u.strip() if is_valid_url(u) else None)

        if not force_reload:
            _MASTER_CATALOG_CACHE = df

        logger.info("Successfully loaded %d master movies from %s", len(df), target_path.name)
        return df

    except Exception as e:
        logger.error("Error reading master catalog from %s: %s", target_path, e)
        empty_df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        if not force_reload:
            _MASTER_CATALOG_CACHE = empty_df
        return empty_df


def matches_person_name(field_val: Any, target_name: str) -> bool:
    """
    Safely matches a person's name against a delimited string (e.g. cast or director).
    Handles:
    - Normalization of whitespace, case, and punctuation.
    - Delimited comma/pipe separation.
    - Word boundary matching (e.g. target 'Vijay' matches 'Joseph Vijay' or 'Vijay Sethupathi').
    - Multi-word matching (e.g. 'Shah Rukh Khan', 'Christopher Nolan', 'Lokesh Kanagaraj').
    """
    if not field_val or not target_name:
        return False
    t = target_name.strip().lower()
    t = re.sub(r"[^\w\s]", "", t).strip()
    if not t:
        return False

    # Canonical alias mapping for famous actors
    if t in ["vijay", "thalapathy", "thalapathy vijay"] and "joseph vijay" in str(field_val).lower():
        return True

    members = re.split(r"[,|;/]+", str(field_val).lower())
    for member in members:
        clean_m = re.sub(r"[^\w\s]", "", member).strip()
        if not clean_m:
            continue
        if t == clean_m:
            return True
        if len(t.split()) > 1:
            if t in clean_m or clean_m in t:
                return True
        else:
            if re.search(r"\b" + re.escape(t) + r"\b", clean_m):
                return True
    return False


def query_master_catalog(
    df: Optional[pd.DataFrame] = None,
    query: Optional[str] = None,
    actor: Optional[str] = None,
    director: Optional[str] = None,
    title: Optional[str] = None,
    similar_to: Optional[str] = None,
    industry: Optional[str] = None,
    genre: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "rating",
    limit: int = 24,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Filters and paginates the master movie dataset using deterministic criteria.
    Supports specific actor (cast), director, title, genre, industry, year bounds, and general query.
    Returns: (list_of_movie_dicts, total_matching_count)
    """
    if df is None:
        df = load_master_catalog()

    if df.empty:
        return [], 0

    filtered = df.copy()

    # 1. Explicit Actor (Cast) Filter
    if actor and str(actor).strip():
        act_clean = str(actor).strip()
        actor_mask = filtered["cast"].apply(lambda c: matches_person_name(c, act_clean))
        filtered = filtered[actor_mask]

    # 2. Explicit Director Filter
    if director and str(director).strip():
        dir_clean = str(director).strip()
        director_mask = filtered["director"].apply(lambda d: matches_person_name(d, dir_clean))
        filtered = filtered[director_mask]

    # 3. Explicit Title Filter
    if title and str(title).strip():
        t_clean = str(title).strip().lower()
        title_mask = filtered["title"].str.lower().str.contains(t_clean, na=False, regex=False)
        filtered = filtered[title_mask]

    # 4. Similar To Reference Title
    if similar_to and str(similar_to).strip():
        sim_q = str(similar_to).strip().lower()
        sim_ref = df[df["title"].str.lower().str.contains(sim_q, na=False, regex=False)]
        if not sim_ref.empty:
            ref_row = sim_ref.iloc[0]
            ref_cid = ref_row["catalog_id"]
            ref_genre = str(ref_row.get("genre", "")).split(",")[0].strip().lower()
            ref_ind = str(ref_row.get("industry", "")).strip().lower()
            # Exclude the reference movie itself
            filtered = filtered[filtered["catalog_id"] != ref_cid]
            # Filter or boost by matching genre/industry if no other filter applied
            if not genre and ref_genre:
                genre_matches = filtered["genre"].str.lower().str.contains(ref_genre, na=False)
                if genre_matches.any():
                    filtered = filtered[genre_matches]

    # 5. General Free-Text Search Query (searches title, cast, and director)
    has_text_query = bool(query and str(query).strip())
    if has_text_query:
        q_clean = str(query).strip().lower()

        def _calc_query_relevance(row: Any) -> float:
            title = str(row.get("title") or "").lower()
            cast = str(row.get("cast") or "").lower()
            director = str(row.get("director") or "").lower()
            genre = str(row.get("genre") or "").lower()
            rel = 0.0

            # Exact title match
            if title == q_clean:
                rel += 150.0
            elif title.startswith(q_clean):
                rel += 110.0
            elif q_clean in title:
                rel += 80.0

            # Prominent Actor Matching
            if q_clean in ["vijay", "thalapathy", "thalapathy vijay", "joseph vijay"]:
                if "joseph vijay" in cast or "thalapathy vijay" in cast:
                    rel += 260.0
                elif re.search(r"\bvijay\b", cast):
                    rel += 150.0
            elif cast:
                members = [m.strip() for m in cast.split(",")]
                for idx, m in enumerate(members[:4]):
                    if q_clean == m:
                        rel += max(120.0 - (idx * 20.0), 60.0)
                        break
                    elif re.search(r"\b" + re.escape(q_clean) + r"\b", m):
                        rel += max(90.0 - (idx * 15.0), 40.0)
                        break
                    elif q_clean in m:
                        rel += max(50.0 - (idx * 10.0), 20.0)
                        break

            # Director matching
            if director:
                if q_clean == director:
                    rel += 95.0
                elif q_clean in director:
                    rel += 70.0

            # Genre matching
            if genre and q_clean in genre:
                rel += 40.0

            return rel

        filtered["_search_rel"] = filtered.apply(_calc_query_relevance, axis=1)
        filtered = filtered[filtered["_search_rel"] > 0]

    # 6. Industry Filtering with Alias Normalization
    normalized_ind = normalize_industry_filter(industry)
    if normalized_ind:
        if normalized_ind == "Indian":
            filtered = filtered[filtered["industry"].str.lower().isin(["bollywood", "tamil", "telugu", "malayalam", "kannada"])]
        else:
            filtered = filtered[filtered["industry"].str.lower() == normalized_ind.lower()]

    # 7. Genre Filtering (case-insensitive substring inside comma-separated genre string)
    if genre and str(genre).strip() and str(genre).strip().lower() not in ["all", "all genres", "any"]:
        g_clean = str(genre).strip().lower()
        filtered = filtered[filtered["genre"].str.lower().str.contains(g_clean, na=False, regex=False)]

    # 8. Release Year Bounds
    if start_year is not None:
        filtered = filtered[filtered["release_year"] >= int(start_year)]
    if end_year is not None:
        filtered = filtered[filtered["release_year"] <= int(end_year)]

    # 9. Rating Threshold
    if min_rating is not None:
        try:
            mr_val = float(min_rating)
            if mr_val > 0.0:
                filtered = filtered[filtered["rating"] >= mr_val]
        except (ValueError, TypeError):
            pass

    total_count = len(filtered)
    if total_count == 0:
        return [], 0

    # 10. Sorting with Relevance Weighting
    sort_clean = (sort_by or "rating").lower()
    if actor and str(actor).strip():
        act_target = str(actor).strip().lower()
        def _calc_actor_rel(cast_val: Any) -> float:
            c_low = str(cast_val).lower()
            if act_target in ["vijay", "thalapathy vijay", "joseph vijay"]:
                if "joseph vijay" in c_low or "thalapathy vijay" in c_low:
                    return 100.0
            members = [m.strip() for m in c_low.split(",")]
            for idx, m in enumerate(members):
                pos_weight = 1.0 / (1.0 + 0.15 * idx)
                if m == act_target:
                    return 90.0 * pos_weight
                if m.startswith(act_target + " "):
                    return 75.0 * pos_weight
                if act_target in m:
                    return 50.0 * pos_weight
            return 10.0

        filtered["_actor_rel"] = filtered["cast"].apply(_calc_actor_rel)
        filtered = filtered.sort_values(by=["_actor_rel", "rating", "release_year"], ascending=[False, False, False])
    elif director and str(director).strip():
        dir_target = str(director).strip().lower()
        def _calc_dir_rel(dir_val: Any) -> float:
            d_low = str(dir_val).lower()
            if d_low == dir_target:
                return 100.0
            if d_low.startswith(dir_target):
                return 80.0
            if dir_target in d_low:
                return 50.0
            return 10.0

        filtered["_dir_rel"] = filtered["director"].apply(_calc_dir_rel)
        filtered = filtered.sort_values(by=["_dir_rel", "rating", "release_year"], ascending=[False, False, False])
    elif has_text_query and "_search_rel" in filtered.columns and sort_clean in ["relevance", "rating", "highest rated", "top rated", "popularity"]:
        filtered = filtered.sort_values(by=["_search_rel", "rating", "release_year"], ascending=[False, False, False])
    elif sort_clean in ["rating", "highest rated", "top rated", "popularity"]:
        filtered = filtered.sort_values(by=["rating", "release_year"], ascending=[False, False])
    elif sort_clean in ["newest", "newest release", "year"]:
        filtered = filtered.sort_values(by=["release_year", "rating"], ascending=[False, False])
    elif sort_clean in ["title", "alphabetical", "a-z"]:
        filtered = filtered.sort_values(by="title", ascending=True)
    else:
        filtered = filtered.sort_values(by=["rating", "release_year"], ascending=[False, False])

    # 11. Pagination
    safe_offset = max(0, int(offset))
    safe_limit = max(1, min(100, int(limit)))
    paged = filtered.iloc[safe_offset : safe_offset + safe_limit]

    # Convert to standard dictionary items with NaN converted to None
    records = paged.to_dict(orient="records")
    clean_records = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]
    return clean_records, total_count


def get_master_movie_by_id(
    identifier: Any,
    df: Optional[pd.DataFrame] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieves full details for a single movie by catalog_id (e.g. 'CINEVORA-0000001')
    or movie_id.
    """
    if df is None:
        df = load_master_catalog()

    if df.empty or identifier is None:
        return None

    id_str = str(identifier).strip()

    # Match by catalog_id first
    cat_match = df[df["catalog_id"] == id_str]
    if not cat_match.empty:
        raw_dict = cat_match.iloc[0].to_dict()
        return {k: (None if pd.isna(v) else v) for k, v in raw_dict.items()}

    # Match by movie_id
    mid_match = df[df["movie_id"].astype(str) == id_str]
    if not mid_match.empty:
        raw_dict = mid_match.iloc[0].to_dict()
        return {k: (None if pd.isna(v) else v) for k, v in raw_dict.items()}

    return None


def get_master_catalog_stats(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Computes summary statistics and filter options from the master catalog."""
    if df is None:
        df = load_master_catalog()

    if df.empty:
        return {
            "total_movies": 0,
            "industries": {},
            "genres": [],
            "year_min": 2021,
            "year_max": 2025,
            "avg_rating": 0.0,
            "trailers_count": 0
        }

    industry_counts = df["industry"].value_counts().to_dict()

    # Collect unique genres
    all_genres = set()
    for g_str in df["genre"].dropna():
        for g in str(g_str).split(","):
            cleaned = g.strip()
            if cleaned and cleaned != "\\N" and len(cleaned) > 1:
                all_genres.add(cleaned)

    valid_years = df[df["release_year"] > 1800]["release_year"]
    y_min = int(valid_years.min()) if not valid_years.empty else 2021
    y_max = int(valid_years.max()) if not valid_years.empty else 2025

    avg_r = float(df[df["rating"] > 0]["rating"].mean()) if (df["rating"] > 0).any() else 0.0
    trailer_count = int(df["trailer_link"].notna().sum())

    return {
        "total_movies": len(df),
        "industries": industry_counts,
        "genres": sorted(list(all_genres)),
        "year_min": y_min,
        "year_max": y_max,
        "avg_rating": round(avg_r, 2),
        "trailers_count": trailer_count
    }


def get_similar_catalog_movies_by_genre(
    catalog_id: str,
    n: int = 6,
    df: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    """
    Recommends similar movies from the master catalog based on shared genre and industry.
    Preserves strict separation from MovieLens trained models without inventing collaborative scores.
    """
    if df is None:
        df = load_master_catalog()

    target = get_master_movie_by_id(catalog_id, df=df)
    if not target or df.empty:
        return []

    target_genres = set([g.strip().lower() for g in str(target.get("genre", "")).split(",") if g.strip()])
    target_industry = str(target.get("industry", "")).lower()

    candidates = df[df["catalog_id"] != target.get("catalog_id")].copy()

    def similarity_score(row):
        r_genres = set([g.strip().lower() for g in str(row["genre"]).split(",") if g.strip()])
        overlap = len(target_genres.intersection(r_genres))
        ind_bonus = 1.0 if str(row["industry"]).lower() == target_industry else 0.0
        rating_val = float(row.get("rating", 0.0)) / 10.0
        return overlap * 2.0 + ind_bonus + rating_val

    candidates["sim_score"] = candidates.apply(similarity_score, axis=1)
    top_candidates = candidates.sort_values(by="sim_score", ascending=False).head(n)
    return top_candidates.to_dict(orient="records")

