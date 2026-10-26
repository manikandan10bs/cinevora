import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { MagnifyingGlass, SortAscending, X, Sparkle } from "@phosphor-icons/react";
import { Input } from "@/components/ui/input";
import { PageContainer } from "@/components/layout/PageContainer";
import { ContentItem } from "@/data/mockContent";
import { PosterCard } from "@/components/content/PosterCard";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { TrailerModal } from "@/components/common/TrailerModal";
import { getSearchHistory, saveSearchTerm } from "@/lib/storage";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { motion, AnimatePresence } from "framer-motion";
import { cinevoraApi, getActiveUserId } from "@/lib/cinevoraClient";

type SearchPageProps = {
  myList: string[];
  onToggleList: (id: string) => void;
};

type SortOption = "relevance" | "rating" | "year-desc" | "year-asc" | "title";

const sortLabels: Record<SortOption, string> = {
  relevance: "Relevance",
  rating: "Top Rated",
  "year-desc": "Newest First",
  "year-asc": "Oldest First",
  title: "A–Z",
};

const cinevoraKeywords = [
  "Vijay",
  "Lokesh Kanagaraj",
  "Action",
  "Interstellar",
  "Sci-Fi",
  "Christopher Nolan",
  "Tamil",
  "Thriller",
  "Psychological",
  "Malayalam",
];

export const SearchPage = ({ myList, onToggleList }: SearchPageProps) => {
  useDocumentMeta(
    "Search Catalog | Cinevora",
    "Search across 3,560 verified cinema titles by actor, director, genre, or keyword."
  );

  const [params, setParams] = useSearchParams();
  const initial = params.get("q") || "";
  const [query, setQuery] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [rawResults, setRawResults] = useState<ContentItem[]>([]);
  const [activeGenres, setActiveGenres] = useState<string[]>([]);
  const [sort, setSort] = useState<SortOption>("relevance");
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [selectedTrailer, setSelectedTrailer] = useState<ContentItem | null>(null);

  const recent = getSearchHistory();
  const activeUser = getActiveUserId();

  // Sync state if URL search param changes
  useEffect(() => {
    if (initial !== query) {
      setQuery(initial);
    }
  }, [initial]);

  // Live debounced search as user types or when query changes
  useEffect(() => {
    let isMounted = true;
    const trimmed = query.trim();

    if (!trimmed) {
      setRawResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const results = await cinevoraApi.searchMovies(trimmed, { limit: 36 });
        if (isMounted) {
          setRawResults(results);
        }
      } catch (err) {
        console.warn("Live search execution error:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }, 250);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [query]);

  // Derived filtered & sorted results
  const results = useMemo(() => {
    let filtered = rawResults;

    if (activeGenres.length > 0) {
      filtered = filtered.filter((item) =>
        activeGenres.every((g) =>
          item.genres.some((ig) => ig.toLowerCase() === g.toLowerCase())
        )
      );
    }

    const sorted = [...filtered];
    if (sort === "rating") sorted.sort((a, b) => parseFloat(b.rating) - parseFloat(a.rating));
    else if (sort === "year-desc") sorted.sort((a, b) => b.year - a.year);
    else if (sort === "year-asc") sorted.sort((a, b) => a.year - b.year);
    else if (sort === "title") sorted.sort((a, b) => a.title.localeCompare(b.title));

    return sorted;
  }, [rawResults, activeGenres, sort]);

  // Available genres in current search results
  const availableGenres = useMemo(() => {
    const set = new Set<string>();
    rawResults.forEach((item) => item.genres.forEach((g) => set.add(g)));
    return Array.from(set).sort();
  }, [rawResults]);

  const toggleGenre = (genre: string) => {
    setActiveGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
  };

  const clearFilters = () => {
    setActiveGenres([]);
    setSort("relevance");
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    saveSearchTerm(query.trim());
    setParams({ q: query.trim() });
    cinevoraApi.recordSearch(activeUser, query.trim());
    setActiveGenres([]);
  };

  const hasFilters = activeGenres.length > 0 || sort !== "relevance";

  return (
    <PageContainer className="pt-32 pb-16">
      <section className="mx-auto max-w-3xl text-center">
        <h1 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-[0.08em] text-foreground">
          Cinevora Master Catalog Search
        </h1>
        <p className="mt-3 text-sm sm:text-base text-muted-foreground">
          Deterministic metadata search grounded in 3,560 verified titles across Indian Cinema and Hollywood.
        </p>

        <form
          onSubmit={onSubmit}
          className="mt-6 flex items-center gap-3 rounded-xl border border-border bg-card px-5 py-3 shadow-lg focus-within:border-primary/70 transition-all"
        >
          <MagnifyingGlass size={26} weight="duotone" className="text-primary shrink-0" />
          <Input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by actor (Vijay), director (Lokesh), title, or genre..."
            className="border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus-visible:ring-0 text-base"
          />
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setParams({});
                clearFilters();
              }}
              className="shrink-0 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              <X size={18} weight="bold" />
            </button>
          )}
        </form>

        {/* Recent & Suggested Keywords */}
        {!initial && (
          <div className="mt-8 space-y-6">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Popular Search Terms
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {cinevoraKeywords.map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => {
                      setQuery(term);
                      setParams({ q: term });
                    }}
                    className="rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary transition-all hover:bg-primary/20 hover:scale-105 cursor-pointer"
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>

            {recent.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Your Recent Queries
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {recent.map((term) => (
                    <button
                      key={term}
                      type="button"
                      onClick={() => {
                        setQuery(term);
                        setParams({ q: term });
                      }}
                      className="rounded-full border border-border bg-card px-3.5 py-1 text-xs text-muted-foreground hover:border-primary hover:text-foreground transition-colors cursor-pointer"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Filter and Sort Bar */}
      <AnimatePresence>
        {initial && rawResults.length > 0 && (
          <motion.section
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="mt-8 pt-4 border-t border-border/40"
          >
            <div className="flex flex-wrap items-center justify-between gap-4">
              {/* Dynamic Genre Chips */}
              <div className="flex flex-wrap gap-2">
                {availableGenres.map((genre) => {
                  const active = activeGenres.includes(genre);
                  return (
                    <button
                      key={genre}
                      type="button"
                      onClick={() => toggleGenre(genre)}
                      className={`rounded-full border px-3 py-1 text-xs font-medium transition-all cursor-pointer ${
                        active
                          ? "border-primary bg-primary/20 text-primary font-bold shadow-sm"
                          : "border-border bg-card text-muted-foreground hover:border-primary/60 hover:text-foreground"
                      }`}
                    >
                      {active && <span className="mr-1">✓</span>}
                      {genre}
                    </button>
                  );
                })}
              </div>

              {/* Sort Menu */}
              <div className="flex shrink-0 items-center gap-2">
                {hasFilters && (
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground hover:border-red-500/60 hover:text-red-400 transition-colors cursor-pointer"
                  >
                    <X size={12} weight="bold" />
                    Reset
                  </button>
                )}
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowSortMenu((v) => !v)}
                    className="flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-foreground hover:border-primary transition-colors cursor-pointer"
                  >
                    <SortAscending size={14} weight="bold" />
                    {sortLabels[sort]}
                  </button>
                  {showSortMenu && (
                    <div className="absolute right-0 top-full z-30 mt-2 w-40 overflow-hidden rounded-xl border border-border bg-card/95 py-1 shadow-xl backdrop-blur-xl">
                      {(Object.entries(sortLabels) as [SortOption, string][]).map(([key, label]) => (
                        <button
                          key={key}
                          type="button"
                          onClick={() => {
                            setSort(key);
                            setShowSortMenu(false);
                          }}
                          className={`w-full px-4 py-2 text-left text-xs transition-colors cursor-pointer ${
                            sort === key
                              ? "bg-primary/10 text-primary font-bold"
                              : "text-foreground hover:bg-card/80 hover:text-primary"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <p className="mt-3 text-xs text-muted-foreground">
              Showing {results.length} of {rawResults.length} catalog results for "
              <span className="text-foreground font-semibold">{initial}</span>"
            </p>
          </motion.section>
        )}
      </AnimatePresence>

      {/* Results Grid */}
      <section className="mt-8">
        {loading ? (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4 xl:grid-cols-6">
            {Array.from({ length: 12 }).map((_, index) => (
              <LoadingSkeleton key={index} className="aspect-[2/3] w-full" />
            ))}
          </div>
        ) : results.length > 0 ? (
          <motion.div
            layout
            className="grid grid-cols-2 gap-5 md:grid-cols-4 xl:grid-cols-6"
          >
            <AnimatePresence mode="popLayout">
              {results.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.2 }}
                >
                  <PosterCard
                    item={item}
                    inList={myList.includes(item.id)}
                    onToggleList={onToggleList}
                    onPlayTrailer={(m) => setSelectedTrailer(m)}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        ) : initial ? (
          <EmptyState
            title={`No catalog results for "${initial}"`}
            description="No matching movies were found in the current 3,560-title master catalog. Try another actor, director, or genre."
          />
        ) : (
          <EmptyState
            title="Search Cinevora's 3,560 Master Catalog Titles"
            description="Try searching for 'Vijay', 'Tamil action movies', 'Lokesh Kanagaraj', 'Interstellar', or 'Sci-Fi'."
          />
        )}
      </section>

      {/* Trailer Modal */}
      {selectedTrailer && (
        <TrailerModal
          open={Boolean(selectedTrailer)}
          title={selectedTrailer.title}
          movieId={selectedTrailer.id}
          trailerUrl={selectedTrailer.trailerUrl}
          onClose={() => setSelectedTrailer(null)}
        />
      )}
    </PageContainer>
  );
};
