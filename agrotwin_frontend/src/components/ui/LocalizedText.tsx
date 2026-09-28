"use client";
import { cloneElement, isValidElement, type ReactNode } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

/** Translate display text through React, without rewriting DOM nodes or farm data. */
export default function LocalizedText({ children }: { children: ReactNode }) {
  const { translate } = useLanguage();
  function render(value: ReactNode): ReactNode {
    if (typeof value === "string") return translate(value);
    if (Array.isArray(value)) return value.map(render);
    if (isValidElement(value)) {
      const props = value.props as Record<string, unknown>;
      const localizedProps = { ...props };
      for (const name of ["aria-label", "title", "placeholder", "alt"]) {
        if (typeof props[name] === "string") localizedProps[name] = translate(props[name]);
      }
      return cloneElement(value, localizedProps, render(props.children as ReactNode));
    }
    return value;
  }
  return <>{render(children)}</>;
}

export function useText() {
  return useLanguage().translate;
}
