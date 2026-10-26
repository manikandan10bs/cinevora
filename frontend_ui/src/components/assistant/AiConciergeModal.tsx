import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkle,
  PaperPlaneTilt,
  Trash,
  X,
  Play,
  Info,
  ArrowsClockwise,
  Star,
  CheckCircle,
} from "@phosphor-icons/react";
import { cinevoraApi, getActiveUserId, adaptCinevoraMovie } from "@/lib/cinevoraClient";
import { ContentItem } from "@/data/mockContent";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: string;
  graph_strategy?: string;
  graph_triples?: string[];
  recommendations?: ContentItem[];
  constraints?: Record<string, any>;
};

const defaultSuggestions = [
  "Movies in Lokesh Cinematic Universe (LCU)",
  "Shah Rukh Khan and Atlee collaborations",
  "Sci-Fi thrillers connected to Interstellar",
  "Movies starring Vijay Sethupathi",
  "Top-rated Malayalam mystery movies",
];

type AiConciergeModalProps = {
  open: boolean;
  onClose: () => void;
  onPlayTrailer?: (item: ContentItem) => void;
};

export const AiConciergeModal = ({
  open,
  onClose,
  onPlayTrailer,
}: AiConciergeModalProps) => {
  const activeUser = getActiveUserId();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "intro-1",
      role: "assistant",
      content:
        "Hello! I am Cinevora's AI Movie Concierge powered by **Gemini 3.5 Flash Lite**. I can help you discover exceptional films across Indian Cinema (Bollywood, Tamil, Telugu, Malayalam, Kannada) and Hollywood grounded in our 3,560-title master catalog. What kind of movie are you looking for?",
      source: "gemini",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusInfo, setStatusInfo] = useState<any>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Check Gemini status on mount
  useEffect(() => {
    if (open) {
      cinevoraApi.getAssistantStatus().then((stat) => {
        if (stat) setStatusInfo(stat);
      });
    }
  }, [open]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const resp = await cinevoraApi.chatWithAssistant(text, activeUser, 4);
      const recs = (resp?.recommendations || []).map(adaptCinevoraMovie);

      const botMsg: Message = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: resp?.reply || resp?.message || "Here are verified movie recommendations from Cinevora's catalog:",
        source: resp?.assistant_mode || resp?.source || "catalog",
        graph_strategy: resp?.graph_strategy,
        graph_triples: resp?.graph_triples,
        recommendations: recs,
        constraints: resp?.detected_constraints || {},
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content:
            "I encountered a momentary connection issue. All catalog searches remain operational in offline grounded mode.",
          source: "catalog",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: "intro-new",
        role: "assistant",
        content: "Chat cleared! How can I curate your next cinema experience?",
        source: "gemini",
      },
    ]);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[160] flex items-center justify-center p-3 sm:p-6"
          onClick={onClose}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-background/85 backdrop-blur-md" />

          {/* Dialog Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 16 }}
            transition={{ duration: 0.28, ease: "easeOut" }}
            className="relative z-10 flex h-[90vh] max-h-[820px] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-primary/30 bg-card/95 shadow-2xl backdrop-blur-xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border/70 px-5 py-4 bg-muted/40">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-primary text-primary-foreground shadow-md shadow-primary/30">
                  <Sparkle size={22} weight="fill" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-foreground">Cinevora AI Concierge</h3>
                    <span className="flex items-center gap-1 rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-bold text-primary ring-1 ring-primary/30">
                      <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                      Gemini 3.5 Flash
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Grounded in 3,560 Verified Titles · Factual Multi-Filter RAG
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleClear}
                  title="Clear Chat"
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground hover:border-border hover:text-foreground hover:bg-card/80 transition-colors cursor-pointer"
                >
                  <Trash size={16} />
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground hover:border-primary hover:text-primary transition-colors cursor-pointer"
                >
                  <X size={16} weight="bold" />
                </button>
              </div>
            </div>

            {/* Messages Body */}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 scroll-smooth"
            >
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-gradient-primary font-medium text-primary-foreground shadow-md"
                        : "bg-muted/80 text-foreground border border-border/60"
                    }`}
                  >
                    {/* Constraints pill if detected */}
                    {msg.constraints && Object.keys(msg.constraints).length > 0 && (
                      <div className="mb-2 flex flex-wrap gap-1.5 pb-1 border-b border-white/10">
                        {Object.entries(msg.constraints).map(([k, v]) => (
                          <span
                            key={k}
                            className="rounded-md bg-primary/20 px-2 py-0.5 text-[10px] font-bold text-primary"
                          >
                            {k}: {String(v)}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Graph RAG Indicator & Relational Badges */}
                    {msg.graph_strategy && (
                      <div className="mb-2 flex flex-wrap items-center gap-2 pb-1.5 border-b border-border/40">
                        <span className="inline-flex items-center gap-1 rounded-full bg-cyan-500/20 border border-cyan-500/40 px-2.5 py-0.5 text-[10px] font-bold text-cyan-300">
                          🕸️ Graph RAG: {msg.graph_strategy.replace(/_/g, " ").toUpperCase()}
                        </span>
                        {msg.graph_triples && msg.graph_triples.length > 0 && (
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {msg.graph_triples.length} graph paths traversed
                          </span>
                        )}
                      </div>
                    )}

                    <div className="whitespace-pre-line">{msg.content}</div>

                    {/* Graph Triples / Multi-Hop Reasoning Paths */}
                    {msg.graph_triples && msg.graph_triples.length > 0 && (
                      <div className="my-2.5 rounded-xl border border-cyan-500/25 bg-cyan-950/25 p-2.5 text-[11px] font-mono text-cyan-200/90 space-y-1">
                        <p className="font-bold uppercase tracking-wider text-[10px] text-cyan-400">
                          Knowledge Graph Paths:
                        </p>
                        {msg.graph_triples.slice(0, 3).map((triple, idx) => (
                          <div key={idx} className="truncate">
                            • {triple}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Grounded Movie Cards */}
                    {msg.recommendations && msg.recommendations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-border/40 space-y-2">
                        <p className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                          <CheckCircle size={14} weight="fill" />
                          Verified Master Catalog Titles ({msg.recommendations.length})
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                          {msg.recommendations.map((rec) => (
                            <div
                              key={rec.id}
                              className="flex gap-3 rounded-xl border border-border bg-card/90 p-2.5 hover:border-primary/50 transition-all shadow-sm"
                            >
                              <img
                                src={rec.posterImage}
                                alt={rec.title}
                                className="h-20 w-14 shrink-0 rounded-lg object-cover"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src =
                                    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200";
                                }}
                              />
                              <div className="flex flex-col justify-between overflow-hidden text-xs">
                                <div>
                                  <Link
                                    to={`/movie/${rec.id}`}
                                    onClick={onClose}
                                    className="font-bold text-foreground hover:text-primary transition-colors truncate block"
                                  >
                                    {rec.title}
                                  </Link>
                                  <div className="flex items-center gap-1 text-[11px] text-muted-foreground mt-0.5">
                                    <Star size={11} weight="fill" className="text-warning" />
                                    <span className="font-semibold text-foreground">
                                      {rec.rating}
                                    </span>
                                    <span>·</span>
                                    <span>{rec.year}</span>
                                    <span>·</span>
                                    <span className="truncate">{rec.genres[0]}</span>
                                  </div>
                                </div>

                                <div className="flex items-center gap-1.5 pt-1">
                                  {onPlayTrailer && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onPlayTrailer(rec);
                                        onClose();
                                      }}
                                      className="inline-flex items-center gap-1 rounded bg-primary/20 px-2 py-1 text-[10px] font-bold text-primary hover:bg-primary/30 transition-colors cursor-pointer"
                                    >
                                      <Play size={10} weight="fill" />
                                      Trailer
                                    </button>
                                  )}
                                  <Link
                                    to={`/movie/${rec.id}`}
                                    onClick={onClose}
                                    className="inline-flex items-center gap-1 rounded bg-muted px-2 py-1 text-[10px] font-medium text-foreground hover:text-primary transition-colors"
                                  >
                                    <Info size={10} weight="bold" />
                                    Details
                                  </Link>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-2 rounded-2xl bg-muted/80 px-4 py-3 text-xs text-muted-foreground max-w-sm">
                  <div className="h-3 w-3 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                  Gemini is parsing query and verifying master catalog constraints...
                </div>
              )}
            </div>

            {/* Quick Suggestions Chips */}
            <div className="border-t border-border/40 px-4 py-2.5 bg-muted/20">
              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
                <span className="text-[11px] font-semibold text-muted-foreground shrink-0 flex items-center gap-1">
                  <Sparkle size={12} className="text-primary" /> Suggestions:
                </span>
                {defaultSuggestions.map((sug) => (
                  <button
                    key={sug}
                    type="button"
                    onClick={() => handleSend(sug)}
                    className="shrink-0 rounded-full border border-border/80 bg-card/80 px-3 py-1 text-xs text-muted-foreground hover:border-primary hover:text-primary hover:bg-primary/10 transition-all cursor-pointer whitespace-nowrap"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Dock */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-3 border-t border-border px-4 py-3 bg-card"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Cinevora AI: e.g. 'Vijay action movies' or 'Sci-Fi directed by Nolan'..."
                className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-primary text-primary-foreground shadow-md transition-all hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <PaperPlaneTilt size={18} weight="fill" />
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
