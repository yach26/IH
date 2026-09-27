"use client";

import React, { useEffect, useRef } from "react";

interface FieldMapProps {
  lat: number;
  lng: number;
  fieldId: string;
  zoom?: number;
  className?: string;
}

export default function FieldMap({
  lat,
  lng,
  fieldId,
  zoom = 14,
  className = "w-full h-full min-h-[160px]",
}: FieldMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);

  useEffect(() => {
    let isMounted = true;

    import("leaflet").then((L) => {
      if (!isMounted || !containerRef.current) return;

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((containerRef.current as any)?._leaflet_id) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        delete (containerRef.current as any)._leaflet_id;
      }

      // Fix broken default icon paths in webpack/Next.js
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(containerRef.current, {
        center: [lat, lng],
        zoom,
        zoomControl: true,
        scrollWheelZoom: false,
        attributionControl: false,
      });

      if (!isMounted) {
        map.remove();
        return;
      }

      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
      }).addTo(map);

      // Green field polygon (~2.5 ha)
      const delta = 0.008;
      const polygon = L.polygon(
        [
          [lat + delta, lng - delta],
          [lat + delta, lng + delta],
          [lat - delta, lng + delta],
          [lat - delta, lng - delta],
        ],
        { color: "#16a34a", fillColor: "#22c55e", fillOpacity: 0.25, weight: 2 }
      ).addTo(map);

      polygon
        .bindTooltip(`<b>Field ${fieldId}</b><br/>2.5 ha`, {
          permanent: true,
          direction: "center",
          className: "leaflet-field-label",
        })
        .openTooltip();
    });

    return () => {
      isMounted = false;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [lat, lng, fieldId, zoom]);

  return (
    <>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <style>{`
        .leaflet-field-label {
          background: #fff;
          border: 2px solid #16a34a;
          border-radius: 6px;
          font-size: 11px;
          color: #166534;
          font-weight: 700;
          padding: 2px 8px;
          white-space: nowrap;
          box-shadow: 0 2px 8px rgba(0,0,0,.1);
        }
        .leaflet-field-label::before { display: none; }
      `}</style>
      <div ref={containerRef} className={className} />
    </>
  );
}
