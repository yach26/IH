"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import LanguageSwitcher from "@/components/ui/LanguageSwitcher";
import { useLanguage } from "@/contexts/LanguageContext";

/**
 * Smoothly scrolls to an in-page anchor, accounting for the sticky header height.
 */
function scrollToAnchor(e: React.MouseEvent<HTMLAnchorElement>, id: string) {
  e.preventDefault();
  const el = document.getElementById(id);
  if (!el) return;
  const headerOffset = 88; // LandingNav height (h-20 = 80px) + 8px breathing room
  const top = el.getBoundingClientRect().top + window.scrollY - headerOffset;
  window.scrollTo({ top, behavior: "smooth" });
}

export default function LandingNav() {
  const { t } = useLanguage();
  const router = useRouter();

  const navLinks = [
    { label: t("nav.howItWorks"),   anchor: "how-it-works"  },
    { label: t("nav.capabilities"), anchor: "capabilities"  },
    { label: t("nav.pilotRegions"), anchor: "pilot-regions" },
    { label: t("nav.resources"),    anchor: "resources"     },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#e5e0d8] bg-[#FAFAFA]/90 backdrop-blur-md">
      <div className="container mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center space-x-12">
          <Link href="/" className="flex flex-col group">
            <span className="text-xl font-semibold text-[#15803D] tracking-tight group-hover:opacity-80 transition-opacity">
              Kisan Saathi
            </span>
            <span className="text-[10px] text-[#15803D]/70 uppercase tracking-widest font-medium">
              Sustainable Fertilizer Support
            </span>
          </Link>

          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-[#1a1a1a]/80">
            {navLinks.map(({ label, anchor }) => (
              <a
                key={anchor}
                href={`#${anchor}`}
                onClick={(e) => scrollToAnchor(e, anchor)}
                className="relative py-1 hover:text-[#15803D] transition-colors duration-200 after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-[#15803D] after:transition-[width] after:duration-300 hover:after:w-full"
              >
                {label}
              </a>
            ))}
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          <LanguageSwitcher />
          <button
            onClick={() => router.push("/dashboard")}
            className="px-5 py-2.5 rounded-sm bg-[#15803D] text-[#FAFAFA] text-sm font-medium hover:bg-[#15803D]/90 active:scale-95 transition-all shadow-sm"
          >
            {t("nav.openDashboard")}
          </button>
        </div>
      </div>
    </header>
  );
}
