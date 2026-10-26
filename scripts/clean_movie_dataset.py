
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "raw" / "Movies_Master.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "Movies_Master_Cleaned.csv"
REPORT_FILE = OUTPUT_DIR / "Movies_Cleaning_Report.txt"

df = pd.read_csv(INPUT_FILE, low_memory=False)

# Standardize column names
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(r"\s+", "_", regex=True)
)

required_columns = [
    "movie_id", "industry", "title", "release_year", "genre",
    "rating", "cast", "director", "movie_poster", "trailer_link",
    "metadata_source", "poster_source", "trailer_source",
    "collection_method"
]

# Add any missing optional columns
for col in required_columns:
    if col not in df.columns:
        df[col] = pd.NA

# Keep the expected columns and their order
df = df[required_columns].copy()
rows_original = len(df)

# Clean text fields
text_columns = [
    "movie_id", "industry", "title", "genre", "cast", "director",
    "movie_poster", "trailer_link", "metadata_source",
    "poster_source", "trailer_source", "collection_method"
]

for col in text_columns:
    df[col] = df[col].astype("string").str.strip()
    df[col] = df[col].replace(
        r"(?i)^\s*(?:nan|none|null|n/?a)?\s*$",
        pd.NA,
        regex=True
    )
    df[col] = df[col].str.replace(r"\s+", " ", regex=True)

# Standardize industry names
industry_map = {
    "kollywood": "Tamil",
    "tamil": "Tamil",
    "tollywood": "Telugu",
    "telugu": "Telugu",
    "bollywood": "Bollywood",
    "hindi": "Bollywood",
    "mollywood": "Malayalam",
    "malayalam": "Malayalam",
    "sandalwood": "Kannada",
    "kannada": "Kannada",
    "hollywood": "Hollywood",
    "bengali": "Bengali"
}

df["industry"] = df["industry"].apply(
    lambda x: industry_map.get(str(x).strip().lower(), x)
    if pd.notna(x) else pd.NA
)

# Clean title and industry
df = df.dropna(subset=["title", "industry"])

# Clean release years
df["release_year"] = pd.to_numeric(
    df["release_year"], errors="coerce"
).astype("Int64")

invalid_year = (
    df["release_year"].notna()
    & ~df["release_year"].between(1888, 2100)
)
df.loc[invalid_year, "release_year"] = pd.NA

# Clean ratings without inventing missing values
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df.loc[~df["rating"].between(0, 10), "rating"] = float("nan")

# Validate URL format; keep only HTTP/HTTPS links
for col in ["movie_poster", "trailer_link"]:
    valid = df[col].str.match(r"^https?://\S+$", case=False, na=False)
    df.loc[~valid, col] = pd.NA

# Remove exact duplicate rows
df = df.drop_duplicates()

# Remove likely duplicates within an industry:
# same normalized title and release year.
# Keep the record with the most populated fields.
df["_title_key"] = (
    df["title"].str.casefold()
    .str.replace(r"[^\w\s]", "", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df["_completeness"] = df.notna().sum(axis=1)

df = df.sort_values("_completeness", ascending=False)

df = df.drop_duplicates(
    subset=["industry", "_title_key", "release_year"],
    keep="first"
)

df = df.drop(columns=["_title_key", "_completeness"])
df = df.reset_index(drop=True)

# Create a unique catalog ID without changing the original movie ID
df.insert(
    0,
    "catalog_id",
    [f"CINEVORA-{i:07d}" for i in range(1, len(df) + 1)]
)

# Save the cleaned dataset
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

industry_counts = df["industry"].value_counts(dropna=False)
poster_count = df["movie_poster"].notna().sum()
trailer_count = df["trailer_link"].notna().sum()

report = [
    f"Original rows: {rows_original}",
    f"Cleaned rows: {len(df)}",
    f"Rows removed: {rows_original - len(df)}",
    f"Movies with poster URLs: {poster_count}",
    f"Movies with trailer URLs: {trailer_count}",
    "",
    "Movies by industry:",
    industry_counts.to_string(),
]

REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

print("\nDataset cleaning completed!")
print("\n".join(report))
print(f"\nCleaned dataset: {OUTPUT_FILE}")
print(f"Cleaning report: {REPORT_FILE}")
