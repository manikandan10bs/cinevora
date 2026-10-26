import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClockCounterClockwise,
  SignOut,
  FilmStrip,
  Star,
  BookmarkSimple,
  Gear,
  Check,
  UserCircle,
} from "@phosphor-icons/react";
import { motion, AnimatePresence } from "framer-motion";
import { Card } from "@/components/ui/card";
import { PageContainer } from "@/components/layout/PageContainer";
import { GenreChip } from "@/components/common/GenreChip";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";
import { getMyList, getWatchProgress, getSearchHistory } from "@/lib/storage";
import { contentItems } from "@/data/mockContent";
import { avatarOptions, getAvatar, setAvatar, type AvatarOption } from "@/lib/avatarStore";
import { useAuth } from "@/hooks/use-auth";
import { AVATAR_CHANGE_EVENT } from "@/lib/brand";

export const ProfilePage = () => {
  useDocumentMeta("Profile | streamXie", "Review your viewing preferences and account settings.");
  const { user, isAnonymous, login, logout } = useAuth();

  const [myList, setMyList] = useState<string[]>([]);
  const [watchedCount, setWatchedCount] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarOption>(getAvatar());
  const [showAvatarPicker, setShowAvatarPicker] = useState(false);
  const favoriteGenres = ["Sci-Fi", "Fantasy", "Drama", "Anime", "Thriller"];

  useEffect(() => {
    setMyList(getMyList());
    const progress = getWatchProgress();
    setWatchedCount(Object.keys(progress).length);
    setRecentSearches(getSearchHistory());
  }, []);

  const savedItems = contentItems.filter((item) => myList.includes(item.id));

  const handlePickAvatar = (av: AvatarOption) => {
    const updated = setAvatar(av.id);
    setSelectedAvatar(updated);
    setShowAvatarPicker(false);
    // dispatch storage event so Navbar updates
    window.dispatchEvent(new Event(AVATAR_CHANGE_EVENT));
  };

  const stats = [
    { label: "Saved titles", value: myList.length, icon: BookmarkSimple },
    { label: "Watched", value: watchedCount, icon: FilmStrip },
    { label: "Recent searches", value: recentSearches.length, icon: ClockCounterClockwise },
  ];

  const displayName = user?.name || "Guest User";
  const accountType = isAnonymous ? "Guest account" : "Premium account";

  return (
    <PageContainer className="pt-32 pb-16">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* Avatar + name */}
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="relative">
            {/* Avatar circle */}
            <button
              type="button"
              onClick={() => setShowAvatarPicker((v) => !v)}
              className="group relative flex h-28 w-28 items-center justify-center rounded-full ring-4 ring-primary/20 transition-all hover:ring-primary/50 focus-visible:outline-none"
              aria-label="Change avatar"
            >
              <div className="h-28 w-28 overflow-hidden rounded-full bg-card ring-1 ring-border">
                <img
                  src={selectedAvatar.image}
                  alt={selectedAvatar.label}
                  className="h-full w-full object-cover"
                  style={{ objectPosition: selectedAvatar.objectPosition }}
                />
              </div>
              <div className="absolute inset-0 flex items-center justify-center rounded-full bg-background/0 opacity-0 transition-all group-hover:bg-background/40 group-hover:opacity-100">
                <span className="text-xs font-medium text-white">Edit</span>
              </div>
            </button>
            <span className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              PRO
            </span>
          </div>

          {/* Avatar picker modal */}
          <AnimatePresence>
            {showAvatarPicker && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -8 }}
                transition={{ duration: 0.18 }}
                className="z-20 rounded-2xl border border-border bg-card/95 p-5 shadow-2xl backdrop-blur-xl"
              >
                <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Choose your avatar</p>
                <div className="grid grid-cols-4 gap-3">
                  {avatarOptions.map((av) => (
                    <button
                      key={av.id}
                      type="button"
                      onClick={() => handlePickAvatar(av)}
                      title={av.label}
                      className={`relative h-14 w-14 overflow-hidden rounded-xl bg-card transition-all hover:scale-110 ${
                        selectedAvatar.id === av.id ? "ring-2 ring-primary ring-offset-2 ring-offset-card" : ""
                      }`}
                    >
                      <img
                        src={av.image}
                        alt={av.label}
                        className="h-full w-full object-cover"
                        style={{ objectPosition: av.objectPosition }}
                      />
                      {selectedAvatar.id === av.id && (
                        <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary">
                          <Check size={9} weight="bold" className="text-primary-foreground" />
                        </span>
                      )}
                    </button>
                  ))}
                </div>
                <p className="mt-3 text-center text-xs text-muted-foreground">Click to select — saved automatically</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div>
            <h1 className="text-3xl font-medium uppercase tracking-[0.1em] text-foreground">
              {displayName}
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {accountType} · {selectedAvatar.label} avatar
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          {stats.map(({ label, value, icon: Icon }) => (
            <Card key={label} className="flex flex-col items-center gap-2 rounded-xl border border-border bg-card p-5 text-center">
              <Icon size={24} weight="duotone" className="text-primary" />
              <p className="text-2xl font-medium text-foreground">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
            </Card>
          ))}
        </div>

        {/* Favorite genres */}
        <Card className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-xl font-medium text-foreground">
            <Star size={20} weight="duotone" className="text-warning" />
            Favorite Genres
          </h2>
          <div className="flex flex-wrap gap-2">
            {favoriteGenres.map((genre) => (
              <Link key={genre} to={`/genre/${encodeURIComponent(genre)}`}>
                <GenreChip label={genre} />
              </Link>
            ))}
          </div>
        </Card>

        {/* Saved items preview */}
        {savedItems.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-8 text-center">
            <p className="text-sm font-medium text-foreground">Your list is empty</p>
            <p className="mt-1.5 text-xs text-muted-foreground">Browse content and save titles to see them here.</p>
            <Link
              to="/browse"
              className="mt-4 inline-flex min-h-[40px] items-center rounded-lg bg-gradient-primary px-6 py-2 text-xs font-medium text-primary-foreground transition-all hover:brightness-110"
            >
              Browse Now
            </Link>
          </div>
        ) : (
          <Card className="rounded-xl border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-xl font-medium text-foreground">
                <BookmarkSimple size={20} weight="duotone" className="text-primary" />
                My List
              </h2>
              <Link to="/my-list" className="text-sm text-primary hover:underline">View all</Link>
            </div>
            <div className="hide-scrollbar flex gap-3 overflow-x-auto pb-2">
              {savedItems.map((item) => (
                <Link
                  key={item.id}
                  to={item.type === "movie" ? `/movie/${item.slug}` : `/series/${item.slug}`}
                  className="shrink-0"
                >
                  <img
                    src={item.posterImage}
                    alt={item.posterAlt}
                    className="h-28 w-20 rounded-lg object-cover ring-1 ring-border transition-all hover:ring-primary"
                  />
                </Link>
              ))}
            </div>
          </Card>
        )}

        {/* Recent searches */}
        {recentSearches.length > 0 && (
          <Card className="rounded-xl border border-border bg-card p-6">
            <h2 className="mb-4 flex items-center gap-2 text-xl font-medium text-foreground">
              <ClockCounterClockwise size={20} weight="duotone" className="text-muted-foreground" />
              Recent Searches
            </h2>
            <div className="flex flex-wrap gap-2">
              {recentSearches.map((q) => (
                <Link
                  key={q}
                  to={`/search?q=${encodeURIComponent(q)}`}
                  className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                >
                  {q}
                </Link>
              ))}
            </div>
          </Card>
        )}

        {/* Settings */}
        <Card className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-xl font-medium text-foreground">
            <Gear size={20} weight="duotone" className="text-muted-foreground" />
            Settings
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3">
              <span className="text-sm text-foreground">Dark cinematic theme</span>
              <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-medium text-primary">Active</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3">
              <span className="text-sm text-foreground">Auto-play next episode</span>
              <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-medium text-primary">On</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3">
              <span className="text-sm text-foreground">Subtitle language</span>
              <span className="text-sm text-muted-foreground">English</span>
            </div>
            {isAnonymous ? (
              <button
                type="button"
                onClick={() => login()}
                className="flex w-full items-center gap-3 rounded-lg border border-primary/40 bg-primary/10 px-4 py-3 text-sm text-primary transition-colors hover:bg-primary/20"
              >
                <UserCircle size={16} weight="bold" />
                Sign in to sync your data
              </button>
            ) : (
              <button
                type="button"
                onClick={() => logout()}
                className="flex w-full items-center gap-3 rounded-lg border border-border bg-background px-4 py-3 text-sm text-muted-foreground transition-colors hover:border-red-500 hover:text-red-400"
              >
                <SignOut size={16} weight="bold" />
                Sign out
              </button>
            )}
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};
