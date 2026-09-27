"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import LandingNav from "@/components/landing/LandingNav";

const navLinks = [
  { name: "Overview",       href: "/"              , carryField: false },
  { name: "Farm",           href: "/dashboard"     , carryField: true  },
  { name: "Simulator",      href: "/simulator"     , carryField: true  },
  { name: "Upload",         href: "/upload"        , carryField: true  },
  { name: "Insights",       href: "/insights"      , carryField: false },
  { name: "Command Center", href: "/command-center", carryField: false },
];

function TopNavigationInner() {
  const pathname = usePathname();
  const router   = useRouter();
  const searchParams = useSearchParams();
  const field = searchParams.get("field");

  if (pathname === "/") {
    return <LandingNav />;
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo + nav links */}
        <div className="flex items-center space-x-8">
          <Link
            href="/"
            className="flex items-center space-x-2 group"
            onClick={(e) => {
              e.preventDefault();
              router.push("/");
            }}
          >
            <span className="text-xl font-semibold text-primary group-hover:opacity-75 transition-opacity">
              AgroTwin AI
            </span>
          </Link>

          <nav className="hidden md:flex items-center space-x-1 text-sm font-medium">
            {navLinks.map((link) => {
              const isActive =
                pathname === link.href ||
                (link.href !== "/" && pathname.startsWith(link.href));
              const href = link.carryField && field
                ? `${link.href}?field=${encodeURIComponent(field)}`
                : link.href;
              return (
                <Link
                  key={link.name}
                  href={href}
                  className={`
                    relative px-3 py-2 rounded-md transition-colors duration-200
                    ${isActive
                      ? "text-primary"
                      : "text-muted hover:text-foreground hover:bg-surface-hover"
                    }
                  `}
                >
                  {link.name}
                  {/* Animated active underline */}
                  {isActive && (
                    <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-primary rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right side controls */}
        <div className="flex items-center space-x-3 text-sm">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-md bg-surface border border-border">
            <span className="text-muted">Region:</span>
            <span className="font-medium text-foreground">Kolhapur</span>
          </div>

          <button className="p-2 rounded-full hover:bg-surface-hover text-muted transition-colors">
            <span className="sr-only">Notifications</span>
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          </button>

          <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-semibold text-xs">
            FM
          </div>
        </div>
      </div>
    </header>
  );
}

export default function TopNavigation() {
  return (
    <Suspense fallback={null}>
      <TopNavigationInner />
    </Suspense>
  );
}
