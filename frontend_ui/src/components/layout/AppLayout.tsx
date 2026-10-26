import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { TwitterLogo, InstagramLogo, GithubLogo, Sparkle, Gauge } from "@phosphor-icons/react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { Navbar, MobileNavMenu } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { Toaster } from "@/components/ui/Toaster-provider";

type AppLayoutProps = {
  children: ReactNode;
  onOpenCommand: () => void;
  onOpenAiConcierge?: () => void;
};

export const AppLayout = ({
  children,
  onOpenCommand,
  onOpenAiConcierge,
}: AppLayoutProps) => {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded-md focus:bg-card focus:px-4 focus:py-2 focus:text-foreground"
      >
        Skip to content
      </a>
      <Navbar onOpenCommand={onOpenCommand} onOpenAiConcierge={onOpenAiConcierge} />
      <motion.main
        id="main-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.35 }}
        className="pb-20 md:pb-8"
      >
        {children}
      </motion.main>

      {/* Cinematic Footer */}
      <footer className="border-t border-border bg-card/60 backdrop-blur-md">
        <PageContainer className="py-12">
          <div className="grid gap-10 md:grid-cols-[280px_1fr] lg:grid-cols-[320px_1fr_1fr_1fr]">
            {/* Brand Column */}
            <div className="space-y-4">
              <Link to="/" className="inline-flex text-foreground hover:text-primary">
                <BrandLogo size="md" textClassName="text-2xl font-black text-foreground" />
              </Link>
              <p className="text-xs leading-relaxed text-muted-foreground">
                Cinevora — Real-Time Movie Recommendation Service with Monitoring Dashboard and Gemini AI Concierge.
                Grounded in a verified 3,560-title master catalog across Indian Cinema and Hollywood.
              </p>
              <div className="flex gap-2.5">
                {[TwitterLogo, InstagramLogo, GithubLogo].map((Icon, i) => (
                  <button
                    key={i}
                    type="button"
                    className="flex h-8 w-8 items-center justify-center rounded-full border border-border text-muted-foreground transition-colors hover:border-primary hover:text-primary cursor-pointer"
                  >
                    <Icon size={15} weight="bold" />
                  </button>
                ))}
              </div>
            </div>

            {/* Catalog Discovery */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-foreground">
                Cinema Regions
              </p>
              <ul className="space-y-2 text-xs">
                {[
                  { label: "Tamil Cinema (Kollywood)", href: "/browse?industry=Tamil" },
                  { label: "Bollywood Cinema (Hindi)", href: "/browse?industry=Bollywood" },
                  { label: "Telugu Cinema (Tollywood)", href: "/browse?industry=Telugu" },
                  { label: "Malayalam Cinema (Mollywood)", href: "/browse?industry=Malayalam" },
                  { label: "Hollywood & Global", href: "/browse?industry=Hollywood" },
                  { label: "All 3,560 Movies", href: "/browse" },
                ].map((item) => (
                  <li key={item.label}>
                    <Link
                      to={item.href}
                      className="text-muted-foreground transition-colors hover:text-primary"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Platform Services */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-foreground">
                Services
              </p>
              <ul className="space-y-2 text-xs">
                <li>
                  <button
                    type="button"
                    onClick={onOpenAiConcierge}
                    className="text-primary font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <Sparkle size={12} weight="fill" />
                    AI Movie Concierge
                  </button>
                </li>
                <li>
                  <Link
                    to="/monitoring"
                    className="text-muted-foreground hover:text-primary flex items-center gap-1"
                  >
                    <Gauge size={12} />
                    MLOps Monitoring Dashboard
                  </Link>
                </li>
                <li>
                  <Link to="/my-list" className="text-muted-foreground hover:text-primary">
                    My Watchlist & Likes
                  </Link>
                </li>
                <li>
                  <Link to="/search" className="text-muted-foreground hover:text-primary">
                    Catalog Keyword Search
                  </Link>
                </li>
              </ul>
            </div>

            {/* Tech Stack */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-foreground">
                Architecture
              </p>
              <ul className="space-y-1.5 text-xs text-muted-foreground font-mono">
                <li>FastAPI 2.0 Backend</li>
                <li>Google Gemini 3.5 Flash</li>
                <li>SQLite Telemetry Database</li>
                <li>TF-IDF & FAISS Retrieval</li>
                <li>React 18 + Tailwind CSS</li>
              </ul>
            </div>
          </div>

          <div className="mt-10 flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between text-[11px] text-muted-foreground">
            <p>© 2026 Cinevora. Master Catalog Cleaned & Grounded Single Source of Truth.</p>
            <p>Non-commercial educational machine learning & recommendation demo.</p>
          </div>
        </PageContainer>
      </footer>

      <MobileNavMenu />
      <Toaster />
    </div>
  );
};
