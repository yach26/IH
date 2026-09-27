"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getUser, isAuthenticated, isAdmin, logout } from "@/lib/auth";

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<ReturnType<typeof getUser>>(null);

  useEffect(() => {
    setUser(getUser());
  }, [pathname]);

  // Don't show nav on login page
  if (pathname === "/login") return null;

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const navLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/simulator", label: "Simulator" },
    { href: "/upload", label: "Upload" },
  ];

  if (isAdmin()) {
    navLinks.push({ href: "/command-centre", label: "Command Centre" });
  }

  return (
    <nav className="bg-white border-b border-border sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-lg font-bold text-ink-primary">
            AgroTwin AI
          </Link>
          <div className="flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  pathname.startsWith(link.href)
                    ? "bg-agri-primary text-white"
                    : "text-ink-secondary hover:bg-bg-subtle"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="text-sm text-ink-secondary">
                {user.name}
                <span className="badge badge-high ml-2">{user.role}</span>
              </span>
              <button onClick={handleLogout} className="btn-secondary text-xs">
                Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="btn-secondary text-xs">
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
