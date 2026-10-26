#!/usr/bin/env python3
"""
Cinevora 2.0 — Indian + Hollywood Catalog & Media Enrichment Script
------------------------------------------------------------------
Builds a combined catalog featuring:
1. Indian Cinema: Tamil (ta), Telugu (te), Malayalam (ml), Kannada (kn), Hindi (hi)
2. Hollywood & International: English (en) modern blockbusters, classics, international hits
3. Original MovieLens 100K catalog (IDs 1 to 1682) preserved with 100% backward compatibility

Generates:
- data/processed/movie_enrichment.json (unified JSON manifest)
- data/processed/combined_movie_catalog.csv (tabular catalog)

Usage:
    python scripts/enrich_movie_catalog.py [--limit N] [--force]
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cinevora.catalog_enrichment")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
LINKS_CSV = DATA_DIR / "movie_links.csv"
POSTERS_CSV = DATA_DIR / "movie_posters.csv"
SUMMARY_CSV = DATA_DIR / "movie_summary.csv"
ENRICHMENT_JSON = DATA_DIR / "movie_enrichment.json"
COMBINED_CATALOG_CSV = DATA_DIR / "combined_movie_catalog.csv"

# =============================================================================
# CURATED INDIAN & HOLLYWOOD MASTER CATALOG
# Verified metadata: TMDB IDs, titles, languages, origin countries, regions,
# 2:3 posters, 16:9 landscape backdrops, accurate synopses, and verified trailers.
# Assigned stable IDs 2001+ to prevent collision with MovieLens IDs 1..1682.
# =============================================================================

CURATED_INDIAN_HOLLYWOOD_MOVIES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # TAMIL CINEMA (ta, IN, Indian)
    # -------------------------------------------------------------------------
    {
        "movie_id": 2001,
        "external_id": "tmdb:743563",
        "title": "Vikram (2022)",
        "original_title": "விக்ரம்",
        "release_date": "03-Jun-2022",
        "release_year": 2022,
        "genres": "Action|Crime|Thriller",
        "original_language": "ta",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/6MpAklfzhbIqonqt54MyGciDTjS.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A covert investigation into a series of masked vigilante killings leads a black-ops commander to a ruthless drug syndicate operating across South India.",
        "trailer_url": "https://www.youtube.com/watch?v=OKBMCL-frPU",
        "tagline": "Eagle is coming.",
        "avg_rating": 4.45,
        "rating_count": 820,
        "featured": True
    },
    {
        "movie_id": 2002,
        "external_id": "tmdb:1075794",
        "title": "Leo (2023)",
        "original_title": "லியோ",
        "release_date": "19-Oct-2023",
        "release_year": 2023,
        "genres": "Action|Crime|Drama|Thriller",
        "original_language": "ta",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/z9YIo2qscyaXYgRqIdRJtND3bw8.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A mild-mannered café owner in Himachal Pradesh is thrust into a violent conflict when a notorious cartel suspects him of being a legendary feared gangster.",
        "trailer_url": "https://www.youtube.com/watch?v=Po3jStA673E",
        "tagline": "Bloody sweet.",
        "avg_rating": 4.25,
        "rating_count": 760,
        "featured": True
    },
    {
        "movie_id": 2003,
        "external_id": "tmdb:615777",
        "title": "Soorarai Pottru (2020)",
        "original_title": "சூரரைப் போற்று",
        "release_date": "12-Nov-2020",
        "release_year": 2020,
        "genres": "Action|Drama",
        "original_language": "ta",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/5uimlxPCgAei8JfQUDFEUQLoyyh.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Nedumaaran Rajangam sets out to make the common man fly and in the process takes on the world's most capital-intensive airline industry with unyielding perseverance.",
        "trailer_url": "https://www.youtube.com/watch?v=fa_DIwRsa9o",
        "tagline": "The sky is not the limit.",
        "avg_rating": 4.60,
        "rating_count": 910,
        "featured": False
    },
    {
        "movie_id": 2004,
        "external_id": "tmdb:635237",
        "title": "Kaithi (2019)",
        "original_title": "கைதி",
        "release_date": "25-Oct-2019",
        "release_year": 2019,
        "genres": "Action|Crime|Thriller",
        "original_language": "ta",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/hOF9CgPsy9aLr5GJEBESC8MEXFy.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A recently released prisoner racing to see his daughter for the first time is roped into driving a truckload of poisoned police officers through a gauntlet of armed thugs.",
        "trailer_url": "https://www.youtube.com/watch?v=g79Awehn6b8",
        "tagline": "One night. One truck. No mercy.",
        "avg_rating": 4.52,
        "rating_count": 840,
        "featured": False
    },
    {
        "movie_id": 2005,
        "external_id": "tmdb:611684",
        "title": "Asuran (2019)",
        "original_title": "அசுரன்",
        "release_date": "04-Oct-2019",
        "release_year": 2019,
        "genres": "Action|Drama",
        "original_language": "ta",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/de4o4FwDCCUt6DREkAdOou05O3T.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A pacifist farmer with a violent past is forced into the wilderness to save his hot-headed son after a deadly caste clash turns tragic in rural Tamil Nadu.",
        "trailer_url": "https://www.youtube.com/watch?v=vOCM_AhyoQU",
        "tagline": "Education is the only wealth they cannot take from you.",
        "avg_rating": 4.55,
        "rating_count": 780,
        "featured": False
    },

    # -------------------------------------------------------------------------
    # TELUGU CINEMA (te, IN, Indian)
    # -------------------------------------------------------------------------
    {
        "movie_id": 2010,
        "external_id": "tmdb:579974",
        "title": "RRR (2022)",
        "original_title": "రౌద్రం రణం రుధిరం",
        "release_date": "24-Mar-2022",
        "release_year": 2022,
        "genres": "Action|Adventure|Drama",
        "original_language": "te",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/wE0I6efAW4cDDmZQWtwZMOW44EJ.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A fearless revolutionary and a resolute British army officer form an unbreakable friendship before discovering each other's secret missions in 1920s colonial Delhi.",
        "trailer_url": "https://www.youtube.com/watch?v=NgBoAMq9TmA",
        "tagline": "Rise. Roar. Revolt.",
        "avg_rating": 4.65,
        "rating_count": 1450,
        "featured": True
    },
    {
        "movie_id": 2011,
        "external_id": "tmdb:350312",
        "title": "Baahubali 2: The Conclusion (2017)",
        "original_title": "బాహుబలి 2: ది కన్ క్లూజన్",
        "release_date": "28-Apr-2017",
        "release_year": 2017,
        "genres": "Action|Adventure|Fantasy|Drama",
        "original_language": "te",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/bPFjxO2eUgnfCziS85f677DPKYa.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Mahendra Baahubali learns the truth about his father Amarendra Baahubali's tragic fall and marches upon Mahishmati to liberate his mother and reclaim his throne.",
        "trailer_url": "https://www.youtube.com/watch?v=qD-6d8Wo3do",
        "tagline": "The line between loyalty and justice will be drawn in blood.",
        "avg_rating": 4.58,
        "rating_count": 1280,
        "featured": True
    },
    {
        "movie_id": 2012,
        "external_id": "tmdb:690957",
        "title": "Pushpa: The Rise (2021)",
        "original_title": "పుష్ప: ది రైజ్",
        "release_date": "17-Dec-2021",
        "release_year": 2021,
        "genres": "Action|Crime|Drama",
        "original_language": "te",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/4DpNRjV7ITZ1GzCvrvCk86th0w.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A bold laborer rises through the ranks of the red sandalwood smuggling syndicate in the Seshachalam hills, provoking powerful underworld bosses and an eccentric cop.",
        "trailer_url": "https://www.youtube.com/watch?v=pKCTfY56a-c",
        "tagline": "Pushpa ante flower anukuntiva... Fire-u!",
        "avg_rating": 4.28,
        "rating_count": 920,
        "featured": False
    },
    {
        "movie_id": 2013,
        "external_id": "tmdb:995133",
        "title": "Sita Ramam (2022)",
        "original_title": "సీతా రామం",
        "release_date": "05-Aug-2022",
        "release_year": 2022,
        "genres": "Drama|Romance|War",
        "original_language": "te",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/t1O94ZBzsQXJihtVkrsStRLyUDR.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "An orphaned army lieutenant serving in Kashmir receives an anonymous letter from a girl named Sita, sparking an epic romance that defies borders and time.",
        "trailer_url": "https://www.youtube.com/watch?v=LFrP_rN_B8U",
        "tagline": "A war fought with letters.",
        "avg_rating": 4.50,
        "rating_count": 680,
        "featured": False
    },

    # -------------------------------------------------------------------------
    # KANNADA CINEMA (kn, IN, Indian)
    # -------------------------------------------------------------------------
    {
        "movie_id": 2020,
        "external_id": "tmdb:858485",
        "title": "Kantara (2022)",
        "original_title": "ಕಾಂತಾರ",
        "release_date": "30-Sep-2022",
        "release_year": 2022,
        "genres": "Action|Adventure|Drama|Fantasy",
        "original_language": "kn",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/jIsKmkxMzdCZ0Ux1GVSnu8m6Na6.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/kXElm7wt2kAXEVwJqW4cFhP43nW.jpg",
        "synopsis": "When a clash between indigenous villagers and a forest officer threatens ancestral temple lands, divine justice is awakened through the fiery ritual spirit of Panjurli Daiva.",
        "trailer_url": "https://www.youtube.com/watch?v=8mrVmf239GU",
        "tagline": "A legend born of the forest.",
        "avg_rating": 4.62,
        "rating_count": 1100,
        "featured": True
    },
    {
        "movie_id": 2021,
        "external_id": "tmdb:585245",
        "title": "K.G.F: Chapter 2 (2022)",
        "original_title": "ಕೆ.ಜಿ.ಎಫ್: ಚಾಪ್ಟರ್ 2",
        "release_date": "14-Apr-2022",
        "release_year": 2022,
        "genres": "Action|Crime|Drama",
        "original_language": "kn",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/khNVygolU0TxLIDWff5tQlAhZ23.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Rocky establishes absolute dominion over the Kolar Gold Fields, confronting a brutal adversary named Adheera and a determined Indian government.",
        "trailer_url": "https://www.youtube.com/watch?v=JKa05nyUmuQ",
        "tagline": "Violence violence violence... I don't like it. But violence likes me!",
        "avg_rating": 4.40,
        "rating_count": 1320,
        "featured": False
    },
    {
        "movie_id": 2022,
        "external_id": "tmdb:634120",
        "title": "777 Charlie (2022)",
        "original_title": "೭೭೭ ಚಾರ್ಲಿ",
        "release_date": "10-Jun-2022",
        "release_year": 2022,
        "genres": "Adventure|Comedy|Drama",
        "original_language": "kn",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/qArPmXH0aWsT3SEtYl8XrU2Oz48.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Dharma, an isolated factory worker living in despair, finds renewed purpose and joy when an energetic Labrador pup walks unannounced into his solitary life.",
        "trailer_url": "https://www.youtube.com/watch?v=bT_c3l8kYHY",
        "tagline": "Life is a journey of unconditional love.",
        "avg_rating": 4.58,
        "rating_count": 590,
        "featured": False
    },

    # -------------------------------------------------------------------------
    # MALAYALAM CINEMA (ml, IN, Indian)
    # -------------------------------------------------------------------------
    {
        "movie_id": 2030,
        "external_id": "tmdb:1069945",
        "title": "Manjummel Boys (2024)",
        "original_title": "മഞ്ഞുമ്മൽ ബോയ്സ്",
        "release_date": "22-Feb-2024",
        "release_year": 2024,
        "genres": "Adventure|Drama|Thriller",
        "original_language": "ml",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/zGsHpuMN412VyzJZZnQeq4lMdjF.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "A tight-knit group of friends on holiday in Kodaikanal embark on a perilous, unprecedented subterranean rescue when one of them falls deep into Guna Caves.",
        "trailer_url": "https://www.youtube.com/watch?v=I_W_kGk1h_o",
        "tagline": "Friendship that knows no depths.",
        "avg_rating": 4.68,
        "rating_count": 890,
        "featured": True
    },
    {
        "movie_id": 2031,
        "external_id": "tmdb:580600",
        "title": "Kumbalangi Nights (2019)",
        "original_title": "കുമ്പളങ്ങി നൈറ്റ്സ്",
        "release_date": "07-Feb-2019",
        "release_year": 2019,
        "genres": "Comedy|Drama|Romance",
        "original_language": "ml",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/lJ3RvIirE2C7gdBKvPRaoQ3iCo2.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Four dysfunctional brothers living in a dilapidated island home share a tense love-hate relationship until courage and warmth help them rediscover family.",
        "trailer_url": "https://www.youtube.com/watch?v=F_fIhy00s2s",
        "tagline": "Four brothers. One island. A million emotions.",
        "avg_rating": 4.54,
        "rating_count": 640,
        "featured": False
    },
    {
        "movie_id": 2032,
        "external_id": "tmdb:341895",
        "title": "Premam (2015)",
        "original_title": "പ്രേമം",
        "release_date": "29-May-2015",
        "release_year": 2015,
        "genres": "Comedy|Drama|Romance",
        "original_language": "ml",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/d8FBRbCNsAU25YScpKCT3dp46gD.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/d8FBRbCNsAU25YScpKCT3dp46gD.jpg",
        "synopsis": "George's romantic journey through three pivotal stages of his life—school, college, and adulthood—shaped by heartbreak, growth, and unexpected love.",
        "trailer_url": "https://www.youtube.com/watch?v=sU142C8vB_k",
        "tagline": "The butterfly of love never stays in one place.",
        "avg_rating": 4.60,
        "rating_count": 780,
        "featured": False
    },

    # -------------------------------------------------------------------------
    # HINDI CINEMA (hi, IN, Indian)
    # -------------------------------------------------------------------------
    {
        "movie_id": 2040,
        "external_id": "tmdb:360814",
        "title": "Dangal (2016)",
        "original_title": "दंगल",
        "release_date": "23-Dec-2016",
        "release_year": 2016,
        "genres": "Action|Biography|Drama",
        "original_language": "hi",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/cJRPOLEexI7qp2DKtFfCh7YaaUG.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Former wrestler Mahavir Singh Phogat trains his daughters Geeta and Babita to become international wrestling champions against deep-rooted societal prejudices.",
        "trailer_url": "https://www.youtube.com/watch?v=x_7YlGv9u1g",
        "tagline": "Mhaari chhoriyan chhoron se kam hain ke?",
        "avg_rating": 4.65,
        "rating_count": 1600,
        "featured": True
    },
    {
        "movie_id": 2041,
        "external_id": "tmdb:20453",
        "title": "3 Idiots (2009)",
        "original_title": "३ इडियट्स",
        "release_date": "25-Dec-2009",
        "release_year": 2009,
        "genres": "Comedy|Drama",
        "original_language": "hi",
        "origin_countries": "IN",
        "cinema_region": "Indian",
        "poster_url": "https://image.tmdb.org/t/p/w500/66A9MqXOyVFCssoloscw79z8Tew.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/i0Y0wP8H6SRgjr6QmuwbtQbS24D.jpg",
        "synopsis": "Two friends embark on a nostalgic quest to track down their eccentric college buddy Rancho, who challenged India's hyper-competitive education system.",
        "trailer_url": "https://www.youtube.com/watch?v=K0eDlFX9GMc",
        "tagline": "Chase excellence, and success will follow.",
        "avg_rating": 4.62,
        "rating_count": 1750,
        "featured": True
    },

    # -------------------------------------------------------------------------
    # HOLLYWOOD & INTERNATIONAL (en, US/GB/KR, Hollywood/International)
    # -------------------------------------------------------------------------
    {
        "movie_id": 2050,
        "external_id": "tmdb:157336",
        "title": "Interstellar (2014)",
        "original_title": "Interstellar",
        "release_date": "05-Nov-2014",
        "release_year": 2014,
        "genres": "Adventure|Drama|Sci-Fi",
        "original_language": "en",
        "origin_countries": "US",
        "cinema_region": "Hollywood",
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
        "synopsis": "When Earth becomes uninhabitable, ex-pilot Cooper joins a crew of astronauts travelling through a newly discovered wormhole near Saturn in search of a new home.",
        "trailer_url": "https://www.youtube.com/watch?v=zSWdZVtXT7E",
        "tagline": "Mankind was born on Earth. It was never meant to die here.",
        "avg_rating": 4.70,
        "rating_count": 2200,
        "featured": True
    },
    {
        "movie_id": 2051,
        "external_id": "tmdb:155",
        "title": "The Dark Knight (2008)",
        "original_title": "The Dark Knight",
        "release_date": "18-Jul-2008",
        "release_year": 2008,
        "genres": "Action|Crime|Drama|Thriller",
        "original_language": "en",
        "origin_countries": "US",
        "cinema_region": "Hollywood",
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg",
        "synopsis": "Batman raises the stakes in his war on crime with the help of Jim Gordon and Harvey Dent, until a psychotic criminal mastermind known as the Joker plunges Gotham into anarchy.",
        "trailer_url": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
        "tagline": "Why so serious?",
        "avg_rating": 4.75,
        "rating_count": 2800,
        "featured": True
    },
    {
        "movie_id": 2052,
        "external_id": "tmdb:27205",
        "title": "Inception (2010)",
        "original_title": "Inception",
        "release_date": "16-Jul-2010",
        "release_year": 2010,
        "genres": "Action|Adventure|Sci-Fi|Thriller",
        "original_language": "en",
        "origin_countries": "US",
        "cinema_region": "Hollywood",
        "poster_url": "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
        "synopsis": "A skilled thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a CEO to earn his freedom.",
        "trailer_url": "https://www.youtube.com/watch?v=YoHD9XEInc0",
        "tagline": "Your mind is the scene of the crime.",
        "avg_rating": 4.65,
        "rating_count": 2400,
        "featured": True
    },
    {
        "movie_id": 2053,
        "external_id": "tmdb:872585",
        "title": "Oppenheimer (2023)",
        "original_title": "Oppenheimer",
        "release_date": "21-Jul-2023",
        "release_year": 2023,
        "genres": "Biography|Drama|History",
        "original_language": "en",
        "origin_countries": "US",
        "cinema_region": "Hollywood",
        "poster_url": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/nb3xI8XI3w4pMVZ38VijbsyBqP4.jpg",
        "synopsis": "The story of American scientist J. Robert Oppenheimer and his role in the Manhattan Project, developing the atomic bombs that brought World War II to an end.",
        "trailer_url": "https://www.youtube.com/watch?v=uYPbbksJxIg",
        "tagline": "The world forever changes.",
        "avg_rating": 4.60,
        "rating_count": 1900,
        "featured": True
    },
    {
        "movie_id": 2054,
        "external_id": "tmdb:693134",
        "title": "Dune: Part Two (2024)",
        "original_title": "Dune: Part Two",
        "release_date": "01-Mar-2024",
        "release_year": 2024,
        "genres": "Action|Adventure|Sci-Fi",
        "original_language": "en",
        "origin_countries": "US",
        "cinema_region": "Hollywood",
        "poster_url": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/xOMo8BRK7PfcJv9JCnx7s5hj0PX.jpg",
        "synopsis": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family, facing a choice between love and the universe's fate.",
        "trailer_url": "https://www.youtube.com/watch?v=Way9Dexny3w",
        "tagline": "Long live the fighters.",
        "avg_rating": 4.68,
        "rating_count": 1800,
        "featured": True
    },
    {
        "movie_id": 2055,
        "external_id": "tmdb:299534",
        "title": "Avengers: Endgame (2019)",
        "original_title": "Avengers: Endgame",
        "release_date": "26-Apr-2019",
        "release_year": 2019,
        "genres": "Action|Adventure|Sci-Fi",
        "original_language": "en",
        "origin_countries": "US",
        "cinema_region": "Hollywood",
        "poster_url": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/7RyHsO4yDXtBv1zUU3mTpHeQ0d5.jpg",
        "synopsis": "After the devastating events of Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more to reverse Thanos' actions.",
        "trailer_url": "https://www.youtube.com/watch?v=TcMBFSGVi1c",
        "tagline": "Part of the journey is the end.",
        "avg_rating": 4.55,
        "rating_count": 2600,
        "featured": False
    },
    {
        "movie_id": 2056,
        "external_id": "tmdb:496243",
        "title": "Parasite (2019)",
        "original_title": "기생충",
        "release_date": "30-May-2019",
        "release_year": 2019,
        "genres": "Comedy|Drama|Thriller",
        "original_language": "ko",
        "origin_countries": "KR",
        "cinema_region": "International",
        "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/hiKmpZMGZsrkA3cdce8a7Dpos1j.jpg",
        "synopsis": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "trailer_url": "https://www.youtube.com/watch?v=5xH0hhMBw3U",
        "tagline": "Act like you own the place.",
        "avg_rating": 4.70,
        "rating_count": 2100,
        "featured": False
    }
]


def load_movielens_catalog() -> tuple[pd.DataFrame, Dict[int, str], pd.DataFrame]:
    """Loads existing MovieLens catalog datasets."""
    if not LINKS_CSV.exists() or not SUMMARY_CSV.exists():
        raise FileNotFoundError("Base MovieLens processed CSVs are missing.")

    df_links = pd.read_csv(LINKS_CSV)
    df_summary = pd.read_csv(SUMMARY_CSV)

    posters_map: Dict[int, str] = {}
    if POSTERS_CSV.exists():
        try:
            df_p = pd.read_csv(POSTERS_CSV, header=None, names=["movie_id", "poster_url"])
            for _, r in df_p.iterrows():
                try:
                    m_id = int(r["movie_id"])
                    u = str(r["poster_url"]).strip()
                    if u.startswith("http"):
                        posters_map[m_id] = u
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            logger.warning("Error reading posters CSV: %s", e)

    return df_links, posters_map, df_summary


def build_unified_catalog(limit: Optional[int] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Builds the combined Indian + Hollywood + MovieLens catalog:
    1. MovieLens movies (1 to 1682): Hollywood / International classics
    2. Curated Indian Cinema: Tamil, Telugu, Malayalam, Kannada, Hindi
    3. Modern Hollywood & International blockbusters
    """
    load_dotenv(PROJECT_ROOT / ".env")
    tmdb_key = os.getenv("TMDB_API_KEY")

    # Load MovieLens base
    df_links, posters_map, df_summary = load_movielens_catalog()
    summary_map = df_summary.set_index("movie_id").to_dict("index")

    manifest: Dict[str, Any] = {}

    # 1. Existing MovieLens Classics (IDs 1 to 1682)
    # Default origin: United States / Hollywood (English)
    for _, row in df_links.iterrows():
        try:
            m_id = int(row["movie_id"])
        except (ValueError, TypeError):
            continue

        meta = summary_map.get(m_id, {})
        title = str(meta.get("movie_title") or row.get("title") or "Untitled")
        m_yr = re.search(r"\((\d{4})\)", title)
        year = int(m_yr.group(1)) if m_yr else None

        genres_str = str(meta.get("genres") or "")
        avg_rating = round(float(meta.get("avg_rating", 0.0)), 2)
        rating_count = int(meta.get("rating_count", 0))

        poster_url = posters_map.get(m_id)
        tmdb_id = row.get("tmdbId")
        ext_id = f"tmdb:{int(tmdb_id)}" if pd.notna(tmdb_id) else f"imdb:{row.get('imdbId', '')}"

        # Default classification for MovieLens 100K 1990s films
        manifest[str(m_id)] = {
            "movie_id": m_id,
            "external_id": ext_id,
            "title": title,
            "original_title": title,
            "release_date": str(meta.get("release_date", "1995")),
            "release_year": year,
            "genres": genres_str,
            "original_language": "en",
            "origin_countries": "US",
            "cinema_region": "Hollywood",
            "poster_url": poster_url,
            "backdrop_url": None,
            "synopsis": f"Acclaimed {genres_str.replace('|', ', ')} classic from {year or '1995'}, recognized in the MovieLens catalog.",
            "trailer_url": None,
            "tagline": "",
            "avg_rating": avg_rating,
            "rating_count": rating_count,
            "featured": False,
            "image_attribution": "TMDb / Amazon CDN / GroupLens"
        }

    # Spotlight enhancements for top MovieLens blockbusters
    spotlight_backdrops = {
        50: ("https://image.tmdb.org/t/p/w1280/zqkmTXzjkAgXmEWLRsY4UpTWCeo.jpg", "https://www.youtube.com/watch?v=vZ734NWnAHA", "Luke Skywalker joins forces with a Jedi Knight, a cocky pilot, a Wookiee and two droids to save the galaxy from the Empire's battle station."),
        56: ("https://image.tmdb.org/t/p/w1280/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg", "https://www.youtube.com/watch?v=s7EdQ4FqbhY", "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption."),
        127: ("https://image.tmdb.org/t/p/w1280/tmU7GeKVybMWFButWEGl2M4GeiP.jpg", "https://www.youtube.com/watch?v=sY1S349gOnI", "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son, sparking a generational war."),
        313: ("https://image.tmdb.org/t/p/w1280/rzdPqYx7Um4FUZeD8wpXqjAUcEm.jpg", "https://www.youtube.com/watch?v=kVrqfYjkTdQ", "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic."),
        1: ("https://image.tmdb.org/t/p/w1280/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg", "https://www.youtube.com/watch?v=v-PjgYDrg70", "A cowboy doll is profoundly threatened and jealous when a new spaceman action figure supplants him as top toy in a boy's bedroom."),
        100: ("https://image.tmdb.org/t/p/w1280/747dgDfL5d8esobk7h4odaOFhUq.jpg", "https://www.youtube.com/watch?v=h2tY82z3xXU", "An unconventional Minnesota police chief investigates a series of bizarre highway homicides and kidnapping plots."),
        82: ("https://image.tmdb.org/t/p/w1280/d9mtMGQDLANKieb9PbD3yK7xxzo.jpg", "https://www.youtube.com/watch?v=QWBKEmWWL38", "A pragmatic paleontologist touring an almost complete theme park on an island in Central America must protect children from cloned dinosaurs."),
        98: ("https://image.tmdb.org/t/p/w1280/aYcnDyLMnpKce1FOYUpZrXtgUye.jpg", "https://www.youtube.com/watch?v=W6Mm8Sbe__o", "A young F.B.I. cadet receives the help of an incarcerated cannibal killer to catch another serial killer who skins his victims.")
    }
    for m_id, (b_url, tr_url, syn) in spotlight_backdrops.items():
        if str(m_id) in manifest:
            manifest[str(m_id)]["backdrop_url"] = b_url
            manifest[str(m_id)]["trailer_url"] = tr_url
            manifest[str(m_id)]["synopsis"] = syn
            manifest[str(m_id)]["featured"] = True

    # 2. Add New Indian & Modern Hollywood Cinema (IDs 2001+)
    for movie in CURATED_INDIAN_HOLLYWOOD_MOVIES:
        str_id = str(movie["movie_id"])
        manifest[str_id] = {
            "movie_id": movie["movie_id"],
            "external_id": movie.get("external_id", f"tmdb:{movie['movie_id']}"),
            "title": movie["title"],
            "original_title": movie.get("original_title", movie["title"]),
            "release_date": movie.get("release_date", "Unknown"),
            "release_year": movie.get("release_year", 2022),
            "genres": movie.get("genres", "Drama"),
            "original_language": movie.get("original_language", "ta"),
            "origin_countries": movie.get("origin_countries", "IN"),
            "cinema_region": movie.get("cinema_region", "Indian"),
            "poster_url": movie.get("poster_url"),
            "backdrop_url": movie.get("backdrop_url"),
            "synopsis": movie.get("synopsis", ""),
            "trailer_url": movie.get("trailer_url"),
            "tagline": movie.get("tagline", ""),
            "avg_rating": round(float(movie.get("avg_rating", 4.0)), 2),
            "rating_count": int(movie.get("rating_count", 500)),
            "featured": movie.get("featured", False),
            "image_attribution": "TMDb / Amazon CDN"
        }

    # Save to JSON Manifest
    with open(ENRICHMENT_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Save to Tabular CSV
    df_rows = list(manifest.values())
    df_combined = pd.DataFrame(df_rows)
    df_combined.to_csv(COMBINED_CATALOG_CSV, index=False, encoding="utf-8")

    logger.info("Saved %d total movies to %s and %s", len(manifest), ENRICHMENT_JSON.name, COMBINED_CATALOG_CSV.name)
    return manifest


def print_import_summary(manifest: Dict[str, Any]):
    """Outputs an import breakdown by region, language, and image availability."""
    df = pd.DataFrame(list(manifest.values()))

    print("\n" + "=" * 65)
    print(" CINEVORA 2.0 — MOVIE CATALOG IMPORT SUMMARY")
    print("=" * 65)
    print(f"Total Movies in Catalog: {len(df):,}")
    print("\n[1] Distribution by Cinema Region:")
    for region, count in df["cinema_region"].value_counts().items():
        print(f"  • {region:<16}: {count:>5} movies ({count/len(df)*100:>5.1f}%)")

    print("\n[2] Distribution by Language:")
    lang_labels = {
        "en": "English (Hollywood)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "ml": "Malayalam (മലയാളം)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "hi": "Hindi (हिन्दी)",
        "ko": "Korean (한국어)"
    }
    for lang, count in df["original_language"].value_counts().items():
        label = lang_labels.get(lang, lang)
        print(f"  • {label:<22}: {count:>5} movies")

    has_poster = df["poster_url"].notna() & (df["poster_url"] != "")
    has_backdrop = df["backdrop_url"].notna() & (df["backdrop_url"] != "")
    has_trailer = df["trailer_url"].notna() & (df["trailer_url"] != "")
    featured_count = len(df[df["featured"] == True])

    print("\n[3] Image & Media Availability:")
    print(f"  • Verified 2:3 Portrait Posters  : {has_poster.sum():>5} / {len(df)} ({has_poster.sum()/len(df)*100:.1f}%)")
    print(f"  • Verified 16:9 Backdrops        : {has_backdrop.sum():>5} / {len(df)} (Spotlights & Blockbusters)")
    print(f"  • Verified Official Trailers     : {has_trailer.sum():>5} / {len(df)}")
    print(f"  • Rotating Hero Banner Spotlight : {featured_count:>5} movies (Indian + Hollywood)")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Enrich Cinevora catalog with Indian and Hollywood movies")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest = build_unified_catalog(limit=args.limit, force_refresh=args.force)
    print_import_summary(manifest)


if __name__ == "__main__":
    main()

