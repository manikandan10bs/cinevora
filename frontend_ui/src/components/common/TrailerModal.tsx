import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Play, ArrowSquareOut, Sparkle, CircleNotch, Copy, Check, ArrowClockwise } from "@phosphor-icons/react";
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
  const [attempt, setAttempt] = useState<number>(1);
  const [attemptsMade, setAttemptsMade] = useState<number | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startResolution = (targetMovieId: string) => {
    setResolving(true);
    setAttempt(1);
    setAttemptsMade(null);
    setCopied(false);

    // Progressively update attempt indicator: 1 -> 2 -> 3
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setAttempt((prev) => (prev < 3 ? prev + 1 : 3));
    }, 2200);

    cinevoraApi
      .getExactTrailerUrl(targetMovieId)
      .then((data) => {
        if (data?.trailer_url && getEmbedTrailerUrl(data.trailer_url)) {
          setActiveUrl(data.trailer_url);
          setSource(data.source || "gemini");
          setAttemptsMade(data.attempts_made || 1);
        } else if (data?.trailer_url) {
          setActiveUrl(data.trailer_url);
          setSource("fallback");
          setAttemptsMade(data.attempts_made || 3);
        }
      })
      .catch((err) => {
        console.warn("Could not resolve trailer via Gemini:", err);
        setSource("fallback");
        setAttemptsMade(3);
      })
      .finally(() => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        setResolving(false);
      });
  };

  useEffect(() => {
    if (!open) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setActiveUrl(trailerUrl);
      setResolving(false);
      setAttempt(1);
      setAttemptsMade(null);
      setCopied(false);
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
      startResolution(movieId);
    } else {
      setActiveUrl(trailerUrl);
      setSource("catalog");
    }

    return () => {
      window.removeEventListener("keydown", handler);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [open, movieId, trailerUrl, onClose]);

  const handleCopy = () => {
    if (activeUrl) {
      navigator.clipboard.writeText(activeUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRetry = () => {
    if (movieId) {
      startResolution(movieId);
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
                    Searching ({attempt}/3)
                  </span>
                ) : source === "gemini" && embedUrl ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/30">
                    <Sparkle size={12} weight="fill" />
                    Gemini Resolved (Found on Request {attemptsMade || 1}/3)
                  </span>
                ) : source === "fallback" || isSearchQuery ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-amber-400 border border-amber-500/30">
                    3 Requests Completed • Search Fallback
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
                /* Animated Attempt Progress Indicator */
                <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
                  <div className="relative flex items-center justify-center">
                    <CircleNotch size={56} className="animate-spin text-primary" />
                    <span className="absolute text-xs font-bold text-primary">
                      {attempt}/3
                    </span>
                  </div>

                  <div className="space-y-1">
                    <p className="text-base sm:text-lg font-semibold text-foreground">
                      trying to find exact youtube url ({attempt}/3)...
                    </p>
                    <p className="text-xs text-muted-foreground max-w-md mx-auto">
                      Asking Google Gemini to find the verified official YouTube watch link (Request {attempt} of 3)
                    </p>
                  </div>

                  {/* 3 Step Pill Indicators */}
                  <div className="flex items-center gap-2 pt-2">
                    {[1, 2, 3].map((step) => (
                      <div
                        key={step}
                        className={`h-2 rounded-full transition-all duration-300 ${
                          step === attempt
                            ? "w-8 bg-primary animate-pulse"
                            : step < attempt
                            ? "w-3 bg-emerald-500"
                            : "w-3 bg-muted/40"
                        }`}
                      />
                    ))}
                  </div>

                  <p className="text-[11px] text-muted-foreground/70 max-w-sm pt-1">
                    Capped at 3 requests. If not found after 3 attempts, YouTube search fallback will be provided automatically.
                  </p>
                </div>
              ) : embedUrl ? (
                /* Embedded YouTube Player */
                <iframe
                  src={embedUrl}
                  title={`${title} Trailer`}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="h-full w-full"
                />
              ) : isSearchQuery ? (
                /* Fallback State after 3 Requests Fail */
                <div className="flex flex-col items-center justify-center gap-4 p-6 sm:p-8 text-center max-w-lg mx-auto">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-amber-500/20 text-amber-400 ring-2 ring-amber-500/30">
                    <Play size={28} weight="fill" />
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-foreground">{title}</h3>
                    <p className="mt-1 text-sm font-medium text-foreground/90">
                      Exact YouTube URL not found after 3 requests.
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Showing verified official YouTube search fallback:
                    </p>
                  </div>

                  {/* Fallback URL box */}
                  <div className="w-full rounded-xl bg-background/80 border border-border p-3 text-left">
                    <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground mb-1">
                      <span>YouTube Search URL:</span>
                      <span className="text-amber-400 font-semibold">3/3 Attempts Completed</span>
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
                      {copied ? "Copied!" : "Copy Link"}
                    </button>

                    {movieId && (
                      <button
                        type="button"
                        onClick={handleRetry}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-all cursor-pointer"
                        title="Retry trailer resolution with 3 Gemini requests"
                      >
                        <ArrowClockwise size={16} />
                        Retry
                      </button>
                    )}
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