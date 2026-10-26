
import pandas as pd
from pathlib import Path
from urllib.parse import quote_plus

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# CSV file path
CSV_PATH = BASE_DIR / "data" / "processed" / "Movies_Master_Cleaned.csv"

# Load dataset
df = pd.read_csv(CSV_PATH)

# Clean column names
df.columns = df.columns.str.strip()

# Print available columns
print("Available columns:")
for col in df.columns:
    print(f"- {col}")

# Find the movie title column automatically
title_candidates = ["title", "movie_title", "movie_name", "name"]
title_col = next(
    (col for col in df.columns if col.lower() in title_candidates),
    None
)

if title_col is None:
    raise ValueError(
        "Movie title column not found. Check the column names printed above."
    )

# Find the existing trailer column, ignoring case
trailer_candidates = ["trailer", "trailer_url", "trailer link", "trailer_link"]
trailer_col = next(
    (col for col in df.columns if col.lower() in trailer_candidates),
    None
)

# If no trailer column exists, create one
if trailer_col is None:
    trailer_col = "trailer"
    df[trailer_col] = pd.NA
    print(f"\nCreated new column: {trailer_col}")

# Identify missing trailer values
mask = (
    df[trailer_col].isna()
    | df[trailer_col].astype(str).str.strip().eq("")
)

# Generate YouTube search URLs for missing values
def generate_trailer_url(movie_name):
    if pd.isna(movie_name) or not str(movie_name).strip():
        return None

    query = f"{str(movie_name).strip()} trailer"
    return "https://www.youtube.com/results?search_query=" + quote_plus(query)

df.loc[mask, trailer_col] = df.loc[mask, title_col].apply(
    generate_trailer_url
)

# Save the updated CSV
df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

print(f"\nMovie title column: {title_col}")
print(f"Trailer column: {trailer_col}")
print(f"Missing trailer values filled: {mask.sum()}")
print(f"Updated file: {CSV_PATH}")
