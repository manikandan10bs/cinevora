import { Link } from "react-router-dom";
import { Play } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { Season } from "@/data/mockContent";
import { getWatchProgress } from "@/lib/storage";

export const EpisodeList = ({ season, contentId }: { season: Season; contentId: string }) => {
  const progress = getWatchProgress()[contentId]?.progress ?? 0;

  return (
    <section className="py-6 md:py-8">
      <h2 className="mb-5 text-2xl font-medium uppercase tracking-[0.12em] text-foreground">
        {season.name}
      </h2>
      <div className="space-y-3">
        {season.episodes.map((episode, index) => (
          <motion.div
            key={episode.id}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.06, duration: 0.35 }}
            className="group flex gap-4 rounded-xl border border-border bg-card p-3 transition-all duration-300 hover:border-primary/50 card-glow"
          >
            {/* Thumbnail */}
            <div className="relative aspect-video w-36 shrink-0 overflow-hidden rounded-lg bg-muted sm:w-44">
              <img
                src={episode.thumbnail}
                alt={episode.title}
                loading="lazy"
                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              {/* Progress indicator */}
              {index === 0 && progress > 0 && (
                <div className="absolute inset-x-0 bottom-0 h-1 bg-muted">
                  <div className="h-full bg-primary" style={{ width: `${progress}%` }} />
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex flex-1 flex-col justify-center gap-1.5 min-w-0">
              <p className="text-sm font-medium text-foreground">
                <span className="text-muted-foreground">{index + 1}. </span>{episode.title}
              </p>
              <p className="text-xs text-muted-foreground">{episode.duration}</p>
              <p className="line-clamp-2 text-xs text-muted-foreground">{episode.synopsis}</p>
            </div>

            {/* Action */}
            <div className="hidden shrink-0 items-center sm:flex">
              <Link
                to={`/watch/${contentId}?episode=${episode.id}`}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-primary text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:scale-110"
                aria-label={`Watch ${episode.title}`}
              >
                <Play size={16} weight="fill" />
              </Link>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
};
