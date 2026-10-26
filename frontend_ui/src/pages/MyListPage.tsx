import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { BookmarkSimple, ClockCounterClockwise, Heart, Play } from "@phosphor-icons/react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { PageContainer } from "@/components/layout/PageContainer";
import { ContentItem, contentItems } from "@/data/mockContent";
import { PosterCard } from "@/components/content/PosterCard";
import { LandscapeCard } from "@/components/content/LandscapeCard";
import { EmptyState } from "@/components/common/EmptyState";
import { TrailerModal } from "@/components/common/TrailerModal";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { getWatchProgress } from "@/lib/storage";
import { cinevoraApi, getActiveUserId } from "@/lib/cinevoraClient";

type MyListPageProps = {
  myList: string[];
  onToggleList: (id: string) => void;
  progressMap: Record<string, number>;
};

export const MyListPage = ({ myList, onToggleList, progressMap }: MyListPageProps) => {
  useDocumentMeta(
    "My List & Watchlist | Cinevora",
    "Manage your persistent Cinevora watchlist, liked movies, and continue watching queue."
  );

  const [tab, setTab] = useState("favorites");
  const [dbFavorites, setDbFavorites] = useState<ContentItem[]>([]);
  const [likedMovies, setLikedMovies] = useState<ContentItem[]>([]);
  const [selectedTrailer, setSelectedTrailer] = useState<ContentItem | null>(null);

  const activeUser = getActiveUserId();

  useEffect(() => {
    let isMounted = true;
    async function loadUserData() {
      try {
        const [favs, likedIds] = await Promise.all([
          cinevoraApi.getUserFavorites(activeUser),
          cinevoraApi.getUserLikes(activeUser),
        ]);

        if (isMounted) {
          setDbFavorites(favs);

          // Resolve liked movie records if possible
          if (likedIds.length > 0) {
            const likedDetails = await Promise.all(
              likedIds.slice(0, 18).map((id) => cinevoraApi.getMovieDetails(id))
            );
            setLikedMovies(likedDetails.filter(Boolean) as ContentItem[]);
          } else {
            setLikedMovies([]);
          }
        }
      } catch (err) {
        console.warn("MyList load error:", err);
      }
    }

    loadUserData();
    return () => {
      isMounted = false;
    };
  }, [activeUser, myList]);

  // Combined favorites from SQLite + local state
  const allFavorites = useMemo(() => {
    const map = new Map<string, ContentItem>();
    dbFavorites.forEach((m) => map.set(m.id, m));
    contentItems
      .filter((item) => myList.includes(item.id))
      .forEach((m) => map.set(m.id, m));
    return Array.from(map.values());
  }, [dbFavorites, myList]);

  const progressData = getWatchProgress();

  const continueWatching = useMemo(
    () =>
      contentItems
        .filter((item) => (progressMap[item.id] ?? 0) > 0 && (progressMap[item.id] ?? 0) < 98)
        .sort((a, b) => {
          const pa = progressData[a.id];
          const pb = progressData[b.id];
          return (pb?.updatedAt ?? 0) - (pa?.updatedAt ?? 0);
        }),
    [progressMap, progressData]
  );

  return (
    <PageContainer className="pt-32 pb-16">
      <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold uppercase tracking-[0.08em] text-foreground">
            My Cinevora List
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Personal cinema hub synced with your SQLite account:{" "}
            <span className="text-primary font-mono">{activeUser}</span>
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          {allFavorites.length} saved · {likedMovies.length} liked · {continueWatching.length} in progress
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-8 grid w-full max-w-xl grid-cols-3 bg-card border border-border">
          <TabsTrigger value="favorites" className="text-foreground flex items-center gap-2">
            <BookmarkSimple size={15} weight="bold" />
            Watchlist
            {allFavorites.length > 0 && (
              <span className="ml-1 rounded-full bg-primary/20 px-1.5 py-0.5 text-[10px] font-bold text-primary">
                {allFavorites.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="likes" className="text-foreground flex items-center gap-2">
            <Heart size={15} weight="bold" />
            Liked
            {likedMovies.length > 0 && (
              <span className="ml-1 rounded-full bg-rose-500/20 px-1.5 py-0.5 text-[10px] font-bold text-rose-400">
                {likedMovies.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="continue" className="text-foreground flex items-center gap-2">
            <ClockCounterClockwise size={15} weight="bold" />
            Continue
            {continueWatching.length > 0 && (
              <span className="ml-1 rounded-full bg-primary/20 px-1.5 py-0.5 text-[10px] font-bold text-primary">
                {continueWatching.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Watchlist Tab */}
        <TabsContent value="favorites">
          {allFavorites.length > 0 ? (
            <div className="grid grid-cols-2 gap-5 md:grid-cols-4 xl:grid-cols-6">
              {allFavorites.map((item) => (
                <PosterCard
                  key={`fav-${item.id}`}
                  item={item}
                  inList={true}
                  onToggleList={onToggleList}
                  onPlayTrailer={(m) => setSelectedTrailer(m)}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Your Watchlist is empty"
              description="Explore the home page or search the catalog and click the Bookmark button to save titles to your list."
            />
          )}
        </TabsContent>

        {/* Liked Movies Tab */}
        <TabsContent value="likes">
          {likedMovies.length > 0 ? (
            <div className="grid grid-cols-2 gap-5 md:grid-cols-4 xl:grid-cols-6">
              {likedMovies.map((item) => (
                <PosterCard
                  key={`like-${item.id}`}
                  item={item}
                  inList={myList.includes(item.id)}
                  onToggleList={onToggleList}
                  onPlayTrailer={(m) => setSelectedTrailer(m)}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No liked movies yet"
              description="Click the Heart button on any movie details page to save your favorite movies and train your personalized recommender."
            />
          )}
        </TabsContent>

        {/* Continue Watching Tab */}
        <TabsContent value="continue">
          {continueWatching.length > 0 ? (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
              {continueWatching.map((item) => (
                <LandscapeCard
                  key={`cont-${item.id}`}
                  item={item}
                  progress={progressMap[item.id] ?? 45}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Nothing in progress"
              description="Movies and series you begin watching will appear here with your playback progress."
            />
          )}
        </TabsContent>
      </Tabs>

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
