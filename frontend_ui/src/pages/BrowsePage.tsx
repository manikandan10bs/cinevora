import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ContentItem } from "@/data/mockContent";
import { PageContainer } from "@/components/layout/PageContainer";
import { QuickFilterChips } from "@/components/browse/QuickFilterChips";
import { PosterCard } from "@/components/content/PosterCard";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { SectionHeader } from "@/components/common/SectionHeader";
import { TrailerModal } from "@/components/common/TrailerModal";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { cinevoraApi } from "@/lib/cinevoraClient";

type BrowsePageProps = {
  myList: string[];
  onToggleList: (id: string) => void;
};

const industryChips = ["All", "Tamil", "Bollywood", "Telugu", "Malayalam", "Kannada", "Hollywood"];

const genres = [
  "All",
  "Action",
  "Adventure",
  "Comedy",
  "Crime",
  "Drama",
  "Horror",
  "Mystery",
  "Romance",
  "Sci-Fi",
  "Thriller",
];

export const BrowsePage = ({ myList, onToggleList }: BrowsePageProps) => {
  useDocumentMeta(
    "Browse Catalog | Cinevora",
    "Filter and explore Cinevora's 3,560 verified movie catalog across Indian cinema and Hollywood."
  );

  const location = useLocation();
  const navigate = useNavigate();

  const queryIndustry = new URLSearchParams(location.search).get("industry") || "All";
  const [activeIndustry, setActiveIndustry] = useState(queryIndustry);
  const [activeGenre, setActiveGenre] = useState("All");
  const [sortBy, setSortBy] = useState("rating");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(24);

  const [items, setItems] = useState<ContentItem[]>([]);
  const [totalCount, setTotalCount] = useState(3560);
  const [totalPages, setTotalPages] = useState(149);
  const [loading, setLoading] = useState(true);
  const [selectedTrailer, setSelectedTrailer] = useState<ContentItem | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadCatalog() {
      try {
        setLoading(true);
        const data = await cinevoraApi.getMasterCatalog({
          page,
          page_size: pageSize,
          industry: activeIndustry === "All" ? undefined : activeIndustry,
          genre: activeGenre === "All" ? undefined : activeGenre,
          sort_by: sortBy,
        });

        if (isMounted) {
          setItems(data.items);
          setTotalCount(data.total);
          setTotalPages(data.total_pages);
        }
      } catch (err) {
        console.warn("Catalog fetch error:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadCatalog();
    return () => {
      isMounted = false;
    };
  }, [activeIndustry, activeGenre, sortBy, page, pageSize]);

  const handleIndustryChange = (ind: string) => {
    setActiveIndustry(ind);
    setPage(1);
    navigate(ind === "All" ? "/browse" : `/browse?industry=${encodeURIComponent(ind)}`, {
      replace: true,
    });
  };

  const handleGenreChange = (g: string) => {
    setActiveGenre(g);
    setPage(1);
  };

  const resetFilters = () => {
    setActiveIndustry("All");
    setActiveGenre("All");
    setSortBy("rating");
    setPage(1);
    navigate("/browse", { replace: true });
  };

  const hasActiveFilters = activeIndustry !== "All" || activeGenre !== "All" || sortBy !== "rating";

  return (
    <PageContainer className="pt-32 pb-16 space-y-6">
      <SectionHeader
        title="Master Catalog"
        subtitle={`${totalCount.toLocaleString()} verified cinema titles · Page ${page} of ${totalPages}`}
        action={
          hasActiveFilters ? (
            <button
              type="button"
              onClick={resetFilters}
              className="rounded-lg border border-border bg-card px-4 py-2 text-xs font-semibold text-muted-foreground hover:border-red-500 hover:text-red-400 transition-colors cursor-pointer"
            >
              Reset Filters
            </button>
          ) : undefined
        }
      />

      {/* Industry Filter Chips */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Cinema Region & Industry
        </p>
        <QuickFilterChips
          filters={industryChips}
          active={activeIndustry}
          onChange={handleIndustryChange}
        />
      </div>

      {/* Genre Filter & Sort Row */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
        <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
          <span className="text-xs font-semibold text-muted-foreground mr-1">Genres:</span>
          {genres.map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => handleGenreChange(g)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
                activeGenre === g
                  ? "border-primary bg-primary/20 text-primary font-bold shadow-sm"
                  : "border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-foreground"
              }`}
            >
              {g}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            className="rounded-xl border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground focus:outline-none focus:border-primary cursor-pointer"
          >
            <option value="rating">Top Rated</option>
            <option value="popularity">Popularity</option>
            <option value="latest">Newest First</option>
            <option value="title">A–Z</option>
          </select>
        </div>
      </div>

      {/* Catalog Grid */}
      <section className="pt-2">
        {loading ? (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4 xl:grid-cols-6">
            {Array.from({ length: 12 }).map((_, index) => (
              <LoadingSkeleton key={index} className="aspect-[2/3] w-full" />
            ))}
          </div>
        ) : items.length > 0 ? (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4 xl:grid-cols-6">
            {items.map((item) => (
              <PosterCard
                key={`cat-${item.id}`}
                item={item}
                inList={myList.includes(item.id)}
                onToggleList={onToggleList}
                onPlayTrailer={(m) => setSelectedTrailer(m)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No movies found in this category"
            description="Try clearing some filters or selecting another cinema industry."
          />
        )}
      </section>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-8 pb-4">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page <= 1 || loading}
            className="rounded-xl border border-border bg-card px-5 py-2 text-xs font-semibold text-foreground hover:border-primary hover:text-primary transition-all disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="text-xs font-mono text-muted-foreground px-2">
            Page <span className="font-bold text-foreground">{page}</span> of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page >= totalPages || loading}
            className="rounded-xl border border-border bg-card px-5 py-2 text-xs font-semibold text-foreground hover:border-primary hover:text-primary transition-all disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}

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
