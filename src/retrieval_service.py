"""
Cinevora Hybrid Movie Retrieval and Verification Service
Implements:
1. Deterministic metadata filtering for factual queries against Movies_Master_Cleaned.csv.
2. Token-level person-name matching with alias resolution (e.g. Vijay -> Joseph Vijay).
3. TF-IDF + Cosine Similarity Semantic Retrieval for plot, theme, and similarity queries.
4. Strict Result-Validation Layer (verifying catalog ID, actor, director, genre, industry, year).
5. 100% decoupling from user profile personalization (no bias in search results).
"""

import os
import re
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.catalog_service import (
    load_master_catalog,
    get_master_catalog_path,
    normalize_industry_filter,
    get_master_movie_by_id
)

logger = logging.getLogger("cinevora.retrieval")

# Explicit person aliases mapping public/popular names to exact catalog credits
PERSON_ALIASES: Dict[str, List[str]] = {
    "vijay": ["joseph vijay", "thalapathy vijay", "vijay"],
    "thalapathy vijay": ["joseph vijay", "thalapathy vijay", "vijay"],
    "thalapathy": ["joseph vijay", "thalapathy vijay"],
    "rajinikanth": ["rajinikanth", "rajini", "superstar rajinikanth"],
    "rajini": ["rajinikanth", "rajini"],
    "kamal haasan": ["kamal haasan", "kamal hassan", "kamal"],
    "kamal hassan": ["kamal haasan", "kamal hassan"],
    "shah rukh khan": ["shah rukh khan", "shahrukh khan", "srk"],
    "shahrukh khan": ["shah rukh khan", "shahrukh khan", "srk"],
    "srk": ["shah rukh khan", "shahrukh khan"],
    "ajith": ["ajith kumar", "ajith"],
    "ajith kumar": ["ajith kumar", "ajith"],
    "suriya": ["suriya", "surya"],
    "surya": ["suriya", "surya"],
    "dhanush": ["dhanush", "dhanush k raja"],
    "vikram": ["chiyaan vikram", "vikram", "kennedy john victor"],
    "chiyaan vikram": ["chiyaan vikram", "vikram"],
    "christopher nolan": ["christopher nolan", "nolan"],
    "nolan": ["christopher nolan", "nolan"],
    "lokesh kanagaraj": ["lokesh kanagaraj"],
    "lokesh": ["lokesh kanagaraj"],
    "quentin tarantino": ["quentin tarantino", "tarantino"],
    "tarantino": ["quentin tarantino", "tarantino"],
    "steven spielberg": ["steven spielberg", "spielberg"],
    "spielberg": ["steven spielberg", "spielberg"]
}


@dataclass
class QueryFilters:
    """Structured query filters for factual and semantic retrieval."""
    actor: Optional[str] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    industry: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    title: Optional[str] = None
    similar_to: Optional[str] = None
    semantic_query: Optional[str] = None
    free_query: Optional[str] = None


def matches_person_name(field_val: Any, target_name: str) -> bool:
    """
    Safely matches a person's name against a delimited string (e.g. cast or director).
    Rules:
    - Normalizes case, whitespace, and punctuation.
    - Resolves known aliases (e.g. 'Vijay' -> 'Joseph Vijay').
    - Performs token-level word matching. Single letter tokens (e.g. 'V' in BTS) NEVER match 'Vijay'.
    - Compound names (e.g. 'Vanitha Vijayakumar') do not produce false positive matches for 'Vijay'.
    """
    if not field_val or not target_name:
        return False

    raw_target = str(target_name).strip().lower()
    clean_target = re.sub(r"[^\w\s]", "", raw_target).strip()
    if not clean_target:
        return False

    # Build candidate target list (target + any configured aliases)
    candidate_targets = [clean_target]
    if clean_target in PERSON_ALIASES:
        candidate_targets.extend(PERSON_ALIASES[clean_target])

    # Deduplicate while preserving order
    seen = set()
    candidate_targets = [c for c in candidate_targets if not (c in seen or seen.add(c))]

    # Delimited cast/director members
    members = re.split(r"[,|;/]+", str(field_val).lower())
    for member in members:
        clean_m = re.sub(r"[^\w\s]", "", member).strip()
        if not clean_m:
            continue

        m_tokens = clean_m.split()
        if not m_tokens:
            continue

        for cand in candidate_targets:
            cand_tokens = cand.split()
            # 1. Exact member match
            if clean_m == cand:
                return True

            # 2. Multi-word target match (e.g. "lokesh kanagaraj" in member "lokesh kanagaraj")
            if len(cand_tokens) > 1:
                if cand in clean_m:
                    return True
            else:
                # 3. Single-word target match (e.g. "vijay", "nolan")
                # Must match a complete token in the member's tokens list
                # E.g. "vijay" in ["joseph", "vijay"] -> True
                # E.g. "vijay" in ["v"] -> False!
                # E.g. "vijay" in ["vanitha", "vijayakumar"] -> False!
                if cand in m_tokens:
                    return True

    return False


class SemanticSearchEngine:
    """
    Lightweight, fast, and deterministic semantic retrieval engine
    using TF-IDF vectorization and cosine similarity over master catalog metadata.
    Index is cached to disk and rebuilt automatically if the CSV is updated.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path(__file__).resolve().parent.parent / "data" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "semantic_index.pkl"
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None
        self._catalog_ids: List[str] = []
        self._initialized = False

    def is_cache_valid(self, csv_path: Path) -> bool:
        """Checks if the cached semantic index is newer than the master CSV."""
        if not self.cache_file.exists():
            return False
        try:
            return self.cache_file.stat().st_mtime >= csv_path.stat().st_mtime
        except Exception:
            return False

    def build_or_load_index(self, df: pd.DataFrame, force_rebuild: bool = False):
        """Builds or loads the TF-IDF vector index for all 3,560 catalog movies."""
        csv_path = get_master_catalog_path()
        if not force_rebuild and self.is_cache_valid(csv_path):
            try:
                with open(self.cache_file, "rb") as f:
                    data = pickle.load(f)
                    self._vectorizer = data["vectorizer"]
                    self._matrix = data["matrix"]
                    self._catalog_ids = data["catalog_ids"]
                    self._initialized = True
                    logger.info("Loaded semantic retrieval index from %s", self.cache_file)
                    return
            except Exception as e:
                logger.warning("Failed loading cached semantic index (%s). Rebuilding...", e)

        # Build index from scratch
        logger.info("Building TF-IDF semantic index for %d catalog movies...", len(df))
        documents = []
        ids = []
        for _, row in df.iterrows():
            cid = str(row["catalog_id"])
            title = str(row.get("title", ""))
            genre = str(row.get("genre", ""))
            industry = str(row.get("industry", ""))
            director = str(row.get("director", ""))
            cast = str(row.get("cast", ""))
            rating = str(row.get("rating", ""))
            
            doc = f"{title} {genre} {industry} Directed by {director}. Starring {cast}. Rating {rating}."
            documents.append(doc)
            ids.append(cid)

        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=25000)
        matrix = vec.fit_transform(documents)

        self._vectorizer = vec
        self._matrix = matrix
        self._catalog_ids = ids
        self._initialized = True

        try:
            with open(self.cache_file, "wb") as f:
                pickle.dump({
                    "vectorizer": vec,
                    "matrix": matrix,
                    "catalog_ids": ids
                }, f)
            logger.info("Successfully persisted semantic index to %s", self.cache_file)
        except Exception as e:
            logger.warning("Failed to persist semantic index to %s: %s", self.cache_file, e)

    def query_similarity(self, query_text: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """Computes cosine similarity between query and all catalog documents."""
        if not self._initialized or self._vectorizer is None or self._matrix is None:
            return []
        try:
            q_vec = self._vectorizer.transform([query_text])
            sims = cosine_similarity(q_vec, self._matrix).flatten()
            top_indices = sims.argsort()[::-1][:top_k]
            results = []
            for idx in top_indices:
                score = float(sims[idx])
                if score > 0.01:
                    results.append((self._catalog_ids[idx], score))
            return results
        except Exception as e:
            logger.error("Error during semantic similarity query: %s", e)
            return []


class MovieRetrievalService:
    """
    Dedicated Movie Retrieval Service providing:
    - Deterministic filtering across all catalog metadata.
    - Semantic retrieval integration.
    - Strict result validation layer.
    - Complete independence from user profile history.
    """

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self.semantic_engine = SemanticSearchEngine()

    def get_catalog(self, force_reload: bool = False) -> pd.DataFrame:
        """Returns the master cleaned movie dataset."""
        if self._df is None or force_reload:
            self._df = load_master_catalog(force_reload=force_reload)
            self.semantic_engine.build_or_load_index(self._df, force_rebuild=force_reload)
        return self._df

    def validate_candidate_movies(
        self,
        candidates: List[Dict[str, Any]],
        filters: QueryFilters
    ) -> List[Dict[str, Any]]:
        """
        Phase 4: Strict Result-Validation Layer.
        Enforces:
        1. Movie ID exists in master catalog.
        2. Requested actor verified in cast metadata (token-level).
        3. Requested director verified in director metadata.
        4. Requested genre verified in genre metadata.
        5. Requested industry verified in industry metadata.
        6. Requested release year range verified.
        7. Deduplicates candidate movies by catalog ID.
        8. Preserves original metadata and artwork links.
        9. Rejects candidates failing ANY explicit filter.
        """
        df = self.get_catalog()
        valid_ids: Set[str] = set(df["catalog_id"].values)
        verified: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()

        for cand in candidates:
            cid = str(cand.get("catalog_id") or cand.get("movie_id") or "").strip()
            # 1. Movie ID must exist in master catalog
            if not cid or cid not in valid_ids:
                continue

            # 4. Remove duplicate movie IDs
            if cid in seen_ids:
                continue

            # Retrieve pristine master record
            master_row = get_master_movie_by_id(cid, df=df)
            if not master_row:
                continue

            # 2. Confirm requested actor is verified in cast metadata
            if filters.actor and str(filters.actor).strip():
                if not matches_person_name(master_row.get("cast", ""), filters.actor):
                    continue

            # 3. Confirm requested director
            if filters.director and str(filters.director).strip():
                if not matches_person_name(master_row.get("director", ""), filters.director):
                    continue

            # 4. Confirm requested genre
            if filters.genre and str(filters.genre).strip() and str(filters.genre).strip().lower() not in ["all", "all genres", "any"]:
                g_req = str(filters.genre).strip().lower()
                cat_genres = str(master_row.get("genre", "")).lower()
                # Skip validation if genre metadata is missing/null (\N) — don't exclude these movies
                if cat_genres and cat_genres not in [r"\n", "nan", "none", ""]:
                    # Split genre tokens
                    tokens = [t.strip() for t in cat_genres.replace("|", ",").split(",") if t.strip()]
                    if not any(g_req in tok for tok in tokens):
                        continue

            # 5. Confirm requested industry / language
            if filters.industry and str(filters.industry).strip():
                norm_req = normalize_industry_filter(filters.industry)
                cat_ind = str(master_row.get("industry", "")).strip().lower()
                if norm_req:
                    if norm_req == "Indian":
                        if cat_ind not in ["bollywood", "tamil", "telugu", "malayalam", "kannada"]:
                            continue
                    elif cat_ind != norm_req.lower():
                        continue

            # 6. Confirm release year constraints
            rel_year = int(master_row.get("release_year", 0))
            if filters.year_from is not None:
                if rel_year < int(filters.year_from):
                    continue
            if filters.year_to is not None:
                if rel_year > int(filters.year_to):
                    continue

            # 7. Confirm title constraint if provided
            if filters.title and str(filters.title).strip():
                t_req = str(filters.title).strip().lower()
                cat_t = str(master_row.get("title", "")).strip().lower()
                if t_req not in cat_t:
                    continue

            # All checks passed: include verified master record
            seen_ids.add(cid)
            # Copy candidate extra fields (e.g. score, suggestion_reason) if present
            merged_rec = dict(master_row)
            if "score" in cand:
                merged_rec["score"] = cand["score"]
            if "suggestion_reason" in cand:
                merged_rec["suggestion_reason"] = cand["suggestion_reason"]
            verified.append(merged_rec)

        return verified

    def search(
        self,
        filters: QueryFilters,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Executes hybrid retrieval:
        - If similar_to or semantic_query is requested: runs semantic retrieval.
        - Otherwise runs deterministic metadata retrieval.
        - Applies Phase 4 strict result validation layer.
        - Never falls back to popular titles when filters produce 0 matches.
        """
        df = self.get_catalog()
        if df.empty:
            return [], 0

        # Route A: Semantic / Similarity Retrieval
        # For 'similar_to': find movies similar to a reference film - ONLY route A
        # For 'semantic_query': find thematically matching movies, BUT apply metadata filters afterwards
        if (filters.similar_to and str(filters.similar_to).strip()) or (filters.semantic_query and str(filters.semantic_query).strip()):
            query_str = ""
            if filters.similar_to:
                # Find the reference movie text
                ref_sim = df[df["title"].str.lower().str.contains(str(filters.similar_to).strip().lower(), na=False, regex=False)]
                if not ref_sim.empty:
                    ref_r = ref_sim.iloc[0]
                    query_str = f"{ref_r['title']} {ref_r['genre']} {ref_r['industry']} Directed by {ref_r['director']} Starring {ref_r['cast']}"
                else:
                    query_str = str(filters.similar_to).strip()
            else:
                query_str = str(filters.semantic_query).strip()

            sem_results = self.semantic_engine.query_similarity(query_str, top_k=200)
            candidate_dicts = []
            for cid, score in sem_results:
                row = get_master_movie_by_id(cid, df=df)
                if row:
                    item = dict(row)
                    item["score"] = round(score, 3)
                    candidate_dicts.append(item)

            # Apply deterministic metadata filters on top of semantic candidates
            # This ensures industry/genre/actor filters are respected even in semantic mode
            if filters.industry and str(filters.industry).strip():
                norm_ind = normalize_industry_filter(filters.industry)
                if norm_ind:
                    if norm_ind == "Indian":
                        candidate_dicts = [m for m in candidate_dicts if str(m.get("industry", "")).lower() in ["bollywood", "tamil", "telugu", "malayalam", "kannada"]]
                    else:
                        candidate_dicts = [m for m in candidate_dicts if str(m.get("industry", "")).lower() == norm_ind.lower()]

            if filters.genre and str(filters.genre).strip() and str(filters.genre).strip().lower() not in ["all", "all genres", "any"]:
                g_req = str(filters.genre).strip().lower()
                candidate_dicts = [m for m in candidate_dicts if g_req in str(m.get("genre", "")).lower()]

            if filters.actor and str(filters.actor).strip():
                act_req = str(filters.actor).strip()
                candidate_dicts = [m for m in candidate_dicts if matches_person_name(str(m.get("cast", "")), act_req)]

            if filters.director and str(filters.director).strip():
                dir_req = str(filters.director).strip()
                candidate_dicts = [m for m in candidate_dicts if matches_person_name(str(m.get("director", "")), dir_req)]

            if filters.year_from is not None:
                candidate_dicts = [m for m in candidate_dicts if int(m.get("release_year", 0)) >= int(filters.year_from)]
            if filters.year_to is not None:
                candidate_dicts = [m for m in candidate_dicts if int(m.get("release_year", 9999)) <= int(filters.year_to)]

            # Apply strict result validation (dedup, validate IDs)
            verified = self.validate_candidate_movies(candidate_dicts, filters)
            
            # If reference movie was given, exclude it from results
            if filters.similar_to:
                ref_m = str(filters.similar_to).strip().lower()
                verified = [m for m in verified if ref_m not in str(m.get("title", "")).lower()]

            # Sort primarily by semantic relevance score, then by rating as tiebreaker
            verified.sort(key=lambda m: (float(m.get("score", 0) or 0), float(m.get("rating", 0) or 0)), reverse=True)

            if verified:
                total_count = len(verified)
                paginated = verified[offset: offset + limit]
                return paginated, total_count
            elif not any([filters.actor, filters.director, filters.genre, filters.industry, filters.year_from, filters.year_to]):
                # Pure semantic query with no metadata filters and no matches
                return [], 0
            # If semantic query yielded no hits but factual metadata filters exist, fall through to Route B

        # Route B: Deterministic Metadata Retrieval
        filtered = df.copy()

        # Resolve actor vs director if query heuristic misassigned a director to actor
        act_val = str(filters.actor).strip() if filters.actor else ""
        dir_val = str(filters.director).strip() if filters.director else ""

        if act_val and not dir_val:
            cast_hits = filtered["cast"].apply(lambda c: matches_person_name(c, act_val)).sum()
            dir_hits = filtered["director"].apply(lambda d: matches_person_name(d, act_val)).sum()
            if cast_hits == 0 and dir_hits > 0:
                dir_val = act_val
                act_val = ""
        elif act_val and dir_val and act_val.lower() == dir_val.lower():
            cast_hits = filtered["cast"].apply(lambda c: matches_person_name(c, act_val)).sum()
            dir_hits = filtered["director"].apply(lambda d: matches_person_name(d, dir_val)).sum()
            if cast_hits == 0 and dir_hits > 0:
                act_val = ""
            elif dir_hits == 0 and cast_hits > 0:
                dir_val = ""

        # 1. Actor constraint
        if act_val:
            actor_mask = filtered["cast"].apply(lambda c: matches_person_name(c, act_val))
            filtered = filtered[actor_mask]
            if filtered.empty:
                return [], 0

        # 2. Director constraint
        if dir_val:
            dir_mask = filtered["director"].apply(lambda d: matches_person_name(d, dir_val))
            filtered = filtered[dir_mask]
            if filtered.empty:
                return [], 0

        # 3. Genre constraint
        if filters.genre and str(filters.genre).strip() and str(filters.genre).strip().lower() not in ["all", "all genres", "any"]:
            g_req = str(filters.genre).strip().lower()
            filtered = filtered[filtered["genre"].str.lower().str.contains(g_req, na=False, regex=False)]
            if filtered.empty:
                return [], 0

        # 4. Industry constraint
        if filters.industry and str(filters.industry).strip():
            norm_ind = normalize_industry_filter(filters.industry)
            if norm_ind:
                if norm_ind == "Indian":
                    filtered = filtered[filtered["industry"].str.lower().isin(["bollywood", "tamil", "telugu", "malayalam", "kannada"])]
                else:
                    filtered = filtered[filtered["industry"].str.lower() == norm_ind.lower()]
            if filtered.empty:
                return [], 0

        # 5. Year constraints
        if filters.year_from is not None:
            filtered = filtered[filtered["release_year"] >= int(filters.year_from)]
        if filters.year_to is not None:
            filtered = filtered[filtered["release_year"] <= int(filters.year_to)]
        if filtered.empty:
            return [], 0

        # 6. Title constraint
        if filters.title and str(filters.title).strip():
            t_req = str(filters.title).strip().lower()
            filtered = filtered[filtered["title"].str.lower().str.contains(t_req, na=False, regex=False)]
            if filtered.empty:
                return [], 0

        # 7. General free query
        # Only apply free_query filter if no explicit structured filters were provided
        has_structured = any([
            act_val,
            dir_val,
            filters.genre and str(filters.genre).strip().lower() not in ["all", "all genres", "any"],
            filters.industry and str(filters.industry).strip(),
            filters.year_from is not None,
            filters.year_to is not None,
            filters.title and str(filters.title).strip()
        ])
        if filters.free_query and str(filters.free_query).strip() and not has_structured:
            fq = str(filters.free_query).strip().lower()
            t_m = filtered["title"].str.lower().str.contains(fq, na=False, regex=False)
            c_m = filtered["cast"].str.lower().str.contains(fq, na=False, regex=False)
            d_m = filtered["director"].str.lower().str.contains(fq, na=False, regex=False)
            filtered = filtered[t_m | c_m | d_m]
            if filtered.empty:
                return [], 0

        if filtered.empty:
            return [], 0

        # Ranking logic:
        # If actor is Vijay / Thalapathy Vijay, prioritize lead billing (Joseph Vijay as lead)
        if act_val and "vijay" in act_val.lower():
            def vijay_rank(row):
                cast_str = str(row.get("cast", ""))
                members = [re.sub(r"[^\w\s]", "", m).strip().lower() for m in cast_str.split(",")]
                if members and ("joseph vijay" in members[0] or members[0] == "vijay"):
                    return 100.0 + float(row.get("rating", 0.0))
                if any("joseph vijay" in m for m in members):
                    return 50.0 + float(row.get("rating", 0.0))
                return float(row.get("rating", 0.0))

            filtered["_rank"] = filtered.apply(vijay_rank, axis=1)
            filtered = filtered.sort_values(by="_rank", ascending=False)
        else:
            filtered = filtered.sort_values(by="rating", ascending=False)

        candidate_dicts = filtered.to_dict(orient="records")

        # Pass candidates through Phase 4 strict validation layer
        verified = self.validate_candidate_movies(candidate_dicts, filters)
        total_count = len(verified)
        paginated = verified[offset: offset + limit]

        return paginated, total_count


# Global singleton instance
movie_retrieval_service = MovieRetrievalService()

__all__ = [
    "PERSON_ALIASES",
    "QueryFilters",
    "matches_person_name",
    "SemanticSearchEngine",
    "MovieRetrievalService",
    "movie_retrieval_service"
]
