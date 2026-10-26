import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeSlash, LockKey, User, Sparkle } from "@phosphor-icons/react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useAuth } from "@/hooks/use-auth";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";

export const LoginPage = () => {
  useDocumentMeta("Sign In | Cinevora", "Sign in to your Cinevora account.");
  const { login, isPending } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!username.trim() || !password.trim()) {
      setError("Please enter both username and password.");
      return;
    }
    try {
      await login({ username: username.trim(), password: password.trim() });
      navigate("/");
    } catch (err: any) {
      setError(err?.message || "Invalid credentials. Please verify your username and password.");
    }
  };

  const handleDemoSignIn = async (demoName: string) => {
    try {
      await login({ name: demoName, username: demoName });
      navigate("/");
    } catch {}
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      {/* Background gradient blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute -bottom-32 -right-32 h-80 w-80 rounded-full bg-primary/8 blur-[100px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <Link to="/" className="text-foreground transition-colors hover:text-primary">
            <BrandLogo size="md" />
          </Link>
          <p className="text-sm text-muted-foreground">Manual Cinevora SQLite Authentication</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-border bg-card/80 p-8 shadow-2xl backdrop-blur-xl">
          <h1 className="mb-2 text-center text-2xl font-bold tracking-tight text-foreground">Sign In</h1>
          <p className="mb-6 text-center text-xs text-muted-foreground">
            Enter your Cinevora username and password to access your personalized feed.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div className="space-y-1.5">
              <label htmlFor="username" className="block text-sm font-medium text-muted-foreground">
                Username
              </label>
              <div className="relative">
                <User size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. alex_chen or manikandan"
                  className="w-full rounded-lg border border-border bg-background pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium text-muted-foreground">
                  Password
                </label>
              </div>
              <div className="relative">
                <LockKey size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-border bg-background pl-10 pr-10 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeSlash size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <p className="rounded-lg border border-red-700/40 bg-red-950/40 px-4 py-2.5 text-xs text-red-400">
                {error}
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isPending}
              className="mt-2 w-full rounded-lg bg-gradient-primary py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed cinematic-glow cursor-pointer"
            >
              {isPending ? "Authenticating…" : "Sign In to Cinevora"}
            </button>
          </form>

          {/* Quick Demo Sign In */}
          <div className="mt-6 pt-4 border-t border-border/60">
            <p className="text-center text-xs text-muted-foreground mb-3">Or quick start with a demo persona:</p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleDemoSignIn("demo_alex")}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-border bg-muted/40 py-2 text-xs font-medium text-foreground hover:border-primary hover:text-primary transition-all cursor-pointer"
              >
                <Sparkle size={13} className="text-primary" />
                Alex (Sci-Fi)
              </button>
              <button
                type="button"
                onClick={() => handleDemoSignIn("demo_sarah")}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-border bg-muted/40 py-2 text-xs font-medium text-foreground hover:border-primary hover:text-primary transition-all cursor-pointer"
              >
                <Sparkle size={13} className="text-primary" />
                Sarah (Indie)
              </button>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don&#39;t have an account?{" "}
            <Link to="/register" className="font-semibold text-primary hover:underline">
              Add / Register User Manually
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};
