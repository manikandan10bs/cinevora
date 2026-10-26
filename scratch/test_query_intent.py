import re
from typing import Dict, Any, Optional, Tuple

GENRE_SYNONYMS = {
    "action": "Action",
    "adventure": "Adventure",
    "animation": "Animation",
    "animated": "Animation",
    "anime": "Animation",
    "children": "Children's",
    "family": "Children's",
    "comedy": "Comedy",
    "funny": "Comedy",
    "crime": "Crime",
    "gangster": "Crime",
    "documentary": "Documentary",
    "drama": "Drama",
    "fantasy": "Fantasy",
    "film-noir": "Film-Noir",
    "noir": "Film-Noir",
    "horror": "Horror",
    "scary": "Horror",
    "musical": "Musical",
    "mystery": "Mystery",
    "suspense": "Mystery",
    "romance": "Romance",
    "romantic": "Romance",
    "love": "Romance",
    "sci-fi": "Sci-Fi",
    "science fiction": "Sci-Fi",
    "thriller": "Thriller",
    "war": "War",
    "western": "Western"
}

INDUSTRY_SYNONYMS = {
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
    "india": "Indian"
}

STOP_WORDS = {
    "movie", "movies", "film", "films", "cinema", "show", "me", "tell", "about",
    "recommend", "give", "list", "find", "some", "good", "best", "top", "great",
    "the", "a", "an", "in", "from", "with", "by", "of", "for", "please"
}

def parse_query_intent(message: str) -> Dict[str, Any]:
    text = message.strip()
    # Normalize punctuation for pattern matching
    clean_text = re.sub(r"[?!.,;]+", " ", text).strip()
    text_lower = clean_text.lower()

    intent: Dict[str, Any] = {
        "actor": None,
        "director": None,
        "genre": None,
        "industry": None,
        "start_year": None,
        "end_year": None,
        "decade_label": None,
        "similar_to": None,
        "title": None,
        "free_query": None
    }

    # 1. Similar to / Like movie
    sim_m = re.search(r"\b(?:similar\s+to|movies?\s+like|films?\s+like|recommend.*like)\s+([A-Za-z0-9\s\:\'\-]+)", clean_text, re.IGNORECASE)
    if sim_m:
        cand_sim = sim_m.group(1).strip()
        cand_sim = re.sub(r"\b(movies?|films?|cinema|please)\b", "", cand_sim, flags=re.IGNORECASE).strip()
        if cand_sim:
            intent["similar_to"] = cand_sim

    # 2. Industry / Language
    for kw, ind in sorted(INDUSTRY_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            intent["industry"] = ind
            break

    # 3. Genre
    for phrase, g in sorted(GENRE_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(phrase) + r"\b", text_lower):
            intent["genre"] = g
            break

    # 4. Year / Decade
    # A. "from 2020 onward", "after 2020", "since 2020", "2020+"
    onward_m = re.search(r"\b(?:from|after|since)\s+((?:19|20)\d{2})\s*(?:onward|onwards|later|\+)?\b", text_lower)
    if onward_m:
        intent["start_year"] = int(onward_m.group(1))
        intent["decade_label"] = f"{intent['start_year']}+"
    else:
        # B. "before 2010", "until 2010"
        before_m = re.search(r"\b(?:before|until|prior\s+to)\s+((?:19|20)\d{2})\b", text_lower)
        if before_m:
            intent["end_year"] = int(before_m.group(1))
            intent["decade_label"] = f"before {intent['end_year']}"
        else:
            # C. 4-digit decade e.g. "1990s", "90s", "2000s"
            dec_m = re.search(r"\b((?:19|20)\d)0['’]?s\b", text_lower)
            if dec_m:
                st_yr = int(dec_m.group(1)) * 10
                intent["start_year"] = st_yr
                intent["end_year"] = st_yr + 9
                intent["decade_label"] = f"{st_yr}s"
            else:
                dec2_m = re.search(r"\b['’]?(80|90|00|10|20)['’]?s\b", text_lower)
                if dec2_m:
                    d_num = int(dec2_m.group(1))
                    st_yr = 2000 + d_num if d_num < 30 else 1900 + d_num
                    intent["start_year"] = st_yr
                    intent["end_year"] = st_yr + 9
                    intent["decade_label"] = f"{st_yr}s"
                else:
                    exact_yr = re.search(r"\b((?:19|20)\d{2})\b", text_lower)
                    if exact_yr:
                        y = int(exact_yr.group(1))
                        intent["start_year"] = y
                        intent["end_year"] = y
                        intent["decade_label"] = str(y)

    # 5. Director pattern
    dir_m = re.search(r"\b(?:directed\s+by|director|direction\s+by)\s+([A-Za-z\s\.\'\-]+)", clean_text, re.IGNORECASE)
    if dir_m:
        cand_dir = dir_m.group(1).strip()
        # Cut off at stop words or other entity markers (in, with, starring, from, etc.)
        cut = re.split(r"\b(in|with|starring|featuring|from|released|movies?|films?)\b", cand_dir, flags=re.IGNORECASE)
        cand_dir = cut[0].strip()
        if cand_dir and cand_dir.lower() not in STOP_WORDS:
            intent["director"] = cand_dir

    # 6. Actor pattern
    # Pattern A: explicit keywords "acted by", "starring", "featuring", "features", "with actor"
    actor_m = re.search(r"\b(?:acted\s+by|starring|featuring|features|with\s+actor|cast\s+member|starred\s+by)\s+([A-Za-z\s\.\'\-]+)", clean_text, re.IGNORECASE)
    if actor_m:
        cand_act = actor_m.group(1).strip()
        cut = re.split(r"\b(in|directed|from|released|movies?|films?)\b", cand_act, flags=re.IGNORECASE)
        cand_act = cut[0].strip()
        if cand_act and cand_act.lower() not in STOP_WORDS:
            intent["actor"] = cand_act
    else:
        # Pattern B: "movies with X" / "films with X"
        actor_m2 = re.search(r"\b(?:movies?|films?)\s+with\s+([A-Za-z\s\.\'\-]+)", clean_text, re.IGNORECASE)
        if actor_m2:
            cand_act = actor_m2.group(1).strip()
            cut = re.split(r"\b(in|directed|from|released)\b", cand_act, flags=re.IGNORECASE)
            cand_act = cut[0].strip()
            if cand_act and cand_act.lower() not in STOP_WORDS:
                intent["actor"] = cand_act
        else:
            # Pattern C: "X action movies" or "X movies" (e.g. "Vijay action movies", "Vijay movies", "Rajinikanth films")
            # Extract candidate before genre or before movies/films
            actor_m3 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)*?)\s+(?:action|comedy|thriller|horror|drama|sci-fi|romance|adventure|crime)\s+(?:movies?|films?)\b", clean_text, re.IGNORECASE)
            if actor_m3:
                cand_act = actor_m3.group(1).strip()
                # Exclude industry names or adjectives
                if cand_act.lower() not in INDUSTRY_SYNONYMS and cand_act.lower() not in STOP_WORDS:
                    intent["actor"] = cand_act
            else:
                actor_m4 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)*?)\s+(?:movies?|films?)\b", clean_text, re.IGNORECASE)
                if actor_m4:
                    cand_act = actor_m4.group(1).strip()
                    # Exclude industry names, genre names, or adjectives
                    cand_lower = cand_act.lower()
                    if (cand_lower not in INDUSTRY_SYNONYMS and 
                        cand_lower not in GENRE_SYNONYMS and 
                        cand_lower not in STOP_WORDS and 
                        cand_lower not in ["recent", "latest", "classic", "modern", "hit", "blockbuster"]):
                        # Check if it was "X directed movies"
                        if "directed" in cand_lower:
                            cand_act = re.sub(r"\bdirected\b", "", cand_act, flags=re.IGNORECASE).strip()
                            intent["director"] = cand_act
                        else:
                            intent["actor"] = cand_act

    # If both director and actor were not found and there's no genre/industry, mark free_query
    if not any([intent["actor"], intent["director"], intent["genre"], intent["industry"], intent["similar_to"], intent["start_year"]]):
        intent["free_query"] = clean_text

    return intent

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

for t in test_cases:
    res = parse_query_intent(t)
    print("QUERY:", t)
    print("  -> Actor:", res["actor"], "| Director:", res["director"], "| Genre:", res["genre"], "| Industry:", res["industry"], "| Year:", f"{res['start_year']}-{res['end_year']}")
