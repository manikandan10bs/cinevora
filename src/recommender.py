"""
Cinevora - Recommender Engine Module
Contains the core recommendation logic, including:
1. Popularity Baseline (Bayesian Damped Rating)
2. Content-Based Filtering (Genre Cosine Similarity & User Genre Profiling)
3. Collaborative Filtering (TruncatedSVD Matrix Factorization)
4. Hybrid Recommendation (Normalized Weighted Blend with Fallbacks)
5. Hard Constraint Filtering (Genre Filtering & Exclusion of Already-Rated Items)
"""

from typing import Dict, List, Optional, Set, Tuple, Union, Any
import logging
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

logger = logging.getLogger("cinevora.recommender")


def _ensure_backend_app_package() -> None:
    """
    Ensures that the backend 'app' package is resolvable and not shadowed
    by frontend/app.py if Streamlit added frontend/ to sys.path.
    """
    if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
        del sys.modules["app"]

    project_root = str(Path(__file__).resolve().parent.parent)
    frontend_dir = str(Path(project_root) / "frontend")

    while frontend_dir in sys.path:
        sys.path.remove(frontend_dir)
    while "frontend" in sys.path:
        sys.path.remove("frontend")

    if project_root in sys.path:
        sys.path.remove(project_root)
    sys.path.insert(0, project_root)


_ensure_backend_app_package()


GENRE_COLUMNS = [
    "unknown",
    "Action",
    "Adventure",
    "Animation",
    "Children's",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western"
]


class CinevoraRecommender:
    """
    Modular Recommender System implementing Popularity, Content-Based,
    Collaborative Filtering (SVD), and Hybrid scoring for Cinevora.
    """

    def __init__(
        self,
        n_latent_factors: int = 20,
        random_state: int = 42,
        popularity_prior_weight: float = 25.0,
        weight_cf: float = 0.50,
        weight_content: float = 0.35,
        weight_popularity: float = 0.15
    ):
        """
        Parameters:
        -----------
        n_latent_factors : Number of latent components for TruncatedSVD.
        random_state : Seed for reproducibility.
        popularity_prior_weight : m0 parameter in Bayesian damped average rating.
                                  Prevents movies with 1-2 ratings from dominating popularity.
        weight_cf : Baseline weight for collaborative filtering in the hybrid model.
        weight_content : Baseline weight for content-based matching in the hybrid model.
        weight_popularity : Baseline weight for popularity fallback in the hybrid model.
        
        Note on weights:
        The weights (0.50 CF, 0.35 Content, 0.15 Popularity) are documented heuristic choices
        designed to balance personalized collaborative signals, content relevance, and item
        quality priors. They are NOT hyperparameter-tuned on the test set.
        """
        self.n_latent_factors = n_latent_factors
        self.random_state = random_state
        self.m0 = popularity_prior_weight

        self.weight_cf = weight_cf
        self.weight_content = weight_content
        self.weight_popularity = weight_popularity

        # Metadata & Mapping structures
        self.movie_metadata: Optional[pd.DataFrame] = None
        self.all_movie_ids: np.ndarray = np.array([])
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}

        self.all_user_ids: np.ndarray = np.array([])
        self.user_id_to_idx: Dict[int, int] = {}
        self.idx_to_user_id: Dict[int, int] = {}

        self.train_user_movies: Dict[int, Set[int]] = {}
        self.global_mean_rating: float = 3.5

        # Component models
        self.genre_matrix: Optional[np.ndarray] = None
        self.movie_years: Optional[np.ndarray] = None
        self.popularity_scores: Optional[np.ndarray] = None
        self.bayesian_ratings: Optional[np.ndarray] = None

        self.user_profiles: Optional[np.ndarray] = None
        self.svd_model: Optional[TruncatedSVD] = None
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None
        self.user_means: Optional[np.ndarray] = None

    def _extract_movie_years(self) -> np.ndarray:
        """
        Extracts release year integer for each catalog item.
        Prioritizes the production/release year in title '(YYYY)',
        then falls back to 'release_date' (DD-Mon-YYYY).
        Returns 0 for missing or unparseable years.
        """
        if self.movie_metadata is None:
            return np.zeros(len(self.all_movie_ids), dtype=np.int32)

        years = np.zeros(len(self.all_movie_ids), dtype=np.int32)
        for i in range(len(self.all_movie_ids)):
            row = self.movie_metadata.iloc[i]
            title = str(row.get("movie_title", ""))
            m_title = re.search(r"\((\d{4})\)", title)
            if m_title:
                years[i] = int(m_title.group(1))
            else:
                rd = str(row.get("release_date", ""))
                m_rd = re.search(r"(\d{4})", rd)
                years[i] = int(m_rd.group(1)) if m_rd else 0
        return years

    def fit(self, train_ratings: pd.DataFrame, movies_df: pd.DataFrame) -> "CinevoraRecommender":
        """
        Fits all recommendation sub-models using the training ratings and movie metadata.
        No test ratings should be passed to this function.
        """
        # 1. Setup Movie Metadata & Indices
        self.movie_metadata = movies_df.copy()
        self.all_movie_ids = self.movie_metadata["movie_id"].values
        self.movie_id_to_idx = {mid: i for i, mid in enumerate(self.all_movie_ids)}
        self.idx_to_movie_id = {i: mid for i, mid in enumerate(self.all_movie_ids)}
        n_movies = len(self.all_movie_ids)

        # Build Genre Matrix (Binary indicators)
        self.genre_matrix = self.movie_metadata[GENRE_COLUMNS].values.astype(np.float32)
        self.movie_years = self._extract_movie_years()

        # 2. Setup User Indices & Training Interactions
        self.all_user_ids = np.sort(train_ratings["user_id"].unique())
        self.user_id_to_idx = {uid: i for i, uid in enumerate(self.all_user_ids)}
        self.idx_to_user_id = {i: uid for i, uid in enumerate(self.all_user_ids)}
        n_users = len(self.all_user_ids)

        self.train_user_movies = train_ratings.groupby("user_id")["movie_id"].apply(set).to_dict()
        self.global_mean_rating = float(train_ratings["rating"].mean())

        # 3. Fit Popularity Baseline (Bayesian Damped Rating)
        # S(m) = (v / (v + m0)) * R + (m0 / (v + m0)) * C
        movie_counts = train_ratings.groupby("movie_id")["rating"].agg(count="count", mean="mean").to_dict(orient="index")
        
        self.bayesian_ratings = np.zeros(n_movies, dtype=np.float32)
        for i, mid in enumerate(self.all_movie_ids):
            stats = movie_counts.get(mid, {"count": 0, "mean": self.global_mean_rating})
            v = stats["count"]
            r = stats["mean"]
            b_rating = (v / (v + self.m0)) * r + (self.m0 / (v + self.m0)) * self.global_mean_rating
            self.bayesian_ratings[i] = b_rating

        # Normalize popularity scores to [0, 1] range
        p_min = self.bayesian_ratings.min()
        p_max = self.bayesian_ratings.max()
        if p_max > p_min:
            self.popularity_scores = (self.bayesian_ratings - p_min) / (p_max - p_min)
        else:
            self.popularity_scores = np.ones(n_movies, dtype=np.float32) * 0.5

        # 4. Fit Content-Based Recommender (User Genre Profiles)
        # For each user, build preference profile vector from movies rated positively (>= 3.0),
        # weighted by centered rating (rating - 2.5).
        self.user_profiles = np.zeros((n_users, len(GENRE_COLUMNS)), dtype=np.float32)
        for uid, group in train_ratings.groupby("user_id"):
            u_idx = self.user_id_to_idx[uid]
            positive_ratings = group[group["rating"] >= 3.0]
            if len(positive_ratings) > 0:
                for _, row in positive_ratings.iterrows():
                    m_idx = self.movie_id_to_idx.get(int(row["movie_id"]))
                    if m_idx is not None:
                        w = float(row["rating"]) - 2.5
                        self.user_profiles[u_idx] += w * self.genre_matrix[m_idx]
                norm = np.linalg.norm(self.user_profiles[u_idx])
                if norm > 0:
                    self.user_profiles[u_idx] /= norm

        # 5. Fit Collaborative Filtering Model (TruncatedSVD)
        # Build interaction matrix (users x movies)
        R = np.zeros((n_users, n_movies), dtype=np.float32)
        mask = np.zeros_like(R, dtype=bool)

        for _, row in train_ratings.iterrows():
            u_idx = self.user_id_to_idx.get(int(row["user_id"]))
            m_idx = self.movie_id_to_idx.get(int(row["movie_id"]))
            if u_idx is not None and m_idx is not None:
                R[u_idx, m_idx] = float(row["rating"])
                mask[u_idx, m_idx] = True

        # Compute user means for mean-centering (handles user rating bias)
        self.user_means = np.zeros(n_users, dtype=np.float32)
        for i in range(n_users):
            user_ratings = R[i, mask[i]]
            self.user_means[i] = user_ratings.mean() if len(user_ratings) > 0 else self.global_mean_rating

        # Center rated entries; unrated entries remain 0 (neutral relative to user mean)
        R_centered = np.zeros_like(R)
        for i in range(n_users):
            R_centered[i, mask[i]] = R[i, mask[i]] - self.user_means[i]

        # Decompose centered matrix using TruncatedSVD
        self.svd_model = TruncatedSVD(
            n_components=min(self.n_latent_factors, n_users - 1, n_movies - 1),
            random_state=self.random_state
        )
        self.user_factors = self.svd_model.fit_transform(R_centered)
        self.item_factors = self.svd_model.components_

        return self

    def predict_rating(self, user_id: int, movie_id: int) -> float:
        """
        Predicts an explicit 1-5 star rating using the Collaborative Filtering model.
        Falls back to Bayesian movie rating or global mean for unseen users/movies.
        """
        u_idx = self.user_id_to_idx.get(user_id)
        m_idx = self.movie_id_to_idx.get(movie_id)

        # Fallback if movie is unknown
        if m_idx is None:
            return self.global_mean_rating

        # Fallback if user is unknown (cold-start)
        if u_idx is None:
            return float(self.bayesian_ratings[m_idx])

        # Collaborative prediction: r_hat = u_factors * item_factors + user_mean
        pred = float(np.dot(self.user_factors[u_idx], self.item_factors[:, m_idx])) + self.user_means[u_idx]
        return float(np.clip(pred, 1.0, 5.0))

    def _get_cf_scores(self, user_idx: int) -> np.ndarray:
        """
        Computes predicted ratings for all movies for a given training user index,
        normalized to [0, 1].
        """
        preds = np.dot(self.user_factors[user_idx], self.item_factors) + self.user_means[user_idx]
        preds = np.clip(preds, 1.0, 5.0)
        # Min-max scale from [1.0, 5.0] to [0.0, 1.0]
        return (preds - 1.0) / 4.0

    def _get_content_scores(self, user_idx: Optional[int], custom_genre_prefs: Optional[List[str]] = None) -> np.ndarray:
        """
        Computes cosine similarity between user profile (or explicit genre preferences)
        and all movie genre vectors. Values are in [0, 1].
        """
        profile = np.zeros((1, len(GENRE_COLUMNS)), dtype=np.float32)

        if custom_genre_prefs:
            for g in custom_genre_prefs:
                if g in GENRE_COLUMNS:
                    idx = GENRE_COLUMNS.index(g)
                    profile[0, idx] = 1.0
            norm = np.linalg.norm(profile[0])
            if norm > 0:
                profile[0] /= norm
        elif user_idx is not None and user_idx < len(self.user_profiles):
            profile[0] = self.user_profiles[user_idx]
        else:
            # No user history or explicit genre preference
            return np.zeros(len(self.all_movie_ids), dtype=np.float32)

        sims = cosine_similarity(profile, self.genre_matrix)[0]
        return np.clip(sims, 0.0, 1.0).astype(np.float32)

    def recommend(
        self,
        user_id: Optional[int] = None,
        n: int = 10,
        model_type: str = "hybrid",
        genre_filter: Optional[str] = None,
        year_range: Optional[Tuple[int, int]] = None,
        exclude_rated: bool = True,
        custom_genre_prefs: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Generates Top-N movie recommendations with optional hard constraints.

        Parameters:
        -----------
        user_id : User ID (if known). If None or unknown, falls back gracefully.
        n : Number of recommendations to return.
        model_type : One of 'hybrid', 'collaborative', 'content', 'popularity'.
        genre_filter : Hard genre constraint (e.g. 'Comedy', 'Action').
                       Only movies tagged with this genre will be returned.
        year_range : Optional (start_year, end_year) inclusive range constraint.
                     Only movies released within this window will be returned.
        exclude_rated : If True and user_id is known, excludes movies already in user's training set.
        custom_genre_prefs : List of genres to build an ad-hoc content profile for new users.

        Returns:
        --------
        pd.DataFrame containing recommended movies with metadata and recommendation score.
        """
        if self.movie_metadata is None:
            raise ValueError("The recommender model must be fitted before calling recommend().")

        n_movies = len(self.all_movie_ids)
        u_idx = self.user_id_to_idx.get(user_id) if user_id is not None else None
        is_unknown_user = (u_idx is None)

        # 1. Compute Base Scores based on model_type
        if model_type == "popularity" or (is_unknown_user and not custom_genre_prefs and model_type == "collaborative"):
            # Pure popularity baseline
            scores = self.popularity_scores.copy()

        elif model_type == "content":
            scores = self._get_content_scores(u_idx, custom_genre_prefs)
            # If user has no content profile, blend popularity
            if np.all(scores == 0.0):
                scores = self.popularity_scores.copy()

        elif model_type == "collaborative":
            scores = self._get_cf_scores(u_idx)

        elif model_type == "hybrid":
            # For cold-start users without collaborative history:
            if is_unknown_user:
                if custom_genre_prefs:
                    cnt_scores = self._get_content_scores(None, custom_genre_prefs)
                    # Blend content preferences with popularity fallback
                    scores = 0.60 * cnt_scores + 0.40 * self.popularity_scores
                else:
                    # Fallback directly to popularity for brand-new users
                    scores = self.popularity_scores.copy()
            else:
                # Active user: Combine CF, Content, and Popularity
                cf_scores = self._get_cf_scores(u_idx)
                cnt_scores = self._get_content_scores(u_idx)
                pop_scores = self.popularity_scores

                scores = (
                    self.weight_cf * cf_scores +
                    self.weight_content * cnt_scores +
                    self.weight_popularity * pop_scores
                )
        else:
            raise ValueError(f"Unknown model_type '{model_type}'. Choose from 'hybrid', 'collaborative', 'content', 'popularity'.")

        scores = scores.copy()

        # 2. Hard Constraint: Exclude already-rated movies from training
        if exclude_rated and user_id is not None and user_id in self.train_user_movies:
            rated_mids = self.train_user_movies[user_id]
            for mid in rated_mids:
                m_idx = self.movie_id_to_idx.get(mid)
                if m_idx is not None:
                    scores[m_idx] = -np.inf

        # 3. Hard Constraint: Genre & Release Year Filtering
        if genre_filter:
            if genre_filter not in GENRE_COLUMNS:
                # Genre requested does not exist in dataset -> return empty result
                return pd.DataFrame(columns=["movie_id", "movie_title", "release_date", "genres", "score", "predicted_rating"])
            genre_col_idx = GENRE_COLUMNS.index(genre_filter)
            genre_matches = (self.genre_matrix[:, genre_col_idx] == 1)
            # Mask out non-matching movies
            scores[~genre_matches] = -np.inf

        if year_range:
            start_year, end_year = year_range
            if self.movie_years is None:
                self.movie_years = self._extract_movie_years()
            year_matches = (self.movie_years >= start_year) & (self.movie_years <= end_year)
            scores[~year_matches] = -np.inf

        # Filter out movies that have been masked to -inf
        candidate_mask = (scores > -np.inf)
        if not np.any(candidate_mask):
            return pd.DataFrame(columns=["movie_id", "movie_title", "release_date", "genres", "score", "predicted_rating"])

        # 4. Rank Candidate Movies by Score
        valid_movie_indices = np.where(candidate_mask)[0]
        valid_scores = scores[valid_movie_indices]

        # Select top-N
        top_k = min(n, len(valid_scores))
        if top_k == 0:
            return pd.DataFrame(columns=["movie_id", "movie_title", "release_date", "genres", "score", "predicted_rating"])

        top_k_rel_indices = np.argpartition(-valid_scores, top_k - 1)[:top_k]
        top_k_rel_indices = top_k_rel_indices[np.argsort(-valid_scores[top_k_rel_indices])]
        top_movie_indices = valid_movie_indices[top_k_rel_indices]

        # 5. Build Result DataFrame
        results = []
        for idx in top_movie_indices:
            mid = int(self.all_movie_ids[idx])
            meta = self.movie_metadata.iloc[idx]
            score_val = float(scores[idx])

            # Compute predicted rating (1-5 scale)
            if user_id is not None and not is_unknown_user:
                pred_rating = self.predict_rating(user_id, mid)
            else:
                pred_rating = float(self.bayesian_ratings[idx])

            # Extract human-readable genre string
            active_genres = [g for g in GENRE_COLUMNS if meta.get(g, 0) == 1]
            genre_str = "|".join(active_genres) if active_genres else "None"

            results.append({
                "movie_id": mid,
                "movie_title": meta["movie_title"],
                "release_date": meta.get("release_date", "Unknown"),
                "genres": genre_str,
                "score": round(score_val, 4),
                "predicted_rating": round(pred_rating, 2)
            })

        return pd.DataFrame(results)

    def save(self, filepath: str) -> None:
        """Saves the fitted model and essential artifacts using joblib."""
        artifacts = {
            "n_latent_factors": self.n_latent_factors,
            "random_state": self.random_state,
            "m0": self.m0,
            "weight_cf": self.weight_cf,
            "weight_content": self.weight_content,
            "weight_popularity": self.weight_popularity,
            "movie_metadata": self.movie_metadata,
            "all_movie_ids": self.all_movie_ids,
            "movie_id_to_idx": self.movie_id_to_idx,
            "idx_to_movie_id": self.idx_to_movie_id,
            "all_user_ids": self.all_user_ids,
            "user_id_to_idx": self.user_id_to_idx,
            "idx_to_user_id": self.idx_to_user_id,
            "train_user_movies": self.train_user_movies,
            "global_mean_rating": self.global_mean_rating,
            "genre_matrix": self.genre_matrix,
            "movie_years": self.movie_years,
            "popularity_scores": self.popularity_scores,
            "bayesian_ratings": self.bayesian_ratings,
            "user_profiles": self.user_profiles,
            "svd_model": self.svd_model,
            "user_factors": self.user_factors,
            "item_factors": self.item_factors,
            "user_means": self.user_means,
        }
        joblib.dump(artifacts, filepath, compress=3)
        print(f"[INFO] CinevoraRecommender artifacts saved to: {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "CinevoraRecommender":
        """Loads fitted model artifacts from joblib file."""
        artifacts = joblib.load(filepath)
        instance = cls(
            n_latent_factors=artifacts["n_latent_factors"],
            random_state=artifacts["random_state"],
            popularity_prior_weight=artifacts["m0"],
            weight_cf=artifacts["weight_cf"],
            weight_content=artifacts["weight_content"],
            weight_popularity=artifacts["weight_popularity"]
        )
        instance.movie_metadata = artifacts["movie_metadata"]
        instance.all_movie_ids = artifacts["all_movie_ids"]
        instance.movie_id_to_idx = artifacts["movie_id_to_idx"]
        instance.idx_to_movie_id = artifacts["idx_to_movie_id"]
        instance.all_user_ids = artifacts["all_user_ids"]
        instance.user_id_to_idx = artifacts["user_id_to_idx"]
        instance.idx_to_user_id = artifacts["idx_to_user_id"]
        instance.train_user_movies = artifacts["train_user_movies"]
        instance.global_mean_rating = artifacts["global_mean_rating"]
        instance.genre_matrix = artifacts["genre_matrix"]
        instance.movie_years = artifacts.get("movie_years")
        if instance.movie_years is None and instance.movie_metadata is not None:
            instance.movie_years = instance._extract_movie_years()
        instance.popularity_scores = artifacts["popularity_scores"]
        instance.bayesian_ratings = artifacts["bayesian_ratings"]
        instance.user_profiles = artifacts["user_profiles"]
        instance.svd_model = artifacts["svd_model"]
        instance.user_factors = artifacts["user_factors"]
        instance.item_factors = artifacts["item_factors"]
        instance.user_means = artifacts["user_means"]
        return instance


# =============================================================================
# Master Cleaned Dataset Recommender (3,560 Movies)
# Grounded strictly in Movies_Master_Cleaned.csv across all 6 film industries.
# =============================================================================
class MasterContentRecommender:
    """
    Content-Based Recommender System for the 3,560-title Master Movie Catalog.
    Grounds all recommendations strictly in Movies_Master_Cleaned.csv.
    Uses TF-IDF metadata representations (industry, genres, director, cast)
    combined with Bayesian quality priors and real-time user preference signals
    (likes, watchlist, searches stored in SQLite).
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df: Optional[pd.DataFrame] = None
        self.tfidf: Optional[TfidfVectorizer] = None
        self.feature_matrix = None
        self.catalog_id_to_idx: Dict[str, int] = {}
        self.movie_id_to_idx: Dict[str, int] = {}
        self.fit(df)

    def fit(self, df: Optional[pd.DataFrame] = None):
        """Fits the TF-IDF representation on the master dataset."""
        from src.catalog_service import load_master_catalog
        if df is None:
            df = load_master_catalog()
        self.df = df.copy()
        if self.df.empty:
            return

        combined_texts = []
        for _, row in self.df.iterrows():
            ind = str(row.get("industry") or "")
            genres = str(row.get("genre") or "").replace(",", " ")
            director = str(row.get("director") or "")
            cast = str(row.get("cast") or "").replace(",", " ")
            # Repeat industry and genres to give them higher semantic weight
            combined_texts.append(f"{ind} {ind} {genres} {genres} {director} {cast}".strip())

        self.tfidf = TfidfVectorizer(max_features=8000, stop_words="english", token_pattern=r"(?u)\b\w+\b")
        self.feature_matrix = self.tfidf.fit_transform(combined_texts)

        self.catalog_id_to_idx = {str(cid).strip(): i for i, cid in enumerate(self.df["catalog_id"])}
        self.movie_id_to_idx = {str(mid).strip(): i for i, mid in enumerate(self.df["movie_id"])}
        logger.info("Fitted MasterContentRecommender on %d movies.", len(self.df))

    def _resolve_movie_idx(self, identifier: Any) -> Optional[int]:
        """Safely resolves movie index by catalog_id or movie_id, correctly handling index 0."""
        if identifier is None:
            return None
        id_str = str(identifier).strip()
        idx = self.catalog_id_to_idx.get(id_str)
        if idx is not None:
            return idx
        return self.movie_id_to_idx.get(id_str)

    def recommend_similar(self, identifier: Any, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Recommends movies similar to catalog_id or movie_id based on content overlap.
        Strictly excludes the queried movie itself.
        """
        if self.df is None or self.df.empty or self.feature_matrix is None:
            self.fit()
        if self.df is None or self.df.empty or self.feature_matrix is None:
            return []

        id_str = str(identifier).strip()
        idx = self.catalog_id_to_idx.get(id_str)
        if idx is None:
            idx = self.movie_id_to_idx.get(id_str)
        if idx is None:
            return []

        target_row = self.df.iloc[idx]
        target_vec = self.feature_matrix[idx : idx + 1]
        sim_scores = cosine_similarity(target_vec, self.feature_matrix)[0]

        # Ratings multiplier [0.8 to 1.2] to prioritize quality similar titles
        ratings = pd.to_numeric(self.df["rating"], errors="coerce").fillna(0.0).to_numpy()
        quality_boost = 0.8 + 0.4 * (ratings / 10.0)
        final_scores = sim_scores * quality_boost

        sorted_indices = final_scores.argsort()[::-1]

        results = []
        for i in sorted_indices:
            if i == idx:
                continue  # Never recommend the movie as itself!
            row_dict = self.df.iloc[i].to_dict()
            clean_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            score_val = float(round(final_scores[i], 3))
            clean_dict["score"] = score_val
            clean_dict["rationale"] = f"Similar to '{target_row.get('title')}' in {target_row.get('genre')}"
            results.append(clean_dict)
            if len(results) >= limit:
                break
        return results

    def recommend_for_user(
        self,
        user_id: str,
        genre: Optional[str] = None,
        industry: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        min_rating: Optional[float] = None,
        limit: int = 10,
        exclude_rated: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recommends movies personalized to a user using their SQLite likes,
        watchlist, and search history. Gracefully falls back to top-rated
        titles across industries for cold-start or guest accounts.
        """
        if self.df is None or self.df.empty or self.feature_matrix is None:
            self.fit()
        if self.df is None or self.df.empty or self.feature_matrix is None:
            return []

        from src.catalog_service import normalize_industry_filter

        # 1. Fetch real user interaction signals from SQLite
        interacted_cids = set()
        user_vecs = []
        last_liked_title = None
        last_liked_genre = None
        genre_weight_map: Dict[str, float] = {}

        try:
            _ensure_backend_app_package()
            from app.db import get_user_likes, get_favorites, get_view_history, get_search_history
            likes = get_user_likes(str(user_id))
            favs = get_favorites(str(user_id))
            views = get_view_history(str(user_id), limit=15)
            searches = get_search_history(str(user_id), limit=10)

            # Liked movies (dominant explicit signal: weight 5.0)
            for m in likes:
                m_str = str(m).strip()
                idx = self._resolve_movie_idx(m_str)
                if idx is not None:
                    interacted_cids.add(self.df.iloc[idx]["catalog_id"])
                    user_vecs.append(self.feature_matrix[idx : idx + 1] * 5.0)
                    m_g = str(self.df.iloc[idx].get("genre") or "")
                    for g in re.split(r"[,|]+", m_g):
                        cg = g.strip().lower()
                        if cg and cg not in ["cinema", "none"]:
                            genre_weight_map[cg] = genre_weight_map.get(cg, 0.0) + 5.0
                    if not last_liked_title:
                        last_liked_title = self.df.iloc[idx]["title"]
                        last_liked_genre = self.df.iloc[idx]["genre"]

            # Watchlist saved movies (high explicit interest: weight 4.0)
            for f in favs:
                m_str = str(f.get("movie_id", "")).strip()
                idx = self._resolve_movie_idx(m_str)
                if idx is not None:
                    interacted_cids.add(self.df.iloc[idx]["catalog_id"])
                    user_vecs.append(self.feature_matrix[idx : idx + 1] * 4.0)
                    m_g = str(self.df.iloc[idx].get("genre") or f.get("genres") or "")
                    for g in re.split(r"[,|]+", m_g):
                        cg = g.strip().lower()
                        if cg and cg not in ["cinema", "none"]:
                            genre_weight_map[cg] = genre_weight_map.get(cg, 0.0) + 4.0
                    if not last_liked_title:
                        last_liked_title = self.df.iloc[idx]["title"]
                        last_liked_genre = self.df.iloc[idx]["genre"]

            # Only incorporate views/searches if user has no explicit likes or favorites
            if not likes and not favs:
                for v in views:
                    m_str = str(v.get("movie_id", "")).strip()
                    idx = self._resolve_movie_idx(m_str)
                    if idx is not None:
                        interacted_cids.add(self.df.iloc[idx]["catalog_id"])
                        user_vecs.append(self.feature_matrix[idx : idx + 1] * 1.5)
                        m_g = str(self.df.iloc[idx].get("genre") or "")
                        for g in re.split(r"[,|]+", m_g):
                            cg = g.strip().lower()
                            if cg and cg not in ["cinema", "none"]:
                                genre_weight_map[cg] = genre_weight_map.get(cg, 0.0) + 1.5

                for s in searches:
                    mid = s.get("matched_movie_id")
                    if mid:
                        m_str = str(mid).strip()
                        idx = self._resolve_movie_idx(m_str)
                        if idx is not None:
                            user_vecs.append(self.feature_matrix[idx : idx + 1] * 1.0)
        except Exception as e:
            logger.warning("Could not fetch user interactions: %s", e)

        # 2. Compute candidate scores
        if user_vecs:
            from scipy.sparse import vstack
            taste_vector = vstack(user_vecs).mean(axis=0)
            taste_vector = np.asarray(taste_vector)
            sim_scores = cosine_similarity(taste_vector, self.feature_matrix)[0]
        else:
            sim_scores = np.zeros(len(self.df))

        ratings = pd.to_numeric(self.df["rating"], errors="coerce").fillna(0.0).to_numpy()
        normalized_ratings = ratings / 10.0

        if genre_weight_map:
            total_gw = sum(genre_weight_map.values()) or 1.0
            norm_genre_weights = {g: w / total_gw for g, w in genre_weight_map.items()}

            def _calc_genre_taste(g_str: Any) -> float:
                if not g_str:
                    return 0.0
                m_genres = [g.strip().lower() for g in re.split(r"[,|]+", str(g_str)) if g.strip()]
                return sum(norm_genre_weights.get(g, 0.0) for g in m_genres)

            genre_taste_scores = self.df["genre"].apply(_calc_genre_taste).to_numpy(dtype=float)
            final_scores = 0.50 * genre_taste_scores + 0.35 * sim_scores + 0.15 * normalized_ratings
        elif user_vecs:
            final_scores = 0.65 * sim_scores + 0.35 * normalized_ratings
        else:
            final_scores = normalized_ratings

        # 3. Apply Hard Constraints
        mask = np.ones(len(self.df), dtype=bool)

        if exclude_rated and interacted_cids:
            mask = mask & (~self.df["catalog_id"].isin(interacted_cids))

        norm_ind = normalize_industry_filter(industry) if industry else None
        if norm_ind:
            if norm_ind == "Indian":
                mask = mask & (self.df["industry"].str.lower().isin(["bollywood", "tamil", "telugu", "malayalam", "kannada"]))
                mask = mask & (self.df["industry"].str.lower() != "hollywood")
            else:
                mask = mask & (self.df["industry"].str.lower() == norm_ind.lower())

        if genre and str(genre).strip() and str(genre).strip().lower() not in ["all", "all genres", "any"]:
            g_clean = str(genre).strip().lower()
            mask = mask & (self.df["genre"].str.lower().str.contains(g_clean, na=False, regex=False))

        years = pd.to_numeric(self.df["release_year"], errors="coerce").fillna(0).astype(int)
        if start_year is not None:
            mask = mask & (years >= int(start_year))
        if end_year is not None:
            mask = mask & (years <= int(end_year))

        if min_rating is not None and min_rating > 0:
            mask = mask & (ratings >= float(min_rating))

        candidate_indices = np.where(mask)[0]
        if len(candidate_indices) == 0:
            return []

        candidate_scores = final_scores[candidate_indices]
        sorted_order = candidate_scores.argsort()[::-1]
        top_indices = candidate_indices[sorted_order[:limit]]

        # Cold-start handling: for new users without interactions, provide diverse curation
        if not user_vecs:
            diverse_results = []
            if norm_ind == "Indian" or (industry and "indian" in str(industry).lower()):
                industries_order = ["Bollywood", "Tamil", "Telugu", "Malayalam", "Kannada"]
            elif norm_ind == "Hollywood":
                industries_order = ["Hollywood"]
            else:
                industries_order = ["Bollywood", "Tamil", "Hollywood", "Telugu", "Malayalam", "Kannada"]
            for ind in industries_order:
                ind_mask = mask & (self.df["industry"].str.lower() == ind.lower())
                ind_indices = np.where(ind_mask)[0]
                if len(ind_indices) > 0:
                    ind_sorted = ind_indices[final_scores[ind_indices].argsort()[::-1]]
                    for idx_item in ind_sorted[: max(1, limit // len(industries_order))]:
                        row_dict = self.df.iloc[idx_item].to_dict()
                        clean_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
                        clean_dict["score"] = float(round(final_scores[idx_item], 3))
                        first_g = str(clean_dict.get("genre", "Cinema")).split(",")[0].strip()
                        clean_dict["rationale"] = f"Spotlight: Top {clean_dict.get('industry', 'Classic')} {first_g}"
                        diverse_results.append(clean_dict)
                        if len(diverse_results) >= limit:
                            break
                if len(diverse_results) >= limit:
                    break

            if len(diverse_results) < limit:
                for i in top_indices:
                    cid = self.df.iloc[i]["catalog_id"]
                    if not any(d["catalog_id"] == cid for d in diverse_results):
                        row_dict = self.df.iloc[i].to_dict()
                        clean_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
                        clean_dict["score"] = float(round(final_scores[i], 3))
                        first_g = str(clean_dict.get("genre", "Cinema")).split(",")[0].strip()
                        clean_dict["rationale"] = f"Popular {clean_dict.get('industry', 'Cinema')} {first_g}"
                        diverse_results.append(clean_dict)
                        if len(diverse_results) >= limit:
                            break
            return diverse_results[:limit]

        results = []
        for i in top_indices:
            row_dict = self.df.iloc[i].to_dict()
            clean_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            score_val = float(round(final_scores[i], 3))
            clean_dict["score"] = score_val

            if last_liked_title and user_vecs:
                clean_dict["rationale"] = f"Based on your interest in '{last_liked_title}' ({last_liked_genre})"
            else:
                first_g = str(clean_dict.get("genre", "Cinema")).split(",")[0].strip()
                clean_dict["rationale"] = f"Top-rated {clean_dict.get('industry', 'Classic')} {first_g} recommendation"

            results.append(clean_dict)

        return results

    def get_movie(self, identifier: Any) -> Optional[Dict[str, Any]]:
        """Retrieves a single movie dict from master catalog by catalog_id or movie_id."""
        if self.df is None or self.df.empty:
            self.fit()
        id_str = str(identifier).strip()
        idx = self.catalog_id_to_idx.get(id_str)
        if idx is None:
            idx = self.movie_id_to_idx.get(id_str)
        if idx is None:
            return None
        row = self.df.iloc[idx].to_dict()
        return {k: (None if pd.isna(v) else v) for k, v in row.items()}

    def recommend_because_you_liked(self, user_id: str, limit: int = 6) -> Dict[str, Any]:
        """Returns recommendations based on the user's most recent liked movie."""
        _ensure_backend_app_package()
        from app.db import get_user_likes
        likes = get_user_likes(str(user_id))
        if not likes:
            return {"source_movie": None, "movies": []}
        most_recent_id = likes[-1]
        source_movie = self.get_movie(most_recent_id)
        if not source_movie:
            return {"source_movie": None, "movies": []}
        recs = self.recommend_similar(most_recent_id, limit=limit)
        return {"source_movie": source_movie, "movies": recs}

    def recommend_from_watchlist(self, user_id: str, limit: int = 6) -> Dict[str, Any]:
        """Returns recommendations similar to movies saved in user's watchlist."""
        _ensure_backend_app_package()
        from app.db import get_favorites
        favs = get_favorites(str(user_id))
        if not favs:
            return {"source_movie": None, "movies": []}
        most_recent = favs[0]
        mid = most_recent.get("movie_id")
        source_movie = self.get_movie(mid)
        if not source_movie:
            return {"source_movie": None, "movies": []}
        recs = self.recommend_similar(mid, limit=limit)
        return {"source_movie": source_movie, "movies": recs}

    def recommend_favorite_genres(self, user_id: str, limit: int = 6) -> Dict[str, Any]:
        """Identifies user's top genres from all interactions and recommends top matches."""
        _ensure_backend_app_package()
        from app.db import get_user_likes, get_favorites, get_view_history, get_search_history
        likes = get_user_likes(str(user_id))
        favs = get_favorites(str(user_id))
        views = get_view_history(str(user_id), limit=20)
        searches = get_search_history(str(user_id), limit=10)

        genre_counts: Dict[str, int] = {}
        for mid in likes:
            m = self.get_movie(mid)
            if m and m.get("genre"):
                for g in str(m["genre"]).split(","):
                    g_clean = g.strip()
                    if g_clean:
                        genre_counts[g_clean] = genre_counts.get(g_clean, 0) + 3

        for f in favs:
            m = self.get_movie(f.get("movie_id"))
            if m and m.get("genre"):
                for g in str(m["genre"]).split(","):
                    g_clean = g.strip()
                    if g_clean:
                        genre_counts[g_clean] = genre_counts.get(g_clean, 0) + 2

        for v in views:
            g_str = v.get("genres")
            if g_str:
                for g in str(g_str).split(","):
                    g_clean = g.strip()
                    if g_clean:
                        genre_counts[g_clean] = genre_counts.get(g_clean, 0) + 1

        for s in searches:
            mg = s.get("matched_genres")
            if mg:
                for g in str(mg).split("|"):
                    g_clean = g.strip()
                    if g_clean:
                        genre_counts[g_clean] = genre_counts.get(g_clean, 0) + 1

        if not genre_counts:
            return {"favorite_genre": None, "movies": []}

        top_genre = max(genre_counts.items(), key=lambda x: x[1])[0]
        recs = self.recommend_for_user(user_id=user_id, genre=top_genre, limit=limit)
        return {"favorite_genre": top_genre, "movies": recs}

    def recommend_discover_new(self, user_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Recommends high-rated critically acclaimed movies from industries/genres user hasn't explored yet."""
        _ensure_backend_app_package()
        from app.db import get_user_likes, get_favorites
        likes = get_user_likes(str(user_id))
        favs = get_favorites(str(user_id))

        interacted_industries = set()
        for mid in likes:
            m = self.get_movie(mid)
            if m and m.get("industry"):
                interacted_industries.add(str(m["industry"]).strip().lower())
        for f in favs:
            m = self.get_movie(f.get("movie_id"))
            if m and m.get("industry"):
                interacted_industries.add(str(m["industry"]).strip().lower())

        all_industries = set(self.df["industry"].str.lower().unique())
        unexplored = all_industries - interacted_industries
        target_ind = list(unexplored)[0] if unexplored else None

        return self.recommend_for_user(
            user_id=user_id,
            industry=target_ind,
            min_rating=7.5,
            limit=limit,
            exclude_rated=True
        )


# Global singleton instance of MasterContentRecommender
master_content_recommender = MasterContentRecommender()
