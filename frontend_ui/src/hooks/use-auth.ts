import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "@/lib/brand";
import { migrateLocalStorageKey } from "@/lib/storageKeys";
import { cinevoraApi, setActiveUserId, DEFAULT_USER_ID } from "@/lib/cinevoraClient";

export type DemoUser = {
  id?: number;
  name: string;
  username?: string;
  email?: string;
};

type LoginOptions = {
  username?: string;
  password?: string;
  name?: string;
  email?: string;
};

type RegisterOptions = {
  username: string;
  password: string;
  displayName?: string;
};

const AUTH_USER_KEY = "streamxie-auth-user";
const LEGACY_AUTH_USER_KEY = "streamora-auth-user";
const listeners = new Set<() => void>();

const emitAuthChange = () => {
  listeners.forEach((listener) => listener());
};

const isBrowser = () => typeof window !== "undefined";

const readUser = (): DemoUser | null => {
  if (!isBrowser()) return null;

  try {
    const session = cinevoraApi.getCurrentUser();
    if (session) {
      return {
        id: session.id,
        name: session.display_name || session.username,
        username: session.username,
      };
    }

    migrateLocalStorageKey(AUTH_USER_KEY, LEGACY_AUTH_USER_KEY);
    const raw = localStorage.getItem(AUTH_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const writeUser = (user: DemoUser | null) => {
  if (!isBrowser()) return;

  if (user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    localStorage.removeItem(LEGACY_AUTH_USER_KEY);
    if (user.username) {
      setActiveUserId(user.username);
    }
  } else {
    localStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(LEGACY_AUTH_USER_KEY);
    cinevoraApi.logoutUser();
  }

  emitAuthChange();
};

const getDisplayName = ({ name, email, username }: LoginOptions) => {
  const trimmedName = name?.trim();
  if (trimmedName) return trimmedName;

  const trimmedUsername = username?.trim();
  if (trimmedUsername) return trimmedUsername;

  const trimmedEmail = email?.trim();
  if (trimmedEmail) return trimmedEmail.split("@")[0] || trimmedEmail;

  return `${BRAND_NAME} Member`;
};

export const useAuth = () => {
  const [user, setUser] = useState<DemoUser | null>(() => readUser());
  const [isPending, setIsPending] = useState(false);

  useEffect(() => {
    const syncUser = () => setUser(readUser());

    listeners.add(syncUser);
    window.addEventListener("storage", syncUser);
    window.addEventListener("cinevora-user-change", syncUser);

    return () => {
      listeners.delete(syncUser);
      window.removeEventListener("storage", syncUser);
      window.removeEventListener("cinevora-user-change", syncUser);
    };
  }, []);

  const login = useCallback(async (options: LoginOptions = {}) => {
    setIsPending(true);

    try {
      const uname = (options.username || options.email || "").trim();
      const pwd = options.password?.trim();

      if (pwd && uname) {
        // Authenticate with real Cinevora FastAPI backend & SQLite DB
        const res = await cinevoraApi.loginUser(uname, pwd);
        const nextUser: DemoUser = {
          id: res.id,
          name: res.display_name || res.username,
          username: res.username,
        };
        writeUser(nextUser);
        setUser(nextUser);
        return nextUser;
      }

      // Fallback local session if no password passed
      const nextUser: DemoUser = {
        name: getDisplayName(options),
        username: uname || undefined,
        email: options.email?.trim() || undefined,
      };

      writeUser(nextUser);
      setUser(nextUser);
      return nextUser;
    } finally {
      setIsPending(false);
    }
  }, []);

  const register = useCallback(async (options: RegisterOptions) => {
    setIsPending(true);

    try {
      const res = await cinevoraApi.registerUser(
        options.username.trim(),
        options.password.trim(),
        options.displayName?.trim()
      );
      const nextUser: DemoUser = {
        id: res.id,
        name: res.display_name || res.username,
        username: res.username,
      };
      writeUser(nextUser);
      setUser(nextUser);
      return nextUser;
    } finally {
      setIsPending(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsPending(true);

    try {
      writeUser(null);
      setUser(null);
    } finally {
      setIsPending(false);
    }
  }, []);

  return {
    user,
    isAnonymous: !user,
    isPending,
    login,
    register,
    logout,
  };
};
