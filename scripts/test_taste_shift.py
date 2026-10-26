import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.recommender import MasterContentRecommender
from src.catalog_service import load_master_catalog
from app.db import toggle_like, get_db_connection

df = load_master_catalog()
rec = MasterContentRecommender(df)

user_test = "unit_test_taste_shift"
with get_db_connection() as conn:
    conn.cursor().execute("DELETE FROM likes WHERE user_id = ?;", (user_test,))
    conn.commit()

# Find an Action movie and a Horror movie
action_m = df[df["genre"].str.lower().str.contains("action", na=False)].iloc[0]
horror_m = df[df["genre"].str.lower().str.contains("horror", na=False)].iloc[0]
toggle_like(user_test, action_m["catalog_id"])
toggle_like(user_test, horror_m["catalog_id"])

recs_ah = rec.recommend_for_user(user_test, limit=6)
print("=== LIKED ACTION + HORROR ===")
print("Liked:", action_m["title"], f"({action_m['genre']})", "+", horror_m["title"], f"({horror_m['genre']})")
print("Recommendations:")
for r in recs_ah:
    print(f"  * {r['title']} | {r['industry']} | {r['genre']}")

# Clear likes and like Drama
with get_db_connection() as conn:
    conn.cursor().execute("DELETE FROM likes WHERE user_id = ?;", (user_test,))
    conn.commit()

drama_m = df[df["genre"].str.lower().str.contains("drama", na=False)].iloc[0]
toggle_like(user_test, drama_m["catalog_id"])

recs_d = rec.recommend_for_user(user_test, limit=6)
print("\n=== CLEARED & LIKED DRAMA ===")
print("Liked:", drama_m["title"], f"({drama_m['genre']})")
print("Recommendations:")
for r in recs_d:
    print(f"  * {r['title']} | {r['industry']} | {r['genre']}")

# Test Indian filter isolation
recs_ind = rec.recommend_for_user(user_test, industry="Indian", limit=8)
print("\n=== REGION = INDIAN RECOMMENDATIONS ===")
has_hollywood = any("hollywood" in str(r["industry"]).lower() for r in recs_ind)
print(f"Has Hollywood movies? {has_hollywood}")
for r in recs_ind[:4]:
    print(f"  * {r['title']} | Industry: {r['industry']}")

# Cleanup
with get_db_connection() as conn:
    conn.cursor().execute("DELETE FROM likes WHERE user_id = ?;", (user_test,))
    conn.commit()
