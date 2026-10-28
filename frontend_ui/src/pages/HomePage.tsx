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
import { StreamingCard } from "@/components/content/StreamingCard";
import { PageContainer } from "@/components/layout/PageContainer";
import { TrailerModal } from "@/components/common/TrailerModal";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { cinevoraApi, getActiveUserId, StreamingMovie } from "@/lib/cinevoraClient";

type HomePageProps = {
  myList: string[];
  onToggleList: (id: string) => void;
  progressMap: Record<string, number>;
};

const initialStreamingMovies: StreamingMovie[] = [
  {
    movie_id: "CINEVORA-0001220",
    title: "Interstellar",
    release_year: "2014",
    genres: "Sci-Fi, Adventure, Drama",
    poster_url: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    backdrop_url: "https://image.tmdb.org/t/p/w1280/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
    rating: 8.7,
    trailer_url: "https://www.youtube.com/watch?v=LY19rHKAaAg",
    streaming_sources: [
      { name: "Prime Video", type: "sub", format: "4K", web_url: "https://www.primevideo.com" },
      { name: "Hotstar", type: "sub", format: "4K", web_url: "https://www.hotstar.com" },
      { name: "Apple TV", type: "rent", format: "4K", web_url: "https://tv.apple.com" }
    ]
  },
  {
    movie_id: "CINEVORA-0000001",
    title: "Inception",
    release_year: "2010",
    genres: "Action, Sci-Fi, Adventure",
    poster_url: "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
    backdrop_url: "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
    rating: 8.8,
    trailer_url: "https://www.youtube.com/watch?v=JE9z-gy4De4",
    streaming_sources: [
      { name: "Netflix", type: "sub", format: "HD", web_url: "https://www.netflix.com" },
      { name: "Prime Video", type: "sub", format: "HD", web_url: "https://www.primevideo.com" }
    ]
  },
  {
    movie_id: "CINEVORA-0000002",
    title: "The Dark Knight",
    release_year: "2008",
    genres: "Action, Crime, Drama",
    poster_url: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    backdrop_url: "https://image.tmdb.org/t/p/w1280/dqK9Hag1054tghRQSqLSfrkvQnA.jpg",
    rating: 9.0,
    trailer_url: "https://www.youtube.com/watch?v=EXeTwQWrcwY",
    streaming_sources: [
      { name: "Prime Video", type: "sub", format: "4K", web_url: "https://www.primevideo.com" },
      { name: "Netflix", type: "sub", format: "HD", web_url: "https://www.netflix.com" }
    ]
  },
  {
    movie_id: "CINEVORA-0000003",
    title: "Spider-Man: Across the Spider-Verse",
    release_year: "2023",
    genres: "Animation, Action, Adventure",
    poster_url: "https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
    backdrop_url: "https://image.tmdb.org/t/p/w1280/4HodYYKEIsGOdinkGi2Ucz6X9i0.jpg",
    rating: 8.6,
    trailer_url: "https://www.youtube.com/watch?v=cqGjhVJWtEg",
    streaming_sources: [
      { name: "Netflix", type: "sub", format: "4K", web_url: "https://www.netflix.com" },
      { name: "Prime Video", type: "rent", format: "4K", web_url: "https://www.primevideo.com" }
    ]
  },
  {
    movie_id: "CINEVORA-0000004",
    title: "Dune: Part Two",
    release_year: "2024",
    genres: "Sci-Fi, Adventure",
    poster_url: "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
    backdrop_url: "https://image.tmdb.org/t/p/w1280/xOMo8BRK7PfcJv9JCnx7s520035.jpg",
    rating: 8.5,
    trailer_url: "https://www.youtube.com/watch?v=Way9Dexny3w",
    streaming_sources: [
      { name: "Prime Video", type: "sub", format: "4K", web_url: "https://www.primevideo.com" },
      { name: "Apple TV", type: "rent", format: "4K", web_url: "https://tv.apple.com" }
    ]
  }
];

export const HomePage = ({ myList, onToggleList }: HomePageProps) => {
  useDocumentMeta(
    "Cinevora — Real-Time Movie Recommendation Service",
    "Discover personalized cinema, trending masterpieces, and Indian & Hollywood hits grounded in 3,560 verified titles."
  );

  const [featured, setFeatured] = useState<ContentItem[]>([]);
  const [recommended, setRecommended] = useState<ContentItem[]>(fallbackRecs);
  const [streamingMovies, setStreamingMovies] = useState<StreamingMovie[]>(initialStreamingMovies);
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

    // WatchMode Streaming Movies
    cinevoraApi.getAvailableStreamingMovies().then((streams) => {
      if (isMounted && streams.length > 0) setStreamingMovies(streams);
    }).catch((err) => console.warn("Streaming movies fallback:", err));

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
        {/* Recommended For You based on you liked and saved */}
        <ContentCarousel
          title="✨ Recommended For You based on you liked and saved"
          subtitle="Real-time personalized cinema picks tailored to your saves and liked titles."
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

        {/* Available for Streaming (WatchMode API Integration) */}
        {streamingMovies.length > 0 && (
          <ContentCarousel
            title="📺 Available for Streaming"
            subtitle="Stream right now on Netflix, Prime Video, Disney+, Apple TV & more via WatchMode."
          >
            {streamingMovies.map((item, index) => (
              <div
                key={`stream-${item.movie_id}-${index}`}
                className="w-[160px] shrink-0 md:w-[200px]"
                style={{ scrollSnapAlign: "start" }}
              >
                <StreamingCard
                  item={item}
                  onPlayTrailer={handlePlayTrailer}
                />
              </div>
            ))}
          </ContentCarousel>
        )}

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
