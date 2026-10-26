import { Link } from "react-router-dom";

type GenreChipProps = {
  label: string;
  /** If true renders a plain <span> (e.g. inside another <Link>) */
  static?: boolean;
};

export const GenreChip = ({ label, static: isStatic }: GenreChipProps) => {
  const cls = "inline-flex rounded-full border border-border bg-secondary/30 px-3 py-1.5 text-xs text-secondary-foreground transition-colors hover:border-primary hover:text-primary";

  if (isStatic) {
    return <span className={cls}>{label}</span>;
  }

  return (
    <Link to={`/genre/${encodeURIComponent(label)}`} className={cls}>
      {label}
    </Link>
  );
};
