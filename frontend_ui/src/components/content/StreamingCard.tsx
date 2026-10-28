import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Play, Star, ArrowSquareOut, Television } from "@phosphor-icons/react";
import { StreamingMovie } from "@/lib/cinevoraClient";
import { ContentItem } from "@/data/mockContent";

type StreamingCardProps = {
  item: StreamingMovie;
  onPlayTrailer?: (item: ContentItem) => void;
};

// Platform-specific brand accents
const getProviderStyle = (name: string) => {
  const n = name.toLowerCase();
  if (n.includes("netflix")) return "bg-red-600/90 hover:bg-red-600 text-white border-red-500/30";
  if (n.includes("prime") || n.includes("amazon")) return "bg-sky-600/90 hover:bg-sky-600 text-white border-sky-400/30";
  if (n.includes("disney") || n.includes("hotstar")) return "bg-indigo-700/90 hover:bg-indigo-700 text-white border-indigo-400/30";
  if (n.includes("apple")) return "bg-zinc-800/90 hover:bg-zinc-700 text-white border-zinc-500/30";
  if (n.includes("hbo") || n.includes("max")) return "bg-purple-700/90 hover:bg-purple-700 text-white border-purple-400/30";
  if (n.includes("hulu")) return "bg-emerald-600/90 hover:bg-emerald-600 text-white border-emerald-400/30";
  return "bg-primary/90 hover:bg-primary text-primary-foreground border-primary/30";
};

export const StreamingCard = ({ item, onPlayTrailer }: StreamingCardProps) => {
  const href = `/movie/${item.movie_id}`;
  const posterUrl =
    item.poster_url ||
    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500";

  const primarySource = item.streaming_sources?.[0];

  const handleTrailer = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onPlayTrailer) {
      onPlayTrailer({
        id: item.movie_id,
        slug: item.movie_id.toLowerCase(),
        title: item.title,
        description: `Streaming available on ${item.streaming_sources?.map((s) => s.name).join(", ") || "major platforms"}.`,
        posterImage: posterUrl,
        backdropImage: item.backdrop_url || posterUrl,
        year: parseInt(item.release_year || "2024", 10),
        category: "Movies",
        genre: item.genres?.split(",") || ["Cinema"],
        rating: (item.rating || 8.0).toFixed(1),
        duration: "Movie",
        featured: false,
        trailerUrl: item.trailer_url,
      });
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.04 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="group relative flex flex-col"
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] overflow-hidden rounded-xl bg-muted card-glow transition-shadow duration-300">
        <Link to={href} className="block h-full w-full">
          <img
            src={posterUrl}
            alt={item.title}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500";
            }}
          />
        </Link>

        {/* Live Streaming Badge */}
        <div className="pointer-events-none absolute left-2.5 top-2.5 flex items-center gap-1.5 rounded-md bg-black/75 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-400 backdrop-blur-md border border-emerald-500/30">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <Television size={12} weight="bold" />
          Stream
        </div>

        {/* Dark overlay on hover */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/95 via-background/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

        {/* Hover Action Buttons */}
        <div className="absolute inset-x-0 bottom-0 flex translate-y-3 flex-col gap-1.5 p-2.5 opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100 z-10">
          {primarySource && (
            <a
              href={primarySource.web_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-bold transition-all shadow-md border ${getProviderStyle(
                primarySource.name
              )}`}
            >
              <ArrowSquareOut size={14} weight="bold" />
              Watch on {primarySource.name}
            </a>
          )}

          <button
            type="button"
            onClick={handleTrailer}
            className="flex items-center justify-center gap-1.5 rounded-lg border border-border/80 bg-background/80 py-1.5 text-xs font-semibold text-foreground backdrop-blur-sm transition-colors hover:border-primary hover:text-primary cursor-pointer"
          >
            <Play size={13} weight="fill" />
            Trailer
          </button>
        </div>
      </div>

      {/* Info beneath poster */}
      <div className="mt-2 space-y-1">
        <Link to={href} className="block">
          <h4 className="truncate text-sm font-semibold text-foreground transition-colors hover:text-primary">
            {item.title}
          </h4>
        </Link>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{item.release_year || "Cinema"}</span>
          <div className="flex items-center gap-1 font-semibold text-amber-400">
            <Star size={12} weight="fill" />
            <span>{(item.rating || 8.0).toFixed(1)}</span>
          </div>
        </div>

        {/* Streaming Provider Pills */}
        <div className="flex flex-wrap items-center gap-1 pt-0.5">
          {item.streaming_sources?.slice(0, 2).map((src, idx) => (
            <a
              key={`${src.name}-${idx}`}
              href={src.web_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold border ${getProviderStyle(
                src.name
              )}`}
              title={`Stream on ${src.name} (${src.format || "HD"})`}
            >
              {src.name}
            </a>
          ))}
          {(item.streaming_sources?.length || 0) > 2 && (
            <span className="text-[10px] text-muted-foreground/80 font-mono">
              +{(item.streaming_sources?.length || 0) - 2} more
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
};
