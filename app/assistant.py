"""
Cinevora Gemini AI Movie Concierge Module
Integrates the official google-genai SDK to interpret user queries and explain recommendations.
Grounded exclusively in Cinevora's verified catalog and recommendation engine.
"""

import re
import json
import logging
from urllib.parse import quote_plus
from typing import Dict, List, Optional, Tuple, Any, Union

from google import genai
from google.genai import types
from google.genai import errors

from app.config import settings
from app.schemas import MovieItem, AssistantChatResponse
from src.catalog_service import query_master_catalog, load_master_catalog, normalize_industry_filter
from src.retrieval_service import movie_retrieval_service, QueryFilters, matches_person_name, PERSON_ALIASES
from src.recommender import GENRE_COLUMNS
from src.knowledge_graph import get_knowledge_graph, CinemaKnowledgeGraph

logger = logging.getLogger("cinevora.assistant")


# Mapping of common conversational query keywords to official MovieLens genres
GENRE_SYNONYMS: Dict[str, str] = {
    "action": "Action",
    "explosive": "Action",
    "superhero": "Action",
    "adventure": "Adventure",
    "quest": "Adventure",
    "journey": "Adventure",
    "animation": "Animation",
    "animated": "Animation",
    "cartoon": "Animation",
    "anime": "Animation",
    "kids": "Children's",
    "children": "Children's",
    "family": "Children's",
    "comedy": "Comedy",
    "funny": "Comedy",
    "hilarious": "Comedy",
    "laugh": "Comedy",
    "humor": "Comedy",
    "crime": "Crime",
    "gangster": "Crime",
    "mafia": "Crime",
    "detective": "Crime",
    "cop": "Crime",
    "police": "Crime",
    "documentary": "Documentary",
    "docuseries": "Documentary",
    "biography": "Documentary",
    "real life": "Documentary",
    "drama": "Drama",
    "emotional": "Drama",
    "tearjerker": "Drama",
    "fantasy": "Fantasy",
    "magic": "Fantasy",
    "wizards": "Fantasy",
    "film-noir": "Film-Noir",
    "noir": "Film-Noir",
    "horror": "Horror",
    "scary": "Horror",
    "spooky": "Horror",
    "creepy": "Horror",
    "slasher": "Horror",
    "musical": "Musical",
    "music": "Musical",
    "singing": "Musical",
    "mystery": "Mystery",
    "whodunit": "Mystery",
    "suspense": "Mystery",
    "romance": "Romance",
    "romantic": "Romance",
    "love story": "Romance",
    "love": "Romance",
    "sci-fi": "Sci-Fi",
    "science fiction": "Sci-Fi",
    "science-fiction": "Sci-Fi",
    "sci fi": "Sci-Fi",
    "scifi": "Sci-Fi",
    "space": "Sci-Fi",
    "alien": "Sci-Fi",
    "futuristic": "Sci-Fi",
    "thriller": "Thriller",
    "thrilling": "Thriller",
    "intense": "Thriller",
    "edge of seat": "Thriller",
    "war": "War",
    "military": "War",
    "combat": "War",
    "western": "Western",
    "cowboy": "Western"
}

LANGUAGE_SYNONYMS = {
    "tamil": "ta",
    "kollywood": "ta",
    "telugu": "te",
    "tollywood": "te",
    "malayalam": "ml",
    "mollywood": "ml",
    "kannada": "kn",
    "sandalwood": "kn",
    "hindi": "hi",
    "bollywood": "hi",
    "english": "en",
    "korean": "ko",
}

REGION_SYNONYMS = {
    "indian": "Indian",
    "india": "Indian",
    "bollywood": "Indian",
    "kollywood": "Indian",
    "tollywood": "Indian",
    "mollywood": "Indian",
    "sandalwood": "Indian",
    "hollywood": "Hollywood",
    "american": "Hollywood",
    "international": "International",
    "foreign": "International",
    "korean": "International",
}

SYSTEM_PROMPT = """You are Cinevora's AI Movie Concierge, an enthusiastic, knowledgeable cinema expert.
Your job is to provide engaging, personalized movie recommendations and explanations in response to the user's inquiry.

STRICT GROUNDING RULES:
1. You MUST ONLY discuss and recommend the movies provided in the 'Verified Recommendations from Cinevora Catalog' list.
2. DO NOT hallucinate, invent, or bring in any movie titles not present in the provided list.
3. DO NOT alter or fabricate ratings, scores, or release years.
4. Explain WHY each recommended movie is a great fit for the user's request based on its themes, genres, and style.
5. Keep your tone warm, articulate, and concise (2-4 brief paragraphs or clean bullet points).
"""


SUPPORTED_CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-1.5-flash"
]


class GeminiAssistant:
    """
    AI Assistant using the official google-genai SDK.
    Grounds natural-language queries in Cinevora's actual recommender engine.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key.strip() if api_key else None
        else:
            self.api_key = settings.get_gemini_api_key()

        self.model_name = model_name or settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None
        self._cached_verification: Optional[Dict[str, Any]] = None
        self._last_verification_time: float = 0.0
        self._verification_ttl: float = 300.0  # 5 minutes TTL

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Gemini Client: %s", type(e).__name__)
                self._client = None

    def verify_connection(self, force: bool = False) -> Dict[str, Any]:
        """
        Actively verifies Gemini API connectivity, key authorization, and model availability.
        Never prints or exposes the API key.
        Returns structured status state:
        - 'connected': Real API verification succeeded
        - 'configuration_missing': GEMINI_API_KEY is not set
        - 'verification_failed': Invalid key, model not found, or unauthorized
        - 'quota_or_network_error': Rate limited (429), quota exceeded, or network failure
        """
        import time
        now = time.time()
        if not force and self._cached_verification and (now - self._last_verification_time < self._verification_ttl):
            return self._cached_verification

        # 1. Configuration check
        if not self.api_key:
            res = {
                "configured": False,
                "verified": False,
                "status_state": "configuration_missing",
                "model": self.model_name,
                "status": "GEMINI_API_KEY is not set in environment (.env). Cinevora will provide grounded catalog recommendations with algorithmic rationale.",
                "fallback_active": True
            }
            self._cached_verification = res
            self._last_verification_time = now
            return res

        # 2. Client initialization check
        if self._client is None:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                res = {
                    "configured": True,
                    "verified": False,
                    "status_state": "verification_failed",
                    "model": self.model_name,
                    "status": f"Gemini client initialization failed ({type(e).__name__}). Operating in catalog fallback mode.",
                    "fallback_active": True
                }
                self._cached_verification = res
                self._last_verification_time = now
                return res

        # 3. Real API verification request
        models_to_try = [self.model_name] + [m for m in SUPPORTED_CANDIDATE_MODELS if m != self.model_name]

        last_err: Optional[Exception] = None
        for m_name in models_to_try:
            try:
                resp = self._client.models.generate_content(
                    model=m_name,
                    contents="ping",
                    config=types.GenerateContentConfig(max_output_tokens=5, temperature=0.0)
                )
                if resp and resp.text:
                    if m_name != self.model_name:
                        logger.info("Configured model '%s' was substituted with verified model '%s'", self.model_name, m_name)
                        self.model_name = m_name

                    res = {
                        "configured": True,
                        "verified": True,
                        "status_state": "connected",
                        "model": self.model_name,
                        "status": f"Connected — Gemini AI Engine verified and active with model '{self.model_name}'.",
                        "fallback_active": False
                    }
                    self._cached_verification = res
                    self._last_verification_time = now
                    return res
            except Exception as err:
                last_err = err
                err_str = str(err).lower()
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    res = {
                        "configured": True,
                        "verified": False,
                        "status_state": "quota_or_network_error",
                        "model": self.model_name,
                        "status": "Gemini API quota or rate limit reached. Operating in offline catalog fallback mode.",
                        "fallback_active": True
                    }
                    self._cached_verification = res
                    self._last_verification_time = now
                    return res
                if "connection" in err_str or "timeout" in err_str or "name resolution" in err_str or "failed to resolve" in err_str or "unreachable" in err_str:
                    res = {
                        "configured": True,
                        "verified": False,
                        "status_state": "quota_or_network_error",
                        "model": self.model_name,
                        "status": "Network error connecting to Gemini API. Operating in offline catalog fallback mode.",
                        "fallback_active": True
                    }
                    self._cached_verification = res
                    self._last_verification_time = now
                    return res
                if "401" in err_str or "403" in err_str or "api_key_invalid" in err_str or "unauthorized" in err_str:
                    res = {
                        "configured": True,
                        "verified": False,
                        "status_state": "verification_failed",
                        "model": self.model_name,
                        "status": "Gemini API key verification failed (invalid key or unauthorized). Operating in catalog fallback mode.",
                        "fallback_active": True
                    }
                    self._cached_verification = res
                    self._last_verification_time = now
                    return res
                continue

        err_type = type(last_err).__name__ if last_err else "ModelUnavailable"
        res = {
            "configured": True,
            "verified": False,
            "status_state": "verification_failed",
            "model": self.model_name,
            "status": f"Configured Gemini model '{self.model_name}' could not be verified ({err_type}). Operating in catalog fallback mode.",
            "fallback_active": True
        }
        self._cached_verification = res
        self._last_verification_time = now
        return res

    @property
    def is_available(self) -> bool:
        """Returns True if the assistant has verified connectivity to Gemini."""
        if not self.api_key:
            return False
        stat = self.verify_connection(force=False)
        return bool(stat.get("verified", False))

    def resolve_exact_trailer(
        self,
        title: str,
        year: Optional[str] = None,
        director: Optional[str] = None,
        industry: Optional[str] = None,
        max_attempts: int = 3
    ) -> str:
        """
        Uses Gemini to find the exact official YouTube trailer video URL.
        Makes up to 3 requests to Gemini.
        If all 3 requests fail or no valid watch link is found, returns:
        https://www.youtube.com/results?search_query={movie_name}+trailer
        """
        clean_t = re.sub(r"\(.*?\)", "", str(title)).strip()
        query_encoded = quote_plus(f"{clean_t} trailer")
        fallback_search_url = f"https://www.youtube.com/results?search_query={query_encoded}"

        if not self.is_available or self._client is None:
            return fallback_search_url

        details = f"Movie: '{clean_t}'"
        if year:
            details += f" ({year})"
        if director:
            details += f", Director: {director}"
        if industry:
            details += f", Industry/Region: {industry}"

        prompts = [
            f"""Identify the exact official YouTube trailer video URL for this movie:
{details}

Respond with ONLY a JSON object:
{{"title": "{clean_t}", "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"}}
The URL MUST be an exact YouTube video watch link (https://www.youtube.com/watch?v=...).""",

            f"""Find the exact YouTube video watch link for the official trailer of the movie '{clean_t}' ({year or ''}).
Provide ONLY the watch link in format: https://www.youtube.com/watch?v=VIDEO_ID""",

            f"""What is the official YouTube trailer watch link for '{clean_t}'? Return ONLY the link: https://www.youtube.com/watch?v=..."""
        ]

        for attempt in range(max_attempts):
            try:
                prompt = prompts[min(attempt, len(prompts) - 1)]
                logger.info("Resolving trailer for '%s' with Gemini (Request %d/%d)...", clean_t, attempt + 1, max_attempts)
                resp = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                raw = (resp.text or "").strip()
                # Match standard 11-char video ID
                m = re.search(r"https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})", raw)
                if m:
                    logger.info("Found exact trailer for '%s' on attempt %d: %s", clean_t, attempt + 1, m.group(0))
                    return m.group(0)
                m_short = re.search(r"https://youtu\.be/([a-zA-Z0-9_-]{11})", raw)
                if m_short:
                    watch_url = f"https://www.youtube.com/watch?v={m_short.group(1)}"
                    logger.info("Found exact trailer for '%s' on attempt %d: %s", clean_t, attempt + 1, watch_url)
                    return watch_url
            except Exception as e:
                logger.warning("Gemini trailer request %d/%d failed for '%s': %s", attempt + 1, max_attempts, clean_t, e)

        logger.info("All %d Gemini requests failed for '%s'. Returning fallback search URL: %s", max_attempts, clean_t, fallback_search_url)
        return fallback_search_url

    def detect_genre_from_text(self, text: str) -> Optional[str]:
        """
        Extracts a matching MovieLens genre from the user's natural language text.
        1. Checks exact official genre names first (e.g., 'Horror', 'Comedy', 'Action').
        2. Falls back to phrase/synonym keywords (e.g., 'scary', 'funny', 'alien').
        """
        text_lower = text.lower()

        # Step 1: Priority check for exact official genre names
        for genre in GENRE_COLUMNS:
            if genre.lower() == "unknown":
                continue
            pattern = r"\b" + re.escape(genre.lower()) + r"\b"
            if re.search(pattern, text_lower):
                return genre

        # Step 2: Synonym and keyword matching
        for phrase, genre in sorted(GENRE_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, text_lower):
                return genre

        return None

    def detect_language_from_text(self, text: str) -> Optional[str]:
        """Detects language code (e.g. 'ta', 'te', 'ml', 'kn', 'hi', 'en') from user text."""
        text_lower = text.lower()
        for phrase, lang_code in LANGUAGE_SYNONYMS.items():
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, text_lower):
                return lang_code
        return None

    def detect_region_from_text(self, text: str) -> Optional[str]:
        """Detects cinema region ('Indian', 'Hollywood', 'International') from user text."""
        text_lower = text.lower()
        for phrase, region in REGION_SYNONYMS.items():
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, text_lower):
                return region
        return None

    def detect_decade_or_year(self, text: str) -> Optional[Tuple[int, int, str]]:
        """
        Extracts a decade or release-year constraint from user text.
        Supports:
        - Named words: 'twenties', 'thirties', ..., 'nineties'
        - Decades: '90s', '90\'s', '1990s', '1990\'s', '80s', '2000s', '2010s', '2020s', etc.
        - Words like 'recent', 'modern', 'latest' (2020-2026)
        - Exact 4-digit years: '1994', '2022', etc.
        Returns: (start_year, end_year, display_label) or None
        """
        text_lower = text.lower()

        # 1. Named word decades
        word_decades = {
            "twenties": (1920, 1929, "1920s"),
            "thirties": (1930, 1939, "1930s"),
            "forties": (1940, 1949, "1940s"),
            "fifties": (1950, 1959, "1950s"),
            "sixties": (1960, 1969, "1960s"),
            "seventies": (1970, 1979, "1970s"),
            "eighties": (1980, 1989, "1980s"),
            "nineties": (1990, 1999, "1990s"),
        }
        for word, val in word_decades.items():
            if re.search(r"\b" + word + r"\b", text_lower):
                return val

        # 2. 4-digit decades e.g. 1990s, 2000s, 2010s, 2020s
        m_4d = re.search(r"\b((?:19|20)\d)0['’]?s\b", text_lower)
        if m_4d:
            start_yr = int(m_4d.group(1)) * 10
            return start_yr, start_yr + 9, f"{start_yr}s"

        # 3. 2-digit decades e.g. 90s, 90's, 80s, '90s, 00s
        m_2d = re.search(r"\b['’]?(00|10|20|30|40|50|60|70|80|90)['’]?s\b", text_lower)
        if m_2d:
            dec_num = int(m_2d.group(1))
            start_yr = 2000 + dec_num if dec_num < 30 else 1900 + dec_num
            prefix = "20" if dec_num < 30 else "19"
            return start_yr, start_yr + 9, f"{prefix}{dec_num:02d}s"

        # 4. Recent / modern / latest cinema indicator
        if re.search(r"\b(recent|modern|latest|new release)\b", text_lower):
            return 2020, 2026, "recent"

        # 5. Exact 4-digit year e.g. "from 1995", "in 2022"
        m_yr = re.search(r"\b((?:19|20)\d{2})\b", text_lower)
        if m_yr:
            y = int(m_yr.group(1))
            return y, y, str(y)

        return None

    def _call_gemini(self, prompt: str) -> str:
        """
        Calls the Gemini Flash model with timeout and error handling.
        Returns the generated text response.
        """
        if not self._client:
            raise RuntimeError("Gemini Client is not configured.")

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=750
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )

        if response and response.text:
            return response.text.strip()

        return "I found some great movie matches for your taste from Cinevora's catalog below!"

    def parse_query_intent(self, message: str) -> Dict[str, Any]:
        """
        Deterministically extracts structured cinema filters from user's natural language inquiry:
        - actor: cast member names (e.g. 'acted by Vijay', 'starring Shah Rukh Khan', 'Vijay action movies')
        - director: director names (e.g. 'directed by Christopher Nolan', 'Lokesh Kanagaraj films')
        - genre: cinematic genre (e.g. 'Horror', 'Action', 'Comedy', 'Sci-Fi')
        - industry: cinema industry/language ('Tamil', 'Bollywood', 'Hollywood', 'Telugu', 'Malayalam', 'Kannada')
        - start_year, end_year, decade_label: release date bounds (e.g. 'from 2020 onward', 'after 2020', '90s', '2023')
        - similar_to: reference movie title for content similarity
        - semantic_query: plot or theme description
        - free_query: remaining descriptive keywords
        """
        text = message.strip()
        # Normalize possessive 's e.g. "Vijay's" -> "Vijay"
        clean_text = re.sub(r"['’]s\b", "", text)
        clean_text = re.sub(r"[?!.,;]+", " ", clean_text).strip()
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
            "semantic_query": None,
            "free_query": None
        }

        stop_words = {
            "movie", "movies", "film", "films", "cinema", "show", "me", "tell", "about",
            "recommend", "give", "list", "find", "some", "good", "best", "top", "great",
            "the", "a", "an", "in", "from", "with", "by", "of", "for", "please"
        }

        # 1. Similar to / Like movie / Theme query
        sim_m = re.search(r"\b(?:similar\s+to|movies?\s+like|films?\s+like|similar\s+in\s+theme\s+to|recommend.*like)\s+([A-Za-z0-9\s\:\'\-]+)", clean_text, re.IGNORECASE)
        if sim_m:
            cand_sim = sim_m.group(1).strip()
            cand_sim = re.sub(r"\b(movies?|films?|cinema|please)\b", "", cand_sim, flags=re.IGNORECASE).strip()
            if cand_sim:
                intent["similar_to"] = cand_sim

        # Check for genuine thematic / plot queries ONLY — do NOT set semantic_query for
        # quality adjectives like "best", "good", "funny", "gripping" or industry words.
        # Semantic search only triggers when the user is describing a theme, plot, or mood concept.
        QUALITY_ADJECTIVES = {
            "best", "good", "great", "top", "popular", "hit", "blockbuster", "must-watch",
            "gripping", "exciting", "amazing", "awesome", "fantastic", "excellent", "nice",
            "wonderful", "epic", "classic", "modern", "recent", "latest", "new", "old",
            "underrated", "hidden", "gem", "recommended", "favourite", "favorite",
            "entertaining", "engaging", "interesting", "fun"
        }
        thematic_keywords = {
            "theme", "plot", "story", "mood", "gritty", "space", "alien", "time travel",
            "mind bending", "twist", "heist", "revenge", "supernatural", "dystopian",
            "post-apocalyptic", "philosophical", "existential", "psychological", "surreal",
            "coming of age", "road trip", "survival", "redemption", "political intrigue",
            "war drama", "based on true story"
        }
        # Only set semantic_query if a genuine theme/plot keyword is present (not quality adjectives)
        clean_lower_words = set(text_lower.split())
        if not intent.get("similar_to") and any(kw in text_lower for kw in thematic_keywords):
            # Strip quality adjectives from the semantic query to keep it meaningful
            semantic_str = " ".join(w for w in clean_text.split() if w.lower() not in QUALITY_ADJECTIVES)
            intent["semantic_query"] = semantic_str.strip() or None

        # 2. Industry / Language detection
        detected_ind = None
        if re.search(r"\b(english|hollywood|american)\b", text_lower):
            detected_ind = "Hollywood"
        elif re.search(r"\b(tamil|kollywood)\b", text_lower):
            detected_ind = "Tamil"
        elif re.search(r"\b(telugu|tollywood)\b", text_lower):
            detected_ind = "Telugu"
        elif re.search(r"\b(bollywood|hindi)\b", text_lower):
            detected_ind = "Bollywood"
        elif re.search(r"\b(malayalam|mollywood)\b", text_lower):
            detected_ind = "Malayalam"
        elif re.search(r"\b(kannada|sandalwood)\b", text_lower):
            detected_ind = "Kannada"

        if not detected_ind:
            for kw, ind in sorted(REGION_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True):
                if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                    detected_ind = ind
                    break

        intent["industry"] = detected_ind

        # 3. Genre detection
        intent["genre"] = self.detect_genre_from_text(text)

        # 4. Year / Decade detection
        after_m = re.search(r"\b(?:after|later\s+than)\s+((?:19|20)\d{2})\b", text_lower)
        onward_m = re.search(r"\b(?:since\s+((?:19|20)\d{2})|from\s+((?:19|20)\d{2})\s*(?:onward|onwards|later|\+)|((?:19|20)\d{2})\s*(?:onward|onwards|\+))\b", text_lower)
        before_m = re.search(r"\b(?:before|until|prior\s+to)\s+((?:19|20)\d{2})\b", text_lower)

        if after_m:
            intent["start_year"] = int(after_m.group(1)) + 1
            intent["decade_label"] = f"after {after_m.group(1)}"
        elif onward_m:
            yr_str = next(g for g in onward_m.groups() if g is not None)
            intent["start_year"] = int(yr_str)
            intent["decade_label"] = f"{intent['start_year']}+"
        elif before_m:
            intent["end_year"] = int(before_m.group(1))
            intent["decade_label"] = f"before {intent['end_year']}"
        else:
            decade_data = self.detect_decade_or_year(text)
            if decade_data:
                intent["start_year"] = decade_data[0]
                intent["end_year"] = decade_data[1]
                intent["decade_label"] = decade_data[2]

        # 5. Director extraction
        dir_m = re.search(r"\b(?:directed\s+by|director|direction\s+by)\s+([A-Za-z\s\.\'\-]+)", clean_text, re.IGNORECASE)
        dir_m2 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)*?)\s+directed\s+(?:movies?|films?)\b", clean_text, re.IGNORECASE)
        if dir_m:
            cand_dir = dir_m.group(1).strip()
            cut = re.split(r"\b(in|with|starring|featuring|from|released|movies?|films?)\b", cand_dir, flags=re.IGNORECASE)
            cand_dir = cut[0].strip()
            if cand_dir and cand_dir.lower() not in stop_words:
                intent["director"] = cand_dir
        elif dir_m2:
            cand_dir = dir_m2.group(1).strip()
            cand_dir = re.sub(r"^(?:please\s+)?(?:can\s+you\s+)?(?:suggest|recommend|show|find|give|list|tell)(?:\s+me)?(?:\s+some|\s+any|\s+a|\s+an|\s+the)?\s+", "", cand_dir, flags=re.IGNORECASE).strip()
            if cand_dir and cand_dir.lower() not in stop_words:
                cat_df = movie_retrieval_service.get_catalog()
                has_dir = cat_df["director"].apply(lambda d: matches_person_name(d, cand_dir)).any()
                if has_dir or cand_dir.lower() in PERSON_ALIASES:
                    intent["director"] = cand_dir

        # 6. Actor extraction with industry/genre token cleansing
        def clean_actor_string(raw_cand: str) -> Tuple[Optional[str], Optional[str]]:
            tokens = raw_cand.split()
            remaining = []
            cand_ind = None
            industry_words = {"tamil", "telugu", "bollywood", "hindi", "malayalam", "kannada", "hollywood", "english", "american", "indian"}
            genre_words = {"action", "comedy", "thriller", "horror", "drama", "sci-fi", "science-fiction", "romance", "adventure", "crime", "mystery", "animation", "fantasy", "musical", "western", "documentary"}
            noise_words = {
                "gripping", "classic", "modern", "recent", "latest", "new", "old",
                "popular", "hit", "blockbuster", "trending", "great", "best", "top",
                "good", "underrated", "scary", "funny", "dark", "superhit", "epic",
                "recommend", "recommends", "recommending", "suggest", "suggests", "suggesting",
                "show", "shows", "give", "find", "get", "list", "tell",
                "some", "any", "few", "a", "an", "the", "one", "two", "three", "four",
                "five", "six", "seven", "eight", "nine", "ten", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                "favorite", "favourites", "awesome", "entertaining", "must-watch", "must", "watch",
                "acted", "acts", "acting", "star", "starred", "starring", "lead", "hero", "actor", "actress",
                "directed", "director", "direction", "film", "films", "movie", "movies", "cinema",
                "please", "can", "you", "i", "want", "need", "looking", "for"
            }
            for tok in tokens:
                t_low = tok.lower()
                if t_low in industry_words:
                    cand_ind = "Hollywood" if t_low in ["english", "american", "hollywood"] else tok.capitalize()
                elif t_low in genre_words or t_low in ["movie", "movies", "film", "films", "cinema"]:
                    continue
                elif t_low in stop_words or t_low in noise_words:
                    continue
                else:
                    remaining.append(tok)
            clean_name = " ".join(remaining).strip() if remaining else None
            return clean_name, cand_ind

        raw_actor = None
        is_implicit = False
        actor_m0 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)*?)\s+acted\s+(?:movies?|films?)\b", clean_text, re.IGNORECASE)
        actor_m1 = re.search(r"\b(?:acted\s+by|starring|featuring|features|with\s+actor|cast\s+member|starred\s+by)\s+([A-Za-z\s\.\'\-]+)", clean_text, re.IGNORECASE)
        actor_m2 = re.search(r"\b(?:movies?|films?)\s+with\s+([A-Za-z\s\.\'\-]+)", clean_text, re.IGNORECASE)
        actor_m3 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)*?)\s+(?:action|comedy|thriller|horror|drama|sci-fi|science-fiction|romance|adventure|crime)\s+(?:movies?|films?)\b", clean_text, re.IGNORECASE)
        actor_m4 = re.search(r"\b([A-Za-z\.\'\-]+(?:\s+[A-Za-z\.\'\-]+)*?)\s+(?:movies?|films?)\b", clean_text, re.IGNORECASE)

        if actor_m0:
            raw_actor = actor_m0.group(1).strip()
            is_implicit = True
        elif actor_m1:
            cand_act = actor_m1.group(1).strip()
            cut = re.split(r"\b(in|directed|from|released|movies?|films?)\b", cand_act, flags=re.IGNORECASE)
            raw_actor = cut[0].strip()
        elif actor_m2:
            cand_act = actor_m2.group(1).strip()
            cut = re.split(r"\b(in|directed|from|released)\b", cand_act, flags=re.IGNORECASE)
            raw_actor = cut[0].strip()
        elif actor_m3:
            raw_actor = actor_m3.group(1).strip()
            is_implicit = True
        elif actor_m4:
            raw_actor = actor_m4.group(1).strip()
            is_implicit = True

        if raw_actor:
            act_name, extra_ind = clean_actor_string(raw_actor)
            if extra_ind and not intent.get("industry"):
                intent["industry"] = extra_ind
            if act_name:
                if intent.get("director") and act_name.lower() in intent["director"].lower():
                    pass  # Don't duplicate director as actor
                elif is_implicit:
                    cat_df = movie_retrieval_service.get_catalog()
                    has_cast = cat_df["cast"].apply(lambda c: matches_person_name(c, act_name)).any()
                    has_dir = cat_df["director"].apply(lambda d: matches_person_name(d, act_name)).any()
                    if has_cast or has_dir or act_name.lower() in PERSON_ALIASES:
                        intent["actor"] = act_name
                else:
                    intent["actor"] = act_name

        if not any([intent["actor"], intent["director"], intent["genre"], intent["industry"], intent["similar_to"], intent["start_year"], intent["semantic_query"]]):
            intent["free_query"] = clean_text
        else:
            intent["free_query"] = None

        return intent

    def parse_query_intent_with_gemini(self, message: str) -> Dict[str, Any]:
        """
        Uses Gemini to extract structured search filters from natural language queries
        using JSON schema enforcement. Falls back safely to deterministic parsing.
        """
        deterministic_intent = self.parse_query_intent(message)

        if not self.is_available or self._client is None:
            return deterministic_intent

        try:
            prompt = (
                f"You are a movie search query parser. Extract structured search filters from this query:\n"
                f"\"{message}\"\n\n"
                "Return ONLY a JSON object with these keys (or null if not mentioned):\n"
                "- actor: name of actor or star (string or null)\n"
                "- director: name of director (string or null)\n"
                "- genre: movie genre e.g. Action, Comedy, Crime, Drama, Horror, Romance, Sci-Fi, Thriller (string or null)\n"
                "- industry: movie industry/language: Tamil, Telugu, Bollywood, Malayalam, Kannada, Hollywood (string or null)\n"
                "- year_from: integer starting year or null\n"
                "- year_to: integer ending year or null\n"
                "- title: specific movie title (string or null)\n"
                "- similar_to: reference movie title for similarity (string or null)\n"
                "- semantic_query: ONLY set this if the user is describing a specific plot, theme, or mood concept (e.g. 'time travel', 'heist', 'supernatural thriller'). "
                "Do NOT set semantic_query for quality adjectives like 'good', 'best', 'gripping', 'amazing', 'funny', 'entertaining'. For those, set genre instead.\n"
                "IMPORTANT: If the query mentions an industry (Tamil, Hollywood etc) or genre, set those fields. "
                "Do NOT set actor for a person known primarily as a director. "
                "Do NOT set semantic_query for quality adjectives or industry/genre words.\n"
            )
            config = types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=250,
                response_mime_type="application/json"
            )
            resp = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            if resp and resp.text:
                parsed = json.loads(resp.text)
                # Quality adjectives that should NEVER become semantic_query
                QUALITY_ADJECTIVES_SET = {
                    "best", "good", "great", "top", "popular", "hit", "gripping", "exciting",
                    "amazing", "awesome", "fantastic", "excellent", "wonderful", "epic",
                    "classic", "modern", "recent", "latest", "new", "old", "underrated",
                    "entertaining", "engaging", "interesting", "fun", "funny", "must watch",
                    "must-watch", "must see", "recommend", "nice", "cool", "brilliant"
                }
                for k in ["actor", "director", "genre", "industry", "start_year", "end_year", "similar_to", "title"]:
                    g_key = "year_from" if k == "start_year" else ("year_to" if k == "end_year" else k)
                    if parsed.get(g_key) and not deterministic_intent.get(k):
                        deterministic_intent[k] = parsed[g_key]
                # Only accept semantic_query if it contains genuine thematic content
                gemini_sem = parsed.get("semantic_query")
                if gemini_sem and not deterministic_intent.get("semantic_query"):
                    sem_lower = str(gemini_sem).strip().lower()
                    # Reject if it's just a quality adjective or matches an industry/genre
                    is_quality = sem_lower in QUALITY_ADJECTIVES_SET or all(w in QUALITY_ADJECTIVES_SET for w in sem_lower.split())
                    is_industry = re.search(r"\b(tamil|telugu|bollywood|hindi|malayalam|kannada|hollywood|english)\b", sem_lower)
                    if not is_quality and not is_industry and len(sem_lower.split()) >= 2:
                        deterministic_intent["semantic_query"] = gemini_sem

                # If any structured filter was identified, clear free_query
                if any([
                    deterministic_intent.get("actor"),
                    deterministic_intent.get("director"),
                    deterministic_intent.get("genre"),
                    deterministic_intent.get("industry"),
                    deterministic_intent.get("start_year"),
                    deterministic_intent.get("end_year"),
                    deterministic_intent.get("title"),
                    deterministic_intent.get("similar_to"),
                    deterministic_intent.get("semantic_query")
                ]):
                    deterministic_intent["free_query"] = None
        except Exception as e:
            logger.debug("Gemini query parsing error (%s), using deterministic intent.", e)

        return deterministic_intent

    def chat(
        self,
        message: str,
        recommender: Any = None,
        user_id: Optional[Union[int, str]] = None,
        genre_override: Optional[str] = None,
        limit: int = 5
    ) -> AssistantChatResponse:
        """
        Interprets natural language queries into deterministic catalog criteria,
        retrieves matching records from Movies_Master_Cleaned.csv, and uses Gemini
        to formulate grounded explanations. Never invents movie records or falls back
        to repetitive arbitrary movies.
        """
        # 1. Parse structured search intent (Gemini-augmented with deterministic fallback)
        intent = self.parse_query_intent_with_gemini(message)

        # Active genre override takes precedence if explicitly supplied
        active_genre = None
        if genre_override and str(genre_override).strip().lower() not in ["all", "all genres", "any"]:
            active_genre = genre_override
        else:
            active_genre = intent.get("genre")

        # 2. Check Cinema Knowledge Graph for Relational / Multi-hop Signals (Graph RAG)
        kg = get_knowledge_graph()
        graph_movies, graph_triples, graph_strategy = kg.search_graph_rag(
            query_text=message,
            intent=intent,
            limit=limit
        )

        matches = []
        total = 0
        used_graph_rag = False

        if graph_strategy != "none" and graph_movies:
            matches = graph_movies
            total = len(graph_movies)
            used_graph_rag = True
            logger.info("Graph RAG activated for query '%s' with strategy '%s' (%d matches)", message, graph_strategy, total)
        else:
            # Fall back to standard structured filtering / semantic search
            query_filters = QueryFilters(
                actor=intent.get("actor"),
                director=intent.get("director"),
                genre=active_genre,
                industry=intent.get("industry"),
                year_from=intent.get("start_year"),
                year_to=intent.get("end_year"),
                title=intent.get("title"),
                similar_to=intent.get("similar_to"),
                semantic_query=intent.get("semantic_query"),
                free_query=intent.get("free_query")
            )
            matches, total = movie_retrieval_service.search(
                filters=query_filters,
                limit=limit,
                offset=0
            )

        # 3. Handle zero matches honestly without returning fake or unrelated movies
        if not matches:
            criteria_parts = []
            if intent.get("actor"):
                criteria_parts.append(f"Actor: '{intent['actor']}'")
            if intent.get("director"):
                criteria_parts.append(f"Director: '{intent['director']}'")
            if active_genre:
                criteria_parts.append(f"Genre: '{active_genre}'")
            if intent.get("industry"):
                criteria_parts.append(f"Industry: '{intent['industry']}'")
            if intent.get("start_year") or intent.get("end_year"):
                criteria_parts.append(f"Release Period: {intent.get('decade_label', '')}")
            criteria_str = ", ".join(criteria_parts) if criteria_parts else f"'{message}'"

            no_match_explanation = (
                f"No movies in Cinevora's catalog matched your search criteria ({criteria_str}). "
                "No matching movies were found in the current catalog. "
                "The available cast or genre metadata may be incomplete. Cinevora's master catalog covers 3,560 verified titles."
            )
            return AssistantChatResponse(
                reply=no_match_explanation,
                recommendations=[],
                detected_actor=intent.get("actor"),
                detected_director=intent.get("director"),
                detected_genre=active_genre,
                detected_decade=intent.get("decade_label"),
                detected_region=intent.get("industry"),
                detected_language=intent.get("industry"),
                model_used=self.model_name if self.is_available else None,
                assistant_mode="gemini_flash" if self.is_available else "catalog_fallback",
                graph_strategy=graph_strategy if used_graph_rag else None,
                graph_triples=graph_triples if used_graph_rag else None
            )

        # 4. Build verified recommendation models from matched catalog records
        recommendations: List[MovieItem] = []
        catalog_summary_lines: List[str] = []

        for row in matches:
            cid = row.get("catalog_id") or str(row.get("movie_id", ""))
            t = str(row.get("title", "Untitled"))
            g = str(row.get("genre", "Cinema"))
            r = float(row.get("rating", 6.0))
            yr = int(row.get("release_year", 2022))
            ind = str(row.get("industry", "Cinema"))
            poster = row.get("movie_poster")
            trailer = row.get("trailer_link")

            item = MovieItem(
                movie_id=cid,
                movie_title=t,
                release_date=str(yr),
                genres=g,
                score=1.0,
                predicted_rating=r,
                cinema_region=ind,
                original_language=ind,
                poster_url=poster,
                backdrop_url=poster,
                trailer_url=trailer
            )
            recommendations.append(item)
            catalog_summary_lines.append(
                f"- Title: {t} ({yr}) | Industry: {ind} | Genres: {g} | "
                f"Rating: {r:.1f}/10.0 | Cast: {row.get('cast', '')} | Director: {row.get('director', '')}"
            )

        catalog_text = "\n".join(catalog_summary_lines)

        # 5. Build filter summary for explanation context
        criteria_parts = []
        if intent.get("actor"):
            criteria_parts.append(f"Actor: {intent['actor']}")
        if intent.get("director"):
            criteria_parts.append(f"Director: {intent['director']}")
        if active_genre:
            criteria_parts.append(f"Genre: {active_genre}")
        if intent.get("industry"):
            criteria_parts.append(f"Industry: {intent['industry']}")
        if intent.get("decade_label"):
            criteria_parts.append(f"Period: {intent['decade_label']}")
        filter_str = " | ".join(criteria_parts) if criteria_parts else "Catalog inquiry"

        # 6. If Gemini is unavailable or not configured, return an algorithmic explanation
        if not self.is_available:
            stat = self.verify_connection(force=False)
            status_note = (
                "an upstream service limit or network quota"
                if stat.get("status_state") == "quota_or_network_error"
                else "offline catalog fallback mode"
            )
            fallback_reply = (
                f"Here are top-ranked movie matches for your request ({filter_str}) "
                f"retrieved directly from Cinevora's 3,560-title master catalog. "
                f"(Note: AI conversational assistant is operating in {status_note})."
            )
            return AssistantChatResponse(
                reply=fallback_reply,
                recommendations=recommendations,
                detected_actor=intent.get("actor"),
                detected_director=intent.get("director"),
                detected_genre=active_genre,
                detected_decade=intent.get("decade_label"),
                detected_region=intent.get("industry"),
                model_used=None,
                assistant_mode="catalog_fallback",
                graph_strategy=graph_strategy if used_graph_rag else None,
                graph_triples=graph_triples if used_graph_rag else None
            )

        # 7. Grounded explanation prompt for Gemini (augmented with Knowledge Graph Paths)
        num_recs = len(recommendations)
        graph_prompt_section = ""
        if used_graph_rag and graph_triples:
            triples_lines = "\n".join(f"- {t}" for t in graph_triples[:6])
            graph_prompt_section = f"""
Knowledge Graph Multi-Hop Relational Paths:
{triples_lines}
Explain to the user the exact cinematic relationships, shared collaborators, or universe connections that link these movies together based on these graph paths!
"""

        user_prompt = f"""The user asked: "{message}"
Retrieval Strategy: {'Graph RAG (' + graph_strategy + ')' if used_graph_rag else 'Catalog Multi-Filter Search'}
Search Filters Applied: {filter_str}
Total matching movies in catalog: {total} | Showing top {num_recs}
{graph_prompt_section}
Verified Recommendations from Cinevora Catalog (title, year, genre, rating, cast, director):
{catalog_text}

Instructions:
- Address the user warmly and directly answer their request.
- Highlight each movie's title, genre, rating and what makes it special.
- Specifically explain the real cinematic connections or relational bridges (e.g., shared universe, director collaborations, or cast synergy).
- ONLY discuss the movies listed above. Do NOT mention or suggest any other films.
- Keep response to 3-4 short paragraphs or a bullet list. Be concise."""

        # 8. Call Gemini with safe fallback
        try:
            explanation = self._call_gemini(user_prompt)
            return AssistantChatResponse(
                reply=explanation,
                recommendations=recommendations,
                detected_actor=intent.get("actor"),
                detected_director=intent.get("director"),
                detected_genre=active_genre,
                detected_decade=intent.get("decade_label"),
                detected_region=intent.get("industry"),
                model_used=self.model_name,
                assistant_mode="gemini_flash",
                graph_strategy=graph_strategy if used_graph_rag else None,
                graph_triples=graph_triples if used_graph_rag else None
            )
        except (errors.APIError, errors.ClientError, errors.ServerError) as api_err:
            logger.error("Gemini API error occurred: %s", type(api_err).__name__)
            fallback_reply = (
                f"Here are {len(recommendations)} verified movie recommendations matching your inquiry ({filter_str}) "
                "retrieved directly from Cinevora's master catalog!"
            )
            return AssistantChatResponse(
                reply=fallback_reply,
                recommendations=recommendations,
                detected_actor=intent.get("actor"),
                detected_director=intent.get("director"),
                detected_genre=active_genre,
                detected_decade=intent.get("decade_label"),
                detected_region=intent.get("industry"),
                model_used=None,
                assistant_mode="catalog_fallback",
                graph_strategy=graph_strategy if used_graph_rag else None,
                graph_triples=graph_triples if used_graph_rag else None
            )
        except Exception as general_err:
            logger.error("Unexpected error in assistant chat: %s", type(general_err).__name__)
            fallback_reply = (
                f"Here are {len(recommendations)} verified movie recommendations matching your inquiry ({filter_str}) "
                "retrieved directly from Cinevora's master catalog."
            )
            return AssistantChatResponse(
                reply=fallback_reply,
                recommendations=recommendations,
                detected_actor=intent.get("actor"),
                detected_director=intent.get("director"),
                detected_genre=active_genre,
                detected_decade=intent.get("decade_label"),
                detected_region=intent.get("industry"),
                model_used=self.model_name if self.is_available else None,
                assistant_mode="catalog_fallback",
                graph_strategy=graph_strategy if used_graph_rag else None,
                graph_triples=graph_triples if used_graph_rag else None
            )
