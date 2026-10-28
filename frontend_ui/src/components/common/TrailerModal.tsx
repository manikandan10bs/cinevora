import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Play, ArrowSquareOut, Sparkle, CircleNotch, Copy, Check, FilmStrip } from "@phosphor-icons/react";
import { getEmbedTrailerUrl, cinevoraApi } from "@/lib/cinevoraClient";

type TrailerModalProps = {
  open: boolean;
  title: string;
  movieId?: string;
  trailerUrl?: string;
  onClose: () => void;
};

export const TrailerModal = ({ open, title, movieId, trailerUrl, onClose }: TrailerModalProps) => {
  const [activeUrl, setActiveUrl] = useState<string | undefined>(trailerUrl);
  const [resolving, setResolving] = useState(false);
  const [source, setSource] = useState<string>("catalog");
  const [copied, setCopied] = useState<boolean>(false);

  const resolveTrailer = (targetMovieId: string) => {
    setResolving(true);
    setCopied(false);

    cinevoraApi
      .getExactTrailerUrl(targetMovieId)
      .then((data) => {
        if (data?.trailer_url && getEmbedTrailerUrl(data.trailer_url)) {
          setActiveUrl(data.trailer_url);
          setSource(data.source || "tmdb");
        } else if (data?.trailer_url) {
          setActiveUrl(data.trailer_url);
          setSource(data.source || "fallback");
        }
      })
      .catch((err) => {
        console.warn("Could not resolve trailer:", err);
        setSource("fallback");
      })
      .finally(() => {
        setResolving(false);
      });
  };

  useEffect(() => {
    if (!open) {
      setActiveUrl(trailerUrl);
      setResolving(false);
      setCopied(false);
      return;
    }

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);

    // Check if we need trailer resolution: TMDB -> Master Catalog -> YouTube search
    const currentEmbed = trailerUrl ? getEmbedTrailerUrl(trailerUrl) : null;
    const isSearchFallback = !trailerUrl || trailerUrl.includes("results?search_query=");

    if (!currentEmbed && isSearchFallback && movieId) {
      resolveTrailer(movieId);
    } else {
      setActiveUrl(trailerUrl);
      setSource("catalog");
    }

    return () => {
      window.removeEventListener("keydown", handler);
    };
  }, [open, movieId, trailerUrl, onClose]);

  const handleCopy = () => {
    if (activeUrl) {
      navigator.clipboard.writeText(activeUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const embedUrl = activeUrl ? getEmbedTrailerUrl(activeUrl) : null;
  const isSearchQuery = activeUrl?.includes("results?search_query=") || source === "fallback";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22 }}
          className="fixed inset-0 z-[150] flex items-center justify-center p-4"
          onClick={onClose}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-background/90 backdrop-blur-md" />

          {/* Modal Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.93, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="relative z-10 w-full max-w-4xl overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div className="flex flex-wrap items-center gap-2.5">
                <p className="text-base font-semibold uppercase tracking-wider text-foreground">
                  🎬 {title} — Official Trailer
                </p>

                {resolving ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/20 px-2.5 py-0.5 text-[11px] font-semibold text-primary animate-pulse">
                    <CircleNotch size={12} className="animate-spin" />
                    Checking TMDB & Catalog
                  </span>
                ) : source === "watchmode" && embedUrl ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/30">
                    <Sparkle size={12} weight="fill" />
                    WatchMode Verified Trailer
                  </span>
                ) : source === "tmdb" && embedUrl ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-cyan-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-400 border border-cyan-500/30">
                    <Sparkle size={12} weight="fill" />
                    TMDB Verified Studio Trailer
                  </span>
                ) : isSearchQuery ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-amber-400 border border-amber-500/30">
                    YouTube Search Query
                  </span>
                ) : null}
              </div>

              <button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-border text-muted-foreground transition-colors hover:border-primary hover:text-primary cursor-pointer"
                aria-label="Close trailer"
              >
                <X size={18} weight="bold" />
              </button>
            </div>

            {/* Video container */}
            <div className="aspect-video w-full bg-black relative flex items-center justify-center">
              {resolving ? (
                <div className="flex flex-col items-center justify-center gap-3 p-8 text-center">
                  <CircleNotch size={48} className="animate-spin text-primary" />
                  <p className="text-base font-medium text-foreground">
                    Locating official trailer from WatchMode & TMDB...
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Verifying official studio releases
                  </p>
                </div>
              ) : embedUrl ? (
                <iframe
                  src={embedUrl}
                  title={`${title} Trailer`}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="h-full w-full"
                />
              ) : isSearchQuery ? (
                /* Instant Search Query Fallback */
                <div className="flex flex-col items-center justify-center gap-4 p-6 sm:p-8 text-center max-w-lg mx-auto">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-amber-500/20 text-amber-400 ring-2 ring-amber-500/30">
                    <Play size={28} weight="fill" />
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-foreground">{title}</h3>
                    <p className="mt-1 text-sm font-medium text-foreground/90">
                      Official video link not in TMDB or Catalog.
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Direct YouTube official trailer search query generated:
                    </p>
                  </div>

                  {/* Fallback URL box */}
                  <div className="w-full rounded-xl bg-background/80 border border-border p-3 text-left">
                    <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground mb-1">
                      <span>YouTube Search URL:</span>
                      <span className="text-amber-400 font-semibold">Direct Query</span>
                    </div>
                    <div className="rounded bg-black/40 p-2 font-mono text-xs text-primary break-all select-all border border-border/50">
                      {activeUrl}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
                    <a
                      href={activeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-xl bg-gradient-primary px-5 py-2.5 font-semibold text-primary-foreground shadow-lg hover:brightness-110 transition-all cursor-pointer text-sm"
                    >
                      <ArrowSquareOut size={18} weight="bold" />
                      Watch Official Trailer on YouTube
                    </a>

                    <button
                      type="button"
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground hover:bg-accent transition-all cursor-pointer"
                    >
                      {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
                      {copied ? "Copied!" : "Copy URL"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center gap-3 text-muted-foreground">
                  <Play size={36} weight="duotone" />
                  <p className="text-sm">Trailer link is being processed for this catalog title.</p>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
