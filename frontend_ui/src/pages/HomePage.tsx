import { useEffect, useState } from "react";
import {
  ContentItem,
  topTenToday,
  trendingNow,
  recommendations as fallbackRecs,
  moviesCollection,
} from "@/data/mockContent";
import { HeroBanner } from "@/components/content/HeroBanner";
import { ContentCarousel } from "@/components/content/ContentCarousel";
import { PosterCard } from "@/components/content/PosterCard";
import { TopRankCard } from "@/components/content/TopRankCard";
import { PageContainer } from "@/components/layout/PageContainer";
import { TrailerModal } from "@/components/common/TrailerModal";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { cinevoraApi, getActiveUserId } from "@/lib/cinevoraClient";

type HomePageProps = {
  myList: string[];
  onToggleList: (id: string) => void;
  progressMap: Record<string, number>;
};

export const HomePage = ({ myList, onToggleList }: HomePageProps) => {
  useDocumentMeta(
    "Cinevora — Real-Time Movie Recommendation Service",
    "Discover personalized cinema, trending masterpieces, and Indian & Hollywood hits grounded in 3,560 verified titles."
  );

  const [featured, setFeatured] = useState<ContentItem[]>([]);
  const [recommended, setRecommended] = useState<ContentItem[]>(fallbackRecs);
  const [trending, setTrending] = useState<ContentItem[]>(trendingNow);
  const [indianCinema, setIndianCinema] = useState<ContentItem[]>(moviesCollection);
  const [hollywood, setHollywood] = useState<ContentItem[]>(trendingNow);
  const [topRated, setTopRated] = useState<ContentItem[]>(topTenToday);
  const [loading, setLoading] = useState(false);
  const [isBackendConnecting, setIsBackendConnecting] = useState(false);

  // Trailer modal state
  const [selectedTrailerMovie, setSelectedTrailerMovie] = useState<ContentItem | null>(null);

  const activeUser = getActiveUserId();

  useEffect(() => {
    let isMounted = true;

    // Check health / wake-up status
    cinevoraApi.getHealth().then(() => {
      if (isMounted) setIsBackendConnecting(false);
    }).catch(() => {
      if (isMounted) setIsBackendConnecting(true);
    });

    // Load each section independently so slow endpoints don't block the page
    cinevoraApi.getFeaturedMovies().then((feat) => {
      if (isMounted && feat.length > 0) setFeatured(feat);
    }).catch((err) => console.warn("Featured movies fallback:", err));

    cinevoraApi.getRecommendations(activeUser, "all", 10).then((recs) => {
      if (isMounted && recs.length > 0) setRecommended(recs);
    }).catch((err) => console.warn("Recommendations fallback:", err));

    cinevoraApi.searchMovies("", { limit: 10 }).then((trend) => {
      if (isMounted && trend.length > 0) setTrending(trend);
    }).catch((err) => console.warn("Trending fallback:", err));

    cinevoraApi.searchMovies("", { cinema_region: "Indian", limit: 10 }).then((ind) => {
      if (isMounted && ind.length > 0) setIndianCinema(ind);
    }).catch((err) => console.warn("Indian cinema fallback:", err));

    cinevoraApi.searchMovies("", { cinema_region: "Hollywood", limit: 10 }).then((hw) => {
      if (isMounted && hw.length > 0) setHollywood(hw);
    }).catch((err) => console.warn("Hollywood fallback:", err));

    cinevoraApi.getMasterCatalog({ sort_by: "rating", page_size: 10 }).then((top) => {
      if (isMounted && top.items.length > 0) setTopRated(top.items);
    }).catch((err) => console.warn("Master catalog fallback:", err));

    return () => {
      isMounted = false;
    };
  }, [activeUser]);

  const handlePlayTrailer = (movie: ContentItem) => {
    setSelectedTrailerMovie(movie);
  };

  return (
    <>
      {/* Dynamic Rotating Hero Banner */}
      <HeroBanner items={featured} onPlayTrailer={handlePlayTrailer} />

      <PageContainer className="py-8 md:py-12 space-y-6">
        {isBackendConnecting && (
          <div className="flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 px-4 py-2.5 text-xs text-primary backdrop-blur-sm animate-pulse">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            <span>Connecting to Cinevora live cloud backend on Render (waking from sleep mode)...</span>
          </div>
        )}
        {/* Recommended For You (Personalized from SQLite Interactions) */}
        <ContentCarousel
          title="✨ Recommended For You"
          subtitle="Real-time personalized picks tailored to your viewing and likes profile."
        >
          {recommended.map((item, index) => (
            <div
              key={`rec-${item.id}-${index}`}
              className="w-[160px] shrink-0 md:w-[200px]"
              style={{ scrollSnapAlign: "start" }}
            >
              <PosterCard
                item={item}
                inList={myList.includes(item.id)}
                onToggleList={onToggleList}
                onPlayTrailer={handlePlayTrailer}
              />
            </div>
          ))}
        </ContentCarousel>

        {/* Top 10 Rated Masterpieces */}
        <ContentCarousel
          title="🔥 Top 10 Masterpieces"
          subtitle="Highest-rated cinema titles across Cinevora's 3,560-movie catalog."
        >
          {topRated.map((item, index) => (
            <div
              key={`top-${item.id}-${index}`}
              className="shrink-0"
              style={{ scrollSnapAlign: "start" }}
            >
              <TopRankCard item={item} rank={index + 1} />
            </div>
          ))}
        </ContentCarousel>

        {/* Trending Now */}
        <ContentCarousel
          title="🍿 Trending on Cinevora"
          subtitle="High-velocity films experiencing strong viewer engagement right now."
        >
          {trending.map((item, index) => (
            <div
              key={`tr-${item.id}-${index}`}
              className="w-[160px] shrink-0 md:w-[200px]"
              style={{ scrollSnapAlign: "start" }}
            >
              <PosterCard
                item={item}
                inList={myList.includes(item.id)}
                onToggleList={onToggleList}
                onPlayTrailer={handlePlayTrailer}
              />
            </div>
          ))}
        </ContentCarousel>

        {/* Indian Cinema Spotlight */}
        <ContentCarousel
          title="🇮🇳 Indian Cinema Spotlight"
          subtitle="Blockbusters across Kollywood, Bollywood, Tollywood, Mollywood, and Sandalwood."
        >
          {indianCinema.map((item, index) => (
            <div
              key={`ind-${item.id}-${index}`}
              className="w-[160px] shrink-0 md:w-[200px]"
              style={{ scrollSnapAlign: "start" }}
            >
              <PosterCard
                item={item}
                inList={myList.includes(item.id)}
                onToggleList={onToggleList}
                onPlayTrailer={handlePlayTrailer}
              />
            </div>
          ))}
        </ContentCarousel>

        {/* Hollywood Hits */}
        <ContentCarousel
          title="🎬 Hollywood & International"
          subtitle="Acclaimed science fiction, thrillers, and dramas."
        >
          {hollywood.map((item, index) => (
            <div
              key={`hw-${item.id}-${index}`}
              className="w-[160px] shrink-0 md:w-[200px]"
              style={{ scrollSnapAlign: "start" }}
            >
              <PosterCard
                item={item}
                inList={myList.includes(item.id)}
                onToggleList={onToggleList}
                onPlayTrailer={handlePlayTrailer}
              />
            </div>
          ))}
        </ContentCarousel>
      </PageContainer>

      {/* Global Trailer Modal */}
      {selectedTrailerMovie && (
        <TrailerModal
          open={Boolean(selectedTrailerMovie)}
          title={selectedTrailerMovie.title}
          movieId={selectedTrailerMovie.id}
          trailerUrl={selectedTrailerMovie.trailerUrl}
          onClose={() => setSelectedTrailerMovie(null)}
        />
      )}
    </>
  );
};
