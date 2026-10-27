import { migrateLocalStorageKey } from "@/lib/storageKeys";

export type WatchProgressEntry = {
  contentId: string;
  episodeId?: string;
  progress: number;
  duration: number;
  updatedAt: number;
};

const MY_LIST_KEY = "streamxie-my-list";
const WATCH_PROGRESS_KEY = "streamxie-watch-progress";
const SEARCH_HISTORY_KEY = "streamxie-search-history";

const LEGACY_MY_LIST_KEY = "streamora-my-list";
const LEGACY_WATCH_PROGRESS_KEY = "streamora-watch-progress";
const LEGACY_SEARCH_HISTORY_KEY = "streamora-search-history";

const migrateStorage = () => {
  migrateLocalStorageKey(MY_LIST_KEY, LEGACY_MY_LIST_KEY);
  migrateLocalStorageKey(WATCH_PROGRESS_KEY, LEGACY_WATCH_PROGRESS_KEY);
  migrateLocalStorageKey(SEARCH_HISTORY_KEY, LEGACY_SEARCH_HISTORY_KEY);
};

export const getMyList = (): string[] => {
  try {
    migrateStorage();
    const raw = localStorage.getItem(MY_LIST_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

export const toggleMyList = (id: string): string[] => {
  const current = getMyList();
  const next = current.includes(id)
    ? current.filter((item) => item !== id)
    : [...current, id];
  localStorage.setItem(MY_LIST_KEY, JSON.stringify(next));
  return next;
};

export const getWatchProgress = (): Record<string, WatchProgressEntry> => {
  try {
    migrateStorage();
    const raw = localStorage.getItem(WATCH_PROGRESS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

export const saveWatchProgress = (entry: WatchProgressEntry) => {
  const current = getWatchProgress();
  current[entry.contentId] = entry;
  localStorage.setItem(WATCH_PROGRESS_KEY, JSON.stringify(current));
};

export const getSearchHistory = (): string[] => {
  try {
    migrateStorage();
    const raw = localStorage.getItem(SEARCH_HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

export const saveSearchTerm = (term: string) => {
  const current = getSearchHistory().filter(
    (item) => item.toLowerCase() !== term.toLowerCase(),
  );
  const next = [term, ...current].slice(0, 6);
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(next));
  return next;
};
