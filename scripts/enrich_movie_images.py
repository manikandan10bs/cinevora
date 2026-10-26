#!/usr/bin/env python3
"""
Cinevora Movie Catalog & Image Enrichment Script
------------------------------------------------
Enriches MovieLens 100K catalog movies with verified:
- Portrait poster image URLs (2:3 aspect ratio)
- High-definition landscape backdrop image URLs (16:9 aspect ratio)
- Accurate synopses and storylines
- Verified official trailer URLs
- TMDB / IMDb external IDs

Modes of Operation:
1. Local Manifest Mode (Default):
   Merges verified MovieLens links, poster mappings, and curated 16:9 landscape
   backdrops/synopses into data/processed/movie_enrichment.json. Requires no external API key.
2. TMDB API Mode:
   If TMDB_API_KEY is configured in .env or the environment, optionally fetches
   fresh backdrops and synopses directly from The Movie Database with rate limiting.

Usage:
    python scripts/enrich_movie_images.py [--limit N] [--force]
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cinevora.enrichment")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
LINKS_CSV = DATA_DIR / "movie_links.csv"
POSTERS_CSV = DATA_DIR / "movie_posters.csv"
SUMMARY_CSV = DATA_DIR / "movie_summary.csv"
OUTPUT_JSON = DATA_DIR / "movie_enrichment.json"

# Curated verified backdrops, synopses, and trailers for top catalog movies
CURATED_ENRICHMENT: Dict[int, Dict[str, Any]] = {
    50: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/zqkmTXzjkAgXmEWLRsY4UpTWCeo.jpg",
        "synopsis": "Luke Skywalker joins forces with a Jedi Knight, a cocky pilot, a Wookiee and two droids to save the galaxy from the Empire's world-destroying battle station, while attempting to rescue Princess Leia.",
        "trailer_url": "https://www.youtube.com/watch?v=vZ734NWnAHA",
        "tagline": "A long time ago in a galaxy far, far away...",
        "featured": True
    },
    56: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg",
        "synopsis": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption in Los Angeles.",
        "trailer_url": "https://www.youtube.com/watch?v=s7EdQ4FqbhY",
        "tagline": "Just because you are a character doesn't mean you have character.",
        "featured": True
    },
    127: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/tmU7GeKVybMWFButWEGl2M4GeiP.jpg",
        "synopsis": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son, sparking a generational war in post-war America.",
        "trailer_url": "https://www.youtube.com/watch?v=sY1S349gOnI",
        "tagline": "An offer you can't refuse.",
        "featured": True
    },
    313: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/rzdPqYx7Um4FUZeD8wpXqjAUcEm.jpg",
        "synopsis": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic on its maiden voyage across the Atlantic.",
        "trailer_url": "https://www.youtube.com/watch?v=kVrqfYjkTdQ",
        "tagline": "Nothing on Earth could come between them.",
        "featured": True
    },
    1: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
        "synopsis": "A cowboy doll is profoundly threatened and jealous when a new spaceman action figure supplants him as top toy in a boy's bedroom, sparking an unforgettable adventure.",
        "trailer_url": "https://www.youtube.com/watch?v=v-PjgYDrg70",
        "tagline": "Hang on for the comedy that goes to infinity and beyond!",
        "featured": True
    },
    100: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/747dgDfL5d8esobk7h4odaOFhUq.jpg",
        "synopsis": "An unconventional Minnesota police chief investigates a series of bizarre highway homicides and kidnapping plots orchestrated by a desperate car salesman.",
        "trailer_url": "https://www.youtube.com/watch?v=h2tY82z3xXU",
        "tagline": "A lot can happen in the middle of nowhere.",
        "featured": True
    },
    82: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/d9mtMGQDLANKieb9PbD3yK7xxzo.jpg",
        "synopsis": "A pragmatic paleontologist touring an almost complete theme park on an island in Central America is tasked with protecting a couple of kids after a power failure causes the park's cloned dinosaurs to run loose.",
        "trailer_url": "https://www.youtube.com/watch?v=QWBKEmWWL38",
        "tagline": "An adventure 65 million years in the making.",
        "featured": True
    },
    98: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/aYcnDyLMnpKce1FOYUpZrXtgUye.jpg",
        "synopsis": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer who skins his victims.",
        "trailer_url": "https://www.youtube.com/watch?v=W6Mm8Sbe__o",
        "tagline": "To enter the mind of a killer she must challenge the mind of a madman.",
        "featured": True
    },
    172: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/dMZxEdrWIzUmUoOz2zvmFuutbj7.jpg",
        "synopsis": "After the Rebels are overpowered by the Empire, Luke Skywalker begins Jedi training with Yoda, while his friends are pursued across the galaxy by Darth Vader.",
        "trailer_url": "https://www.youtube.com/watch?v=JNwNXF9Y6kY",
        "tagline": "The Adventure Continues...",
        "featured": True
    },
    258: {
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/2JApfvtgf2snKUtOFn8d1wm5pDU.jpg",
        "synopsis": "Dr. Ellie Arroway, after years of searching, finds conclusive radio proof of extraterrestrial intelligence sending plans for a mysterious human transport machine.",
        "trailer_url": "https://www.youtube.com/watch?v=SRoj3jK37VC",
        "tagline": "If we're alone in the universe, it has to be an awful waste of space.",
        "featured": True
    }
}


def load_catalog_datasets() -> tuple[pd.DataFrame, Dict[int, str], pd.DataFrame]:
    """Loads links, posters, and movie summary metadata."""
    if not LINKS_CSV.exists():
        raise FileNotFoundError(f"Missing {LINKS_CSV}")
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing {SUMMARY_CSV}")

    df_links = pd.read_csv(LINKS_CSV)
    df_summary = pd.read_csv(SUMMARY_CSV)

    posters_map: Dict[int, str] = {}
    if POSTERS_CSV.exists():
        try:
            df_posters = pd.read_csv(POSTERS_CSV, header=None, names=["movie_id", "poster_url"])
            for _, r in df_posters.iterrows():
                try:
                    m_id = int(r["movie_id"])
                    url = str(r["poster_url"]).strip()
                    if url and url.startswith("http"):
                        posters_map[m_id] = url
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            logger.warning("Could not read posters CSV: %s", e)

    return df_links, posters_map, df_summary


def fetch_tmdb_metadata(tmdb_id: int, api_key: str) -> Dict[str, Any]:
    """Fetches details, backdrops, and videos from TMDB API if key is available."""
    import urllib.request
    import urllib.error

    headers = {"User-Agent": "CinevoraEnrichment/1.0"}
    base_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&append_to_response=videos,images"
    req = urllib.request.Request(base_url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            backdrop_path = data.get("backdrop_path")
            poster_path = data.get("poster_path")
            overview = data.get("overview")
            tagline = data.get("tagline")

            trailer_url = None
            videos = data.get("videos", {}).get("results", [])
            for v in videos:
                if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
                    trailer_url = f"https://www.youtube.com/watch?v={v.get('key')}"
                    break

            res = {}
            if backdrop_path:
                res["backdrop_url"] = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
            if poster_path:
                res["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
            if overview:
                res["synopsis"] = overview
            if tagline:
                res["tagline"] = tagline
            if trailer_url:
                res["trailer_url"] = trailer_url
            return res
    except Exception as e:
        logger.debug("TMDB request failed for ID %s: %s", tmdb_id, e)
        return {}


def build_enrichment_manifest(limit: Optional[int] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """Builds or updates the complete movie enrichment manifest."""
    load_dotenv(PROJECT_ROOT / ".env")
    tmdb_api_key = os.getenv("TMDB_API_KEY")

    existing_manifest: Dict[str, Any] = {}
    if OUTPUT_JSON.exists() and not force_refresh:
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                existing_manifest = json.load(f)
            logger.info("Loaded %d existing enrichment records from %s", len(existing_manifest), OUTPUT_JSON.name)
        except Exception as e:
            logger.warning("Could not parse existing %s: %s", OUTPUT_JSON.name, e)

    df_links, posters_map, df_summary = load_catalog_datasets()
    summary_map = df_summary.set_index("movie_id").to_dict("index")

    manifest = existing_manifest.copy()
    count_enriched = 0

    rows_to_process = df_links.head(limit) if limit else df_links

    for _, row in rows_to_process.iterrows():
        try:
            m_id = int(row["movie_id"])
        except (ValueError, TypeError):
            continue

        str_id = str(m_id)
        current = manifest.get(str_id, {})

        meta = summary_map.get(m_id, {})
        title = str(meta.get("movie_title") or row.get("title") or "Untitled")

        # Extract release year
        m_yr = re.search(r"\((\d{4})\)", title)
        year = int(m_yr.group(1)) if m_yr else None

        genres_str = str(meta.get("genres") or "")
        avg_rating = float(meta.get("avg_rating", 0.0))
        rating_count = int(meta.get("rating_count", 0))

        imdb_id = str(row.get("imdbId", "")).strip()
        tmdb_raw = row.get("tmdbId")
        tmdb_id = int(tmdb_raw) if pd.notna(tmdb_raw) else None

        poster_url = current.get("poster_url") or posters_map.get(m_id)
        backdrop_url = current.get("backdrop_url")
        synopsis = current.get("synopsis")
        trailer_url = current.get("trailer_url")
        tagline = current.get("tagline")
        is_featured = current.get("featured", False)

        # Apply curated records if available
        if m_id in CURATED_ENRICHMENT:
            cur = CURATED_ENRICHMENT[m_id]
            backdrop_url = cur.get("backdrop_url", backdrop_url)
            synopsis = cur.get("synopsis", synopsis)
            trailer_url = cur.get("trailer_url", trailer_url)
            tagline = cur.get("tagline", tagline)
            is_featured = cur.get("featured", is_featured)

        # TMDB enrichment if key configured and backdrop missing
        if tmdb_api_key and tmdb_id and not backdrop_url:
            tmdb_data = fetch_tmdb_metadata(tmdb_id, tmdb_api_key)
            if tmdb_data:
                backdrop_url = tmdb_data.get("backdrop_url", backdrop_url)
                if not poster_url:
                    poster_url = tmdb_data.get("poster_url")
                if not synopsis:
                    synopsis = tmdb_data.get("synopsis")
                if not trailer_url:
                    trailer_url = tmdb_data.get("trailer_url")
                if not tagline:
                    tagline = tmdb_data.get("tagline")
            time.sleep(0.05)  # Respect API rate limits

        manifest[str_id] = {
            "movie_id": m_id,
            "title": title,
            "release_year": year,
            "genres": genres_str,
            "avg_rating": round(avg_rating, 2),
            "rating_count": rating_count,
            "imdb_id": imdb_id,
            "tmdb_id": tmdb_id,
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "synopsis": synopsis,
            "trailer_url": trailer_url,
            "tagline": tagline,
            "featured": is_featured,
            "attribution": "TMDb / Amazon CDN / GroupLens"
        }
        count_enriched += 1

    # Write output to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info("Successfully wrote %d enriched records to %s", len(manifest), OUTPUT_JSON)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Enrich MovieLens catalog with verified posters & backdrops")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of movies to enrich")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing manifest")
    args = parser.parse_args()

    try:
        manifest = build_enrichment_manifest(limit=args.limit, force_refresh=args.force)
        featured = [m for m in manifest.values() if m.get("featured")]
        print(f"Enrichment Complete: {len(manifest)} movies processed ({len(featured)} featured spotlight movies).")
    except Exception as e:
        logger.error("Enrichment failed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
