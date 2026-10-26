"""
Cinevora - Real-Time Movie Recommendation Service
Step 2: Model Training and Offline Evaluation

This script:
1. Loads raw MovieLens 100K ratings and movie metadata.
2. Performs a stratified per-user train-test split (80% train / 20% test per user)
   with a fixed random seed to guarantee no data leakage.
3. Fits the CinevoraRecommender (Popularity, Content-Based, Collaborative Filtering, and Hybrid).
4. Evaluates all models on held-out test data using Precision@10, Recall@10, NDCG@10, and RMSE.
5. Saves model artifacts under models/ and split datasets under data/processed/.
6. Generates evaluation comparison charts and JSON summaries under reports/.
7. Displays a comprehensive evaluation report in the console.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

# Use non-interactive backend for matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure local imports work regardless of run location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recommender import CinevoraRecommender, GENRE_COLUMNS


# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "ml-100k"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

RANDOM_SEED = 42
TEST_FRACTION = 0.20
RELEVANCE_THRESHOLD = 4.0  # Test ratings >= 4.0 are classified as relevant (liked) items
TOP_K = 10

RATINGS_COLUMNS = ["user_id", "movie_id", "rating", "timestamp"]
MOVIE_COLUMNS = ["movie_id", "movie_title", "release_date", "video_release_date", "imdb_url"] + GENRE_COLUMNS


# -----------------------------------------------------------------------------
# Data Loading & Partitioning
# -----------------------------------------------------------------------------
def locate_raw_files(base_dir: Path) -> Tuple[Path, Path]:
    """Locates u.data and u.item files within base_dir or a nested subfolder."""
    primary_data = base_dir / "u.data"
    primary_item = base_dir / "u.item"
    if primary_data.exists() and primary_item.exists():
        return primary_data, primary_item

    nested_data = base_dir / "ml-100k" / "u.data"
    nested_item = base_dir / "ml-100k" / "u.item"
    if nested_data.exists() and nested_item.exists():
        return nested_data, nested_item

    raise FileNotFoundError(
        f"Missing 'u.data' or 'u.item' in {base_dir}. Verify that MovieLens 100K is extracted."
    )


def load_dataset(data_path: Path, item_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads ratings and movie metadata with correct types and encodings."""
    print(f"[INFO] Loading ratings from: {data_path.name}")
    ratings_df = pd.read_csv(
        data_path,
        sep="\t",
        names=RATINGS_COLUMNS,
        engine="c",
        dtype={"user_id": int, "movie_id": int, "rating": int, "timestamp": int}
    )

    print(f"[INFO] Loading movie metadata from: {item_path.name}")
    movies_df = pd.read_csv(
        item_path,
        sep="|",
        names=MOVIE_COLUMNS,
        encoding="latin-1",
        engine="python"
    )

    return ratings_df, movies_df


def stratified_per_user_split(
    ratings_df: pd.DataFrame,
    test_size: float = 0.20,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits interactions by sampling test_size fraction per user.
    This guarantees every user is present in both train and test sets,
    preventing user cold-start bias during offline test evaluation.
    """
    train_indices = []
    test_indices = []

    for _, group in ratings_df.groupby("user_id"):
        n_user_ratings = len(group)
        n_test = max(1, int(n_user_ratings * test_size))
        
        # Deterministic shuffle per user
        shuffled = group.sample(frac=1.0, random_state=random_seed).index
        test_indices.extend(shuffled[:n_test])
        train_indices.extend(shuffled[n_test:])

    train_df = ratings_df.loc[train_indices].copy().reset_index(drop=True)
    test_df = ratings_df.loc[test_indices].copy().reset_index(drop=True)

    print(f"[INFO] Train interactions: {len(train_df):,} | Test interactions: {len(test_df):,}")
    print(f"[INFO] Unique users in Train: {train_df['user_id'].nunique()} | in Test: {test_df['user_id'].nunique()}")

    return train_df, test_df


# -----------------------------------------------------------------------------
# Evaluation Engine
# -----------------------------------------------------------------------------
def evaluate_ranking_metrics(
    recommender: CinevoraRecommender,
    test_df: pd.DataFrame,
    model_type: str,
    k: int = 10,
    relevance_threshold: float = 4.0
) -> Dict[str, float]:
    """
    Evaluates Precision@K, Recall@K, and NDCG@K across all test users.
    - Ground truth relevant items: Test interactions with rating >= relevance_threshold.
    - Candidates: Entire movie catalog excluding items in the user's training set.
    """
    # Group test ratings by user for ground-truth sets
    test_relevant_by_user = (
        test_df[test_df["rating"] >= relevance_threshold]
        .groupby("user_id")["movie_id"]
        .apply(set)
        .to_dict()
    )

    precisions: List[float] = []
    recalls: List[float] = []
    ndcgs: List[float] = []

    # Precompute standard logarithmic discounts: 1 / log2(rank + 1) for rank 1..K
    rank_discounts = 1.0 / np.log2(np.arange(2, k + 2))

    for user_id, rel_items in test_relevant_by_user.items():
        if not rel_items:
            continue

        # Generate Top-K recommendations using the specified model
        rec_df = recommender.recommend(
            user_id=user_id,
            n=k,
            model_type=model_type,
            exclude_rated=True
        )

        rec_movie_ids = rec_df["movie_id"].tolist()
        hits = [1 if mid in rel_items else 0 for mid in rec_movie_ids]
        n_hits = sum(hits)

        # 1. Precision@K = |Hits| / K
        precision_at_k = n_hits / k

        # 2. Recall@K = |Hits| / |Relevant Test Items|
        recall_at_k = n_hits / len(rel_items)

        # 3. NDCG@K = DCG@K / IDCG@K
        dcg = np.sum(np.array(hits) * rank_discounts[:len(hits)])
        ideal_hits_count = min(k, len(rel_items))
        idcg = np.sum(rank_discounts[:ideal_hits_count])
        ndcg_at_k = float(dcg / idcg) if idcg > 0 else 0.0

        precisions.append(precision_at_k)
        recalls.append(recall_at_k)
        ndcgs.append(ndcg_at_k)

    return {
        f"precision@{k}": float(np.mean(precisions)),
        f"recall@{k}": float(np.mean(recalls)),
        f"ndcg@{k}": float(np.mean(ndcgs)),
        "users_evaluated": len(precisions)
    }


def evaluate_rmse(
    recommender: CinevoraRecommender,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Dict[str, float]:
    """
    Evaluates Root Mean Squared Error (RMSE) on held-out test ratings:
    1. Global Mean Baseline (predicts training global mean for every test pair).
    2. Movie Mean Baseline (predicts training movie mean with global fallback).
    3. Collaborative Filtering (TruncatedSVD latent factor reconstruction).
    """
    y_true = test_df["rating"].values.astype(float)

    # 1. Global Mean Baseline
    global_mean = float(train_df["rating"].mean())
    y_pred_global = np.full_like(y_true, global_mean)
    rmse_global = float(np.sqrt(mean_squared_error(y_true, y_pred_global)))

    # 2. Movie Mean Baseline
    movie_means = train_df.groupby("movie_id")["rating"].mean().to_dict()
    y_pred_movie_mean = np.array([movie_means.get(mid, global_mean) for mid in test_df["movie_id"]])
    rmse_movie_mean = float(np.sqrt(mean_squared_error(y_true, y_pred_movie_mean)))

    # 3. Collaborative Filtering SVD Predictions
    y_pred_cf = []
    for _, row in test_df.iterrows():
        pred = recommender.predict_rating(int(row["user_id"]), int(row["movie_id"]))
        y_pred_cf.append(pred)
    y_pred_cf = np.array(y_pred_cf)
    rmse_cf = float(np.sqrt(mean_squared_error(y_true, y_pred_cf)))

    return {
        "rmse_global_baseline": round(rmse_global, 4),
        "rmse_movie_mean_baseline": round(rmse_movie_mean, 4),
        "rmse_collaborative_svd": round(rmse_cf, 4)
    }


# -----------------------------------------------------------------------------
# Visualization & Reports
# -----------------------------------------------------------------------------
def plot_model_comparison(results: Dict[str, Dict[str, float]], save_path: Path):
    """
    Generates a clear side-by-side bar chart comparing models on ranking metrics.
    """
    models = ["popularity", "content", "collaborative", "hybrid"]
    display_names = ["Popularity (Base)", "Content-Based", "Collab SVD", "Hybrid"]
    metrics = ["precision@10", "recall@10", "ndcg@10"]
    metric_labels = ["Precision@10", "Recall@10", "NDCG@10"]

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ["#3B82F6", "#10B981", "#8B5CF6"]

    for i, (m_key, m_label, col) in enumerate(zip(metrics, metric_labels, colors)):
        values = [results[m][m_key] for m in models]
        rects = ax.bar(x + (i - 1) * width, values, width, label=m_label, color=col, edgecolor="#1F2937", zorder=3)
        # Add value labels on top of bars
        for rect in rects:
            h = rect.get_height()
            ax.annotate(
                f"{h:.3f}",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold"
            )

    ax.set_ylabel("Score", fontsize=11, labelpad=8)
    ax.set_title("Recommendation Model Comparison on Held-Out Test Set (K=10, Threshold >= 4.0)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, fontsize=10, fontweight="semibold")
    ax.legend(frameon=True, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
    ax.set_ylim(0, max([results[m]["ndcg@10"] for m in models]) * 1.25)

    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"[INFO] Comparison chart saved to: {save_path.name}")


def display_results(results: Dict[str, Dict[str, float]], rmse_results: Dict[str, float]):
    """Prints a structured ASCII report of evaluation metrics."""
    border = "=" * 80
    sub_border = "-" * 80

    print("\n" + border)
    print("  CINEVORA — RECOMMENDER MODEL OFFLINE EVALUATION REPORT")
    print(f"  Test Set: {TEST_FRACTION * 100:.0f}% stratified per user | Relevance Threshold: Rating >= {RELEVANCE_THRESHOLD:.1f}")
    print(border)

    print("\n[1] RANKING METRICS (Top-10 Recommendations)")
    print(sub_border)
    header = f"  {'Model':<24} {'Precision@10':<16} {'Recall@10':<16} {'NDCG@10':<16} {'Rel to Base'}"
    print(header)
    print(sub_border)

    base_ndcg = results["popularity"]["ndcg@10"]

    model_display_names = {
        "popularity": "Popularity Baseline",
        "content": "Content-Based",
        "collaborative": "Collaborative (SVD)",
        "hybrid": "Hybrid Engine"
    }

    for key, name in model_display_names.items():
        m = results[key]
        p = m["precision@10"]
        r = m["recall@10"]
        n = m["ndcg@10"]
        diff_pct = ((n - base_ndcg) / base_ndcg * 100) if base_ndcg > 0 else 0.0
        diff_str = f"{diff_pct:+.1f}% NDCG" if key != "popularity" else "BASELINE"
        print(f"  {name:<24} {p:<16.4f} {r:<16.4f} {n:<16.4f} {diff_str}")

    print("\n[2] RATING PREDICTION METRICS (RMSE)")
    print(sub_border)
    print(f"  * Global Mean Baseline:     RMSE = {rmse_results['rmse_global_baseline']:.4f}")
    print(f"  * Movie Mean Baseline:      RMSE = {rmse_results['rmse_movie_mean_baseline']:.4f}")
    print(f"  * Collaborative SVD Model:  RMSE = {rmse_results['rmse_collaborative_svd']:.4f}")
    improvement = (
        (rmse_results['rmse_global_baseline'] - rmse_results['rmse_collaborative_svd'])
        / rmse_results['rmse_global_baseline'] * 100
    )
    print(f"  * Error Reduction vs Global: {improvement:.2f}%")

    print("\n[3] MODEL DESIGN & WEIGHTING CHOICES")
    print(sub_border)
    print("  * Component Weights: Collaborative = 0.50 | Content = 0.35 | Popularity = 0.15")
    print("  * Rationale: Collaborative filtering delivers highest personalized relevance,")
    print("    content-based matching ensures topical alignment, and Bayesian popularity provides")
    print("    stability against sparse items and new user cold starts.")
    print("  * Weights are heuristic baselines and NOT overfitted on the test set.")

    print("\n" + border)
    print("  Model Training & Evaluation Completed.")
    print(border + "\n")


# -----------------------------------------------------------------------------
# Main Execution Flow
# -----------------------------------------------------------------------------
def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("[INFO] Starting Cinevora Recommender Training & Evaluation Pipeline...")

    # Ensure required output directories exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Locate and load raw data
    data_path, item_path = locate_raw_files(RAW_DATA_DIR)
    ratings_df, movies_df = load_dataset(data_path, item_path)

    # 2. Stratified train-test split
    train_df, test_df = stratified_per_user_split(
        ratings_df,
        test_size=TEST_FRACTION,
        random_seed=RANDOM_SEED
    )

    # 3. Save train/test partitions for reproducibility
    train_df.to_csv(PROCESSED_DATA_DIR / "train_ratings.csv", index=False)
    test_df.to_csv(PROCESSED_DATA_DIR / "test_ratings.csv", index=False)

    # Save clean movie metadata lookup
    movie_metadata_export = movies_df[["movie_id", "movie_title", "release_date"] + GENRE_COLUMNS]
    movie_metadata_export.to_csv(PROCESSED_DATA_DIR / "movie_metadata.csv", index=False)
    print(f"[INFO] Processed datasets saved to: {PROCESSED_DATA_DIR}")

    # 4. Fit the Recommender Engine on training interactions only
    print("\n[INFO] Fitting CinevoraRecommender models on training data...")
    recommender = CinevoraRecommender(
        n_latent_factors=20,
        random_state=RANDOM_SEED,
        popularity_prior_weight=25.0,
        weight_cf=0.50,
        weight_content=0.35,
        weight_popularity=0.15
    )
    recommender.fit(train_ratings=train_df, movies_df=movies_df)

    # 5. Evaluate ranking models on held-out test interactions
    print("\n[INFO] Evaluating Top-10 ranking metrics across held-out test users...")
    evaluation_results = {}
    for model_name in ["popularity", "content", "collaborative", "hybrid"]:
        metrics = evaluate_ranking_metrics(
            recommender=recommender,
            test_df=test_df,
            model_type=model_name,
            k=TOP_K,
            relevance_threshold=RELEVANCE_THRESHOLD
        )
        evaluation_results[model_name] = metrics

    # 6. Evaluate rating prediction RMSE
    print("[INFO] Evaluating rating prediction RMSE...")
    rmse_metrics = evaluate_rmse(recommender, train_df, test_df)

    # 7. Save model artifacts
    model_artifact_path = MODELS_DIR / "recommender_model.joblib"
    recommender.save(str(model_artifact_path))

    # 8. Save evaluation results as JSON
    eval_report = {
        "ranking_metrics": evaluation_results,
        "rating_prediction_rmse": rmse_metrics,
        "evaluation_config": {
            "test_fraction": TEST_FRACTION,
            "random_seed": RANDOM_SEED,
            "relevance_threshold": RELEVANCE_THRESHOLD,
            "top_k": TOP_K,
            "hybrid_weights": {
                "collaborative": recommender.weight_cf,
                "content": recommender.weight_content,
                "popularity": recommender.weight_popularity
            }
        }
    }
    with open(REPORTS_DIR / "recommendation_evaluation.json", "w") as f:
        json.dump(eval_report, f, indent=2)
    print(f"[INFO] Evaluation report saved to: reports/recommendation_evaluation.json")

    # 9. Plot and save comparison chart
    chart_path = REPORTS_DIR / "model_comparison.png"
    plot_model_comparison(evaluation_results, chart_path)

    # 10. Print console report
    display_results(evaluation_results, rmse_metrics)


if __name__ == "__main__":
    main()
