import avatar1Image from "@/assets/avatars/streamxie-avatar-1.png";
import avatar2Image from "@/assets/avatars/streamxie-avatar-2.png";
import avatar3Image from "@/assets/avatars/streamxie-avatar-3.png";
import avatar4Image from "@/assets/avatars/streamxie-avatar-4.png";
import avatar5Image from "@/assets/avatars/streamxie-avatar-5.png";
import avatar6Image from "@/assets/avatars/streamxie-avatar-6.png";
import avatar7Image from "@/assets/avatars/streamxie-avatar-7.png";
import { migrateLocalStorageKey } from "@/lib/storageKeys";

// Avatar preference stored in localStorage (UI-only preference, not SDK data)
const AVATAR_KEY = "streamxie-avatar";
const LEGACY_AVATAR_KEY = "streamora-avatar";

export type AvatarOption = {
  id: string;
  label: string;
  image: string;
  objectPosition?: string;
};

export const avatarOptions: AvatarOption[] = [
  { id: "av1", label: "Avatar 1", image: avatar1Image },
  { id: "av2", label: "Avatar 2", image: avatar2Image },
  { id: "av3", label: "Avatar 3", image: avatar3Image },
  { id: "av4", label: "Avatar 4", image: avatar4Image },
  { id: "av5", label: "Avatar 5", image: avatar5Image },
  { id: "av6", label: "Avatar 6", image: avatar6Image },
  { id: "av7", label: "Avatar 7", image: avatar7Image, objectPosition: "center top" },
];

export const getAvatarById = (id?: string): AvatarOption =>
  avatarOptions.find((a) => a.id === id) ?? avatarOptions[0];

export const getAvatar = (): AvatarOption => {
  try {
    migrateLocalStorageKey(AVATAR_KEY, LEGACY_AVATAR_KEY);
    const raw = localStorage.getItem(AVATAR_KEY);
    if (raw) {
      return getAvatarById(raw);
    }
  } catch { /* ignore */ }
  return avatarOptions[0];
};

export const setAvatar = (id: string): AvatarOption => {
  migrateLocalStorageKey(AVATAR_KEY, LEGACY_AVATAR_KEY);
  localStorage.setItem(AVATAR_KEY, id);
  return getAvatarById(id);
};
