"""
Cinevora Cinema Knowledge Graph Engine (Graph RAG)
Constructs an in-memory heterogeneous knowledge graph of movies, actors, directors,
genres, industries, and cinematic universes for multi-hop relational retrieval.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

import networkx as nx
import pandas as pd

logger = logging.getLogger("cinevora.graph")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "Movies_Master_Cleaned.csv"

# Pre-defined known cinematic universes & franchises popular in Indian & World Cinema
KNOWN_UNIVERSES = {
    "lcu": {
        "name": "Lokesh Cinematic Universe (LCU)",
        "keywords": ["lcu", "lokesh universe", "kaithi", "vikram", "leo"],
        "directors": ["lokesh kanagaraj"],
        "titles": ["vikram", "leo", "kaithi", "master"]
    },
    "yrf_spy": {
        "name": "YRF Spy Universe",
        "keywords": ["spy universe", "yrf spy", "pathaan", "tiger", "war"],
        "titles": ["pathaan", "war", "war 2", "tiger 3", "ek tha tiger", "tiger zinda hai"]
    },
    "cop_universe": {
        "name": "Rohit Shetty Cop Universe",
        "keywords": ["cop universe", "singham", "simmba", "sooryavanshi"],
        "directors": ["rohit shetty"],
        "titles": ["singham", "singham returns", "simmba", "sooryavanshi", "singham again"]
    },
    "kgf_universe": {
        "name": "KGF / Prashanth Neel Cinema Realm",
        "keywords": ["kgf", "kgf universe", "salaar", "prashanth neel"],
        "directors": ["prashanth neel"],
        "titles": ["k.g.f: chapter 1", "k.g.f: chapter 2", "salaar"]
    },
    "baahubali": {
        "name": "Baahubali Saga",
        "keywords": ["baahubali", "rajamouli universe"],
        "directors": ["s.s. rajamouli", "ss rajamouli", "rajamouli"],
        "titles": ["baahubali: the beginning", "baahubali 2: the conclusion"]
    },
    "mcu": {
        "name": "Marvel Cinematic Universe (MCU)",
        "keywords": ["mcu", "marvel", "avengers", "iron man", "thor", "captain america"],
        "titles": ["iron man", "the avengers", "avengers: endgame", "avengers: infinity war", "thor", "captain america", "spider-man", "guardians of the galaxy"]
    },
    "nolan_multiverse": {
        "name": "Christopher Nolan Mind-Bending Realm",
        "keywords": ["nolan", "christopher nolan", "mind bending", "non linear"],
        "directors": ["christopher nolan"],
        "titles": ["interstellar", "oppenheimer", "inception", "the dark knight", "tenet", "memento", "dunkirk", "the prestige"]
    }
}


def normalize_text(text: Optional[str]) -> str:
    """Normalizes names and titles for case-insensitive graph matching."""
    if not text or not isinstance(text, str):
        return ""
    # Strip year tags like (2023) or extra brackets
    cleaned = re.sub(r"\(.*?\)", "", text)
    cleaned = cleaned.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


class CinemaKnowledgeGraph:
    """
    Heterogeneous in-memory knowledge graph representing movies, actors, directors,
    genres, industries, and franchises for Graph-RAG relational reasoning.
    """

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = Path(csv_path or CSV_PATH)
        self.graph = nx.MultiGraph()
        
        # Fast lookup indices
        self.title_to_node: Dict[str, str] = {}
        self.catalog_id_to_node: Dict[str, str] = {}
        self.actor_to_node: Dict[str, str] = {}
        self.director_to_node: Dict[str, str] = {}
        self.genre_to_node: Dict[str, str] = {}
        self.industry_to_node: Dict[str, str] = {}
        self.universe_to_node: Dict[str, str] = {}
        
        # Raw movie records cache
        self.movie_records: Dict[str, Dict[str, Any]] = {}
        
        self.is_built = False
        self._build_graph()

    def _build_graph(self):
        """Constructs graph nodes and edges from master catalog CSV."""
        if not self.csv_path.exists():
            logger.warning(f"Catalog CSV not found at {self.csv_path}. Graph will be empty.")
            return

        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            logger.error(f"Failed to read catalog CSV for knowledge graph: {e}")
            return

        logger.info(f"Building Cinema Knowledge Graph from {len(df)} titles...")

        # 1. Register Universe Nodes
        for u_key, u_data in KNOWN_UNIVERSES.items():
            u_node = f"universe:{u_key}"
            self.graph.add_node(
                u_node,
                node_type="universe",
                key=u_key,
                name=u_data["name"]
            )
            self.universe_to_node[u_key] = u_node

        # 2. Process Movies
        for _, row in df.iterrows():
            cid = str(row.get("catalog_id", f"MOVIE-{row.get('movie_id', '')}"))
            title = str(row.get("title", "Untitled"))
            norm_title = normalize_text(title)
            year = int(row.get("release_year", 2022)) if pd.notna(row.get("release_year")) else 2022
            rating = float(row.get("rating", 6.0)) if pd.notna(row.get("rating")) else 6.0
            industry = str(row.get("industry", "Cinema")).strip()
            genre_str = str(row.get("genre", "Drama")).strip()
            director = str(row.get("director", "")).strip() if pd.notna(row.get("director")) else ""
            cast_str = str(row.get("cast", "")).strip() if pd.notna(row.get("cast")) else ""
            poster = str(row.get("movie_poster", "")) if pd.notna(row.get("movie_poster")) else ""
            trailer = str(row.get("trailer_link", "")) if pd.notna(row.get("trailer_link")) else ""

            movie_node = f"movie:{cid}"
            self.graph.add_node(
                movie_node,
                node_type="movie",
                catalog_id=cid,
                title=title,
                norm_title=norm_title,
                year=year,
                rating=rating,
                industry=industry,
                genre=genre_str,
                director=director,
                cast=cast_str,
                poster=poster,
                trailer=trailer
            )
            self.title_to_node[norm_title] = movie_node
            self.catalog_id_to_node[cid] = movie_node
            self.movie_records[cid] = row.to_dict()

            # Industry Edge
            if industry and industry.lower() != "nan":
                norm_ind = normalize_text(industry)
                ind_node = f"industry:{norm_ind}"
                if ind_node not in self.graph:
                    self.graph.add_node(ind_node, node_type="industry", name=industry)
                    self.industry_to_node[norm_ind] = ind_node
                self.graph.add_edge(movie_node, ind_node, relation="BELONGS_TO_INDUSTRY")

            # Genre Edges
            for g in genre_str.split(","):
                g_clean = g.strip()
                if not g_clean or g_clean.lower() == "nan":
                    continue
                norm_g = normalize_text(g_clean)
                genre_node = f"genre:{norm_g}"
                if genre_node not in self.graph:
                    self.graph.add_node(genre_node, node_type="genre", name=g_clean)
                    self.genre_to_node[norm_g] = genre_node
                self.graph.add_edge(movie_node, genre_node, relation="HAS_GENRE")

            # Director Edge
            if director and director.lower() not in ["nan", "unknown", "\\n", "none"]:
                norm_dir = normalize_text(director)
                dir_node = f"director:{norm_dir}"
                if dir_node not in self.graph:
                    self.graph.add_node(dir_node, node_type="director", name=director)
                    self.director_to_node[norm_dir] = dir_node
                self.graph.add_edge(movie_node, dir_node, relation="DIRECTED_BY")

            # Cast Edges
            if cast_str and cast_str.lower() not in ["nan", "unknown", "\\n", "none"]:
                actors = [a.strip() for a in re.split(r"[,|]", cast_str) if a.strip()]
                for actor in actors[:8]:  # Up to 8 primary actors
                    norm_act = normalize_text(actor)
                    if not norm_act or len(norm_act) < 2:
                        continue
                    act_node = f"actor:{norm_act}"
                    if act_node not in self.graph:
                        self.graph.add_node(act_node, node_type="actor", name=actor)
                        self.actor_to_node[norm_act] = act_node
                    self.graph.add_edge(movie_node, act_node, relation="STARRING")

            # Cinematic Universe Linkage
            for u_key, u_data in KNOWN_UNIVERSES.items():
                is_in_u = False
                # Check director match first
                if director:
                    norm_dir = normalize_text(director)
                    for ud in u_data.get("directors", []):
                        if ud in norm_dir:
                            is_in_u = True
                            break

                # Check title match with exact or boundary precision
                if not is_in_u:
                    for ut in u_data.get("titles", []):
                        # For single short common words like 'master', 'war', require exact title
                        if ut in ["master", "war", "tiger", "thor", "leo"]:
                            if norm_title == ut:
                                is_in_u = True
                                break
                        else:
                            if re.search(r"\b" + re.escape(ut) + r"\b", norm_title):
                                is_in_u = True
                                break

                if is_in_u:
                    u_node = self.universe_to_node[u_key]
                    self.graph.add_edge(movie_node, u_node, relation="PART_OF_UNIVERSE")

        self.is_built = True
        logger.info(
            f"Knowledge Graph ready: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges."
        )

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics of the Knowledge Graph."""
        node_types = {}
        for _, attrs in self.graph.nodes(data=True):
            ntype = attrs.get("node_type", "unknown")
            node_types[ntype] = node_types.get(ntype, 0) + 1
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_breakdown": node_types
        }

    def resolve_movie_node(self, title_query: str) -> Optional[str]:
        """Finds a movie node matching a title with exact or partial token match."""
        norm_q = normalize_text(title_query)
        if not norm_q:
            return None
        # Exact match
        if norm_q in self.title_to_node:
            return self.title_to_node[norm_q]
        # Partial match
        for title, node in self.title_to_node.items():
            if norm_q == title or (len(norm_q) >= 4 and norm_q in title):
                return node
        return None

    def resolve_person_nodes(self, name_query: str) -> List[Tuple[str, str]]:
        """
        Finds matching actor or director nodes for a given query name.
        Sorts candidates by exact match priority and graph degree (movie count).
        Returns list of (node_id, person_type).
        """
        norm_q = normalize_text(name_query)
        if not norm_q or len(norm_q) < 3:
            return []

        # Known aliases
        ALIASES = {
            "srk": "shah rukh khan",
            "thalapathy": "vijay",
            "thalapathy vijay": "vijay",
            "thala": "ajith kumar",
            "superstar": "rajinikanth",
            "nolan": "christopher nolan",
            "kamal": "kamal haasan"
        }
        if norm_q in ALIASES:
            norm_q = ALIASES[norm_q]

        candidates = []

        # Check directors
        for d_name, node in self.director_to_node.items():
            if norm_q == d_name:
                score = 100 + self.graph.degree(node)
                candidates.append((score, node, "director"))
            elif re.search(r"\b" + re.escape(norm_q) + r"\b", d_name):
                score = 50 + self.graph.degree(node)
                candidates.append((score, node, "director"))
            elif norm_q in d_name:
                score = 10 + self.graph.degree(node)
                candidates.append((score, node, "director"))

        # Check actors
        for a_name, node in self.actor_to_node.items():
            if norm_q == a_name:
                score = 100 + self.graph.degree(node)
                candidates.append((score, node, "actor"))
            elif re.search(r"\b" + re.escape(norm_q) + r"\b", a_name):
                score = 50 + self.graph.degree(node)
                candidates.append((score, node, "actor"))
            elif norm_q in a_name:
                score = 10 + self.graph.degree(node)
                candidates.append((score, node, "actor"))

        # Sort descending by match score + degree
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [(c[1], c[2]) for c in candidates]

    def find_universe_movies(self, universe_query: str, limit: int = 10) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Retrieves movies belonging to a cinematic universe or franchise.
        Returns (movies_list, graph_triples).
        """
        norm_q = normalize_text(universe_query)
        matched_u_node = None
        u_name = "Universe"

        for u_key, u_data in KNOWN_UNIVERSES.items():
            for kw in u_data.get("keywords", []):
                if kw in norm_q or norm_q in kw:
                    matched_u_node = self.universe_to_node[u_key]
                    u_name = u_data["name"]
                    break
            if matched_u_node:
                break

        if not matched_u_node:
            return [], []

        matched_movies = []
        triples = []

        # Find all movies connected to this universe node
        for neighbor in self.graph.neighbors(matched_u_node):
            if self.graph.nodes[neighbor].get("node_type") == "movie":
                cid = self.graph.nodes[neighbor]["catalog_id"]
                raw_movie = self.movie_records.get(cid)
                if raw_movie:
                    matched_movies.append(raw_movie)
                    m_title = raw_movie.get("title")
                    triples.append(f"('{m_title}') --[PART_OF_UNIVERSE]--> ({u_name})")

        # Sort by rating
        matched_movies.sort(key=lambda m: float(m.get("rating", 0)), reverse=True)
        return matched_movies[:limit], triples

    def find_multi_hop_related(
        self,
        movie_title: str,
        limit: int = 6,
        industry_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Performs 2-hop graph walk starting from a reference movie to find
        the most organically connected movies (shared director, shared cast, shared genre/universe).
        Returns (scored_movies_list, reasoning_triples).
        """
        movie_node = self.resolve_movie_node(movie_title)
        if not movie_node:
            return [], []

        source_movie = self.graph.nodes[movie_node]
        source_title = source_movie.get("title", movie_title)
        source_cid = source_movie.get("catalog_id")

        # 1-hop neighbors: directors, actors, genres, industry, universe
        first_hop = list(self.graph.neighbors(movie_node))

        # 2-hop scores
        candidate_scores: Dict[str, float] = {}
        paths_explanation: Dict[str, List[str]] = {}

        for hop1 in first_hop:
            h1_attrs = self.graph.nodes[hop1]
            h1_type = h1_attrs.get("node_type")
            h1_name = h1_attrs.get("name", hop1)

            # Weighting scheme for relational closeness
            if h1_type == "director":
                weight = 5.0
                rel_label = "DIRECTED_BY"
            elif h1_type == "actor":
                weight = 3.5
                rel_label = "STARRING"
            elif h1_type == "universe":
                weight = 4.0
                rel_label = "PART_OF_UNIVERSE"
            elif h1_type == "genre":
                weight = 1.0
                rel_label = "HAS_GENRE"
            elif h1_type == "industry":
                weight = 0.5
                rel_label = "IN_INDUSTRY"
            else:
                weight = 0.5
                rel_label = "RELATED_TO"

            # 2-hop step: other movies connected to this entity
            for hop2 in self.graph.neighbors(hop1):
                if hop2 == movie_node:
                    continue  # Skip self
                h2_attrs = self.graph.nodes[hop2]
                if h2_attrs.get("node_type") == "movie":
                    cid2 = h2_attrs.get("catalog_id")
                    if not cid2:
                        continue

                    # Industry constraint check if requested
                    if industry_filter:
                        m_ind = str(h2_attrs.get("industry", "")).lower()
                        if industry_filter.lower() not in m_ind:
                            continue

                    candidate_scores[cid2] = candidate_scores.get(cid2, 0.0) + weight

                    # Record path
                    m2_title = h2_attrs.get("title", cid2)
                    path_str = f"('{source_title}') --[{rel_label}]--> ({h1_name}) <--[{rel_label}]-- ('{m2_title}')"
                    if cid2 not in paths_explanation:
                        paths_explanation[cid2] = []
                    if len(paths_explanation[cid2]) < 3:
                        paths_explanation[cid2].append(path_str)

        # Sort candidate movies by aggregated graph connectivity score
        sorted_cids = sorted(candidate_scores.keys(), key=lambda c: candidate_scores[c], reverse=True)

        matched_movies = []
        all_triples = []
        for cid in sorted_cids[:limit]:
            raw = self.movie_records.get(cid)
            if raw:
                # Attach graph score to movie record
                rec = dict(raw)
                rec["graph_connectivity_score"] = round(candidate_scores[cid], 1)
                matched_movies.append(rec)
                all_triples.extend(paths_explanation.get(cid, []))

        return matched_movies, all_triples

    def find_collaborations(
        self,
        entity_a: str,
        entity_b: str,
        limit: int = 6
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Finds movies where two entities (e.g. Actor + Director, or Actor + Actor)
        collaborate directly or share a 2-hop bridge.
        """
        nodes_a = self.resolve_person_nodes(entity_a)
        nodes_b = self.resolve_person_nodes(entity_b)

        if not nodes_a or not nodes_b:
            return [], []

        node_a = nodes_a[0][0]
        node_b = nodes_b[0][0]
        name_a = self.graph.nodes[node_a].get("name", entity_a)
        name_b = self.graph.nodes[node_b].get("name", entity_b)

        # Movies connected to A
        movies_a = {n for n in self.graph.neighbors(node_a) if self.graph.nodes[n].get("node_type") == "movie"}
        # Movies connected to B
        movies_b = {n for n in self.graph.neighbors(node_b) if self.graph.nodes[n].get("node_type") == "movie"}

        # Direct intersection
        direct_intersection = movies_a.intersection(movies_b)
        matched_movies = []
        triples = []

        if direct_intersection:
            for m_node in direct_intersection:
                cid = self.graph.nodes[m_node]["catalog_id"]
                raw = self.movie_records.get(cid)
                if raw:
                    matched_movies.append(raw)
                    m_title = raw.get("title")
                    triples.append(f"({name_a}) --[COLLABORATION]--> ('{m_title}') <--[COLLABORATION]-- ({name_b})")

        # If direct intersection has fewer than limit, add 2-hop bridge movies
        if len(matched_movies) < limit:
            for m_node in list(movies_a)[:limit]:
                if m_node not in direct_intersection:
                    cid = self.graph.nodes[m_node]["catalog_id"]
                    raw = self.movie_records.get(cid)
                    if raw and raw not in matched_movies:
                        matched_movies.append(raw)
                        m_title = raw.get("title")
                        triples.append(f"({name_a}) --[COLLABORATION]--> ('{m_title}')")

        return matched_movies[:limit], triples

    def search_graph_rag(
        self,
        query_text: str,
        intent: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[str], str]:
        """
        Main Graph RAG inference pipeline:
        Analyzes query intent, performs multi-hop relational graph retrieval,
        and extracts ground-truth reasoning triples for Gemini.
        Returns: (movies, triples, strategy_name)
        """
        intent = intent or {}
        q_lower = query_text.lower()

        # Strategy 1: Cinematic Universe / Franchise
        for u_data in KNOWN_UNIVERSES.values():
            for kw in u_data.get("keywords", []):
                if re.search(r"\b" + re.escape(kw) + r"\b", q_lower):
                    movies, triples = self.find_universe_movies(kw, limit=limit)
                    if movies:
                        return movies, triples, "universe_traversal"

        # Strategy 2: Dual-Entity Collaborations (Actor + Director or 2 actors)
        actor = intent.get("actor")
        director = intent.get("director")
        if actor and director:
            movies, triples = self.find_collaborations(actor, director, limit=limit)
            if movies:
                return movies, triples, "collaboration_bridge"

        # Check for multiple names in query: e.g. "Vijay and Lokesh" or "Shah Rukh Khan and Atlee"
        collab_m = re.search(r"\b([A-Za-z\s\.\'\-]+)\s+(?:and|with|\&)\s+([A-Za-z\s\.\'\-]+)\b", query_text, re.IGNORECASE)
        if collab_m:
            stop_re = r"\b(movies?|films?|cinema|actor|director|starring|directed\s+by|featuring|hits?)\b"
            cand1 = re.sub(stop_re, "", collab_m.group(1), flags=re.IGNORECASE).strip()
            cand2 = re.sub(stop_re, "", collab_m.group(2), flags=re.IGNORECASE).strip()
            # Verify if both candidates match people in our graph
            if cand1 and cand2 and self.resolve_person_nodes(cand1) and self.resolve_person_nodes(cand2):
                movies, triples = self.find_collaborations(cand1, cand2, limit=limit)
                if movies:
                    return movies, triples, "collaboration_bridge"

        # Strategy 3: "Similar to [Movie]" or "Movies like [Movie]" Multi-hop relational walk
        similar_to = intent.get("similar_to")
        if similar_to:
            movies, triples = self.find_multi_hop_related(
                similar_to,
                limit=limit,
                industry_filter=intent.get("industry")
            )
            if movies:
                return movies, triples, "multi_hop_relational"

        # Strategy 4: Mentioned Movie Title in query
        # Check if query references any known movie title
        for t_norm, m_node in self.title_to_node.items():
            if len(t_norm) >= 4 and re.search(r"\b" + re.escape(t_norm) + r"\b", q_lower):
                m_title = self.graph.nodes[m_node].get("title", t_norm)
                movies, triples = self.find_multi_hop_related(
                    m_title,
                    limit=limit,
                    industry_filter=intent.get("industry")
                )
                if movies:
                    return movies, triples, "multi_hop_title_pivot"

        # Strategy 5: Person pivot (Director or Actor 1-hop + 2-hop ecosystem)
        if director:
            d_nodes = self.resolve_person_nodes(director)
            if d_nodes:
                d_node = d_nodes[0][0]
                d_name = self.graph.nodes[d_node].get("name", director)
                connected_movies = [
                    self.movie_records[self.graph.nodes[n]["catalog_id"]]
                    for n in self.graph.neighbors(d_node)
                    if self.graph.nodes[n].get("node_type") == "movie" and self.graph.nodes[n].get("catalog_id") in self.movie_records
                ]
                if connected_movies:
                    triples = [f"({d_name}) --[DIRECTED_BY]--> ('{m.get('title')}')" for m in connected_movies[:limit]]
                    return connected_movies[:limit], triples, "director_ecosystem"

        if actor:
            a_nodes = self.resolve_person_nodes(actor)
            if a_nodes:
                a_node = a_nodes[0][0]
                a_name = self.graph.nodes[a_node].get("name", actor)
                connected_movies = [
                    self.movie_records[self.graph.nodes[n]["catalog_id"]]
                    for n in self.graph.neighbors(a_node)
                    if self.graph.nodes[n].get("node_type") == "movie" and self.graph.nodes[n].get("catalog_id") in self.movie_records
                ]
                if connected_movies:
                    triples = [f"({a_name}) --[STARRING]--> ('{m.get('title')}')" for m in connected_movies[:limit]]
                    return connected_movies[:limit], triples, "actor_filmography"

        return [], [], "none"


# Global singleton instance
_knowledge_graph_instance: Optional[CinemaKnowledgeGraph] = None


def get_knowledge_graph() -> CinemaKnowledgeGraph:
    """Returns the singleton CinemaKnowledgeGraph instance, building it on first access."""
    global _knowledge_graph_instance
    if _knowledge_graph_instance is None:
        _knowledge_graph_instance = CinemaKnowledgeGraph()
    return _knowledge_graph_instance
