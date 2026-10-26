import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  MagnifyingGlass,
  UserCircle,
  BookmarkSimple,
  House,
  FilmStrip,
  Television,
  GridFour,
  List as ListIcon,
  X,
  CaretDown,
  Sparkle,
  Gauge,
  User,
  SignOut,
  SignIn,
  UserPlus,
} from "@phosphor-icons/react";
import { getAvatar, type AvatarOption } from "@/lib/avatarStore";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useAuth } from "@/hooks/use-auth";
import { AVATAR_CHANGE_EVENT, LEGACY_AVATAR_CHANGE_EVENT } from "@/lib/brand";
import { DEMO_ACCOUNTS, getActiveUserId, setActiveUserId } from "@/lib/cinevoraClient";

type NavbarProps = {
  onOpenCommand: () => void;
  onOpenAiConcierge?: () => void;
};

const browseCategories = [
  { label: "Tamil (Kollywood)", href: "/browse?industry=Tamil" },
  { label: "Bollywood (Hindi)", href: "/browse?industry=Bollywood" },
  { label: "Telugu (Tollywood)", href: "/browse?industry=Telugu" },
  { label: "Malayalam (Mollywood)", href: "/browse?industry=Malayalam" },
  { label: "Kannada (Sandalwood)", href: "/browse?industry=Kannada" },
  { label: "Hollywood & Global", href: "/browse?industry=Hollywood" },
];

export const Navbar = ({ onOpenCommand, onOpenAiConcierge }: NavbarProps) => {
  const { user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [browseDropdownOpen, setBrowseDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [avatar, setAvatarState] = useState<AvatarOption>(getAvatar());
  const [currentUserId, setCurrentUserId] = useState(getActiveUserId());

  const dropdownRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 32);
    handler();
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
    setBrowseDropdownOpen(false);
    setUserDropdownOpen(false);
  }, [location.pathname, location.search]);

  // Refresh avatar when profile page changes it
  useEffect(() => {
    const handler = () => setAvatarState(getAvatar());
    window.addEventListener(AVATAR_CHANGE_EVENT, handler);
    window.addEventListener(LEGACY_AVATAR_CHANGE_EVENT, handler);
    return () => {
      window.removeEventListener(AVATAR_CHANGE_EVENT, handler);
      window.removeEventListener(LEGACY_AVATAR_CHANGE_EVENT, handler);
    };
  }, []);

  // Listen to Cinevora user change event
  useEffect(() => {
    const handler = () => setCurrentUserId(getActiveUserId());
    window.addEventListener("cinevora-user-change", handler);
    return () => window.removeEventListener("cinevora-user-change", handler);
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setBrowseDropdownOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const isHome = location.pathname === "/";
  const isTransparent = isHome && !scrolled;
  const isBrowseActive = location.pathname === "/browse";

  const handleSelectUser = (key: string) => {
    setActiveUserId(key);
    setUserDropdownOpen(false);
    window.location.reload(); // Reload to refresh personalized recommendations
  };

  const isCustomUser = Boolean(user && user.username);
  const matchedDemo = DEMO_ACCOUNTS.find((a) => a.key === currentUserId);
  const activeDisplayName = isCustomUser
    ? user!.name || user!.username || "Cinevora User"
    : matchedDemo?.name || currentUserId;
  const activeRoleSubtitle = isCustomUser
    ? `@${user!.username} (SQLite DB)`
    : matchedDemo?.role || "Demo Persona";
  const avatarLetter = (activeDisplayName[0] || "U").toUpperCase();

  const handleLogout = async () => {
    await logout();
    setUserDropdownOpen(false);
    navigate("/");
    window.location.reload();
  };


  return (
    <>
      <header
        className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
          isTransparent
            ? "bg-transparent"
            : "border-b border-border/60 bg-background/95 shadow-sm backdrop-blur-md"
        }`}
      >
        <nav className="mx-auto flex max-w-container items-center justify-between gap-4 px-6 py-3 md:px-12 lg:gap-8">
          {/* Brand Logo */}
          <Link
            to="/"
            className="shrink-0 text-foreground transition-colors hover:text-primary focus-visible:outline-none flex items-center gap-2"
          >
            <BrandLogo size="sm" textClassName="text-xl font-black tracking-wider text-foreground" />
          </Link>

          {/* Desktop Nav Items */}
          <div className="hidden flex-1 items-center justify-center lg:flex">
            <NavigationMenu>
              <NavigationMenuList className="flex items-center gap-1">
                {/* Home */}
                <NavigationMenuItem>
                  <NavLink
                    to="/"
                    end
                    className={({ isActive: a }) =>
                      `relative flex h-9 items-center rounded-lg px-3.5 text-sm font-medium transition-colors ${
                        a ? "text-primary" : "text-muted-foreground hover:text-foreground"
                      }`
                    }
                  >
                    {({ isActive: a }) => (
                      <>
                        Home
                        {a && (
                          <span className="absolute inset-x-3 -bottom-0.5 h-0.5 rounded-full bg-primary" />
                        )}
                      </>
                    )}
                  </NavLink>
                </NavigationMenuItem>

                {/* Browse Dropdown */}
                <NavigationMenuItem>
                  <div ref={dropdownRef} className="relative">
                    <button
                      type="button"
                      onClick={() => setBrowseDropdownOpen((v) => !v)}
                      className={`relative flex h-9 items-center gap-1.5 rounded-lg px-3.5 text-sm font-medium transition-colors cursor-pointer ${
                        isBrowseActive ? "text-primary" : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Browse Catalog
                      <CaretDown
                        size={12}
                        weight="bold"
                        className={`transition-transform duration-200 ${
                          browseDropdownOpen ? "rotate-180" : ""
                        }`}
                      />
                      {isBrowseActive && (
                        <span className="absolute inset-x-3 -bottom-0.5 h-0.5 rounded-full bg-primary" />
                      )}
                    </button>

                    {browseDropdownOpen && (
                      <div className="absolute left-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-card/95 py-1.5 shadow-2xl backdrop-blur-xl">
                        <div className="px-3 py-2">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                            Cinema Regions
                          </p>
                        </div>
                        {browseCategories.map((cat) => (
                          <Link
                            key={cat.label}
                            to={cat.href}
                            className="flex items-center gap-2.5 px-4 py-2 text-xs font-medium text-foreground hover:bg-primary/10 hover:text-primary transition-colors"
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                            {cat.label}
                          </Link>
                        ))}
                        <div className="mx-3 my-1.5 border-t border-border" />
                        <Link
                          to="/browse"
                          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-primary hover:bg-primary/10 transition-colors"
                        >
                          <GridFour size={14} weight="duotone" />
                          View All 3,560 Movies
                        </Link>
                      </div>
                    )}
                  </div>
                </NavigationMenuItem>

                {/* My List */}
                <NavigationMenuItem>
                  <NavLink
                    to="/my-list"
                    className={({ isActive: a }) =>
                      `relative flex h-9 items-center rounded-lg px-3.5 text-sm font-medium transition-colors ${
                        a ? "text-primary" : "text-muted-foreground hover:text-foreground"
                      }`
                    }
                  >
                    {({ isActive: a }) => (
                      <>
                        My List
                        {a && (
                          <span className="absolute inset-x-3 -bottom-0.5 h-0.5 rounded-full bg-primary" />
                        )}
                      </>
                    )}
                  </NavLink>
                </NavigationMenuItem>

                {/* Monitoring Dashboard */}
                <NavigationMenuItem>
                  <NavLink
                    to="/monitoring"
                    className={({ isActive: a }) =>
                      `relative flex h-9 items-center gap-1.5 rounded-lg px-3.5 text-sm font-medium transition-colors ${
                        a ? "text-primary" : "text-muted-foreground hover:text-foreground"
                      }`
                    }
                  >
                    {({ isActive: a }) => (
                      <>
                        <Gauge size={15} weight="bold" />
                        Monitoring
                        {a && (
                          <span className="absolute inset-x-3 -bottom-0.5 h-0.5 rounded-full bg-primary" />
                        )}
                      </>
                    )}
                  </NavLink>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>
          </div>

          {/* Right side desktop controls */}
          <div className="hidden items-center gap-3 md:flex">
            {/* AI Concierge Trigger Button */}
            {onOpenAiConcierge && (
              <button
                type="button"
                onClick={onOpenAiConcierge}
                className="flex h-9 items-center gap-1.5 rounded-xl border border-primary/40 bg-gradient-to-r from-primary/20 via-cyan-500/10 to-primary/20 px-3.5 text-xs font-bold text-primary shadow-sm hover:brightness-110 hover:shadow-primary/25 transition-all cursor-pointer"
              >
                <Sparkle size={15} weight="fill" className="text-primary animate-pulse" />
                AI Concierge
              </button>
            )}

            {/* Quick Search Button */}
            <button
              type="button"
              aria-label="Open search"
              onClick={onOpenCommand}
              className="flex h-9 min-w-[170px] items-center justify-between gap-3 rounded-xl border border-border bg-card/60 px-3.5 py-2 text-xs text-muted-foreground backdrop-blur-sm transition-all hover:border-primary/60 hover:text-foreground cursor-pointer"
            >
              <span className="flex items-center gap-2">
                <MagnifyingGlass size={15} weight="bold" className="text-primary" />
                <span>Search catalog...</span>
              </span>
              <kbd className="hidden rounded border border-border bg-muted px-1.5 py-0.5 text-[9px] font-mono text-muted-foreground xl:block">
                ⌘K
              </kbd>
            </button>

            {/* User Account / Profile Dropdown */}
            <div ref={userMenuRef} className="relative">
              <button
                type="button"
                onClick={() => setUserDropdownOpen((v) => !v)}
                className="flex items-center gap-2 rounded-xl border border-border bg-card/80 px-2.5 py-1 text-xs font-semibold text-foreground hover:border-primary transition-all cursor-pointer"
                title="Account & Profile Management"
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-primary font-bold text-[10px]">
                  {avatarLetter}
                </span>
                <span className="hidden xl:inline">{activeDisplayName.split(" ")[0]}</span>
                <CaretDown size={11} weight="bold" className="text-muted-foreground" />
              </button>

              {userDropdownOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-2xl border border-border bg-card/95 py-2 shadow-2xl backdrop-blur-xl">
                  {/* Active Profile Info */}
                  <div className="px-4 py-2 border-b border-border/50">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                      Active Profile
                    </p>
                    <p className="text-xs font-bold text-primary mt-0.5 truncate">{activeDisplayName}</p>
                    <p className="text-[11px] text-muted-foreground">{activeRoleSubtitle}</p>
                  </div>

                  {/* Manual User Management Actions */}
                  <div className="py-1 border-b border-border/50">
                    <Link
                      to="/register"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-foreground hover:bg-primary/10 hover:text-primary transition-colors"
                    >
                      <UserPlus size={15} weight="bold" className="text-primary" />
                      <span>Manual Add / Register User</span>
                    </Link>

                    {isCustomUser ? (
                      <button
                        type="button"
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-4 py-2 text-xs font-medium text-red-400 hover:bg-red-500/10 transition-colors text-left cursor-pointer"
                      >
                        <SignOut size={15} weight="bold" />
                        <span>Log Out ({user?.username})</span>
                      </button>
                    ) : (
                      <Link
                        to="/login"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-foreground hover:bg-primary/10 hover:text-primary transition-colors"
                      >
                        <SignIn size={15} weight="bold" className="text-emerald-400" />
                        <span>Sign In with Account</span>
                      </Link>
                    )}
                  </div>

                  {/* Demo Personas */}
                  <div className="py-1">
                    <p className="px-4 py-1 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                      Demo Personas
                    </p>
                    {DEMO_ACCOUNTS.map((acc) => (
                      <button
                        key={acc.key}
                        type="button"
                        onClick={() => handleSelectUser(acc.key)}
                        className={`w-full flex items-center justify-between px-4 py-1.5 text-xs text-left transition-colors cursor-pointer ${
                          acc.key === currentUserId && !isCustomUser
                            ? "bg-primary/15 text-primary font-bold"
                            : "text-foreground hover:bg-muted/60"
                        }`}
                      >
                        <div>
                          <div>{acc.name}</div>
                          <div className="text-[10px] text-muted-foreground">{acc.role}</div>
                        </div>
                        {acc.key === currentUserId && !isCustomUser && (
                          <span className="text-primary text-xs font-bold">✓</span>
                        )}
                      </button>
                    ))}
                  </div>

                  <div className="mx-3 my-1 border-t border-border" />
                  <Link
                    to="/profile"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-foreground hover:text-primary transition-colors"
                  >
                    <User size={14} />
                    Account Settings
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Mobile Right Controls */}
          <div className="flex items-center gap-2 md:hidden">
            {onOpenAiConcierge && (
              <button
                type="button"
                onClick={onOpenAiConcierge}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary border border-primary/40 cursor-pointer"
                title="AI Concierge"
              >
                <Sparkle size={16} weight="fill" />
              </button>
            )}
            <button
              type="button"
              onClick={onOpenCommand}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground"
            >
              <MagnifyingGlass size={16} />
            </button>
            <button
              type="button"
              onClick={() => setMobileMenuOpen((v) => !v)}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground"
            >
              {mobileMenuOpen ? <X size={18} /> : <ListIcon size={18} />}
            </button>
          </div>
        </nav>

        {/* Mobile menu drawer */}
        {mobileMenuOpen && (
          <div className="border-b border-border bg-card/95 px-6 py-4 md:hidden space-y-3">
            <Link to="/" className="block py-1.5 text-sm font-semibold text-foreground">
              Home
            </Link>
            <Link to="/browse" className="block py-1.5 text-sm font-semibold text-foreground">
              Browse Catalog (3,560 titles)
            </Link>
            <Link to="/my-list" className="block py-1.5 text-sm font-semibold text-foreground">
              My Watchlist
            </Link>
            <Link to="/monitoring" className="block py-1.5 text-sm font-semibold text-foreground">
              Monitoring Dashboard
            </Link>
            <div className="pt-2 border-t border-border/50 flex flex-col gap-2">
              <Link
                to="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-medium text-primary flex items-center gap-2"
              >
                <UserPlus size={16} />
                + Add / Register User Manually
              </Link>
              {isCustomUser ? (
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    handleLogout();
                  }}
                  className="text-left text-sm font-medium text-red-400 flex items-center gap-2"
                >
                  <SignOut size={16} />
                  Log Out ({user?.username})
                </button>
              ) : (
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-sm font-medium text-emerald-400 flex items-center gap-2"
                >
                  <SignIn size={16} />
                  Sign In with Account
                </Link>
              )}
            </div>
            {onOpenAiConcierge && (
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onOpenAiConcierge();
                }}
                className="w-full text-left py-1.5 text-sm font-bold text-primary flex items-center gap-2"
              >
                <Sparkle size={15} weight="fill" />
                Launch AI Concierge
              </button>
            )}
          </div>
        )}
      </header>
    </>
  );
};

export const MobileNavMenu = () => {
  const location = useLocation();

  const items = [
    { label: "Home", href: "/", icon: House },
    { label: "Browse", href: "/browse", icon: FilmStrip },
    { label: "Search", href: "/search", icon: MagnifyingGlass },
    { label: "My List", href: "/my-list", icon: BookmarkSimple },
    { label: "Monitor", href: "/monitoring", icon: Gauge },
  ];

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-background/95 backdrop-blur-md md:hidden">
      <div className="grid grid-cols-5">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            location.pathname === item.href ||
            (item.href !== "/" && location.pathname.startsWith(item.href));
          return (
            <Link
              key={item.label}
              to={item.href}
              className={`flex min-h-[60px] flex-col items-center justify-center gap-1 px-2 py-3 text-[10px] font-medium transition-colors ${
                active ? "text-primary" : "text-muted-foreground hover:text-foreground"
              }`}
              aria-label={item.label}
            >
              <Icon size={20} weight={active ? "fill" : "regular"} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
