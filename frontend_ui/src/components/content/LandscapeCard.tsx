import { Link } from "react-router-dom";
import { Play, Clock, CheckCircle } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { ContentItem } from "@/data/mockContent";
import { getWatchProgress } from "@/lib/storage";

type LandscapeCardProps = {
  item: ContentItem;
  progress?: number;
  /** Duration seconds for "X min left" display — overridden by storage if available */
  durationSeconds?: number;
  /** Optional episode title for continue watching label */
  episodeTitle?: string;
};

export const LandscapeCard = ({ item, progress = 0, durationSeconds, episodeTitle }: LandscapeCardProps) => {
  const href = `/watch/${item.id}`;

  // Prefer real storage data over passed prop
  const storedProgress = getWatchProgress()[item.id];
  const realProgress = storedProgress?.progress ?? progress;
  const realDuration = storedProgress?.duration ?? durationSeconds ?? 0;
  const pct = Math.round(Math.min(Math.max(realProgress, 0), 100));

  // Format seconds → "HH:MM:SS" or "MM:SS"
  const formatTime = (secs: number) => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    return `${m}:${String(s).padStart(2, "0")}`;
  };

  // Compute remaining seconds
  let timeLeftLabel = "";
  let timeLeftSecs = 0;
  if (realDuration > 0 && pct > 0 && pct < 100) {
    timeLeftSecs = Math.round(realDuration * (1 - pct / 100));
    const mins = Math.floor(timeLeftSecs / 60);
    const hrs = Math.floor(timeLeftSecs / 3600);
    if (hrs > 0) {
      const remMins = Math.floor((timeLeftSecs % 3600) / 60);
      timeLeftLabel = `${hrs}h ${remMins}m left`;
    } else if (mins > 0) {
      timeLeftLabel = `${mins}m left`;
    }
  }

  const isFinished = pct >= 98;

  return (
    <motion.div
      whileHover={{ scale: 1.015 }}
      transition={{ duration: 0.2 }}
      className="group overflow-hidden rounded-xl border border-border bg-card transition-all duration-300 hover:border-primary/50 card-glow"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video overflow-hidden bg-muted">
        <img
          src={item.backdropImage}
          alt={item.heroAlt}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-transparent" />

        {/* Play overlay */}
        <Link
          to={href}
          className="absolute inset-0 flex items-center justify-center"
          aria-label={`Play ${item.title}`}
          onClick={(e) => e.stopPropagation()}
        >
          <span className="flex h-14 w-14 items-center justify-center rounded-full border border-white/20 bg-background/50 text-white opacity-0 backdrop-blur-sm transition-all duration-300 group-hover:opacity-100 group-hover:scale-110">
            <Play size={22} weight="fill" />
          </span>
        </Link>

        {/* Bottom meta overlay */}
        <div className="absolute inset-x-0 bottom-0 p-3">
          <p className="truncate text-sm font-medium text-foreground drop-shadow">{item.title}</p>
          {episodeTitle && (
            <p className="truncate text-[11px] text-gray-300/80 drop-shadow">{episodeTitle}</p>
          )}
          <p className="mt-0.5 flex items-center gap-1 text-xs text-gray-300 drop-shadow">
            {isFinished ? (
              <>
                <CheckCircle size={11} weight="fill" className="shrink-0 text-success" />
                Watched
              </>
            ) : timeLeftLabel ? (
              <>
                <Clock size={11} weight="bold" className="shrink-0 text-primary" />
                {timeLeftLabel}
              </>
            ) : pct > 0 ? (
              <>
                <Clock size={11} weight="bold" className="shrink-0" />
                {pct}% watched
              </>
            ) : (
              item.duration
            )}
          </p>
        </div>
      </div>

      {/* Progress bar */}
      {pct > 0 && (
        <div className="h-1 bg-muted">
          <div
            className={`h-full transition-all duration-300 ${isFinished ? "bg-success/70" : "bg-gradient-primary"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-xs text-muted-foreground">{item.genres.slice(0, 2).join(" · ")}</span>
        <Link
          to={href}
          className="text-xs font-medium text-primary transition-colors hover:underline"
        >
          {isFinished ? "Watch Again" : pct > 0 ? "Resume" : "Watch"}
        </Link>
      </div>
    </motion.div>
  );
};
