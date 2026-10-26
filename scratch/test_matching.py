import pandas as pd
import re

df = pd.read_csv("data/processed/Movies_Master_Cleaned.csv")

def matches_name(field_val: str, target: str) -> bool:
    if not field_val or not target:
        return False
    t = target.strip().lower()
    members = [m.strip().lower() for m in str(field_val).split(",")]
    for m in members:
        if t == m:
            return True
        if len(t.split()) > 1:
            if t in m or m in t:
                return True
        else:
            if re.search(r"\b" + re.escape(t) + r"\b", m):
                return True
    return False

for actor in ["Vijay", "Shah Rukh Khan", "Rajinikanth", "Leonardo DiCaprio", "Dhanush"]:
    cnt = sum(1 for c in df["cast"] if matches_name(c, actor))
    print(f"Actor '{actor}': {cnt} movies found")

for dir_name in ["Christopher Nolan", "Lokesh Kanagaraj", "Mani Ratnam", "Prashanth Neel"]:
    cnt = sum(1 for d in df["director"] if matches_name(d, dir_name))
    print(f"Director '{dir_name}': {cnt} movies found")
