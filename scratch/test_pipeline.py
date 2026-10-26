import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scratch.test_query_intent import parse_query_intent
from src.catalog_service import query_master_catalog

test_cases = [
    "Show me movies acted by Vijay.",
    "Movies directed by Christopher Nolan",
    "Tamil horror movies",
    "Movies directed by Lokesh Kanagaraj",
    "Vijay action movies from 2020 onward",
    "Movies starring Shah Rukh Khan",
    "Movies similar to Interstellar",
    "Best 90s Hollywood action movies",
    "Rajinikanth films",
    "Bollywood comedy movies with Akshay Kumar",
    "Movies directed by Quentin Tarantino in Tamil",
    "Recommend a thriller"
]

for q in test_cases:
    intent = parse_query_intent(q)
    matches, total = query_master_catalog(
        actor=intent.get("actor"),
        director=intent.get("director"),
        title=intent.get("title"),
        similar_to=intent.get("similar_to"),
        industry=intent.get("industry"),
        genre=intent.get("genre"),
        start_year=intent.get("start_year"),
        end_year=intent.get("end_year"),
        query=intent.get("free_query"),
        limit=5,
        sort_by="rating"
    )
    print(f"\n==========================================")
    print(f"QUERY: '{q}'")
    print(f"TOTAL MATCHES: {total}")
    for idx, m in enumerate(matches[:3]):
        print(f"  [{idx+1}] {m['title']} ({m['release_year']}) | Industry: {m['industry']} | Genre: {m['genre']} | Director: {m['director']} | Cast: {m['cast'][:45]}...")
