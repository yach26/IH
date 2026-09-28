import type { WhatIfPlanSide } from "@/lib/api";
import type { CropModelProps } from "@/components/features/CropModel";

type Sufficiency = CropModelProps["nutrientSufficiency"];
type WaterLevel = CropModelProps["waterStress"];
type Vigor = CropModelProps["vigor"];

const NUTRIENTS = ["N", "P2O5", "K2O"] as const;

/** Nutrient sufficiency from the real gap/shortfall/excess the backend already
 * returns for this scenario side — never a separate invented score. */
export function deriveNutrientSufficiency(side: WhatIfPlanSide | null | undefined): Sufficiency {
  if (!side) return "unknown";
  const totalGap = NUTRIENTS.reduce((sum, n) => sum + (side.gap[n] || 0), 0);
  const totalShortfall = NUTRIENTS.reduce((sum, n) => sum + (side.shortfall[n] || 0), 0);
  const totalExcess = NUTRIENTS.reduce((sum, n) => sum + (side.excess[n] || 0), 0);
  if (totalGap <= 0) return totalExcess > 0 ? "suboptimal" : "optimal";
  const shortfallRatio = totalShortfall / totalGap;
  if (shortfallRatio > 0.3) return "deficient";
  if (totalExcess > totalGap * 0.5) return "suboptimal";
  return "optimal";
}

/** Field-level water stress (Low/Elevated/Not available) is the real signal
 * already computed by /twin from irrigation type + weather forecast. A
 * hypothetical what-if rainfall can only nudge the SCENARIO side one notch
 * better/worse relative to the field's actual forecast — it never runs a
 * new water-balance calculation of its own. */
export function deriveWaterStress(
  twinLabel: string | undefined,
  hypotheticalRainMm: number | null,
  actualRainMm: number | null | undefined
): WaterLevel {
  const base: WaterLevel = twinLabel === "Elevated" ? "moderate" : twinLabel === "Low" ? "none" : "unknown";
  if (hypotheticalRainMm == null || actualRainMm == null || Number.isNaN(hypotheticalRainMm)) return base;
  const order: WaterLevel[] = ["none", "moderate", "high"];
  const idx = order.indexOf(base === "unknown" ? "none" : base);
  if (hypotheticalRainMm < actualRainMm) return order[Math.min(idx + 1, order.length - 1)];
  if (hypotheticalRainMm > actualRainMm) return order[Math.max(idx - 1, 0)];
  return base;
}

/** Vigor is a deterministic combination of the two signals above — no
 * randomness, no slider read directly, only the already-derived states. */
export function deriveVigor(nutrient: Sufficiency, water: WaterLevel): Vigor {
  const nutrientScore = nutrient === "optimal" ? 0 : nutrient === "suboptimal" ? -1 : nutrient === "deficient" ? -2 : 0;
  const waterScore = water === "none" ? 0 : water === "moderate" ? -1 : water === "high" ? -2 : 0;
  const total = nutrientScore + waterScore;
  if (total === 0) return "thriving";
  if (total >= -1) return "healthy";
  if (total >= -3) return "below-average";
  return "stressed";
}

const KNOWN_CROPS = ["Banana", "Cotton", "Sugarcane", "Rice"];

/** "Cotton (Bt)" -> "Cotton"; anything unrecognized is passed through as-is
 * so CropModel can fall back to its illustrative (non-3D) plant. */
export function normalizeCropType(crop: string | null | undefined): string {
  if (!crop) return "";
  const clean = crop.split("(")[0].trim();
  return KNOWN_CROPS.find((known) => clean.toLowerCase().includes(known.toLowerCase())) || clean;
}
