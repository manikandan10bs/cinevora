export const migrateLocalStorageKey = (currentKey: string, legacyKey: string) => {
  try {
    if (localStorage.getItem(currentKey) === null) {
      const legacyValue = localStorage.getItem(legacyKey);
      if (legacyValue !== null) localStorage.setItem(currentKey, legacyValue);
    }
  } catch {
    // Local storage can be unavailable in strict browser privacy modes.
  }
};
