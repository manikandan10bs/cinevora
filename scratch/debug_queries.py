import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant import GeminiAssistant
from src.retrieval_service import movie_retrieval_service, QueryFilters

asst = GeminiAssistant()

# Check intent for Vijay's Tamil action movies
q1 = "Vijay's Tamil action movies"
intent1_det = asst.parse_query_intent(q1)
print("Query 1 deterministic intent:", intent1_det)
intent1_gem = asst.parse_query_intent_with_gemini(q1)
print("Query 1 Gemini intent:", intent1_gem)

f1 = QueryFilters(
    actor=intent1_gem.get("actor"),
    director=intent1_gem.get("director"),
    genre=intent1_gem.get("genre"),
    industry=intent1_gem.get("industry"),
    year_from=intent1_gem.get("start_year"),
    year_to=intent1_gem.get("end_year"),
    title=intent1_gem.get("title")
)
recs1, tot1 = movie_retrieval_service.search(f1)
print("Retrieval total 1:", tot1)


# Check intent for English science-fiction movies
q2 = "English science-fiction movies"
intent2_det = asst.parse_query_intent(q2)
print("\nQuery 2 deterministic intent:", intent2_det)
intent2_gem = asst.parse_query_intent_with_gemini(q2)
print("Query 2 Gemini intent:", intent2_gem)

f2 = QueryFilters(
    actor=intent2_gem.get("actor"),
    director=intent2_gem.get("director"),
    genre=intent2_gem.get("genre"),
    industry=intent2_gem.get("industry"),
    year_from=intent2_gem.get("start_year"),
    year_to=intent2_gem.get("end_year"),
    title=intent2_gem.get("title")
)
recs2, tot2 = movie_retrieval_service.search(f2)
print("Retrieval total 2:", tot2)
