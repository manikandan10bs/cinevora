type SectionHeaderProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
};

export const SectionHeader = ({
  title,
  subtitle,
  action,
}: SectionHeaderProps) => {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div className="space-y-1.5 min-w-0">
        <h2 className="text-xl font-medium uppercase tracking-[0.12em] text-foreground md:text-2xl">
          {title}
        </h2>
        {subtitle ? (
          <p className="max-w-lg truncate text-sm text-muted-foreground">
            {subtitle}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0 mt-0.5">{action}</div> : null}
    </div>
  );
};
