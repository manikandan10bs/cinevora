import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeSlash, LockKey, User, CheckCircle } from "@phosphor-icons/react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useAuth } from "@/hooks/use-auth";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";

export const RegisterPage = () => {
  useDocumentMeta("Create Account | Cinevora", "Create your manual Cinevora user account.");
  const { register, isPending } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const cleanUsername = username.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
    if (!cleanUsername || cleanUsername.length < 3) {
      setError("Username must be at least 3 characters (letters, numbers, underscores).");
      return;
    }
    if (!password.trim()) {
      setError("Please enter a password.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      await register({
        username: cleanUsername,
        password: password.trim(),
        displayName: displayName.trim() || cleanUsername,
      });
      setSuccess(true);
      setTimeout(() => {
        navigate("/");
      }, 1200);
    } catch (err: any) {
      setError(err?.message || "Failed to create user account. Username may already exist.");
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4 py-12">
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
        <div className="mb-8 flex flex-col items-center gap-3">
          <Link to="/" className="text-foreground transition-colors hover:text-primary">
            <BrandLogo size="md" />
          </Link>
          <p className="text-sm text-muted-foreground">Manual Cinevora User Creation</p>
        </div>

        <div className="rounded-2xl border border-border bg-card/80 p-8 shadow-2xl backdrop-blur-xl">
          <h1 className="mb-2 text-center text-2xl font-bold tracking-tight text-foreground">
            Manual Add User
          </h1>
          <p className="mb-6 text-center text-xs text-muted-foreground">
            Create a persistent user account with salted PBKDF2 hashing in SQLite.
          </p>

          {success ? (
            <div className="flex flex-col items-center justify-center gap-3 py-6 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                <CheckCircle size={32} weight="fill" />
              </div>
              <h3 className="text-base font-semibold text-foreground">User Created Successfully!</h3>
              <p className="text-xs text-muted-foreground">
                Welcome, {displayName || username}! Redirecting to home...
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Username */}
              <div className="space-y-1.5">
                <label htmlFor="username" className="block text-sm font-medium text-muted-foreground">
                  Username <span className="text-primary">*</span>
                </label>
                <div className="relative">
                  <User size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="username"
                    type="text"
                    autoComplete="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. cinema_lover99"
                    className="w-full rounded-lg border border-border bg-background pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                  />
                </div>
              </div>

              {/* Display Name */}
              <div className="space-y-1.5">
                <label htmlFor="displayName" className="block text-sm font-medium text-muted-foreground">
                  Display / Full Name
                </label>
                <div className="relative">
                  <User size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="displayName"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Manikanthan N"
                    className="w-full rounded-lg border border-border bg-background pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <label htmlFor="reg-password" className="block text-sm font-medium text-muted-foreground">
                  Password <span className="text-primary">*</span>
                </label>
                <div className="relative">
                  <LockKey size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="reg-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 6 characters"
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

              {/* Confirm Password */}
              <div className="space-y-1.5">
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-muted-foreground">
                  Confirm Password <span className="text-primary">*</span>
                </label>
                <div className="relative">
                  <LockKey size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="confirmPassword"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full rounded-lg border border-border bg-background pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                  />
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
                {isPending ? "Creating Account…" : "Register User in SQLite"}
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};
