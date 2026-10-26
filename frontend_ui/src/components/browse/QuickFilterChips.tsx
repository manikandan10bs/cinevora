type QuickFilterChipsProps = {
  filters: string[];
  active: string;
  onChange: (value: string) => void;
};

export const QuickFilterChips = ({
  filters,
  active,
  onChange,
}: QuickFilterChipsProps) => {
  return (
    <div className="flex flex-wrap gap-3">
      {filters.map((filter) => (
        <button
          key={filter}
          type="button"
          onClick={() => onChange(filter)}
          className={`min-h-[44px] rounded-full border px-4 py-2 text-sm transition-colors ${active === filter ? "border-primary bg-primary/15 text-primary" : "border-border bg-card text-foreground hover:border-primary hover:text-primary"}`}
        >
          {filter}
        </button>
      ))}
    </div>
  );
};
