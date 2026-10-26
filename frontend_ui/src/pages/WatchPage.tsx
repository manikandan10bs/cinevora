import { useMemo, useState } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { Play } from "@phosphor-icons/react";
import { PageContainer } from "@/components/layout/PageContainer";
import { contentItems, recommendations } from "@/data/mockContent";
import { VideoPlayer } from "@/components/watch/VideoPlayer";
import { LandscapeCard } from "@/components/content/LandscapeCard";
import { SectionHeader } from "@/components/common/SectionHeader";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";

type WatchPageProps = {
  progressMap: Record<string, number>;
};

export const WatchPage = ({ progressMap }: WatchPageProps) => {
  const { id } = useParams();
  const [params] = useSearchParams();
  const episodeId = params.get("episode");

  const item = useMemo(
    () => contentItems.find((entry) => entry.id === id) ?? contentItems[0],
    [id],
  );

  const allEpisodes = useMemo(
    () => item.seasons?.flatMap((s) => s.episodes) ?? [],
    [item],
  );

  const [activeSeason, setActiveSeason] = useState(item.seasons?.[0]?.id ?? "");
  const currentSeasonEpisodes = useMemo(
    () => item.seasons?.find((s) => s.id === activeSeason)?.episodes ?? allEpisodes,
    [item, activeSeason, allEpisodes],
  );

  useDocumentMeta(
    `Watch ${item.title} | streamXie`,
    `Watch ${item.title} on streamXie.`,
  );

  return (
    <PageContainer className="pt-28 pb-16">
      <div className="grid gap-8 xl:grid-cols-[1fr_340px]">
        {/* Main column */}
        <div className="space-y-6">
          <VideoPlayer item={item} episodeId={episodeId} allEpisodes={allEpisodes} />

          {/* Episode navigation for series */}
          {item.seasons && item.seasons.length > 0 && (
            <section className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <SectionHeader title="Episodes" />
                {item.seasons.length > 1 && (
                  <div className="flex gap-2 flex-wrap">
                    {item.seasons.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => setActiveSeason(s.id)}
                        className={`rounded-lg border px-4 py-2 text-sm transition-colors ${activeSeason === s.id ? "border-primary bg-primary/15 text-primary" : "border-border bg-card text-foreground hover:border-primary hover:text-primary"}`}
                      >
                        {s.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {currentSeasonEpisodes.map((episode) => {
                  const isActive = episode.id === episodeId || (!episodeId && episode.id === allEpisodes[0]?.id);
                  return (
                    <Link
                      key={episode.id}
                      to={`/watch/${item.id}?episode=${episode.id}`}
                      className={`flex gap-3 rounded-xl border p-3 transition-all hover:border-primary ${isActive ? "border-primary bg-primary/10" : "border-border bg-card hover:bg-card/80"}`}
                    >
                      <div className="relative aspect-video w-28 shrink-0 overflow-hidden rounded-lg bg-muted">
                        <img src={episode.thumbnail} alt={episode.title} className="h-full w-full object-cover" />
                        {isActive && (
                          <div className="absolute inset-0 flex items-center justify-center bg-background/50">
                            <Play size={18} weight="fill" className="text-primary" />
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col justify-center gap-1 min-w-0">
                        <p className={`truncate text-sm font-medium ${isActive ? "text-primary" : "text-foreground"}`}>{episode.title}</p>
                        <p className="text-xs text-muted-foreground">{episode.duration}</p>
                        <p className="line-clamp-2 text-xs text-muted-foreground">{episode.synopsis}</p>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="hidden xl:block">
          <div className="sticky top-24 space-y-5">
            <SectionHeader title="Up Next" subtitle="Keep watching." />
            <div className="space-y-4">
              {recommendations.slice(0, 6).map((rec, index) => (
                <LandscapeCard
                  key={`${rec.id}-${index}`}
                  item={rec}
                  progress={progressMap[rec.id] ?? 0}
                />
              ))}
            </div>
          </div>
        </aside>
      </div>
    </PageContainer>
  );
};
