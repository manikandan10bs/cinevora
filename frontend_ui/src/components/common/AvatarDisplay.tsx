import { getAvatar, getAvatarById } from "@/lib/avatarStore";

type AvatarDisplayProps = {
  size?: number;
  className?: string;
  avatarId?: string;
};

export const AvatarDisplay = ({ size = 36, className = "", avatarId }: AvatarDisplayProps) => {
  const avatar = avatarId ? getAvatarById(avatarId) : getAvatar();

  return (
    <div
      className={`overflow-hidden rounded-full bg-card ring-1 ring-border ${className}`}
      style={{ width: size, height: size }}
      title={avatar.label}
    >
      <img
        src={avatar.image}
        alt={avatar.label}
        className="h-full w-full object-cover"
        style={{ objectPosition: avatar.objectPosition }}
      />
    </div>
  );
};
