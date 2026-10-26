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
  const [recommended, setRecommended] = useState<ContentItem[]>([]);
  const [trending, setTrending] = useState<ContentItem[]>([]);
  const [indianCinema, setIndianCinema] = useState<ContentItem[]>([]);
  const [hollywood, setHollywood] = useState<ContentItem[]>([]);
  const [topRated, setTopRated] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Trailer modal state
  const [selectedTrailerMovie, setSelectedTrailerMovie] = useState<ContentItem | null>(null);

  const activeUser = getActiveUserId();

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const [feat, recs, trend, ind, hw, top] = await Promise.all([
          cinevoraApi.getFeaturedMovies(),
          cinevoraApi.getRecommendations(activeUser, "all", 10),
          cinevoraApi.searchMovies("", { limit: 10 }),
          cinevoraApi.searchMovies("", { cinema_region: "Indian", limit: 10 }),
          cinevoraApi.searchMovies("", { cinema_region: "Hollywood", limit: 10 }),
          cinevoraApi.getMasterCatalog({ sort_by: "rating", page_size: 10 }),
        ]);

        if (isMounted) {
          if (feat.length > 0) setFeatured(feat);
          setRecommended(recs.length > 0 ? recs : fallbackRecs);
          setTrending(trend.length > 0 ? trend : trendingNow);
          setIndianCinema(ind.length > 0 ? ind : moviesCollection);
          setHollywood(hw.length > 0 ? hw : trendingNow);
          setTopRated(top.items.length > 0 ? top.items : topTenToday);
        }
      } catch (err) {
        console.warn("Failed to fetch Cinevora homepage data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
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
