import { FilmStrip } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

type EmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
};

export const EmptyState = ({ title, description, actionLabel, actionHref }: EmptyStateProps) => {
  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 px-8 py-16 text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-border bg-muted text-primary">
        <FilmStrip size={48} weight="duotone" />
      </div>
      <h3 className="text-2xl font-medium text-foreground">{title}</h3>
      <p className="mt-3 max-w-md text-sm text-muted-foreground md:text-base">{description}</p>
      {actionLabel && actionHref && (
        <Link
          to={actionHref}
          className="mt-6 inline-flex min-h-[48px] items-center rounded-xl bg-gradient-primary px-8 py-3 text-sm font-medium text-primary-foreground transition-all hover:brightness-110"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
};
