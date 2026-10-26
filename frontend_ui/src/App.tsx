import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { CommandPalette } from "@/components/common/CommandPalette";
import { AiConciergeModal } from "@/components/assistant/AiConciergeModal";
import { HomePage } from "@/pages/HomePage";
import { BrowsePage } from "@/pages/BrowsePage";
import { MovieDetailPage } from "@/pages/MovieDetailPage";
import { SeriesDetailPage } from "@/pages/SeriesDetailPage";
import { WatchPage } from "@/pages/WatchPage";
import { SearchPage } from "@/pages/SearchPage";
import { MyListPage } from "@/pages/MyListPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { GenrePage } from "@/pages/GenrePage";
import { StaticPage } from "@/pages/StaticPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { MonitoringPage } from "@/pages/MonitoringPage";
import { getMyList, getWatchProgress, toggleMyList } from "@/lib/storage";
import { toast } from "@/hooks/use-toast";
import { cinevoraApi, getActiveUserId } from "@/lib/cinevoraClient";

const ScrollToTop = () => {
  const location = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [location.pathname, location.search]);

  return null;
};

const AppRoutes = () => {
  const [commandOpen, setCommandOpen] = useState(false);
  const [aiConciergeOpen, setAiConciergeOpen] = useState(false);
  const [myList, setMyList] = useState<string[]>([]);
  const [progressVersion, setProgressVersion] = useState(0);

  const activeUser = getActiveUserId();

  // Load initial watchlist from SQLite + localStorage
  useEffect(() => {
    const local = getMyList();
    setMyList(local);

    cinevoraApi.getUserFavorites(activeUser).then((favs) => {
      if (favs && favs.length > 0) {
        const remoteIds = favs.map((f) => f.id);
        const combined = Array.from(new Set([...local, ...remoteIds]));
        setMyList(combined);
      }
    });

    const interval = window.setInterval(
      () => setProgressVersion((current) => current + 1),
      1000
    );
    return () => window.clearInterval(interval);
  }, [activeUser]);

  const progressMap = useMemo(() => {
    const progress = getWatchProgress();
    return Object.fromEntries(
      Object.entries(progress).map(([key, value]) => [key, value.progress])
    );
  }, [progressVersion]);

  const handleToggleList = async (id: string) => {
    const prev = myList;
    const isCurrentlyIn = prev.includes(id);

    if (isCurrentlyIn) {
      // Remove from list
      const next = toggleMyList(id);
      setMyList(next);
      await cinevoraApi.removeFavorite(activeUser, id);
      toast({
        title: "Removed from Watchlist",
        variant: "default",
      });
    } else {
      // Add to list
      const next = toggleMyList(id);
      setMyList(next);

      // Fetch metadata to save in SQLite
      cinevoraApi.getMovieDetails(id).then((movie) => {
        if (movie) {
          cinevoraApi.addFavorite(activeUser, movie);
        }
      });

      toast({
        title: "Added to Watchlist",
        variant: "success",
      });
    }
  };

  return (
    <>
      <ScrollToTop />
      <AppLayout
        onOpenCommand={() => setCommandOpen(true)}
        onOpenAiConcierge={() => setAiConciergeOpen(true)}
      >
        <Routes>
          <Route
            path="/"
            element={
              <HomePage
                myList={myList}
                onToggleList={handleToggleList}
                progressMap={progressMap}
              />
            }
          />
          <Route
            path="/browse"
            element={
              <BrowsePage myList={myList} onToggleList={handleToggleList} />
            }
          />
          <Route
            path="/movie/:slug"
            element={
              <MovieDetailPage
                myList={myList}
                onToggleList={handleToggleList}
              />
            }
          />
          <Route
            path="/series/:slug"
            element={
              <SeriesDetailPage
                myList={myList}
                onToggleList={handleToggleList}
              />
            }
          />
          <Route
            path="/watch/:id"
            element={<WatchPage progressMap={progressMap} />}
          />
          <Route
            path="/search"
            element={
              <SearchPage myList={myList} onToggleList={handleToggleList} />
            }
          />
          <Route
            path="/my-list"
            element={
              <MyListPage
                myList={myList}
                onToggleList={handleToggleList}
                progressMap={progressMap}
              />
            }
          />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/dashboard" element={<MonitoringPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route
            path="/genre/:name"
            element={<GenrePage myList={myList} onToggleList={handleToggleList} />}
          />
          <Route path="/privacy" element={<StaticPage page="privacy" />} />
          <Route path="/terms" element={<StaticPage page="terms" />} />
          <Route path="/cookies" element={<StaticPage page="cookies" />} />
          <Route path="/about" element={<StaticPage page="about" />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Routes>
      </AppLayout>

      {/* Global Command Palette (⌘K) */}
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />

      {/* Cinevora AI Movie Concierge Floating Modal (Gemini 3.5 Flash) */}
      <AiConciergeModal
        open={aiConciergeOpen}
        onClose={() => setAiConciergeOpen(false)}
      />
    </>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
