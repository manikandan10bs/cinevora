import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant import GeminiAssistant

asst = GeminiAssistant()

print("--- Test 1: Vijay's Tamil action movies ---")
r1 = asst.chat("Vijay's Tamil action movies", limit=5)
print("Count:", len(r1.recommendations))
for m in r1.recommendations:
    print(f"  {m.movie_id} | {m.movie_title} ({m.release_date}) | {m.cinema_region} | {m.genres}")

print("\n--- Test 2: English science-fiction movies ---")
r2 = asst.chat("English science-fiction movies", limit=5)
print("Count:", len(r2.recommendations))
for m in r2.recommendations:
    print(f"  {m.movie_id} | {m.movie_title} ({m.release_date}) | {m.cinema_region} | {m.genres}")

print("\n--- Test 3: Movies directed by Lokesh Kanagaraj ---")
r3 = asst.chat("Movies directed by Lokesh Kanagaraj", limit=5)
print("Count:", len(r3.recommendations))
for m in r3.recommendations:
    print(f"  {m.movie_id} | {m.movie_title} ({m.release_date}) | {m.cinema_region} | {m.genres}")

print("\n--- Test 4: Tamil thriller movies released after 2020 ---")
r4 = asst.chat("Tamil thriller movies released after 2020", limit=5)
print("Count:", len(r4.recommendations))
for m in r4.recommendations:
    print(f"  {m.movie_id} | {m.movie_title} ({m.release_date}) | {m.cinema_region} | {m.genres}")

print("\n--- Test 5: Impossible / No-match query ---")
r5 = asst.chat("Movies directed by Quentin Tarantino in Tamil", limit=5)
print("Count:", len(r5.recommendations))
print("Reply snippet:", r5.reply[:120])
