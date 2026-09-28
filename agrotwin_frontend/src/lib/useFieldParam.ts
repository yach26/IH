"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { getFields, type FieldSummary } from "@/lib/api";

const LAST_FIELD_KEY = "agrotwin:lastFieldId";

/**
 * The URL's ?field= is the source of truth while present. Some nav links
 * (Insights, Command Center) don't carry it, so landing on one of those and
 * coming back would otherwise lose the selection and force the user back
 * through onboarding — instead we remember the last selected field in
 * localStorage and restore it into the URL the next time a field-scoped
 * page loads with no ?field= of its own.
 * Also exposes the full field list (for a selector dropdown) and a setter
 * that updates both state and the URL so the selection survives navigation
 * and can be shared/linked (e.g. dashboard -> upload page).
 */
export function useFieldParam() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryField = searchParams.get("field");

  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [fieldsError, setFieldsError] = useState<string | null>(null);
  const [fieldsLoaded, setFieldsLoaded] = useState(false);
  const fieldId = queryField?.trim() || "";

  // Restore the last-used field into the URL when this page has none of its own.
  useEffect(() => {
    if (fieldId) {
      try {
        localStorage.setItem(LAST_FIELD_KEY, fieldId);
      } catch {
        // localStorage unavailable (private mode, etc.) — selection just
        // won't survive a field-less nav hop; not fatal.
      }
      return;
    }
    let remembered: string | null = null;
    try {
      remembered = localStorage.getItem(LAST_FIELD_KEY);
    } catch {
      remembered = null;
    }
    if (remembered) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("field", remembered);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }
    // Only re-run when the URL's own field param changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fieldId]);

  useEffect(() => {
    let cancelled = false;

    function load(isRetry: boolean) {
      getFields()
        .then((list) => {
          if (cancelled) return;
          setFields(list);
          setFieldsError(null);
          setFieldsLoaded(true);
        })
        .catch((err) => {
          if (cancelled) return;
          // The very first request from a freshly-opened dev-server tab can
          // occasionally race a still-settling connection; one silent retry
          // clears that without surfacing a false "unavailable" state to the user.
          if (!isRetry) {
            setTimeout(() => !cancelled && load(true), 800);
            return;
          }
          setFieldsError(err instanceof Error ? err.message : "Failed to load fields");
          setFieldsLoaded(true);
        });
    }

    load(false);
    return () => {
      cancelled = true;
    };
  }, []);

  const setFieldId = useCallback(
    (next: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (next) params.set("field", next);
      else params.delete("field");
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  return { fieldId, setFieldId, fields, fieldsLoaded, fieldsError };
}
