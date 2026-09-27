"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { getFields, type FieldSummary } from "@/lib/api";

/**
 * Only an explicit URL selection identifies the active field.
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
