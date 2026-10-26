export const LoadingSkeleton = ({ className = "" }: { className?: string }) => {
  return (
    <div
      className={`skeleton-shimmer rounded-lg ${className}`}
      aria-hidden="true"
    />
  );
};
