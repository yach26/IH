"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { getFields, type FieldSummary } from "@/lib/api";

const FALLBACK_FIELD_ID = "REAL-001";

/**
 * Resolves the active field for a page: ?field= query param -> first field
 * from the real /fields list -> a hardcoded fallback only as a last resort.
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
  const [fieldId, setFieldIdState] = useState<string>(queryField || FALLBACK_FIELD_ID);

  useEffect(() => {
    let cancelled = false;

    function load(isRetry: boolean) {
      getFields()
        .then((list) => {
          if (cancelled) return;
          setFields(list);
          setFieldsError(null);
          setFieldsLoaded(true);
          if (!queryField && list.length > 0) {
            setFieldIdState(list[0].field_code);
          }
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Intentional one-way sync from the URL's ?field= into local state (e.g. back/forward
  // navigation or an external link changing the param) — not a render-derivable value.
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (queryField && queryField !== fieldId) {
      setFieldIdState(queryField);
    }
  }, [queryField, fieldId]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const setFieldId = useCallback(
    (next: string) => {
      setFieldIdState(next);
      const params = new URLSearchParams(searchParams.toString());
      params.set("field", next);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  return { fieldId, setFieldId, fields, fieldsLoaded, fieldsError };
}
