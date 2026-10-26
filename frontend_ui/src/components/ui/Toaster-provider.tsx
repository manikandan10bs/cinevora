import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, WarningCircle, X } from "@phosphor-icons/react";
import { useToastStore } from "@/hooks/use-toast";

const icons = {
  success: <CheckCircle size={18} weight="fill" className="text-success shrink-0" />,
  error: <WarningCircle size={18} weight="fill" className="text-error shrink-0" />,
  warning: <WarningCircle size={18} weight="fill" className="text-warning shrink-0" />,
  default: null,
};

export const Toaster = () => {
  const { toasts } = useToastStore();

  return (
    <div className="fixed bottom-24 right-4 z-[200] flex flex-col gap-2 md:bottom-6 md:right-6" aria-live="polite">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 12, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.25 }}
            className="flex min-w-[260px] max-w-sm items-start gap-3 rounded-xl border border-border bg-card/95 px-4 py-3.5 shadow-xl backdrop-blur-md"
          >
            {icons[t.variant ?? "default"]}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground">{t.title}</p>
              {t.description && (
                <p className="mt-0.5 text-xs text-muted-foreground">{t.description}</p>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};
