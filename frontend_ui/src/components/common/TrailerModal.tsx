import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Play, ArrowSquareOut, Sparkle, CircleNotch } from "@phosphor-icons/react";
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

  useEffect(() => {
    if (!open) {
      setActiveUrl(trailerUrl);
      setResolving(false);
      return;
    }

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);

    // Check if we need Gemini trailer resolution
    const currentEmbed = trailerUrl ? getEmbedTrailerUrl(trailerUrl) : null;
    const isSearchFallback = !trailerUrl || trailerUrl.includes("results?search_query=");

    if (!currentEmbed && isSearchFallback && movieId) {
      // Automatically attempt exact trailer resolution with Gemini Flash
      setResolving(true);
      cinevoraApi
        .getExactTrailerUrl(movieId)
        .then((data) => {
          if (data?.trailer_url && getEmbedTrailerUrl(data.trailer_url)) {
            setActiveUrl(data.trailer_url);
            setSource(data.source || "gemini");
          } else if (data?.trailer_url) {
            setActiveUrl(data.trailer_url);
            setSource(data.source || "fallback");
          }
        })
        .catch((err) => {
          console.warn("Could not resolve trailer via Gemini:", err);
        })
        .finally(() => {
          setResolving(false);
        });
    } else {
      setActiveUrl(trailerUrl);
    }

    return () => window.removeEventListener("keydown", handler);
  }, [open, movieId, trailerUrl, onClose]);

  const embedUrl = activeUrl ? getEmbedTrailerUrl(activeUrl) : null;
  const isSearchQuery = activeUrl?.includes("results?search_query=");

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

          {/* Modal */}
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
              <div className="flex items-center gap-2.5">
                <p className="text-base font-semibold uppercase tracking-wider text-foreground">
                  🎬 {title} — Official Trailer
                </p>
                {source === "gemini" && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-primary/20 px-2.5 py-0.5 text-[10px] font-bold text-primary">
                    <Sparkle size={11} weight="fill" />
                    Gemini Resolved
                  </span>
                )}
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

            {/* Video area */}
            <div className="aspect-video w-full bg-black relative flex items-center justify-center">
              {resolving ? (
                <div className="flex flex-col items-center justify-center gap-3 p-8 text-center text-muted-foreground">
                  <CircleNotch size={36} className="animate-spin text-primary" />
                  <p className="text-sm font-medium text-foreground">
                    Resolving exact official trailer with Gemini 3.5 Flash...
                  </p>
                  <p className="text-xs text-muted-foreground max-w-sm">
                    Querying master movie metadata and official YouTube releases
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
                <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/20 text-primary ring-2 ring-primary">
                    <Play size={32} weight="fill" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-foreground">{title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground max-w-md">
                      Verified catalog trailer query generated. Open the official YouTube stream in a new tab:
                    </p>
                  </div>
                  <a
                    href={activeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl bg-gradient-primary px-6 py-3 font-semibold text-primary-foreground shadow-lg hover:brightness-110 transition-all cursor-pointer"
                  >
                    <ArrowSquareOut size={18} weight="bold" />
                    Watch Official Trailer on YouTube
                  </a>
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
