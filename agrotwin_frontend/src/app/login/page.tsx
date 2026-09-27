"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login, isAuthenticated } from "@/lib/auth";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated()) {
    router.replace("/dashboard");
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(email, password);
      const next = searchParams.get("next") || "/dashboard";
      if (user.role === "admin" && next === "/dashboard") {
        router.replace("/command-centre");
      } else {
        router.replace(next);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-light px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-ink-primary">AgroTwin AI</h1>
          <p className="text-sm text-ink-secondary mt-1">Sign in to your account</p>
        </div>

        <div className="card-clean">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="text-xs font-semibold text-ink-secondary block mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-clean"
                placeholder="admin@agrotwin.demo"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="text-xs font-semibold text-ink-secondary block mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-clean"
                placeholder="Enter password"
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-ink-muted mb-2">Demo accounts:</p>
            <div className="space-y-1 text-xs text-ink-secondary">
              <p><strong>Admin:</strong> admin@agrotwin.demo / admin123</p>
              <p><strong>Farmer:</strong> farmer@agrotwin.demo / farmer123</p>
              <p><strong>Agronomist:</strong> agronomist@agrotwin.demo / agro123</p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-ink-muted mt-4">
          DEMO AUTH — not for production use
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm text-ink-secondary">Loading...</p>
        </div>
      </div>
    }>
      <LoginContent />
    </Suspense>
  );
}
