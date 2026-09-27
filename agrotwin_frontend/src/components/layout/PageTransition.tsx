"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

/**
 * Wraps page content in a fade + slight upward slide animation that
 * plays every time the Next.js pathname changes.
 */
export default function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Kick off the animation on every route change
    el.style.opacity = "0";
    el.style.transform = "translateY(14px)";

    // Double-rAF ensures the browser has painted the initial state
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.transition = "opacity 0.38s ease, transform 0.38s ease";
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
      });
    });

    // Clean up transition property after it completes so it doesn't
    // interfere with any child CSS transitions
    const timer = setTimeout(() => {
      if (el) el.style.transition = "";
    }, 420);

    return () => clearTimeout(timer);
  }, [pathname]);

  return (
    <div ref={ref} style={{ opacity: 0, transform: "translateY(14px)" }}>
      {children}
    </div>
  );
}
