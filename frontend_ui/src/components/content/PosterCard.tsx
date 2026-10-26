import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { BookmarkSimple, Play, Star, Info } from "@phosphor-icons/react";
import { ContentItem } from "@/data/mockContent";

type PosterCardProps = {
  item: ContentItem;
  inList: boolean;
  onToggleList: (id: string) => void;
  onPlayTrailer?: (item: ContentItem) => void;
};

const categoryColors: Record<string, string> = {
  Movies: "bg-cyan-500/80 text-white",
  Series: "bg-violet-500/80 text-white",
  Bollywood: "bg-amber-500/80 text-white",
  Kollywood: "bg-rose-500/80 text-white",
  Tollywood: "bg-orange-500/80 text-white",
  Mollywood: "bg-emerald-500/80 text-white",
  Hollywood: "bg-blue-500/80 text-white",
};

export const PosterCard = ({
  item,
  inList,
  onToggleList,
  onPlayTrailer,
}: PosterCardProps) => {
  const href = `/movie/${item.id}`;
  const categoryBadge = item.country || item.category || "Cinema";
  const badgeClass = categoryColors[categoryBadge] ?? "bg-card/80 text-foreground";

  return (
    <motion.div
      whileHover={{ scale: 1.04 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="group relative"
    >
      {/* Poster with Clickable Link */}
      <div className="relative aspect-[2/3] overflow-hidden rounded-xl bg-muted card-glow transition-shadow duration-300">
        <Link to={href} className="block h-full w-full">
          <img
            src={item.posterImage}
            alt={item.posterAlt || item.title}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500";
            }}
          />
        </Link>

        {/* Category / Region badge */}
        <span
          className={`pointer-events-none absolute left-2.5 top-2.5 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider backdrop-blur-sm ${badgeClass}`}
        >
          {categoryBadge}
        </span>

        {/* Dark overlay on hover */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/95 via-background/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

        {/* Hover actions */}
        <div className="absolute inset-x-0 bottom-0 flex translate-y-3 flex-col gap-2 p-3 opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100 z-10">
          {onPlayTrailer ? (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onPlayTrailer(item);
              }}
              className="flex min-h-[40px] items-center justify-center gap-2 rounded-lg bg-gradient-primary text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 shadow-lg shadow-primary/20"
            >
              <Play size={16} weight="fill" />
              Watch Trailer
            </button>
          ) : (
            <Link
              to={`/watch/${item.id}`}
              className="flex min-h-[40px] items-center justify-center gap-2 rounded-lg bg-gradient-primary text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 shadow-lg shadow-primary/20"
              onClick={(e) => e.stopPropagation()}
            >
              <Play size={16} weight="fill" />
              Play
            </Link>
          )}

          <div className="flex gap-2">
            <Link
              to={href}
              className="flex flex-1 min-h-[36px] items-center justify-center gap-1 rounded-lg bg-card/90 text-xs font-medium text-foreground backdrop-blur-sm transition-all hover:bg-primary/20 hover:text-primary border border-border"
              onClick={(e) => e.stopPropagation()}
            >
              <Info size={14} weight="bold" />
              Details
            </Link>
            <button
              type="button"
              aria-label={inList ? "Remove from Watchlist" : "Add to Watchlist"}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onToggleList(item.id);
              }}
              className={`inline-flex min-h-[36px] min-w-[36px] items-center justify-center rounded-lg text-sm font-medium transition-all ${
                inList
                  ? "bg-primary/30 text-primary ring-1 ring-primary"
                  : "bg-card/90 text-foreground backdrop-blur-sm hover:bg-primary/20 hover:text-primary border border-border"
              }`}
            >
              <BookmarkSimple size={16} weight={inList ? "fill" : "bold"} />
            </button>
          </div>
        </div>
      </div>

      {/* Title & Metadata */}
      <div className="mt-3 space-y-1 px-0.5">
        <Link
          to={href}
          className="block truncate text-sm font-medium text-foreground transition-colors hover:text-primary"
          title={item.title}
        >
          {item.title}
        </Link>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Star size={11} weight="fill" className="shrink-0 text-warning" />
          <span className="font-semibold text-foreground">{item.rating}</span>
          <span>·</span>
          <span>{item.year}</span>
          <span>·</span>
          <span className="truncate">{item.genres[0]}</span>
        </div>
      </div>
    </motion.div>
  );
};
