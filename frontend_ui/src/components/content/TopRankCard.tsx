import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Star } from "@phosphor-icons/react";
import { ContentItem } from "@/data/mockContent";

type TopRankCardProps = {
  item: ContentItem;
  rank: number;
};

export const TopRankCard = ({ item, rank }: TopRankCardProps) => {
  const href = item.type === "movie" ? `/movie/${item.slug}` : `/series/${item.slug}`;
  const isTop3 = rank <= 3;

  return (
    <motion.div
      whileHover={{ scale: 1.03 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="group relative flex min-w-[220px] items-stretch overflow-hidden rounded-xl border border-border bg-card transition-all duration-300 hover:border-primary/50 card-glow"
    >
      {/* Rank */}
      <div className="flex w-14 shrink-0 items-end justify-center pb-3">
        <span
          className={`text-[3.5rem] font-black leading-none tracking-tighter ${isTop3 ? "text-gradient-primary" : "text-muted-foreground/40"}`}
        >
          {rank}
        </span>
      </div>

      {/* Poster */}
      <div className="relative my-3 aspect-[2/3] w-[72px] shrink-0 overflow-hidden rounded-lg">
        <img
          src={item.posterImage}
          alt={item.posterAlt}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
      </div>

      {/* Info */}
      <div className="flex flex-col justify-center gap-1.5 px-3 py-3">
        <Link
          to={href}
          className="line-clamp-2 text-sm font-medium text-foreground leading-snug transition-colors hover:text-primary"
        >
          {item.title}
        </Link>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Star size={10} weight="fill" className="text-warning" />
          <span>{item.rating}</span>
          <span>·</span>
          <span>{item.year}</span>
        </div>
        <p className="text-xs text-muted-foreground">{item.genres.slice(0, 2).join(" · ")}</p>
      </div>
    </motion.div>
  );
};
