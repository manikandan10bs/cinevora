import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  BookmarkSimple,
  Play,
  Star,
  VideoCamera,
  Heart,
  ArrowLeft,
  Sparkle,
  Television,
  ArrowSquareOut,
} from "@phosphor-icons/react";
import { PageContainer } from "@/components/layout/PageContainer";
import { ContentItem, contentItems } from "@/data/mockContent";
import { GenreChip } from "@/components/common/GenreChip";
import { SynopsisSection } from "@/components/details/SynopsisSection";
import { CastGrid } from "@/components/details/CastGrid";
import { PosterCard } from "@/components/content/PosterCard";
import { TrailerModal } from "@/components/common/TrailerModal";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { cinevoraApi, getActiveUserId, StreamingSource } from "@/lib/cinevoraClient";
import { toast } from "@/hooks/use-toast";

type MovieDetailPageProps = {
  myList: string[];
  onToggleList: (id: string) => void;
};

export const MovieDetailPage = ({ myList, onToggleList }: MovieDetailPageProps) => {
  const { slug } = useParams<{ slug: string }>();
  const activeUser = getActiveUserId();

  const [movie, setMovie] = useState<ContentItem | null>(null);
  const [relatedMovies, setRelatedMovies] = useState<ContentItem[]>([]);
  const [streamingSources, setStreamingSources] = useState<StreamingSource[]>([]);
  const [trailerOpen, setTrailerOpen] = useState(false);
  const [liked, setLiked] = useState(false);
  const [loading, setLoading] = useState(true);

  // Dynamic document title
  useDocumentMeta(
    movie ? `${movie.title} | Cinevora` : "Movie Details | Cinevora",
    movie?.description || "Curated cinema from Cinevora master catalog."
  );

  useEffect(() => {
    let isMounted = true;
    async function loadMovieAndRelated() {
      if (!slug) return;
      try {
        setLoading(true);

        // Fetch streaming availability via WatchMode
        cinevoraApi.getMovieStreamingSources(slug).then((res) => {
          if (isMounted && res?.sources?.length > 0) {
            setStreamingSources(res.sources);
          }
        }).catch(() => {});

        // 1. Fetch movie details from FastAPI backend
        let item = await cinevoraApi.getMovieDetails(slug);

        // Fallback to local mock content if backend lookup returns null
        if (!item) {
          item =
            contentItems.find(
              (entry) =>
                entry.id.toLowerCase() === slug.toLowerCase() ||
                entry.slug.toLowerCase() === slug.toLowerCase()
            ) || contentItems[0];
        }

        if (isMounted && item) {
          setMovie(item);

          // 2. Track user viewing interaction in SQLite
          cinevoraApi.recordView(activeUser, item.id, item.title, 180);

          // 3. Check if movie is liked in SQLite
          const likes = await cinevoraApi.getUserLikes(activeUser);
          if (isMounted) {
            setLiked(likes.includes(item.id));
          }

          // 4. Fetch 4 related movies sharing the exact primary genre
          const primaryGenre = item.genres[0] || "Action";
          const related = await cinevoraApi.getSameGenreMovies(item.id, primaryGenre, 4);
          if (isMounted) {
            setRelatedMovies(related);
          }
        }
      } catch (err) {
        console.warn("Movie detail loading error:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadMovieAndRelated();
    return () => {
      isMounted = false;
    };
  }, [slug, activeUser]);

  if (!movie) {
    return (
      <PageContainer className="pt-32 pb-20 text-center">
        <div className="flex flex-col items-center justify-center gap-4 py-20">
          <div className="h-12 w-12 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-muted-foreground text-sm">Loading Cinevora movie details...</p>
        </div>
      </PageContainer>
    );
  }

  const inList = myList.includes(movie.id);

  const handleToggleLike = async () => {
    const nextState = !liked;
    setLiked(nextState);
    const success = await cinevoraApi.toggleLike(activeUser, movie.id);
    toast({
      title: success ? "Liked movie!" : "Unliked movie",
      description: movie.title,
      variant: success ? "success" : "default",
    });
  };

  return (
    <>
      {/* Hero Backdrop Spotlight */}
      <section className="relative min-h-[75vh] overflow-hidden pt-[72px]">
        <motion.img
          key={movie.id}
          initial={{ scale: 1.04, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          src={movie.backdropImage || movie.heroImage}
          alt={movie.heroAlt || movie.title}
          className="absolute inset-0 h-full w-full object-cover object-center"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1600";
          }}
        />
        <div className="absolute inset-0 bg-hero-overlay" />
        <div className="absolute inset-0 bg-gradient-to-r from-background/95 via-background/60 to-transparent" />

        <PageContainer className="relative flex min-h-[75vh] items-end py-16">
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55 }}
            className="flex flex-col gap-6 md:flex-row md:items-end md:gap-8"
          >
            {/* Poster Card */}
            <div className="hidden md:block w-48 shrink-0">
              <img
                src={movie.posterImage}
                alt={movie.posterAlt || movie.title}
                className="w-full rounded-2xl shadow-2xl ring-1 ring-white/10 aspect-[2/3] object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500";
                }}
              />
            </div>

            {/* Info Column */}
            <div className="max-w-2xl space-y-4">
              {/* Region and Verification Tags */}
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 rounded-full border border-primary/40 bg-primary/15 px-3 py-1 text-xs font-bold uppercase tracking-widest text-primary">
                  <Sparkle size={13} weight="fill" />
                  {movie.country || "Master Catalog"}
                </span>
                <span className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-white backdrop-blur-sm">
                  ID: {movie.id}
                </span>
              </div>

              <h1 className="text-4xl font-extrabold uppercase tracking-[0.05em] text-foreground sm:text-5xl md:text-6xl drop-shadow-md">
                {movie.title}
              </h1>

              {/* Meta row */}
              <div className="flex flex-wrap items-center gap-3 text-sm text-gray-200">
                <span className="flex items-center gap-1.5 font-bold text-warning">
                  <Star size={15} weight="fill" />
                  {movie.rating} / 10
                </span>
                <span className="text-gray-500">·</span>
                <span>{movie.year}</span>
                <span className="text-gray-500">·</span>
                <span>{movie.duration}</span>
                <span className="text-gray-500">·</span>
                <span className="font-semibold text-primary">{movie.country}</span>
              </div>

              {/* Genres */}
              <div className="flex flex-wrap gap-2">
                {movie.genres.map((genre) => (
                  <GenreChip key={genre} label={genre} />
                ))}
              </div>

              <p className="max-w-xl text-base leading-relaxed text-gray-200 md:text-lg">
                {movie.description}
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setTrailerOpen(true)}
                  className="inline-flex min-h-[50px] items-center gap-2.5 rounded-xl bg-gradient-primary px-7 py-3 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:scale-[1.03] hover:brightness-110 cursor-pointer"
                >
                  <Play size={18} weight="fill" />
                  Play Trailer
                </button>

                <button
                  type="button"
                  onClick={() => onToggleList(movie.id)}
                  className={`inline-flex min-h-[50px] items-center gap-2 rounded-xl border px-5 py-3 text-sm font-semibold transition-all cursor-pointer ${
                    inList
                      ? "border-primary bg-primary/20 text-primary"
                      : "border-border bg-card/80 text-foreground hover:border-primary hover:text-primary backdrop-blur-sm"
                  }`}
                >
                  <BookmarkSimple size={18} weight={inList ? "fill" : "bold"} />
                  {inList ? "Saved in Watchlist" : "Add to Watchlist"}
                </button>

                <button
                  type="button"
                  onClick={handleToggleLike}
                  className={`inline-flex min-h-[50px] items-center gap-2 rounded-xl border px-5 py-3 text-sm font-semibold transition-all cursor-pointer ${
                    liked
                      ? "border-rose-500 bg-rose-500/20 text-rose-400"
                      : "border-border bg-card/80 text-foreground hover:border-rose-500 hover:text-rose-400 backdrop-blur-sm"
                  }`}
                >
                  <Heart size={18} weight={liked ? "fill" : "bold"} />
                  {liked ? "Liked" : "Like"}
                </button>
              </div>

              {/* Streaming Providers via WatchMode */}
              {streamingSources.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 pt-2">
                  <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 mr-1">
                    <Television size={15} weight="bold" />
                    Available on:
                  </span>
                  {streamingSources.slice(0, 5).map((src, idx) => (
                    <a
                      key={`${src.name}-${idx}`}
                      href={src.web_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card/90 px-3 py-1.5 text-xs font-semibold text-foreground hover:border-primary hover:text-primary transition-all shadow-sm"
                    >
                      <ArrowSquareOut size={13} weight="bold" />
                      {src.name}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </PageContainer>
      </section>

      {/* Synopsis, Cast, and 4 Same-Genre Related Movies */}
      <PageContainer className="py-8 md:py-12 space-y-12">
        <SynopsisSection text={movie.longDescription || movie.description} />

        {movie.cast && movie.cast.length > 0 && <CastGrid cast={movie.cast} />}

        {/* 4 Related Movies from Same Genre with Chainable Navigation */}
        <section className="space-y-4 pt-4 border-t border-border/40">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl md:text-2xl font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
                🎬 Related {movie.genres[0] || "Cinema"} Movies
              </h2>
              <p className="text-xs md:text-sm text-muted-foreground mt-0.5">
                Top-rated films sharing the same genre. Click any card to explore its trailer & recommendations.
              </p>
            </div>
            <span className="text-xs font-semibold text-primary">
              {relatedMovies.length} verified titles
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 pt-2">
            {relatedMovies.map((related) => (
              <PosterCard
                key={`rel-${related.id}`}
                item={related}
                inList={myList.includes(related.id)}
                onToggleList={onToggleList}
                onPlayTrailer={(relItem) => {
                  setMovie(relItem);
                  setTrailerOpen(true);
                }}
              />
            ))}
          </div>
        </section>
      </PageContainer>

      {/* Trailer Modal */}
      <TrailerModal
        open={trailerOpen}
        title={movie.title}
        movieId={movie.id}
        trailerUrl={movie.trailerUrl}
        onClose={() => setTrailerOpen(false)}
      />
    </>
  );
};
