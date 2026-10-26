import re
from typing import Dict, Any, Optional, Tuple

def parse_movie_query(query: str) -> Dict[str, Any]:
    text = query.strip()
    text_lower = text.lower()
    
    extracted: Dict[str, Any] = {
        "actor": None,
        "director": None,
        "genre": None,
        "industry": None,
        "start_year": None,
        "end_year": None,
        "title": None,
        "similar_to": None,
        "raw_query": query
    }
    
    # 1. Similar to / like movie
    sim_m = re.search(r"\b(?:similar\s+to|like|recommend.*like)\s+['\"]?([A-Za-z0-9\s\:\'\-]+?)['\"]?(?:\s+(?:movie|film|in|from)|$)", text, re.IGNORECASE)
    if sim_m:
        extracted["similar_to"] = sim_m.group(1).strip()

    # 2. Director pattern
    dir_m = re.search(r"\b(?:directed\s+by|director|direction\s+by)\s+['\"]?([A-Za-z\s\.\'\-]+?)['\"]?(?:\s+(?:in|from|with|starring|released|movies?|films?)|$)", text, re.IGNORECASE)
    if dir_m:
        extracted["director"] = dir_m.group(1).strip()
    else:
        # e.g. "Christopher Nolan movies" or "Christopher Nolan films"
        dir_m2 = re.search(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)\s+(?:movies?|films?)", text)
        # We can verify against director list in catalog
        
    # 3. Actor pattern
    actor_m = re.search(r"\b(?:acted\s+by|starring|featuring|features|with\s+actor|cast\s+member|star|starred\s+by)\s+['\"]?([A-Za-z\s\.\'\-]+?)['\"]?(?:\s+(?:in|from|directed|released|movies?|films?)|$)", text, re.IGNORECASE)
    if actor_m:
        extracted["actor"] = actor_m.group(1).strip()
    else:
        # e.g. "movies with Vijay", "films with Shah Rukh Khan"
        actor_m2 = re.search(r"\b(?:movies?|films?)\s+with\s+['\"]?([A-Za-z\s\.\'\-]+?)['\"]?(?:\s+(?:in|from|directed)|$)", text, re.IGNORECASE)
        if actor_m2:
            extracted["actor"] = actor_m2.group(1).strip()
        else:
            # e.g. "movies of Vijay" or "films of Dhanush"
            actor_m3 = re.search(r"\b(?:movies?|films?)\s+of\s+['\"]?([A-Za-z\s\.\'\-]+?)['\"]?(?:\s+(?:in|from|directed)|$)", text, re.IGNORECASE)
            if actor_m3:
                extracted["actor"] = actor_m3.group(1).strip()
            else:
                # e.g. "Vijay action movies" -> "Vijay", "Action"
                actor_m4 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)?)\s+(?:action|comedy|thriller|horror|drama|sci-fi|romance|adventure|crime)\s+(?:movies?|films?)", text, re.IGNORECASE)
                if actor_m4:
                    cand = actor_m4.group(1).strip()
                    if cand.lower() not in ["tamil", "telugu", "hindi", "malayalam", "kannada", "bollywood", "hollywood", "indian", "top", "best", "good", "new", "recent"]:
                        extracted["actor"] = cand
                else:
                    # e.g. "Vijay movies" or "Shah Rukh Khan films"
                    actor_m5 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)?)\s+(?:movies?|films?)", text, re.IGNORECASE)
                    if actor_m5:
                        cand = actor_m5.group(1).strip()
                        if cand.lower() not in ["tamil", "telugu", "hindi", "malayalam", "kannada", "bollywood", "hollywood", "indian", "top", "best", "good", "new", "recent", "action", "comedy", "thriller", "horror", "drama", "sci-fi", "romance", "adventure", "crime"]:
                            extracted["actor"] = cand

    # Clean up actor if captured filler words
    if extracted["actor"]:
        extracted["actor"] = re.sub(r"\b(movies?|films?|cinema)\b", "", extracted["actor"], flags=re.IGNORECASE).strip()

    # Clean up director if captured filler words
    if extracted["director"]:
        extracted["director"] = re.sub(r"\b(movies?|films?|cinema)\b", "", extracted["director"], flags=re.IGNORECASE).strip()

    # 4. Industry / Region
    industries = {
        "bollywood": "Bollywood",
        "hindi": "Bollywood",
        "tamil": "Tamil",
        "kollywood": "Tamil",
        "telugu": "Telugu",
        "tollywood": "Telugu",
        "malayalam": "Malayalam",
        "mollywood": "Malayalam",
        "kannada": "Kannada",
        "sandalwood": "Kannada",
        "hollywood": "Hollywood",
        "american": "Hollywood",
        "indian": "Indian",
        "india": "Indian",
    }
    for kw, ind in industries.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            extracted["industry"] = ind
            break

    # 5. Genre
    genres = [
        "action", "adventure", "animation", "children's", "comedy", "crime",
        "documentary", "drama", "fantasy", "film-noir", "horror", "musical",
        "mystery", "romance", "sci-fi", "thriller", "war", "western"
    ]
    for g in genres:
        if re.search(r"\b" + re.escape(g) + r"\b", text_lower):
            extracted["genre"] = g.capitalize()
            break

    # 6. Year range
    # e.g. "from 2020 onward", "after 2020", "since 2020", "2020 and later"
    onward_m = re.search(r"\b(?:from|after|since)\s+((?:19|20)\d{2})\s*(?:onward|onwards|later|\+)?\b", text_lower)
    if onward_m:
        extracted["start_year"] = int(onward_m.group(1))
    else:
        # e.g. "before 2010", "until 2010"
        before_m = re.search(r"\b(?:before|until|prior\s+to)\s+((?:19|20)\d{2})\b", text_lower)
        if before_m:
            extracted["end_year"] = int(before_m.group(1))
        else:
            # 4-digit decade e.g. "90s", "1990s"
            dec_m = re.search(r"\b((?:19|20)\d)0['’]?s\b", text_lower)
            if dec_m:
                st_yr = int(dec_m.group(1)) * 10
                extracted["start_year"] = st_yr
                extracted["end_year"] = st_yr + 9
            else:
                # 2-digit decade e.g. "90s", "80s"
                dec2_m = re.search(r"\b['’]?(80|90|00|10|20)['’]?s\b", text_lower)
                if dec2_m:
                    d_num = int(dec2_m.group(1))
                    st_yr = 2000 + d_num if d_num < 30 else 1900 + d_num
                    extracted["start_year"] = st_yr
                    extracted["end_year"] = st_yr + 9
                else:
                    exact_yr = re.search(r"\b((?:19|20)\d{2})\b", text_lower)
                    if exact_yr:
                        y = int(exact_yr.group(1))
                        extracted["start_year"] = y
                        extracted["end_year"] = y

    return extracted

# Test cases
test_queries = [
    "Show me movies acted by Vijay.",
    "Movies directed by Christopher Nolan",
    "Tamil horror movies",
    "Movies directed by Lokesh Kanagaraj",
    "Vijay action movies from 2020 onward",
    "Movies starring Shah Rukh Khan",
    "Movies similar to Interstellar",
    "Best 90s Hollywood action movies",
    "Rajinikanth films",
    "Bollywood comedy movies"
]

for q in test_queries:
    print(q, "-->", parse_movie_query(q))
