import { motion } from "framer-motion";
import { CastMember } from "@/data/mockContent";

function getInitials(name: string): string {
  if (!name) return "A";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export const CastGrid = ({ cast }: { cast: CastMember[] }) => {
  if (!cast || cast.length === 0) return null;

  return (
    <section className="py-8 md:py-10">
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-2xl font-medium uppercase tracking-[0.12em] text-foreground">
          Ensemble Cast
        </h2>
        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full border border-border bg-card text-muted-foreground">
          {cast.length} Verified Actors
        </span>
      </div>

      <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {cast.map((member, i) => (
          <motion.div
            key={`${member.name}-${i}`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
            className="flex items-center gap-3 p-3 rounded-xl border border-border/80 bg-card hover:border-primary/50 transition-all card-glow"
          >
            {/* Initials Avatar Badge */}
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 via-primary/10 to-transparent border border-primary/30 text-primary font-bold text-sm tracking-wider shadow-inner">
              {getInitials(member.name)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-foreground" title={member.name}>
                {member.name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {member.role || "Cast"}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
};
