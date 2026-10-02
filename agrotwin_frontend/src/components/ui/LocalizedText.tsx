"use client";
import { type ReactNode } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

/** Translate display text through React, without rewriting DOM nodes or farm data. */
export default function LocalizedText({ children }: { children: ReactNode }) {
  const { translate } = useLanguage();
  function render(value: ReactNode): ReactNode {
    if (typeof value === "string") return translate(value);
    if (Array.isArray(value)) return value.map(render);
    return value;
  }
  return <>{render(children)}</>;
}

export function useText() {
  return useLanguage().translate;
}
