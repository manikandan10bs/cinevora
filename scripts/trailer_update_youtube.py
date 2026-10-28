"""
Cinevora Trailer Updater Script powered by Google Gemini
Finds exact YouTube trailer watch links (https://www.youtube.com/watch?v=VIDEO_ID) for movies
with null, empty, or fallback search query trailer values.

Rules:
1. Try up to 3 requests to Gemini per movie.
2. If any of the 3 requests returns a valid YouTube watch link, use it.
3. If all 3 requests fail, fall back to:
   https://www.youtube.com/results?search_query={movie_name}+trailer
"""

import os
import sys
import re
import time
import argparse
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# CSV file path
CSV_PATH = BASE_DIR / "data" / "processed" / "Movies_Master_Cleaned.csv"


def get_gemini_client():
    """Initializes Google GenAI Gemini client using app settings or environment variable."""
    try:
        from app.config import settings
        api_key = settings.get_gemini_api_key()
        model_name = settings.GEMINI_MODEL
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if not api_key:
        return None, model_name

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return client, model_name
    except Exception as e:
        print(f"Warning: Could not initialize Gemini client: {e}")
        return None, model_name


def resolve_trailer_with_gemini(client, model_name, movie_name, year=None, director=None, max_requests=3):
    """
    Tries up to 3 requests to Gemini to find the exact YouTube trailer URL.
    If all 3 fail, returns the YouTube search query fallback URL:
    https://www.youtube.com/results?search_query={movie_name}+trailer
    """
    clean_title = re.sub(r"\(.*?\)", "", str(movie_name)).strip()
    fallback_url = "https://www.youtube.com/results?search_query=" + quote_plus(f"{clean_title} trailer")

    if client is None:
        return fallback_url, "fallback (no gemini client)"

    from google.genai import types

    details = f"Movie: '{clean_title}'"
    if year and pd.notna(year):
        try:
            details += f" ({int(year)})"
        except Exception:
            details += f" ({year})"
    if director and pd.notna(director):
        details += f", Director: {director}"

    prompts = [
        # Request 1: Structured JSON prompt
        f"""Identify the exact official YouTube trailer video URL for this movie:
{details}
Respond with ONLY a JSON object:
{{"title": "{clean_title}", "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"}}
The URL MUST be an exact YouTube video watch link (https://www.youtube.com/watch?v=...).""",

        # Request 2: Direct link prompt
        f"""Find the exact official YouTube trailer watch link for the movie '{clean_title}'.
Provide ONLY the exact 11-character video ID watch link: https://www.youtube.com/watch?v=VIDEO_ID""",

        # Request 3: Final fallback link query
        f"""What is the full YouTube trailer link for '{clean_title}'? Return ONLY https://www.youtube.com/watch?v=..."""
    ]

    for req_idx in range(max_requests):
        try:
            prompt = prompts[min(req_idx, len(prompts) - 1)]
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            raw = (resp.text or "").strip()

            # Match standard YouTube watch URL: https://www.youtube.com/watch?v=...
            m = re.search(r"https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})", raw)
            if m:
                return m.group(0), f"gemini (request {req_idx + 1})"

            # Match youtu.be short URL
            m_short = re.search(r"https://youtu\.be/([a-zA-Z0-9_-]{11})", raw)
            if m_short:
                return f"https://www.youtube.com/watch?v={m_short.group(1)}", f"gemini (request {req_idx + 1})"

            print(f"    [Request {req_idx + 1}/{max_requests}] No exact link in response: {raw[:60]}...")
        except Exception as e:
            print(f"    [Request {req_idx + 1}/{max_requests}] Error from Gemini: {e}")
            time.sleep(0.5)

    return fallback_url, f"fallback (failed after {max_requests} requests)"


def main():
    parser = argparse.ArgumentParser(description="Update movie trailers using Google Gemini (max 3 requests) with search fallback.")
    parser.add_argument("--limit", type=int, default=10, help="Max number of movies to process (default: 10)")
    parser.add_argument("--all", action="store_true", help="Process all candidate movies")
    args = parser.parse_args()

    # Load dataset
    print(f"Loading dataset from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    # Find the movie title column automatically
    title_candidates = ["title", "movie_title", "movie_name", "name"]
    title_col = next((col for col in df.columns if col.lower() in title_candidates), None)
    if title_col is None:
        raise ValueError("Movie title column not found.")

    # Find the trailer column
    trailer_candidates = ["trailer_link", "trailer", "trailer_url", "trailer link"]
    trailer_col = next((col for col in df.columns if col.lower() in trailer_candidates), None)
    if trailer_col is None:
        trailer_col = "trailer_link"
        df[trailer_col] = pd.NA
        print(f"Created new column: {trailer_col}")

    # Optional helper columns
    year_col = next((col for col in df.columns if "year" in col.lower() or "date" in col.lower()), None)
    director_col = next((col for col in df.columns if "director" in col.lower()), None)

    # Identify candidate movies: null, empty, or fallback search query URLs
    mask = (
        df[trailer_col].isna()
        | df[trailer_col].astype(str).str.strip().eq("")
        | df[trailer_col].astype(str).str.contains("search_query", na=False)
    )

    candidates = df[mask].copy()
    candidate_count = len(candidates)
    print(f"\nTotal movies: {len(df)}")
    print(f"Movies needing exact trailer resolution: {candidate_count}")

    if candidate_count == 0:
        print("All movies already have exact trailer video links!")
        return

    limit = candidate_count if args.all else min(args.limit, candidate_count)
    selected_indices = candidates.index[:limit]
    print(f"Processing {limit} movies (Rule: Max 3 Gemini requests -> Fallback to YouTube search)...\n")

    client, model_name = get_gemini_client()
    if client:
        print(f"Google Gemini is ACTIVE (Model: {model_name})\n")
    else:
        print("Google Gemini is not configured. Using search query fallback directly.\n")

    exact_found_count = 0
    fallback_count = 0

    for i, idx in enumerate(selected_indices, 1):
        row = df.loc[idx]
        title = str(row[title_col])
        year = row[year_col] if year_col else None
        director = row[director_col] if director_col else None

        print(f"[{i}/{limit}] Resolving: '{title}'...")
        trailer_url, source = resolve_trailer_with_gemini(
            client=client,
            model_name=model_name,
            movie_name=title,
            year=year,
            director=director,
            max_requests=3
        )

        df.at[idx, trailer_col] = trailer_url

        if "gemini" in source:
            exact_found_count += 1
            print(f"  --> FOUND EXACT: {trailer_url} ({source})")
        else:
            fallback_count += 1
            print(f"  --> FALLBACK: {trailer_url} ({source})")

        # Gentle throttle between movies to respect API quotas
        if client:
            time.sleep(0.5)

    # Save the updated CSV
    backup_path = CSV_PATH.with_suffix(".csv.bak")
    df.to_csv(backup_path, index=False, encoding="utf-8-sig")
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 70)
    print("TRAILER UPDATE SUMMARY")
    print("=" * 70)
    print(f"Movies processed:          {limit}")
    print(f"Exact trailers resolved:   {exact_found_count}")
    print(f"Fallbacks assigned:        {fallback_count}")
    print(f"Updated CSV:               {CSV_PATH}")
    print(f"Backup created:            {backup_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
