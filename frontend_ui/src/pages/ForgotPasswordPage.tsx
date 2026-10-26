import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Envelope, CheckCircle } from "@phosphor-icons/react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";

export const ForgotPasswordPage = () => {
  useDocumentMeta("Forgot Password | streamXie", "Reset your streamXie password.");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    window.setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
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
          {submitted ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center gap-4 text-center py-4"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-950/60 border border-green-700/40">
                <CheckCircle size={28} weight="fill" className="text-green-400" />
              </div>
              <h1 className="text-xl font-semibold text-foreground">Check your inbox</h1>
              <p className="text-sm text-muted-foreground leading-relaxed">
                We&#39;ve sent a password reset link to <span className="text-foreground font-medium">{email}</span>.
                Check your spam folder if it doesn&#39;t arrive within a few minutes.
              </p>
              <Link
                to="/login"
                className="mt-2 inline-flex items-center rounded-lg bg-gradient-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110"
              >
                Back to sign in
              </Link>
            </motion.div>
          ) : (
            <>
              <h1 className="mb-2 text-center text-2xl font-semibold tracking-tight text-foreground">Forgot password?</h1>
              <p className="mb-6 text-center text-sm text-muted-foreground">
                Enter your email and we&#39;ll send you a reset link.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label htmlFor="fp-email" className="block text-sm font-medium text-muted-foreground">Email address</label>
                  <div className="relative">
                    <Envelope size={16} weight="duotone" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      id="fp-email"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className="w-full rounded-lg border border-border bg-background pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-gradient-primary py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed cinematic-glow"
                >
                  {loading ? "Sending…" : "Send reset link"}
                </button>
              </form>

              <p className="mt-6 text-center text-sm text-muted-foreground">
                Remembered it?{" "}
                <Link to="/login" className="font-medium text-primary hover:underline">Sign in</Link>
              </p>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
};
