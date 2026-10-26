import { useToastStore } from "@/hooks/use-toast"
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"

export function Toaster() {
  const { toasts } = useToastStore()

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, variant }) {
        const toastVariant = variant === "success" ? "success" : variant === "error" ? "destructive" : "default"

        return (
          <Toast key={id} variant={toastVariant}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && (
                <ToastDescription>{description}</ToastDescription>
              )}
            </div>
            <ToastClose />
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}
