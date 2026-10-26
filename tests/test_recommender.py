"""
Unit Tests for Cinevora Recommender Engine
Tests cover:
1. Hard genre filtering constraints
2. Recommendation ranking monotonicity
3. Unknown user cold-start fallbacks
4. Empty and edge-case results
5. Exclusion of already-rated items
6. Model artifact persistence round-trip
"""

import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd
import numpy as np

from src.recommender import CinevoraRecommender, GENRE_COLUMNS


@pytest.fixture(scope="module")
def sample_dataset():
    """Creates a minimal synthetic MovieLens-format dataset for fast, isolated testing."""
    genres_data = {
        "unknown": [0, 0, 0, 0],
        "Action": [1, 0, 1, 0],
        "Adventure": [1, 0, 0, 0],
        "Animation": [0, 1, 0, 0],
        "Children's": [0, 1, 0, 0],
        "Comedy": [0, 1, 1, 0],
        "Crime": [0, 0, 0, 0],
        "Documentary": [0, 0, 0, 0],
        "Drama": [0, 0, 0, 1],
        "Fantasy": [0, 0, 0, 0],
        "Film-Noir": [0, 0, 0, 0],
        "Horror": [0, 0, 0, 0],
        "Musical": [0, 0, 0, 0],
        "Mystery": [0, 0, 0, 0],
        "Romance": [0, 0, 0, 0],
        "Sci-Fi": [0, 0, 0, 0],
        "Thriller": [0, 0, 0, 0],
        "War": [0, 0, 0, 0],
        "Western": [0, 0, 0, 0],
    }

    movies_df = pd.DataFrame({
        "movie_id": [101, 102, 103, 104],
        "movie_title": ["Action Blast", "Cartoon Laughs", "Action Comedy", "Serious Drama"],
        "release_date": ["01-Jan-1995", "01-Jan-1996", "01-Jan-1997", "01-Jan-1998"],
        "video_release_date": [np.nan, np.nan, np.nan, np.nan],
        "imdb_url": ["http://a", "http://b", "http://c", "http://d"],
        **genres_data
    })

    ratings_df = pd.DataFrame({
        "user_id":   [1, 1, 2, 2, 3, 3],
        "movie_id":  [101, 102, 102, 103, 101, 104],
        "rating":    [5, 4, 2, 5, 4, 5],
        "timestamp": [1000, 1001, 1002, 1003, 1004, 1005]
    })

    return ratings_df, movies_df


@pytest.fixture(scope="module")
def fitted_recommender(sample_dataset):
    """Instantiates and fits the recommender on the sample dataset."""
    ratings_df, movies_df = sample_dataset
    rec = CinevoraRecommender(n_latent_factors=2, random_state=42)
    rec.fit(train_ratings=ratings_df, movies_df=movies_df)
    return rec


# -----------------------------------------------------------------------------
# 1. Hard Genre Filtering Tests
# -----------------------------------------------------------------------------
def test_hard_genre_filtering_comedy(fitted_recommender):
    """Verifies that filtering by Comedy returns ONLY movies with the Comedy tag."""
    recs = fitted_recommender.recommend(user_id=1, n=5, genre_filter="Comedy", exclude_rated=False)
    assert not recs.empty
    for _, row in recs.iterrows():
        assert "Comedy" in row["genres"], f"Expected 'Comedy' in genres, got: {row['genres']}"


def test_hard_genre_filtering_action(fitted_recommender):
    """Verifies that filtering by Action returns ONLY action movies."""
    recs = fitted_recommender.recommend(user_id=2, n=5, genre_filter="Action", exclude_rated=False)
    assert not recs.empty
    for _, row in recs.iterrows():
        assert "Action" in row["genres"]


def test_hard_year_range_filtering(fitted_recommender):
    """Verifies filtering by year_range returns only movies in that window."""
    recs = fitted_recommender.recommend(user_id=1, n=5, year_range=(1995, 1996), exclude_rated=False)
    assert not recs.empty
    assert len(recs) == 2
    for _, row in recs.iterrows():
        assert row["movie_id"] in [101, 102]


def test_year_range_with_zero_matches_returns_empty(fitted_recommender):
    """Verifies year_range with no matching catalog years returns empty DataFrame."""
    recs = fitted_recommender.recommend(user_id=1, n=5, year_range=(1920, 1929), exclude_rated=False)
    assert isinstance(recs, pd.DataFrame)
    assert len(recs) == 0


# -----------------------------------------------------------------------------
# 2. Empty Results & Edge Cases
# -----------------------------------------------------------------------------
def test_nonexistent_genre_filter_returns_empty_dataframe(fitted_recommender):
    """Verifies that querying a non-existent genre returns an empty DataFrame gracefully."""
    recs = fitted_recommender.recommend(user_id=1, n=5, genre_filter="NonExistentGenre")
    assert isinstance(recs, pd.DataFrame)
    assert len(recs) == 0
    assert "movie_id" in recs.columns
    assert "score" in recs.columns


def test_genre_with_zero_catalog_items_returns_empty(fitted_recommender):
    """Verifies that querying a known genre with no catalog matches returns empty DataFrame."""
    recs = fitted_recommender.recommend(user_id=1, n=5, genre_filter="Western", exclude_rated=False)
    assert isinstance(recs, pd.DataFrame)
    assert len(recs) == 0


# -----------------------------------------------------------------------------
# 3. Recommendation Ranking Tests
# -----------------------------------------------------------------------------
def test_recommendation_ranking_monotonicity(fitted_recommender):
    """Verifies that recommendation results are strictly sorted in descending score order."""
    recs = fitted_recommender.recommend(user_id=1, n=4, exclude_rated=False)
    scores = recs["score"].tolist()
    assert scores == sorted(scores, reverse=True), "Recommendations must be sorted descending by score."


def test_recommendation_predicted_ratings_in_valid_range(fitted_recommender):
    """Verifies predicted ratings lie within the standard 1.0 to 5.0 range."""
    recs = fitted_recommender.recommend(user_id=1, n=4, exclude_rated=False)
    for pred in recs["predicted_rating"]:
        assert 1.0 <= pred <= 5.0, f"Predicted rating {pred} is outside [1.0, 5.0]."


# -----------------------------------------------------------------------------
# 4. Unknown User (Cold-Start) Fallback Tests
# -----------------------------------------------------------------------------
def test_unknown_user_fallback(fitted_recommender):
    """Verifies that an unknown user ID does not crash and receives valid popularity recommendations."""
    unknown_user_id = 999999
    recs = fitted_recommender.recommend(user_id=unknown_user_id, n=3, model_type="hybrid")
    assert len(recs) == 3
    assert all(isinstance(mid, (int, np.integer)) for mid in recs["movie_id"])

    # Test predict_rating fallback for unknown user
    pred_rating = fitted_recommender.predict_rating(user_id=unknown_user_id, movie_id=101)
    assert 1.0 <= pred_rating <= 5.0


def test_unknown_user_with_explicit_genre_prefs(fitted_recommender):
    """Verifies an ad-hoc content recommendation for a new user with selected genre preferences."""
    recs = fitted_recommender.recommend(
        user_id=None,
        n=2,
        model_type="hybrid",
        custom_genre_prefs=["Comedy"]
    )
    assert len(recs) > 0
    # Top recommendation should align with Comedy
    assert "Comedy" in recs.iloc[0]["genres"]


# -----------------------------------------------------------------------------
# 5. Exclude Already-Rated Movies Test
# -----------------------------------------------------------------------------
def test_exclude_rated_movies(fitted_recommender):
    """Verifies that already-rated movies are excluded from recommendations when exclude_rated=True."""
    # User 1 rated movie_id 101 and 102 in sample dataset
    recs = fitted_recommender.recommend(user_id=1, n=4, exclude_rated=True)
    recommended_ids = set(recs["movie_id"])
    assert 101 not in recommended_ids
    assert 102 not in recommended_ids


# -----------------------------------------------------------------------------
# 6. Artifact Serialization Roundtrip Test
# -----------------------------------------------------------------------------
def test_model_save_and_load_roundtrip(fitted_recommender):
    """Verifies model serialization and deserialization produces identical output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_model_path = Path(tmp_dir) / "test_model.joblib"
        fitted_recommender.save(str(tmp_model_path))
        assert tmp_model_path.exists()

        reloaded = CinevoraRecommender.load(str(tmp_model_path))
        recs_orig = fitted_recommender.recommend(user_id=1, n=2, exclude_rated=False)
        recs_reloaded = reloaded.recommend(user_id=1, n=2, exclude_rated=False)

        pd.testing.assert_frame_equal(recs_orig, recs_reloaded)
