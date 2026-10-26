import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeSlash, LockKey, CheckCircle } from "@phosphor-icons/react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";

export const ResetPasswordPage = () => {
  useDocumentMeta("Reset Password | streamXie", "Set a new password for your streamXie account.");
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!password.trim()) { setError("Please enter a new password."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    if (password !== confirmPassword) { setError("Passwords do not match."); return; }
    setLoading(true);
    window.setTimeout(() => {
      setLoading(false);
      setDone(true);
      window.setTimeout(() => navigate("/login"), 2000);
    }, 1200);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
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
        </div>

        <div className="rounded-2xl border border-border bg-card/80 p-8 shadow-2xl backdrop-blur-xl">
          {done ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center gap-4 text-center py-4"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-950/60 border border-green-700/40">
                <CheckCircle size={28} weight="fill" className="text-green-400" />
              </div>
              <h1 className="text-xl font-semibold text-foreground">Password updated!</h1>
              <p className="text-sm text-muted-foreground">Redirecting you to sign in…</p>
            </motion.div>
          ) : (
            <>
              <h1 className="mb-2 text-center text-2xl font-semibold tracking-tight text-foreground">Set new password</h1>
              <p className="mb-6 text-center text-sm text-muted-foreground">
                Choose a strong password. You&#39;ll be signed in after.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label htmlFor="new-password" className="block text-sm font-medium text-muted-foreground">New password</label>
                  <div className="relative">
                    <LockKey size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      id="new-password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min. 8 characters"
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

                <div className="space-y-1.5">
                  <label htmlFor="rp-confirm" className="block text-sm font-medium text-muted-foreground">Confirm new password</label>
                  <div className="relative">
                    <LockKey size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      id="rp-confirm"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat new password"
                      className="w-full rounded-lg border border-border bg-background pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                    />
                  </div>
                </div>

                {/* Password strength hint */}
                {password.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="flex gap-1">
                      {[1, 2, 3, 4].map((n) => (
                        <div
                          key={n}
                          className={`h-1 flex-1 rounded-full transition-all ${
                            password.length >= n * 3
                              ? n <= 1 ? "bg-red-500" : n <= 2 ? "bg-orange-500" : n <= 3 ? "bg-yellow-500" : "bg-green-500"
                              : "bg-border"
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      {password.length < 4 ? "Very weak" : password.length < 7 ? "Weak" : password.length < 10 ? "Good" : "Strong"}
                    </p>
                  </div>
                )}

                {error && (
                  <p className="rounded-lg border border-red-700/40 bg-red-950/40 px-4 py-2.5 text-xs text-red-400">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-gradient-primary py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed cinematic-glow"
                >
                  {loading ? "Saving…" : "Update password"}
                </button>
              </form>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
};
