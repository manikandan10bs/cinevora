/**
 * Cinevora API Client & Data Adapter
 * Connects streamXie UI components with Cinevora's FastAPI backend (http://127.0.0.1:8000)
 * Single Source of Truth: 3,560-title Master Catalog & SQLite cinevora.db
 */

import { ContentItem, CastMember } from "@/data/mockContent";

export type StreamingSource = {
  source_id?: number;
  name: string;
  type: string;
  region?: string;
  format?: string;
  price?: number | null;
  web_url: string;
};

export type StreamingMovie = {
  movie_id: string;
  title: string;
  release_year?: string;
  genres?: string;
  poster_url?: string;
  backdrop_url?: string;
  rating?: number;
  trailer_url?: string;
  streaming_sources: StreamingSource[];
};

export const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  ((import.meta as any).env?.PROD
    ? "https://cinevora-z42e.onrender.com"
    : "http://127.0.0.1:8000");

export const DEFAULT_USER_ID = "demo_alex";

export const DEMO_ACCOUNTS = [
  { key: "demo_alex", name: "Alex Chen", role: "Sci-Fi & Cyberpunk Enthusiast", avatar: "a1" },
  { key: "demo_sarah", name: "Sarah Miller", role: "Classic & Indie Aficionado", avatar: "a2" },
  { key: "demo_dev", name: "Dev Mode", role: "MLOps & Catalog Admin", avatar: "a3" },
];

export function getActiveUserId(): string {
  try {
    return localStorage.getItem("cinevora_active_user") || DEFAULT_USER_ID;
  } catch {
    return DEFAULT_USER_ID;
  }
}

export function setActiveUserId(userId: string): void {
  try {
    localStorage.setItem("cinevora_active_user", userId);
    window.dispatchEvent(new Event("cinevora-user-change"));
  } catch {}
}

/**
 * Builds YouTube video watch or search query URL fallback.
 */
export function getEffectiveTrailerUrl(movie: any, title?: string): string {
  const direct = movie?.trailer_url || movie?.trailer_link;
  if (
    direct &&
    typeof direct === "string" &&
    direct.trim().startsWith("http") &&
    !direct.toLowerCase().includes("none") &&
    !direct.toLowerCase().includes("nan") &&
    direct.trim() !== "\\N"
  ) {
    return direct.trim();
  }

  const cleanTitle = (title || movie?.title || movie?.movie_title || "movie")
    .replace(/\s*\(\d{4}\)/, "")
    .trim();
  const castStr = movie?.cast || "";
  const leadCast = typeof castStr === "string" ? castStr.split(/[,|]/)[0].trim() : "";
  const year = movie?.release_year || movie?.year || movie?.release_date?.slice?.(0, 4) || "";

  const parts = [cleanTitle];
  if (leadCast && !leadCast.toLowerCase().includes("ensemble")) {
    parts.push(leadCast);
  }
  if (year && String(year).match(/\b(19\d\d|20\d\d)\b/)) {
    parts.push(String(year));
  }
  parts.push("trailer");

  return `https://www.youtube.com/results?search_query=${encodeURIComponent(parts.join(" "))}`;
}

/**
 * Converts YouTube watch URLs to embeddable URLs for iframes.
 */
export function getEmbedTrailerUrl(url: string): string | null {
  if (!url) return null;
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/);
  if (match && match[1]) {
    return `https://www.youtube-nocookie.com/embed/${match[1]}?autoplay=1&mute=0&rel=0`;
  }
  return null;
}

/**
 * Parses delimited cast string into CastMember list.
 */
function parseCastMembers(castStr?: string): CastMember[] {
  if (!castStr || typeof castStr !== "string") {
    return [{ name: "Ensemble Cast", role: "Cast", image: "" }];
  }
  const names = castStr.split(/[,|]/).map((n) => n.trim()).filter(Boolean);
  if (names.length === 0) {
    return [{ name: "Ensemble Cast", role: "Cast", image: "" }];
  }
  return names.slice(0, 8).map((name, idx) => ({
    name,
    role: idx === 0 ? "Lead Actor" : "Cast",
    image: "",
  }));
}

/**
 * Converts a Cinevora backend movie record into streamXie's ContentItem format.
 */
export function adaptCinevoraMovie(raw: any): ContentItem {
  const id = String(raw?.catalog_id || raw?.movie_id || raw?.id || "m-unknown");
  const title = String(raw?.title || raw?.movie_title || "Untitled Cinema");
  const year = Number(raw?.release_year || raw?.release_date?.slice?.(0, 4) || 2024);
  const rating = Number(raw?.avg_rating || raw?.rating || raw?.predicted_rating || 7.5).toFixed(1);

  // Genre parsing
  let genres: string[] = [];
  if (Array.isArray(raw?.genre_list) && raw.genre_list.length > 0) {
    genres = raw.genre_list;
  } else if (typeof raw?.genres === "string") {
    genres = raw.genres.split(/[,|]/).map((g: string) => g.trim()).filter(Boolean);
  } else if (typeof raw?.genre === "string") {
    genres = raw.genre.split(/[,|]/).map((g: string) => g.trim()).filter(Boolean);
  }
  if (genres.length === 0) genres = ["Cinema"];

  const poster =
    raw?.poster_url ||
    raw?.movie_poster ||
    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500";
  const backdrop =
    raw?.backdrop_url ||
    poster;

  const synopsis =
    raw?.synopsis ||
    (raw?.director
      ? `Directed by ${raw.director}. Starring ${raw?.cast || "celebrated cast"}.`
      : "A masterwork from Cinevora's verified cinema catalog.");

  const trailerUrl = getEffectiveTrailerUrl(raw, title);

  return {
    id,
    slug: id.toLowerCase(),
    title,
    description: synopsis,
    longDescription: synopsis,
    type: "movie",
    category: "Movies",
    genres,
    rating,
    year,
    duration: "2h 10m",
    country: raw?.cinema_region || raw?.industry || "Cinema",
    status: "Available",
    heroImage: backdrop,
    posterImage: poster,
    backdropImage: backdrop,
    heroAlt: title,
    posterAlt: title,
    tags: [raw?.cinema_region || raw?.industry || "Cinema", ...genres.slice(0, 2)],
    featured: Boolean(raw?.score && raw.score > 0.8),
    cast: parseCastMembers(raw?.cast),
    trailerUrl,
  };
}

// ----------------------------------------------------------------------------
// Cinevora API Service Methods
// ----------------------------------------------------------------------------

export const cinevoraApi = {
  /**
   * Health Check
   */
  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
  },

  /**
   * Featured movies for Hero Banner
   */
  async getFeaturedMovies(): Promise<ContentItem[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/movies/featured`);
      if (!res.ok) throw new Error("Failed to load featured movies");
      const data = await res.json();
      return (data || []).map(adaptCinevoraMovie);
    } catch (err) {
      console.warn("Featured movies fallback:", err);
      return [];
    }
  },

  /**
   * Real-Time Personalized Recommendations
   */
  async getRecommendations(
    userId: string = getActiveUserId(),
    category: string = "all",
    limit: number = 12
  ): Promise<ContentItem[]> {
    try {
      // First try /recommendations, fallback to /movies/recommendations
      let res = await fetch(
        `${API_BASE_URL}/recommendations?user_id=${encodeURIComponent(userId)}&limit=${limit}`
      );
      if (!res.ok) {
        res = await fetch(
          `${API_BASE_URL}/movies/recommendations?user_id=${encodeURIComponent(userId)}&category=${encodeURIComponent(category)}&limit=${limit}`
        );
      }
      if (!res.ok) throw new Error("Failed to load recommendations");
      const data = await res.json();
      const items = data?.recommendations || [];
      return items.map(adaptCinevoraMovie);
    } catch (err) {
      console.warn("Recommendations fallback:", err);
      return [];
    }
  },

  /**
   * Get Movie Details by ID or Catalog ID
   */
  async getMovieDetails(movieId: string): Promise<ContentItem | null> {
    try {
      // Try /movies/{id} first, then /movies/catalog/{id}
      let res = await fetch(`${API_BASE_URL}/movies/${encodeURIComponent(movieId)}`);
      if (!res.ok) {
        res = await fetch(`${API_BASE_URL}/movies/catalog/${encodeURIComponent(movieId)}`);
      }
      if (!res.ok) return null;
      const data = await res.json();
      return adaptCinevoraMovie(data);
    } catch (err) {
      console.warn(`Movie details error for ${movieId}:`, err);
      return null;
    }
  },

  /**
   * Get 4 Same-Genre Related Movies for Chainable Browsing
   */
  async getSameGenreMovies(
    movieId: string,
    primaryGenre: string,
    limit: number = 4
  ): Promise<ContentItem[]> {
    try {
      const cleanGenre = primaryGenre?.split?.(",")?.[0]?.trim() || "Action";
      const res = await fetch(
        `${API_BASE_URL}/movies/search?genre=${encodeURIComponent(cleanGenre)}&limit=${limit + 4}`
      );
      if (!res.ok) return [];
      const data = await res.json();
      const items = (data?.results || [])
        .map(adaptCinevoraMovie)
        .filter((m: ContentItem) => m.id !== movieId);
      return items.slice(0, limit);
    } catch (err) {
      console.warn("Same genre error:", err);
      return [];
    }
  },

  /**
   * Deterministic Movie Search with Structured Filters
   */
  async searchMovies(
    query?: string,
    options: {
      genre?: string;
      cinema_region?: string;
      limit?: number;
    } = {}
  ): Promise<ContentItem[]> {
    try {
      const params = new URLSearchParams();
      if (query && query.trim()) params.append("query", query.trim());
      if (options.genre && options.genre !== "All") params.append("genre", options.genre);
      if (options.cinema_region && options.cinema_region !== "All") {
        params.append("region", options.cinema_region);
        params.append("cinema_region", options.cinema_region);
      }
      params.append("limit", String(options.limit || 30));

      const res = await fetch(`${API_BASE_URL}/movies/search?${params.toString()}`);
      if (!res.ok) return [];
      const data = await res.json();
      return (data?.results || []).map(adaptCinevoraMovie);
    } catch (err) {
      console.warn("Search error:", err);
      return [];
    }
  },

  /**
   * Master Catalog Paginated Listing
   */
  async getMasterCatalog(params: {
    page?: number;
    page_size?: number;
    genre?: string;
    industry?: string;
    search?: string;
    sort_by?: string;
  } = {}): Promise<{ items: ContentItem[]; total: number; page: number; total_pages: number }> {
    try {
      const qs = new URLSearchParams();
      const limit = params.page_size || 24;
      const offset = ((params.page || 1) - 1) * limit;

      qs.append("limit", String(limit));
      qs.append("offset", String(offset));
      if (params.genre && params.genre !== "All") qs.append("genre", params.genre);
      if (params.industry && params.industry !== "All") qs.append("industry", params.industry);
      if (params.search && params.search.trim()) qs.append("query", params.search.trim());
      if (params.sort_by) qs.append("sort_by", params.sort_by);

      const res = await fetch(`${API_BASE_URL}/movies/catalog?${qs.toString()}`);
      if (!res.ok) throw new Error("Failed to load catalog");
      const data = await res.json();
      return {
        items: (data?.results || []).map(adaptCinevoraMovie),
        total: data?.total || data?.count || 3560,
        page: params.page || 1,
        total_pages: Math.ceil((data?.total || 3560) / limit),
      };
    } catch (err) {
      console.warn("Master catalog error:", err);
      return { items: [], total: 0, page: 1, total_pages: 1 };
    }
  },

  /**
   * Toggle Like (SQLite via /likes)
   */
  async toggleLike(userId: string, movieId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/likes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, movie_id: movieId }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      return Boolean(data?.liked);
    } catch (err) {
      console.error("Toggle like error:", err);
      return false;
    }
  },

  /**
   * Get User Likes (SQLite via /likes)
   */
  async getUserLikes(userId: string): Promise<string[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/likes?user_id=${encodeURIComponent(userId)}`);
      if (!res.ok) return [];
      const data = await res.json();
      return data?.liked_movie_ids || [];
    } catch (err) {
      return [];
    }
  },

  /**
   * Add to Watchlist (Favorites - SQLite via /favorites)
   */
  async addFavorite(userId: string, movie: ContentItem): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/favorites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          movie_id: movie.id,
          movie_title: movie.title,
          genres: movie.genres.join(", "),
          rating: parseFloat(movie.rating) || 7.0,
        }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  /**
   * Remove from Watchlist (Favorites - SQLite via /favorites/{id})
   */
  async removeFavorite(userId: string, movieId: string): Promise<boolean> {
    try {
      const res = await fetch(
        `${API_BASE_URL}/favorites/${encodeURIComponent(movieId)}?user_id=${encodeURIComponent(userId)}`,
        { method: "DELETE" }
      );
      return res.ok;
    } catch {
      return false;
    }
  },

  /**
   * Get User Watchlist (Favorites - SQLite via /favorites)
   */
  async getUserFavorites(userId: string): Promise<ContentItem[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/favorites?user_id=${encodeURIComponent(userId)}`);
      if (!res.ok) return [];
      const data = await res.json();
      return (data?.favorites || []).map(adaptCinevoraMovie);
    } catch {
      return [];
    }
  },

  /**
   * Record Movie View Activity (SQLite via /history/view)
   */
  async recordView(userId: string, movieId: string, movieTitle: string, durationSec: number = 120): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/history/view`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          movie_id: movieId,
          movie_title: movieTitle,
        }),
      });
    } catch {}
  },

  /**
   * Record Search Query (SQLite via /history/search)
   */
  async recordSearch(userId: string, queryText: string): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/history/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          query: queryText,
        }),
      });
    } catch {}
  },

  /**
   * AI Movie Concierge Chat (Gemini 3.5 Flash Lite + Grounded Catalog via /assistant/chat)
   */
  async chatWithAssistant(message: string, userId: string = getActiveUserId(), limit: number = 5): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        user_id: userId,
        limit,
      }),
    });
    if (!res.ok) throw new Error("Assistant chat request failed");
    return res.json();
  },

  /**
   * AI Concierge Status via /assistant/status
   */
  async getAssistantStatus(): Promise<any> {
    try {
      const res = await fetch(`${API_BASE_URL}/assistant/status`);
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  },

  /**
   * MLOps Telemetry Metrics via /monitoring/metrics
   */
  async getMonitoringMetrics(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/monitoring/metrics`);
    if (!res.ok) throw new Error("Failed to load monitoring metrics");
    return res.json();
  },

  /**
   * MLOps Telemetry Recent Events via /monitoring/events
   */
  async getMonitoringEvents(limit: number = 30): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/monitoring/events?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to load monitoring events");
    return res.json();
  },

  /**
   * Destructive operation: Clear all monitoring telemetry and user interaction history.
   * Requires confirmText === "CLEAR_ALL_DATA".
   */
  async clearMonitoringData(confirmText: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/monitoring/clear-data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm_text: confirmText }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to clear monitoring data");
    }
    return res.json();
  },

  /**
   * Resolves exact YouTube trailer: TMDB first -> Master Catalog -> YouTube search query fallback.
   */
  async getExactTrailerUrl(movieId: string): Promise<{
    movie_id: string;
    movie_title: string;
    trailer_url: string;
    source: string;
    attempts_made?: number;
    max_attempts?: number;
  }> {
    const res = await fetch(`${API_BASE_URL}/movies/${encodeURIComponent(movieId)}/trailer`);
    if (!res.ok) {
      throw new Error("Failed to resolve trailer URL");
    }
    return res.json();
  },

  /**
   * Fetches movies available for streaming via WatchMode API.
   */
  async getAvailableStreamingMovies(): Promise<StreamingMovie[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/movies/streaming/available`);
      if (!res.ok) return [];
      return res.json();
    } catch {
      return [];
    }
  },

  /**
   * Fetches real-time streaming providers (Netflix, Prime, Disney+, etc.) for a specific movie.
   */
  async getMovieStreamingSources(movieId: string): Promise<{
    movie_id: string;
    title: string;
    has_streaming: boolean;
    sources: StreamingSource[];
  }> {
    try {
      const res = await fetch(`${API_BASE_URL}/movies/${encodeURIComponent(movieId)}/streaming`);
      if (!res.ok) return { movie_id: movieId, title: "", has_streaming: false, sources: [] };
      return res.json();
    } catch {
      return { movie_id: movieId, title: "", has_streaming: false, sources: [] };
    }
  },

  /**
   * Real SQLite User Authentication: Login
   */
  async loginUser(username: string, password: string): Promise<{
    id: number;
    username: string;
    display_name: string;
    created_at?: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid username or password");
    }
    const data = await res.json();
    try {
      localStorage.setItem("cinevora_user_session", JSON.stringify(data));
      setActiveUserId(data.username);
    } catch {}
    return data;
  },

  /**
   * Real SQLite User Authentication: Manual Registration
   */
  async registerUser(
    username: string,
    password: string,
    displayName?: string
  ): Promise<{
    id: number;
    username: string;
    display_name: string;
    created_at?: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username,
        password,
        display_name: displayName || username,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to register new account");
    }
    const data = await res.json();
    try {
      localStorage.setItem("cinevora_user_session", JSON.stringify(data));
      setActiveUserId(data.username);
    } catch {}
    return data;
  },

  /**
   * Log out active user and reset to demo session
   */
  logoutUser(): void {
    try {
      localStorage.removeItem("cinevora_user_session");
      localStorage.setItem("cinevora_active_user", DEFAULT_USER_ID);
      window.dispatchEvent(new Event("cinevora-user-change"));
    } catch {}
  },

  /**
   * Get parsed active user session if available
   */
  getCurrentUser(): { id: number; username: string; display_name: string } | null {
    try {
      const raw = localStorage.getItem("cinevora_user_session");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
};
