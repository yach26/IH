"use client";

import React, { useEffect, useRef } from "react";

interface PilotRegion {
  name: string;
  lat: number;
  lng: number;
  crops: string;
  district: string;
}

const PILOT_REGIONS: PilotRegion[] = [
  { name: "Jalgaon",  lat: 21.0077, lng: 75.5626, crops: "Banana, Cotton",   district: "Jalgaon District"  },
  { name: "Kolhapur", lat: 16.705,  lng: 74.2433, crops: "Sugarcane, Rice",  district: "Kolhapur District" },
];

interface PilotRegionsMapProps {
  className?: string;
}

export default function PilotRegionsMap({ className = "w-full h-[420px]" }: PilotRegionsMapProps) {
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

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;

      const map = L.map(containerRef.current, {
        center: [18.5, 75.5],
        zoom: 7,
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
        maxZoom: 18,
      }).addTo(map);

      // Subtle Maharashtra bounding box
      L.rectangle([[15.5, 72.6], [22.0, 80.9]], {
        color: "#0F4D35",
        fillColor: "#0F4D35",
        fillOpacity: 0.06,
        weight: 1.5,
        dashArray: "6 4",
      }).addTo(map);

      // Gold pulsing dot icon
      const goldIcon = L.divIcon({
        className: "",
        html: `<div style="
          width:18px;height:18px;
          background:#d4af37;
          border:3px solid #fff;
          border-radius:50%;
          box-shadow:0 0 0 5px rgba(212,175,55,0.25), 0 2px 8px rgba(0,0,0,.2);
        "></div>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
        popupAnchor: [0, -14],
      });

      PILOT_REGIONS.forEach((region) => {
        const marker = L.marker([region.lat, region.lng], { icon: goldIcon }).addTo(map);

        marker.bindPopup(
          `<div style="font-family:sans-serif;min-width:130px;">
            <div style="font-weight:700;font-size:13px;color:#0F4D35;margin-bottom:4px;">${region.name}</div>
            <div style="font-size:11px;color:#666;margin-bottom:3px;">${region.district}</div>
            <div style="font-size:11px;font-weight:600;color:#333;">Crops: ${region.crops}</div>
          </div>`,
          { closeButton: false }
        );

        marker
          .bindTooltip(
            `<b>${region.name}</b><br/><span style="font-size:10px;color:#888">${region.crops}</span>`,
            { permanent: true, direction: "top", offset: [0, -14], className: "pilot-region-label" }
          )
          .openTooltip();
      });
    });

    return () => {
      isMounted = false;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <style>{`
        .pilot-region-label {
          background: #fff;
          border: 2px solid #0F4D35;
          border-radius: 8px;
          font-size: 11px;
          color: #0F4D35;
          font-weight: 700;
          padding: 4px 10px;
          box-shadow: 0 2px 8px rgba(0,0,0,.12);
          text-align: center;
        }
        .pilot-region-label::before { display: none; }
      `}</style>
      <div ref={containerRef} className={className} style={{ borderRadius: "8px", overflow: "hidden" }} />
    </>
  );
}
