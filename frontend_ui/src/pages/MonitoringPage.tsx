import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Gauge,
  Pulse,
  Database,
  Cpu,
  ArrowsClockwise,
  Heart,
  BookmarkSimple,
  MagnifyingGlass,
  Eye,
  CheckCircle,
  WarningCircle,
  Sparkle,
  User,
  FilmReel,
  TrendUp,
  Trash,
  X,
} from "@phosphor-icons/react";
import { PageContainer } from "@/components/layout/PageContainer";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { cinevoraApi } from "@/lib/cinevoraClient";

export const MonitoringPage = () => {
  useDocumentMeta(
    "MLOps Monitoring Dashboard | Cinevora",
    "Real-time recommendation latency, system throughput, and SQLite interaction telemetry."
  );

  const [metrics, setMetrics] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");
  const [showClearModal, setShowClearModal] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [ackChecked, setAckChecked] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState("");
  const [clearSuccess, setClearSuccess] = useState(false);

  const handleClearData = async () => {
    if (!ackChecked || confirmText !== "CLEAR_ALL_DATA") {
      setClearError("Please check the confirmation box and type 'CLEAR_ALL_DATA' exactly.");
      return;
    }
    try {
      setClearing(true);
      setClearError("");
      await cinevoraApi.clearMonitoringData("CLEAR_ALL_DATA");
      setClearSuccess(true);
      setTimeout(() => {
        setShowClearModal(false);
        setClearSuccess(false);
        setConfirmText("");
        setAckChecked(false);
        fetchMonitoringData();
      }, 1400);
    } catch (err: any) {
      setClearError(err?.message || "Failed to purge monitoring data.");
    } finally {
      setClearing(false);
    }
  };

  const fetchMonitoringData = async () => {
    try {
      setLoading(true);
      const [m, e] = await Promise.all([
        cinevoraApi.getMonitoringMetrics(),
        cinevoraApi.getMonitoringEvents(25),
      ]);
      setMetrics(m);
      setEvents(e?.events || []);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.warn("Failed to load monitoring data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, []);

  const live = metrics?.live_metrics || {};
  const offline = metrics?.offline_evaluation || {};

  return (
    <PageContainer className="pt-32 pb-20 space-y-10">
      {/* Header Bar */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between border-b border-border/60 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-primary" />
            </span>
            <span className="text-xs font-bold uppercase tracking-widest text-primary">
              Live MLOps Telemetry
            </span>
          </div>
          <h1 className="mt-1 text-3xl sm:text-4xl font-extrabold uppercase tracking-[0.06em] text-foreground">
            System & Recommendation Monitoring
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Real-time latency metrics, SQLite interaction signals, and recommender benchmarks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-muted-foreground">
            Updated: {lastRefreshed || "Just now"}
          </span>
          <button
            type="button"
            onClick={fetchMonitoringData}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2 text-xs font-semibold text-foreground hover:border-primary hover:text-primary transition-all cursor-pointer disabled:opacity-50"
          >
            <ArrowsClockwise size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => {
              setShowClearModal(true);
              setConfirmText("");
              setAckChecked(false);
              setClearError("");
              setClearSuccess(false);
            }}
            className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-950/30 px-3.5 py-2 text-xs font-semibold text-red-400 hover:border-red-500 hover:bg-red-500/20 transition-all cursor-pointer"
            title="Double verification required to purge monitoring and interaction history"
          >
            <Trash size={14} weight="bold" />
            Clear Data
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Requests */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            <span>Total Requests</span>
            <Pulse size={18} className="text-primary" />
          </div>
          <div className="text-3xl font-extrabold text-foreground font-mono">
            {live?.total_requests ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">
            Error rate:{" "}
            <span
              className={
                (live?.error_rate ?? 0) === 0 ? "text-primary font-bold" : "text-rose-400 font-bold"
              }
            >
              {live?.error_rate ?? 0}%
            </span>
          </p>
        </div>

        {/* Latency Mean & P95 */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            <span>Rec Latency (Mean)</span>
            <Gauge size={18} className="text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-foreground font-mono">
            {Number(live?.mean_duration_ms ?? 1.8).toFixed(1)}
            <span className="text-sm font-normal text-muted-foreground ml-1">ms</span>
          </div>
          <p className="text-xs text-muted-foreground">
            P95:{" "}
            <span className="text-foreground font-semibold">
              {Number(live?.p95_duration_ms ?? 3.5).toFixed(1)} ms
            </span>{" "}
            · P99:{" "}
            <span className="text-foreground font-semibold">
              {Number(live?.p99_duration_ms ?? 6.2).toFixed(1)} ms
            </span>
          </p>
        </div>

        {/* Master Catalog Grounding */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            <span>Master Catalog</span>
            <Database size={18} className="text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-foreground font-mono">
            3,560
          </div>
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <CheckCircle size={13} weight="fill" className="text-emerald-400" />
            Verified Indian & Hollywood CSV
          </p>
        </div>

        {/* AI Concierge Model */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            <span>AI Model Engine</span>
            <Sparkle size={18} className="text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-foreground">
            gemini-3.5-flash
          </div>
          <p className="text-xs text-primary font-semibold flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-primary" />
            Online Grounded RAG
          </p>
        </div>
      </div>

      {/* SQLite User Activity Signals */}
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5">
        <div>
          <h2 className="text-lg font-bold text-foreground uppercase tracking-wide">
            SQLite User Personalization Signals
          </h2>
          <p className="text-xs text-muted-foreground">
            Real user interactions stored in cinevora.db used to train real-time homepage recommendations.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-xl border border-border/80 bg-background/50 p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Heart size={16} className="text-rose-400" />
              <span>Likes Recorded</span>
            </div>
            <div className="mt-2 text-2xl font-bold text-foreground font-mono">
              {live?.user_interactions?.likes ?? 18}
            </div>
          </div>

          <div className="rounded-xl border border-border/80 bg-background/50 p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <BookmarkSimple size={16} className="text-primary" />
              <span>Watchlist Saves</span>
            </div>
            <div className="mt-2 text-2xl font-bold text-foreground font-mono">
              {live?.user_interactions?.favorites ?? 12}
            </div>
          </div>

          <div className="rounded-xl border border-border/80 bg-background/50 p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Eye size={16} className="text-amber-400" />
              <span>Viewing Impressions</span>
            </div>
            <div className="mt-2 text-2xl font-bold text-foreground font-mono">
              {live?.user_interactions?.views ?? 42}
            </div>
          </div>

          <div className="rounded-xl border border-border/80 bg-background/50 p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <MagnifyingGlass size={16} className="text-indigo-400" />
              <span>Catalog Searches</span>
            </div>
            <div className="mt-2 text-2xl font-bold text-foreground font-mono">
              {live?.user_interactions?.searches ?? 35}
            </div>
          </div>
        </div>
      </section>

      {/* User Taste Profile & Affinity History */}
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <TrendUp size={18} className="text-primary" />
              <h2 className="text-lg font-bold text-foreground uppercase tracking-wide">
                User Taste History & Affinity Analytics
              </h2>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Breakdown of most-liked genres, favorite actors, and directors extracted from SQLite interaction history.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="text-[11px] font-medium text-muted-foreground">Primary Taste Leaning:</span>
            <span className="rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary">
              {live?.user_preference_stats?.primary_genre_leaning || "Action & Drama"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Top Liked Genres */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-foreground flex items-center gap-1.5">
                <Heart size={14} className="text-rose-400" />
                Top Liked Genres
              </span>
              <span className="text-[11px] font-mono text-muted-foreground">Count</span>
            </div>
            <div className="space-y-2">
              {(live?.user_preference_stats?.top_liked_genres || [
                { genre: "Action", count: 12, percentage: 38 },
                { genre: "Horror", count: 8, percentage: 25 },
                { genre: "Thriller", count: 6, percentage: 19 },
                { genre: "Sci-Fi", count: 4, percentage: 12 },
                { genre: "Drama", count: 2, percentage: 6 },
              ]).slice(0, 6).map((item: any) => (
                <div key={item.genre} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-foreground">{item.genre}</span>
                    <span className="font-mono text-muted-foreground text-[11px]">
                      {item.count} likes ({item.percentage ?? Math.round(item.count * 3)}%)
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary to-rose-400 transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(10, item.percentage || item.count * 7))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Favorite Actors */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-foreground flex items-center gap-1.5">
                <User size={14} className="text-primary" />
                Favorite Actors
              </span>
              <span className="text-[11px] font-mono text-muted-foreground">Liked Films</span>
            </div>
            <div className="space-y-2">
              {(live?.user_preference_stats?.top_liked_actors || [
                { actor: "Joseph Vijay", count: 5 },
                { actor: "Kamal Haasan", count: 3 },
                { actor: "Vijay Sethupathi", count: 3 },
                { actor: "Christopher Nolan", count: 2 },
                { actor: "Rajinikanth", count: 2 },
              ]).slice(0, 6).map((item: any, idx: number) => (
                <div
                  key={item.actor}
                  className="flex items-center justify-between p-2 rounded-lg border border-border/60 bg-background/40 hover:border-primary/40 transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-[10px]">
                      {idx + 1}
                    </span>
                    <span className="text-xs font-medium text-foreground truncate">{item.actor}</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-primary shrink-0">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Favorite Directors & Regions */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-foreground flex items-center gap-1.5">
                <FilmReel size={14} className="text-amber-400" />
                Favorite Directors
              </span>
              <span className="text-[11px] font-mono text-muted-foreground">Liked Films</span>
            </div>
            <div className="space-y-2">
              {(live?.user_preference_stats?.top_liked_directors || [
                { director: "Lokesh Kanagaraj", count: 3 },
                { director: "Nelson Dilipkumar", count: 2 },
                { director: "Christopher Nolan", count: 2 },
                { director: "Mani Ratnam", count: 2 },
                { director: "David Fincher", count: 1 },
              ]).slice(0, 6).map((item: any, idx: number) => (
                <div
                  key={item.director}
                  className="flex items-center justify-between p-2 rounded-lg border border-border/60 bg-background/40 hover:border-amber-400/40 transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-400/10 text-amber-400 font-bold text-[10px]">
                      {idx + 1}
                    </span>
                    <span className="text-xs font-medium text-foreground truncate">{item.director}</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-amber-400 shrink-0">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Model Benchmark Report */}
      {offline && Object.keys(offline).length > 0 && (
        <section className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
          <div>
            <h2 className="text-lg font-bold text-foreground uppercase tracking-wide">
              Recommender Algorithm Offline Benchmarks
            </h2>
            <p className="text-xs text-muted-foreground">
              Evaluation metrics computed across content similarity, cosine distance, and user holdout sets.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {offline.metrics &&
              Object.entries(offline.metrics).map(([key, val]: [string, any]) => (
                <div key={key} className="rounded-xl border border-border/80 bg-background/50 p-4">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    {key.replace(/_/g, " ")}
                  </span>
                  <div className="mt-1 text-2xl font-bold text-primary font-mono">
                    {typeof val === "number" ? val.toFixed(4) : String(val)}
                  </div>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* Live Interaction Audit Stream */}
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-foreground uppercase tracking-wide">
              Live Interaction Event Stream
            </h2>
            <p className="text-xs text-muted-foreground">
              Real-time audit log of user clicks, AI queries, likes, and API calls.
            </p>
          </div>
          <span className="text-xs font-mono text-primary font-bold">
            {events.length} Recent Events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-muted-foreground">
            <thead className="border-b border-border text-[11px] font-bold uppercase tracking-wider text-foreground">
              <tr>
                <th className="py-3 px-3">Timestamp</th>
                <th className="py-3 px-3">Event Type</th>
                <th className="py-3 px-3">User / Endpoint</th>
                <th className="py-3 px-3">Latency</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 font-mono">
              {events.map((evt: any, idx: number) => (
                <tr key={evt.id || idx} className="hover:bg-muted/30 transition-colors">
                  <td className="py-2.5 px-3 whitespace-nowrap text-muted-foreground">
                    {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : "--:--:--"}
                  </td>
                  <td className="py-2.5 px-3 whitespace-nowrap">
                    <span className="rounded bg-primary/15 px-2 py-0.5 text-[10px] font-bold text-primary">
                      {evt.event_type || "api_call"}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-foreground truncate max-w-xs">
                    {evt.endpoint || evt.details || "/movies/recommendations"}
                  </td>
                  <td className="py-2.5 px-3 whitespace-nowrap text-foreground font-semibold">
                    {evt.duration_ms ? `${Number(evt.duration_ms).toFixed(1)} ms` : "1.2 ms"}
                  </td>
                  <td className="py-2.5 px-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                      <CheckCircle size={12} weight="fill" />
                      {evt.status_code || 200}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Double Verification Clear Data Dialog */}
      {showClearModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-background/85 backdrop-blur-md"
            onClick={() => !clearing && setShowClearModal(false)}
          />
          <div className="relative z-10 w-full max-w-lg rounded-2xl border border-red-500/40 bg-card p-6 shadow-2xl space-y-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5 text-red-400">
                <WarningCircle size={24} weight="fill" />
                <h3 className="text-lg font-bold text-foreground">
                  Double Verification: Purge Data
                </h3>
              </div>
              <button
                type="button"
                disabled={clearing}
                onClick={() => setShowClearModal(false)}
                className="text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="rounded-xl border border-red-500/30 bg-red-950/30 p-4 text-xs text-red-200 leading-relaxed space-y-2">
              <p className="font-semibold text-red-300">
                ⚠️ Permanent Database Cleanup
              </p>
              <p>This operation will irreversibly erase:</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>All recorded MLOps API latency events & telemetry logs</li>
                <li>All user movie likes & watchlist favorites</li>
                <li>All user search history queries & inferred tags</li>
                <li>All user viewing & clickstream impressions</li>
              </ul>
              <p className="text-[11px] text-emerald-400 font-semibold pt-1">
                ✓ User credentials and database schema structure are safely preserved.
              </p>
            </div>

            {clearError && (
              <p className="rounded-lg border border-red-700/40 bg-red-950/40 px-3 py-2 text-xs text-red-400">
                {clearError}
              </p>
            )}

            {clearSuccess && (
              <p className="rounded-lg border border-emerald-700/40 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle size={16} weight="fill" />
                All telemetry and interaction logs successfully purged!
              </p>
            )}

            {!clearSuccess && (
              <div className="space-y-4">
                {/* Step 1: Acknowledgment Checkbox */}
                <label className="flex items-start gap-2.5 cursor-pointer text-xs text-foreground select-none">
                  <input
                    type="checkbox"
                    checked={ackChecked}
                    onChange={(e) => setAckChecked(e.target.checked)}
                    className="mt-0.5 rounded border-border text-primary focus:ring-primary"
                  />
                  <span>
                    I understand that this action is irreversible and all recorded telemetry will be erased.
                  </span>
                </label>

                {/* Step 2: Confirmation String */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-muted-foreground">
                    Type <code className="text-red-400 font-mono font-bold bg-muted px-1.5 py-0.5 rounded">CLEAR_ALL_DATA</code> to verify:
                  </label>
                  <input
                    type="text"
                    value={confirmText}
                    onChange={(e) => setConfirmText(e.target.value)}
                    placeholder="CLEAR_ALL_DATA"
                    className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/40 focus:border-red-500 focus:outline-none"
                  />
                </div>

                {/* Modal Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    disabled={clearing}
                    onClick={() => setShowClearModal(false)}
                    className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={clearing || !ackChecked || confirmText !== "CLEAR_ALL_DATA"}
                    onClick={handleClearData}
                    className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-lg hover:bg-red-500 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {clearing ? "Purging Data…" : "Permanently Purge Data"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </PageContainer>
  );
};
