INDUSTRY_WORDS = {"tamil", "telugu", "bollywood", "hindi", "malayalam", "kannada", "hollywood", "english", "american", "indian"}
GENRE_WORDS = {"action", "comedy", "thriller", "horror", "drama", "sci-fi", "science-fiction", "romance", "adventure", "crime", "mystery", "animation", "fantasy"}

def clean_actor_candidate(cand_act: str):
    tokens = cand_act.split()
    remaining = []
    detected_ind = None
    for tok in tokens:
        t_low = tok.lower()
        if t_low in INDUSTRY_WORDS:
            detected_ind = tok.capitalize() if t_low != "english" and t_low != "american" else "Hollywood"
        elif t_low in GENRE_WORDS or t_low in ["movie", "movies", "film", "films"]:
            pass
        else:
            remaining.append(tok)
    
    clean_actor = " ".join(remaining).strip() if remaining else None
    return clean_actor, detected_ind

act1, ind1 = clean_actor_candidate("Vijay Tamil")
print("Vijay Tamil -> Actor:", act1, "| Ind:", ind1)

act2, ind2 = clean_actor_candidate("English science-fiction")
print("English science-fiction -> Actor:", act2, "| Ind:", ind2)
