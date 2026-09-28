"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { getFields, type FieldSummary } from "@/lib/api";

/** A field is selected only by an explicit URL or user action, never browser history. */
export function useFieldParam() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryField = searchParams.get("field");

  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [fieldsError, setFieldsError] = useState<string | null>(null);
  const [fieldsLoaded, setFieldsLoaded] = useState(false);
  const requestedField = queryField?.trim() || "";
  const fieldId = fieldsLoaded && !fieldsError && fields.some(
    field => field.field_code === requestedField || String(field.field_id) === requestedField
  ) ? requestedField : "";

  useEffect(() => {
    let cancelled = false;

    function load(isRetry: boolean) {
      getFields()
        .then((list) => {
          if (cancelled) return;
          setFields(list.filter(field => !field.is_demo && !/^REAL-\d+$/.test(field.field_code)));
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
