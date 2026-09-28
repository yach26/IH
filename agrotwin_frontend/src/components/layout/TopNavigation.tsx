"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Bell, Landmark } from "lucide-react";
import LandingNav from "@/components/landing/LandingNav";
import { useLanguage } from "@/contexts/LanguageContext";

const navLinks = [
  { name: "Overview",       href: "/"              , carryField: false },
  { name: "Farm",           href: "/dashboard"     , carryField: true  },
  { name: "Simulator",      href: "/simulator"     , carryField: true  },
  { name: "Upload",         href: "/upload"        , carryField: true  },
  { name: "Insights",       href: "/insights"      , carryField: false },
  { name: "Command Center", href: "/command-center", carryField: false },
];

const LANGUAGES: { code: "en" | "hi" | "mr"; label: string }[] = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
];

function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();
  return (
    <select
      value={language}
      onChange={(e) => setLanguage(e.target.value as "en" | "hi" | "mr")}
      aria-label="Select language"
      className="text-xs font-medium bg-transparent border border-border rounded-sm px-2 py-1 text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-primary"
    >
      {LANGUAGES.map((l) => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  );
}

function TopNavigationInner() {
  const pathname = usePathname();
  const router   = useRouter();
  const searchParams = useSearchParams();
  const field = searchParams.get("field");

  if (pathname === "/") {
    return <LandingNav />;
  }

  return (
    <header className="no-print sticky top-0 z-50 w-full bg-surface">
      {/* Official identity strip */}
      <div className="border-b border-border">
        <div className="container mx-auto px-4 h-9 flex items-center justify-between text-[11px] text-muted">
          <span>Kisan Saathi · Farm nutrient decision support · Kolhapur pilot</span>
          <LanguageSwitcher />
        </div>
      </div>

      <div className="border-b border-border bg-surface/95 backdrop-blur-md">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          {/* Emblem + scheme name */}
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="flex items-center gap-3 group"
              onClick={(e) => {
                e.preventDefault();
                router.push("/");
              }}
            >
              <span className="flex items-center justify-center w-9 h-9 rounded-full bg-primary/10 text-primary border border-primary/30">
                <Landmark className="w-5 h-5" strokeWidth={1.75} />
              </span>
              <span className="leading-tight">
                <span className="block font-serif text-lg font-bold text-primary group-hover:opacity-80 transition-opacity">
                  Kisan Saathi
                </span>
                <span className="block text-[10px] text-muted -mt-0.5">Digital Krishi Twin</span>
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
                      relative px-3 py-2 rounded-sm transition-colors duration-200
                      ${isActive
                        ? "text-primary"
                        : "text-muted hover:text-foreground hover:bg-surface-hover"
                      }
                    `}
                  >
                    {link.name}
                    {isActive && (
                      <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-primary rounded-full" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center space-x-3 text-sm">
            <Link href="/dashboard" className="rounded-lg border border-primary px-3 py-2 text-primary font-semibold">New field</Link>
            <button className="p-2 rounded-full hover:bg-surface-hover text-muted transition-colors">
              <span className="sr-only">Notifications</span>
              <Bell className="w-5 h-5" strokeWidth={1.75} />
            </button>
            <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-semibold text-xs">
              FM
            </div>
          </div>
        </div>
      </div>
      <div className="tricolor-bar" />
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
