"""
Cinevora Trailer Enrichment Script powered by Google Gemini
Enriches movies that currently have fallback YouTube search query URLs
with exact YouTube trailer video watch links (https://www.youtube.com/watch?v=VIDEO_ID).
"""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google import genai
from google.genai import types
from urllib.parse import quote_plus
from app.config import settings

CSV_PATH = PROJECT_ROOT / "data" / "processed" / "Movies_Master_Cleaned.csv"


def enrich_batch(client, batch_movies, max_attempts=3):
    """
    Sends a batch of movies to Gemini to get exact YouTube trailer URLs.
    Tries up to max_attempts (3 requests).
    """
    clean_batch = []
    for m in batch_movies:
        clean_batch.append({
            "catalog_id": str(m["catalog_id"]),
            "title": str(m["title"]),
            "year": int(m["release_year"]) if pd.notna(m["release_year"]) else None,
            "director": str(m["director"]) if pd.notna(m["director"]) else None,
            "industry": str(m["industry"]) if pd.notna(m["industry"]) else None
        })

    prompt = f"""You are a cinema metadata assistant. For each movie below, find its exact official YouTube trailer URL.
The URL must be a valid YouTube watch link in the format https://www.youtube.com/watch?v=VIDEO_ID.

Movies:
{json.dumps(clean_batch, indent=2)}

Return ONLY a valid JSON array of objects matching this exact format:
[
  {{"catalog_id": "...", "title": "...", "youtube_url": "https://www.youtube.com/watch?v=..."}}
]
"""

    for attempt in range(max_attempts):
        try:
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            raw = (resp.text or "").strip()
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                results = json.loads(m.group(0))
                matched = {
                    item["catalog_id"]: item.get("youtube_url")
                    for item in results
                    if item.get("youtube_url") and ("watch?v=" in item["youtube_url"] or "youtu.be/" in item["youtube_url"])
                }
                if matched:
                    return matched
            print(f"  [Batch Attempt {attempt + 1}/{max_attempts}] Could not parse exact URLs, retrying...")
        except Exception as e:
            print(f"  [Batch Attempt {attempt + 1}/{max_attempts}] Error calling Gemini: {e}")
            time.sleep(0.5)

    return {}


def main():
    parser = argparse.ArgumentParser(description="Enrich movie trailers using Google Gemini")
    parser.add_argument("--limit", type=int, default=50, help="Max number of movies to enrich")
    parser.add_argument("--batch-size", type=int, default=8, help="Number of movies per Gemini prompt")
    parser.add_argument("--all", action="store_true", help="Process all candidate movies")
    args = parser.parse_args()

    api_key = settings.get_gemini_api_key()
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print(f"Loading catalog from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    total_movies = len(df)
    
    # Identify candidates
    mask = df["trailer_link"].isna() | df["trailer_link"].str.contains("search_query", na=False)
    candidates = df[mask].copy()
    candidate_count = len(candidates)
    print(f"Total movies: {total_movies}, Candidates with fallback/missing trailer: {candidate_count}")

    if candidate_count == 0:
        print("All movies already have exact trailers!")
        return

    limit = candidate_count if args.all else min(args.limit, candidate_count)
    selected_indices = candidates.index[:limit]
    print(f"Enriching up to {limit} movies (Batch size: {args.batch_size})...")

    updated_count = 0
    batch = []
    batch_indices = []

    for idx in selected_indices:
        row = df.loc[idx]
        batch.append({
            "catalog_id": row.get("catalog_id", f"INDEX-{idx}"),
            "title": row.get("title", "Unknown"),
            "release_year": row.get("release_year"),
            "director": row.get("director"),
            "industry": row.get("industry")
        })
        batch_indices.append(idx)

        if len(batch) >= args.batch_size:
            trailer_map = enrich_batch(client, batch, max_attempts=3)
            for b_idx, m_info in zip(batch_indices, batch):
                cid = m_info["catalog_id"]
                if cid in trailer_map:
                    df.at[b_idx, "trailer_link"] = trailer_map[cid]
                    updated_count += 1
                    print(f"  [OK] {m_info['title']} -> {trailer_map[cid]}")
                else:
                    clean_title = re.sub(r"\(.*?\)", "", str(m_info["title"])).strip()
                    fallback_url = "https://www.youtube.com/results?search_query=" + quote_plus(f"{clean_title} trailer")
                    df.at[b_idx, "trailer_link"] = fallback_url
                    print(f"  [Fallback after 3 requests] {m_info['title']} -> {fallback_url}")
            batch = []
            batch_indices = []
            time.sleep(1.0)  # Gentle rate limiting

    if batch:
        trailer_map = enrich_batch(client, batch, max_attempts=3)
        for b_idx, m_info in zip(batch_indices, batch):
            cid = m_info["catalog_id"]
            if cid in trailer_map:
                df.at[b_idx, "trailer_link"] = trailer_map[cid]
                updated_count += 1
                print(f"  [OK] {m_info['title']} -> {trailer_map[cid]}")
            else:
                clean_title = re.sub(r"\(.*?\)", "", str(m_info["title"])).strip()
                fallback_url = "https://www.youtube.com/results?search_query=" + quote_plus(f"{clean_title} trailer")
                df.at[b_idx, "trailer_link"] = fallback_url
                print(f"  [Fallback after 3 requests] {m_info['title']} -> {fallback_url}")

    print(f"\nSuccessfully enriched {updated_count}/{limit} movies with exact YouTube trailers!")

    if updated_count > 0:
        # Save back to CSV
        backup_path = CSV_PATH.with_suffix(".csv.bak")
        df.to_csv(backup_path, index=False)
        df.to_csv(CSV_PATH, index=False)
        print(f"Saved updated catalog to {CSV_PATH} (Backup created at {backup_path})")


if __name__ == "__main__":
    main()
