import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MagnifyingGlass, FilmStrip, Sparkle } from "@phosphor-icons/react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ContentItem } from "@/data/mockContent";
import { getSearchHistory, saveSearchTerm } from "@/lib/storage";
import { cinevoraApi } from "@/lib/cinevoraClient";

type CommandPaletteProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const popularKeywords = [
  "Vijay",
  "Action",
  "Lokesh Kanagaraj",
  "Christopher Nolan",
  "Interstellar",
  "Sci-Fi",
  "Horror",
  "Thriller",
  "Leo",
  "Tamil",
  "Bollywood",
];

export const CommandPalette = ({ open, onOpenChange }: CommandPaletteProps) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState<string[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    setRecent(getSearchHistory());
  }, [open]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        onOpenChange(!open);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onOpenChange]);

  // Debounced search against Cinevora Master Catalog
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timeout = setTimeout(async () => {
      try {
        const hits = await cinevoraApi.searchMovies(query.trim(), { limit: 8 });
        setResults(hits);
      } catch (err) {
        console.warn("Command palette search error:", err);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timeout);
  }, [query]);

  const goToResult = (value: string, href?: string) => {
    const nextRecent = saveSearchTerm(value);
    setRecent(nextRecent);
    onOpenChange(false);
    if (href) {
      navigate(href);
    } else {
      navigate(`/search?q=${encodeURIComponent(value)}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && query.trim()) {
      goToResult(query.trim());
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-border bg-card text-card-foreground sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-left text-xl font-medium uppercase tracking-[0.1em] text-foreground flex items-center justify-between">
            <span>Quick Catalog Search</span>
            <span className="text-xs font-mono text-muted-foreground uppercase font-normal">
              3,560 Titles
            </span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="flex items-center gap-3 rounded-md border border-border bg-input px-4">
            <MagnifyingGlass
              size={24}
              weight="duotone"
              className={loading ? "animate-pulse text-primary" : "text-muted-foreground"}
            />
            <Input
              autoFocus
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search by actor (Vijay), director (Nolan), title, or genre..."
              className="border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus-visible:ring-0 text-base"
            />
            {loading && (
              <span className="text-xs text-primary font-mono animate-pulse">
                Searching...
              </span>
            )}
          </div>

          {!query.trim() ? (
            <div className="space-y-5">
              <div>
                <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Recent Searches
                </p>
                <div className="flex flex-wrap gap-2">
                  {recent.length > 0 ? (
                    recent.map((term) => (
                      <button
                        key={term}
                        type="button"
                        onClick={() => goToResult(term)}
                        className="rounded-full border border-border bg-muted/60 px-3 py-1.5 text-xs text-foreground transition-colors hover:border-primary hover:text-primary cursor-pointer"
                      >
                        {term}
                      </button>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      No recent searches recorded.
                    </p>
                  )}
                </div>
              </div>

              <div>
                <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Popular Keywords
                </p>
                <div className="flex flex-wrap gap-2">
                  {popularKeywords.map((term) => (
                    <button
                      key={term}
                      type="button"
                      onClick={() => goToResult(term)}
                      className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs text-primary transition-all hover:bg-primary/20 cursor-pointer"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <ul className="space-y-2 max-h-[360px] overflow-y-auto pr-1" aria-label="Search results">
              {results.length > 0 ? (
                results.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => goToResult(item.title, `/details/${item.id}`)}
                      className="flex w-full items-center gap-3 rounded-xl border border-border/80 bg-background/50 p-2.5 text-left transition-all hover:border-primary hover:bg-muted/40 cursor-pointer group"
                    >
                      <img
                        src={item.posterImage}
                        alt={item.posterAlt}
                        loading="lazy"
                        className="h-16 w-11 rounded-md object-cover border border-border/50 shrink-0"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                            {item.title}
                          </p>
                          <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">
                            ★ {item.rating}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">
                          {item.country} · {item.year} · {item.genres.join(", ")}
                        </p>
                      </div>
                      <FilmStrip
                        size={22}
                        weight="duotone"
                        className="text-muted-foreground group-hover:text-primary transition-colors shrink-0"
                      />
                    </button>
                  </li>
                ))
              ) : !loading ? (
                <li className="rounded-xl border border-border bg-background/50 p-8 text-center">
                  <p className="text-sm font-semibold text-foreground">
                    No matching cinema found for "{query}".
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Press Enter to view all fuzzy matches or try searching by actor or director.
                  </p>
                </li>
              ) : null}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
