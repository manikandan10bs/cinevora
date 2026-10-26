import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval_service import movie_retrieval_service, QueryFilters
from src.recommender import master_content_recommender
from app.db import init_db, toggle_like, get_user_likes

init_db()
user = "test_adapt_debug"
for m in list(get_user_likes(user)):
    toggle_like(user, m)

h_movies, _ = movie_retrieval_service.search(QueryFilters(genre="Horror"), limit=3)
print("Found horror movies:", len(h_movies))
for m in h_movies:
    print(" ", m["catalog_id"], m["title"], m["genre"], m["rating"])
    toggle_like(user, m["catalog_id"])

recs = master_content_recommender.recommend_for_user(user, limit=5)
print("\nRecommendations for user with 3 horror likes:")
for r in recs:
    print(" ", r["catalog_id"], r["title"], r["genre"], r["score"])
