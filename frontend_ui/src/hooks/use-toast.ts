import { useCallback, useEffect, useRef, useState } from "react";

export type ToastVariant = "default" | "success" | "error" | "warning";

export type Toast = {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
};

let _listeners: Array<(toasts: Toast[]) => void> = [];
let _toasts: Toast[] = [];

const notify = () => {
  _listeners.forEach((fn) => fn([..._toasts]));
};

export const toast = (opts: Omit<Toast, "id">) => {
  const id = Math.random().toString(36).slice(2);
  _toasts = [{ id, ...opts }, ..._toasts].slice(0, 4);
  notify();
  window.setTimeout(() => {
    _toasts = _toasts.filter((t) => t.id !== id);
    notify();
  }, 3200);
};

export const useToastStore = () => {
  const [toasts, setToasts] = useState<Toast[]>(_toasts);
  const cbRef = useRef<(t: Toast[]) => void>(() => {});
  cbRef.current = setToasts;

  const stable = useCallback((t: Toast[]) => cbRef.current(t), []);

  useEffect(() => {
    _listeners.push(stable);
    return () => {
      _listeners = _listeners.filter((fn) => fn !== stable);
    };
  }, [stable]);

  return { toasts };
};
