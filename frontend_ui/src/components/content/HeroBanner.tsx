import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Info, Play, Star } from "@phosphor-icons/react";
import { motion, AnimatePresence } from "framer-motion";
import { ContentItem, featuredItems } from "@/data/mockContent";
import { GenreChip } from "@/components/common/GenreChip";
import { PageContainer } from "@/components/layout/PageContainer";

const SLIDE_DURATION = 8000;

type HeroBannerProps = {
  items?: ContentItem[];
  onPlayTrailer?: (item: ContentItem) => void;
};

export const HeroBanner = ({ items, onPlayTrailer }: HeroBannerProps) => {
  const slides = items && items.length > 0 ? items : featuredItems;
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  const progressRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Safe active slide
  const active = slides[activeIndex % slides.length] || slides[0];

  const goTo = (index: number) => {
    setActiveIndex(index % slides.length);
    setProgress(0);
    startTimeRef.current = Date.now();
  };

  useEffect(() => {
    if (paused) {
      if (progressRef.current) cancelAnimationFrame(progressRef.current);
      return;
    }

    startTimeRef.current = Date.now() - (progress * SLIDE_DURATION) / 100;

    const tick = () => {
      const elapsed = Date.now() - startTimeRef.current;
      const pct = Math.min((elapsed / SLIDE_DURATION) * 100, 100);
      setProgress(pct);
      if (pct >= 100) {
        setActiveIndex((current) => (current + 1) % slides.length);
        setProgress(0);
        startTimeRef.current = Date.now();
      }
      progressRef.current = requestAnimationFrame(tick);
    };

    progressRef.current = requestAnimationFrame(tick);
    return () => {
      if (progressRef.current) cancelAnimationFrame(progressRef.current);
    };
  }, [paused, activeIndex, slides.length]);

  const href = `/movie/${active.id}`;

  // Keyboard navigation for hero slides
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === "INPUT") return;
      if (e.key === "ArrowRight") goTo((activeIndex + 1) % slides.length);
      if (e.key === "ArrowLeft") goTo((activeIndex - 1 + slides.length) % slides.length);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [activeIndex, slides.length]);

  return (
    <section
      className="relative min-h-[90vh] overflow-hidden pt-[72px]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Backdrop */}
      <AnimatePresence mode="wait">
        <motion.div
          key={active.id}
          initial={{ opacity: 0, scale: 1.04 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 0.85, ease: "easeInOut" }}
          className="absolute inset-0"
        >
          <img
            src={active.backdropImage || active.heroImage}
            alt={active.heroAlt || active.title}
            className="h-full w-full object-cover object-center"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1600";
            }}
          />
          {/* Multi-layer cinematic overlay */}
          <div className="absolute inset-0 bg-hero-overlay" />
          <div className="absolute inset-0 bg-gradient-to-r from-background/95 via-background/50 to-transparent" />
        </motion.div>
      </AnimatePresence>

      {/* Content */}
      <PageContainer className="relative flex min-h-[90vh] items-end pb-20">
        <AnimatePresence mode="wait">
          <motion.div
            key={`content-${active.id}`}
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.65, ease: "easeOut" }}
            className="max-w-2xl space-y-4"
          >
            {/* Tagline / Industry */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-primary/40 bg-primary/15 px-3 py-1 text-xs font-bold uppercase tracking-widest text-primary shadow-sm">
                ⭐ Cinevora Spotlight
              </span>
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-white backdrop-blur-sm">
                {active.country || active.category || "Master Catalog"}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-4xl font-extrabold uppercase tracking-[0.06em] text-foreground sm:text-5xl md:text-6xl lg:text-7xl drop-shadow-md">
              {active.title}
            </h1>

            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-2 text-sm text-gray-200">
              <span className="flex items-center gap-1 font-semibold">
                <Star size={14} weight="fill" className="text-warning" />
                {active.rating}
              </span>
              <span className="text-gray-500">·</span>
              <span>{active.year}</span>
              <span className="text-gray-500">·</span>
              <span>{active.duration}</span>
              <span className="text-gray-500">·</span>
              <span className="font-medium text-primary">{active.country}</span>
            </div>

            {/* Description */}
            <p className="max-w-xl text-base leading-relaxed text-gray-200 md:text-lg line-clamp-3">
              {active.description}
            </p>

            {/* Genres */}
            <div className="flex flex-wrap gap-2">
              {active.genres.map((genre) => (
                <GenreChip key={genre} label={genre} />
              ))}
            </div>

            {/* CTA */}
            <div className="flex flex-wrap gap-4 pt-2">
              {onPlayTrailer ? (
                <button
                  type="button"
                  onClick={() => onPlayTrailer(active)}
                  className="inline-flex min-h-[52px] items-center gap-3 rounded-xl bg-gradient-primary px-8 py-3 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:scale-[1.03] hover:brightness-110 cursor-pointer"
                >
                  <Play size={20} weight="fill" />
                  Watch Trailer
                </button>
              ) : (
                <Link
                  to={href}
                  className="inline-flex min-h-[52px] items-center gap-3 rounded-xl bg-gradient-primary px-8 py-3 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:scale-[1.03] hover:brightness-110"
                >
                  <Play size={20} weight="fill" />
                  Watch Trailer
                </Link>
              )}
              <Link
                to={href}
                className="inline-flex min-h-[52px] items-center gap-3 rounded-xl border border-white/30 bg-white/10 px-8 py-3 text-base font-medium text-white backdrop-blur-sm transition-all hover:border-white/60 hover:bg-white/20"
              >
                <Info size={20} weight="duotone" />
                More Info
              </Link>
            </div>

            {/* Slide indicators with progress */}
            <div className="flex items-center gap-3 pt-4">
              {slides.map((item, index) => (
                <button
                  key={item.id}
                  type="button"
                  aria-label={`Go to slide ${index + 1}: ${item.title}`}
                  onClick={() => goTo(index)}
                  className="group relative h-1.5 rounded-full bg-white/20 transition-all cursor-pointer"
                  style={{ width: index === activeIndex ? 56 : 20 }}
                >
                  {index === activeIndex && (
                    <span
                      className="absolute inset-y-0 left-0 rounded-full bg-primary transition-none"
                      style={{ width: `${progress}%` }}
                    />
                  )}
                  {index !== activeIndex && (
                    <span className="absolute inset-0 rounded-full bg-white/30 group-hover:bg-white/60 transition-colors" />
                  )}
                </button>
              ))}
              <span className="ml-2 text-xs font-mono text-white/60">
                {activeIndex + 1} / {slides.length}
              </span>
            </div>
          </motion.div>
        </AnimatePresence>
      </PageContainer>
    </section>
  );
};
