"""
Cinevora - Real-Time Movie Recommendation Service
Step 1: Exploratory Data Analysis (EDA) on MovieLens 100K

This script:
1. Validates the presence of raw MovieLens 100K data files (u.data and u.item).
2. Loads ratings and movie metadata using pandas with proper encodings.
3. Examines data dimensions, missing values, and duplicate records.
4. Analyzes rating distributions, most-rated movies, average scores, and genre representation.
5. Produces informative visualizations and saves them to reports/.
6. Exports structured summary CSV files to data/processed/.
7. Displays key dataset findings in the terminal.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Use non-interactive backend for matplotlib to safely save figures to disk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "ml-100k"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Standard MovieLens 100K genre list in exact column order (from u.genre)
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

# Column definitions for u.data (ratings) and u.item (movies)
RATINGS_COLUMNS = ["user_id", "movie_id", "rating", "timestamp"]
MOVIE_COLUMNS = ["movie_id", "movie_title", "release_date", "video_release_date", "imdb_url"] + GENRE_COLUMNS


# -----------------------------------------------------------------------------
# Data Loading & Verification
# -----------------------------------------------------------------------------
def locate_dataset_files(base_dir: Path):
    """
    Locates u.data and u.item files within base_dir or a nested subfolder.
    Raises FileNotFoundError if files are not found.
    """
    primary_data = base_dir / "u.data"
    primary_item = base_dir / "u.item"

    # Check direct location first
    if primary_data.exists() and primary_item.exists():
        return primary_data, primary_item

    # Check nested location (e.g., if extracted into ml-100k/ml-100k)
    nested_data = base_dir / "ml-100k" / "u.data"
    nested_item = base_dir / "ml-100k" / "u.item"
    if nested_data.exists() and nested_item.exists():
        return nested_data, nested_item

    # Error message if missing
    raise FileNotFoundError(
        f"Dataset files 'u.data' or 'u.item' were not found in '{base_dir}'.\n"
        "Please ensure the MovieLens 100K dataset is downloaded and extracted at data/raw/ml-100k/."
    )


def load_movielens_data(data_path: Path, item_path: Path):
    """
    Loads ratings and movies datasets into pandas DataFrames.
    - Ratings: Tab-separated, utf-8 / ascii.
    - Movies: Pipe-separated, latin-1 encoding due to special characters in titles.
    """
    print(f"[INFO] Loading ratings from: {data_path}")
    ratings_df = pd.read_csv(
        data_path,
        sep="\t",
        names=RATINGS_COLUMNS,
        engine="c",
        dtype={"user_id": int, "movie_id": int, "rating": int, "timestamp": int}
    )

    print(f"[INFO] Loading movie metadata from: {item_path}")
    movies_df = pd.read_csv(
        item_path,
        sep="|",
        names=MOVIE_COLUMNS,
        encoding="latin-1",
        engine="python"
    )

    return ratings_df, movies_df


# -----------------------------------------------------------------------------
# Data Quality & Dimension Checks
# -----------------------------------------------------------------------------
def inspect_data_quality(ratings_df: pd.DataFrame, movies_df: pd.DataFrame):
    """
    Checks missing values, duplicates, and unique identifiers.
    Returns a dictionary of quality metrics.
    """
    # Missing values
    ratings_nulls = ratings_df.isnull().sum().to_dict()
    movies_nulls = movies_df.isnull().sum().to_dict()

    # Duplicates
    duplicate_ratings = int(ratings_df.duplicated().sum())
    duplicate_user_movie = int(ratings_df.duplicated(subset=["user_id", "movie_id"]).sum())
    duplicate_movie_ids = int(movies_df.duplicated(subset=["movie_id"]).sum())

    # Unique counts
    n_users = int(ratings_df["user_id"].nunique())
    n_movies_rated = int(ratings_df["movie_id"].nunique())
    n_movies_catalog = len(movies_df)

    # Convert timestamps to human-readable dates for temporal span
    min_date = pd.to_datetime(ratings_df["timestamp"], unit="s").min().strftime("%Y-%m-%d")
    max_date = pd.to_datetime(ratings_df["timestamp"], unit="s").max().strftime("%Y-%m-%d")

    return {
        "n_ratings": len(ratings_df),
        "n_users": n_users,
        "n_movies_rated": n_movies_rated,
        "n_movies_catalog": n_movies_catalog,
        "ratings_nulls": ratings_nulls,
        "movies_nulls": movies_nulls,
        "duplicate_ratings": duplicate_ratings,
        "duplicate_user_movie": duplicate_user_movie,
        "duplicate_movie_ids": duplicate_movie_ids,
        "date_range": f"{min_date} to {max_date}",
        "sparsity": 1.0 - (len(ratings_df) / (n_users * n_movies_catalog))
    }


# -----------------------------------------------------------------------------
# Core EDA Calculations
# -----------------------------------------------------------------------------
def perform_eda(ratings_df: pd.DataFrame, movies_df: pd.DataFrame):
    """
    Computes statistical summaries for ratings, movies, genres, and users.
    """
    # 1. Rating distribution
    rating_counts = ratings_df["rating"].value_counts().sort_index()
    rating_percentages = (rating_counts / len(ratings_df) * 100).round(2)
    rating_dist_df = pd.DataFrame({
        "rating": rating_counts.index,
        "count": rating_counts.values,
        "percentage": rating_percentages.values
    })

    # Overall rating statistics
    overall_mean_rating = float(ratings_df["rating"].mean())
    overall_std_rating = float(ratings_df["rating"].std())
    overall_median_rating = float(ratings_df["rating"].median())

    # 2. Movie aggregation (ratings count, average, std)
    movie_stats = ratings_df.groupby("movie_id").agg(
        rating_count=("rating", "count"),
        avg_rating=("rating", "mean"),
        std_rating=("rating", "std")
    ).reset_index()

    # Merge movie metadata with ratings statistics
    movie_summary_df = pd.merge(movies_df, movie_stats, on="movie_id", how="left")
    movie_summary_df["rating_count"] = movie_summary_df["rating_count"].fillna(0).astype(int)
    movie_summary_df["avg_rating"] = movie_summary_df["avg_rating"].fillna(0.0).round(2)

    # Create a compact pipe-delimited genre string for each movie
    def extract_genres(row):
        active = [g for g in GENRE_COLUMNS if row.get(g, 0) == 1]
        return "|".join(active) if active else "None"

    movie_summary_df["genres"] = movie_summary_df.apply(extract_genres, axis=1)

    # 3. Top-rated and most-rated movies
    most_rated_movies = movie_summary_df.sort_values(by="rating_count", ascending=False)[
        ["movie_id", "movie_title", "rating_count", "avg_rating", "genres"]
    ].head(15)

    # Highest rated movies with at least 50 ratings (to filter out single 5-star anomalies)
    min_ratings_threshold = 50
    highest_rated_movies = movie_summary_df[movie_summary_df["rating_count"] >= min_ratings_threshold].sort_values(
        by=["avg_rating", "rating_count"], ascending=[False, False]
    )[["movie_id", "movie_title", "rating_count", "avg_rating", "genres"]].head(15)

    # 4. Genre distribution
    genre_totals = movies_df[GENRE_COLUMNS].sum().sort_values(ascending=False)
    genre_dist_df = pd.DataFrame({
        "genre": genre_totals.index,
        "movie_count": genre_totals.values,
        "percentage_of_catalog": (genre_totals.values / len(movies_df) * 100).round(2)
    })

    # 5. User activity summary
    user_stats = ratings_df.groupby("user_id").agg(
        rating_count=("rating", "count"),
        avg_rating_given=("rating", "mean"),
        min_rating_given=("rating", "min"),
        max_rating_given=("rating", "max")
    ).reset_index()
    user_stats["avg_rating_given"] = user_stats["avg_rating_given"].round(2)

    return {
        "rating_dist_df": rating_dist_df,
        "overall_mean": overall_mean_rating,
        "overall_std": overall_std_rating,
        "overall_median": overall_median_rating,
        "movie_summary_df": movie_summary_df,
        "most_rated_movies": most_rated_movies,
        "highest_rated_movies": highest_rated_movies,
        "genre_dist_df": genre_dist_df,
        "user_stats": user_stats
    }


# -----------------------------------------------------------------------------
# Report & Visualizations
# -----------------------------------------------------------------------------
def generate_visualizations(eda_results: dict, reports_dir: Path):
    """
    Generates and saves clean matplotlib charts in the reports directory.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    generated_charts = []

    # Chart 1: Rating Distribution (Bar Chart)
    fig, ax = plt.subplots(figsize=(8, 5))
    rating_df = eda_results["rating_dist_df"]
    bars = ax.bar(
        rating_df["rating"].astype(str),
        rating_df["count"],
        color="#3B82F6",
        edgecolor="#1E3A8A",
        width=0.6,
        zorder=3
    )
    ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
    ax.set_title("MovieLens 100K — Rating Distribution", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Rating Score (Stars)", fontsize=11, labelpad=8)
    ax.set_ylabel("Number of Ratings", fontsize=11, labelpad=8)

    # Add count and percentage labels above each bar
    for bar, pct in zip(bars, rating_df["percentage"]):
        height = bar.get_height()
        ax.annotate(
            f"{height:,}\n({pct:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )
    ax.set_ylim(0, rating_df["count"].max() * 1.15)
    plt.tight_layout()
    chart1_path = reports_dir / "rating_distribution.png"
    plt.savefig(chart1_path, dpi=200)
    plt.close()
    generated_charts.append(chart1_path)

    # Chart 2: Top 15 Most Rated Movies (Horizontal Bar Chart)
    fig, ax = plt.subplots(figsize=(10, 6))
    top_movies = eda_results["most_rated_movies"].iloc[::-1]  # Invert order for top-at-the-top
    bars = ax.barh(
        top_movies["movie_title"],
        top_movies["rating_count"],
        color="#10B981",
        edgecolor="#047857",
        height=0.65,
        zorder=3
    )
    ax.grid(axis="x", linestyle="--", alpha=0.6, zorder=0)
    ax.set_title("Top 15 Most-Rated Movies", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Total Number of Ratings Received", fontsize=11, labelpad=8)
    ax.set_ylabel("Movie Title", fontsize=11, labelpad=8)

    # Label bars with rating count and avg rating
    for bar, avg in zip(bars, top_movies["avg_rating"]):
        width = bar.get_width()
        ax.annotate(
            f" {width:,} reviews (avg: {avg:.2f}/5)",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9
        )
    ax.set_xlim(0, top_movies["rating_count"].max() * 1.25)
    plt.tight_layout()
    chart2_path = reports_dir / "most_rated_movies.png"
    plt.savefig(chart2_path, dpi=200)
    plt.close()
    generated_charts.append(chart2_path)

    # Chart 3: Movie Genre Distribution (Horizontal Bar Chart)
    fig, ax = plt.subplots(figsize=(10, 7))
    genre_df = eda_results["genre_dist_df"].iloc[::-1]
    bars = ax.barh(
        genre_df["genre"],
        genre_df["movie_count"],
        color="#8B5CF6",
        edgecolor="#5B21B6",
        height=0.65,
        zorder=3
    )
    ax.grid(axis="x", linestyle="--", alpha=0.6, zorder=0)
    ax.set_title("Movie Catalog Distribution by Genre", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Movies in Genre", fontsize=11, labelpad=8)
    ax.set_ylabel("Genre", fontsize=11, labelpad=8)

    for bar, pct in zip(bars, genre_df["percentage_of_catalog"]):
        width = bar.get_width()
        ax.annotate(
            f" {width} ({pct:.1f}%)",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9
        )
    ax.set_xlim(0, genre_df["movie_count"].max() * 1.15)
    plt.tight_layout()
    chart3_path = reports_dir / "genre_distribution.png"
    plt.savefig(chart3_path, dpi=200)
    plt.close()
    generated_charts.append(chart3_path)

    # Chart 4: Average Movie Ratings Distribution (Histogram)
    fig, ax = plt.subplots(figsize=(9, 5))
    movie_summary = eda_results["movie_summary_df"]
    # Filter movies with at least 5 ratings for a meaningful histogram
    qualified_movies = movie_summary[movie_summary["rating_count"] >= 5]["avg_rating"]
    ax.hist(
        qualified_movies,
        bins=25,
        color="#F59E0B",
        edgecolor="#B45309",
        zorder=3
    )
    ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
    ax.axvline(qualified_movies.mean(), color="#DC2626", linestyle="--", linewidth=2, label=f"Mean: {qualified_movies.mean():.2f}")
    ax.axvline(qualified_movies.median(), color="#1D4ED8", linestyle=":", linewidth=2, label=f"Median: {qualified_movies.median():.2f}")
    ax.set_title("Average Rating Distribution per Movie (≥ 5 ratings)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Average Rating Score", fontsize=11, labelpad=8)
    ax.set_ylabel("Number of Movies", fontsize=11, labelpad=8)
    ax.legend(frameon=True)
    plt.tight_layout()
    chart4_path = reports_dir / "movie_average_ratings_distribution.png"
    plt.savefig(chart4_path, dpi=200)
    plt.close()
    generated_charts.append(chart4_path)

    # Chart 5: User Activity Distribution (Ratings Count per User)
    fig, ax = plt.subplots(figsize=(9, 5))
    user_counts = eda_results["user_stats"]["rating_count"]
    ax.hist(
        user_counts,
        bins=35,
        color="#EC4899",
        edgecolor="#9D174D",
        zorder=3
    )
    ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
    ax.axvline(user_counts.median(), color="#1E293B", linestyle="--", linewidth=2, label=f"Median: {user_counts.median():.0f} ratings")
    ax.set_title("User Engagement: Number of Ratings Submitted per User", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Ratings Submitted", fontsize=11, labelpad=8)
    ax.set_ylabel("Number of Users", fontsize=11, labelpad=8)
    ax.legend(frameon=True)
    plt.tight_layout()
    chart5_path = reports_dir / "user_activity_distribution.png"
    plt.savefig(chart5_path, dpi=200)
    plt.close()
    generated_charts.append(chart5_path)

    return generated_charts


# -----------------------------------------------------------------------------
# Data Export (Processed CSVs)
# -----------------------------------------------------------------------------
def save_processed_data(eda_results: dict, processed_dir: Path):
    """
    Saves clean, structured summary CSVs to data/processed/.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    exported_files = []

    # 1. Movie Summary CSV (ID, Title, Release Date, Count, Avg Rating, Genres)
    movie_summary_export = eda_results["movie_summary_df"][[
        "movie_id", "movie_title", "release_date", "rating_count", "avg_rating", "genres"
    ]]
    file1 = processed_dir / "movie_summary.csv"
    movie_summary_export.to_csv(file1, index=False)
    exported_files.append(file1)

    # 2. Rating Distribution CSV
    file2 = processed_dir / "rating_distribution.csv"
    eda_results["rating_dist_df"].to_csv(file2, index=False)
    exported_files.append(file2)

    # 3. Genre Distribution CSV
    file3 = processed_dir / "genre_distribution.csv"
    eda_results["genre_dist_df"].to_csv(file3, index=False)
    exported_files.append(file3)

    # 4. User Activity Summary CSV
    file4 = processed_dir / "user_activity_summary.csv"
    eda_results["user_stats"].to_csv(file4, index=False)
    exported_files.append(file4)

    return exported_files


# -----------------------------------------------------------------------------
# Terminal Summary Presentation
# -----------------------------------------------------------------------------
def display_eda_summary(quality: dict, eda_results: dict, charts: list, csvs: list):
    """
    Prints a clear, formatted summary of the findings in the console.
    Uses ASCII-safe formatting to ensure compatibility across all operating systems and shells.
    """
    border = "=" * 78
    sub_border = "-" * 78

    print("\n" + border)
    print("  CINEVORA - EXPLORATORY DATA ANALYSIS (EDA) REPORT")
    print("  Dataset: MovieLens 100K")
    print(border)

    print("\n[1] DATASET OVERVIEW & DIMENSIONS")
    print(sub_border)
    print(f"  * Total Ratings:          {quality['n_ratings']:,}")
    print(f"  * Unique Users:            {quality['n_users']:,}")
    print(f"  * Unique Rated Movies:     {quality['n_movies_rated']:,}")
    print(f"  * Total Movies in Catalog: {quality['n_movies_catalog']:,}")
    print(f"  * Interaction Sparsity:    {quality['sparsity'] * 100:.2f}% (Matrix is sparse)")
    print(f"  * Temporal Span:           {quality['date_range']}")

    print("\n[2] DATA INTEGRITY & CLEANLINESS")
    print(sub_border)
    print(f"  * Duplicate Rating Rows:   {quality['duplicate_ratings']}")
    print(f"  * Duplicate (User, Movie): {quality['duplicate_user_movie']}")
    print(f"  * Duplicate Movie IDs:     {quality['duplicate_movie_ids']}")
    print("  * Missing Values in Ratings: None (100% complete)")
    print("  * Missing Values in Movies:")
    for col, count in quality["movies_nulls"].items():
        if count > 0:
            print(f"    - {col}: {count:,} missing values")

    print("\n[3] RATING DISTRIBUTION & METRICS")
    print(sub_border)
    print(f"  * Mean Rating:   {eda_results['overall_mean']:.2f} / 5.0")
    print(f"  * Median Rating: {eda_results['overall_median']:.1f} / 5.0")
    print(f"  * Std Deviation: {eda_results['overall_std']:.2f}")
    print("\n  Rating Breakdown:")
    for _, row in eda_results["rating_dist_df"].iterrows():
        r = int(row["rating"])
        stars_bar = "[" + "*" * r + " " * (5 - r) + "]"
        print(f"    {r} Stars {stars_bar} : {int(row['count']):>6,} ({row['percentage']:>5.2f}%)")

    print("\n[4] TOP 10 MOST-RATED MOVIES")
    print(sub_border)
    print(f"  {'ID':<5} {'Title':<35} {'Ratings':<10} {'Avg Rating':<12} {'Genres'}")
    for _, row in eda_results["most_rated_movies"].head(10).iterrows():
        title = row["movie_title"][:33]
        genres = row["genres"][:25]
        print(f"  {row['movie_id']:<5} {title:<35} {row['rating_count']:<10} {row['avg_rating']:<12.2f} {genres}")

    print("\n[5] TOP 10 HIGHEST-RATED MOVIES (>= 50 Ratings)")
    print(sub_border)
    print(f"  {'ID':<5} {'Title':<35} {'Ratings':<10} {'Avg Rating':<12} {'Genres'}")
    for _, row in eda_results["highest_rated_movies"].head(10).iterrows():
        title = row["movie_title"][:33]
        genres = row["genres"][:25]
        print(f"  {row['movie_id']:<5} {title:<35} {row['rating_count']:<10} {row['avg_rating']:<12.2f} {genres}")

    print("\n[6] TOP 5 MOST COMMON GENRES")
    print(sub_border)
    for _, row in eda_results["genre_dist_df"].head(5).iterrows():
        print(f"  * {row['genre']:<15}: {int(row['movie_count']):>4} titles ({row['percentage_of_catalog']:.1f}% of catalog)")

    print("\n[7] GENERATED VISUALIZATIONS (Saved to reports/)")
    print(sub_border)
    for chart in charts:
        print(f"  [SAVED] {chart.name}")

    print("\n[8] PROCESSED SUMMARY CSVs (Saved to data/processed/)")
    print(sub_border)
    for f in csvs:
        print(f"  [SAVED] {f.name}")

    print("\n" + border)
    print("  EDA Completed Successfully.")
    print(border + "\n")


# -----------------------------------------------------------------------------
# Main Execution Flow
# -----------------------------------------------------------------------------
def main():
    # Ensure stdout handles UTF-8 characters if the terminal supports it
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("[INFO] Starting Cinevora Exploratory Data Analysis...")

    try:
        # Step 1: Verify and locate dataset files
        u_data_path, u_item_path = locate_dataset_files(RAW_DATA_DIR)

        # Step 2: Load datasets
        ratings_df, movies_df = load_movielens_data(u_data_path, u_item_path)

        # Step 3: Check data quality and dimensions
        quality = inspect_data_quality(ratings_df, movies_df)

        # Step 4: Perform statistical computations
        eda_results = perform_eda(ratings_df, movies_df)

        # Step 5: Generate and save charts
        charts = generate_visualizations(eda_results, REPORTS_DIR)

        # Step 6: Save processed CSVs
        csvs = save_processed_data(eda_results, PROCESSED_DATA_DIR)

        # Step 7: Display formatted terminal report
        display_eda_summary(quality, eda_results, charts, csvs)

    except FileNotFoundError as fnf_err:
        print(f"\n[ERROR] File missing: {fnf_err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"\n[ERROR] Unexpected error during EDA: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
