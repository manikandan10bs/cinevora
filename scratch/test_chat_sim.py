import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assistant import GeminiAssistant

asst = GeminiAssistant()

print("--- Test Similarity: Movies similar in theme to Leo ---")
r = asst.chat("Movies similar in theme to Leo", limit=5)
print("Count:", len(r.recommendations))
for m in r.recommendations:
    print(f"  {m.movie_id} | {m.movie_title} ({m.release_date}) | {m.cinema_region} | {m.genres}")
print("Reply snippet:", r.reply[:200])
