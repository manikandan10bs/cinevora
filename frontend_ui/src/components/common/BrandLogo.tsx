import brandLogoUrl from "@/assets/streamxie-brand-logo.png";
import { BRAND_NAME } from "@/lib/brand";
import { cn } from "@/lib/utils";

type BrandLogoSize = "sm" | "md" | "lg";

type BrandLogoProps = {
  size?: BrandLogoSize;
  showText?: boolean;
  className?: string;
  markClassName?: string;
  textClassName?: string;
};

const sizeStyles: Record<BrandLogoSize, { mark: string; text: string }> = {
  sm: {
    mark: "h-8 w-11",
    text: "text-base",
  },
  md: {
    mark: "h-10 w-14",
    text: "text-xl",
  },
  lg: {
    mark: "h-12 w-16",
    text: "text-2xl",
  },
};

export const BrandLogo = ({
  size = "sm",
  showText = true,
  className,
  markClassName,
  textClassName,
}: BrandLogoProps) => {
  const styles = sizeStyles[size];

  return (
    <span className={cn("inline-flex items-center gap-2.5 text-current", className)}>
      <span className={cn("flex shrink-0 items-center justify-center", styles.mark, markClassName)}>
        <img
          src={brandLogoUrl}
          alt=""
          aria-hidden="true"
          className="h-full w-full object-contain drop-shadow-[0_0_12px_hsl(var(--color-primary)/0.28)]"
        />
      </span>
      {showText && (
        <span className={cn("font-bold tracking-[0.08em]", styles.text, textClassName)}>
          {BRAND_NAME}
        </span>
      )}
    </span>
  );
};
