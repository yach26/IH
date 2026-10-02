---
document_type: fco_specification
issuing_authority: FCO-India
publication_date: "2023"
region: all
crops: [all]
nutrients: [N, P, K]
source: fco_fertilizer_spec.md
---

# Fertilizer Control Order (FCO) — Nutrient Content Specifications (2023 Update)

## Purpose

The Fertilizer Control Order specifies minimum guaranteed nutrient content for each type of fertilizer product.
These values are mandatory legal minimums enforced by the Government of India.
AgroTwin AI uses ONLY these FCO-specified percentages for product conversion calculations.
LLMs must NEVER modify or guess fertilizer product percentages — only these FCO-certified values are valid.

---

## Standard Fertilizer Products — NPK Percentages

### Urea (Carbamide)

**product**: UREA
**document_type**: fco_specification
**nutrient**: N

- N content: 46.0% (minimum guaranteed)
- Form: Amide nitrogen (converts to ammonium then nitrate in soil)
- Application timing: Split application recommended to reduce leaching loss.
  - Never apply more than 50 kg N/ha per single dose.
  - Apply when soil is moist but no rain forecast for 24 hours.
- Volatilisation risk: High if applied on surface at pH > 7.5 or temperature > 35 degrees C.
  Incorporation recommended for alkaline soils.

Conversion formula: kg Urea = kg N needed / 0.46

---

### DAP — Di-Ammonium Phosphate

**product**: DAP
**document_type**: fco_specification
**nutrients**: [N, P]

- N content: 18.0% (minimum guaranteed)
- P2O5 content: 46.0% (minimum guaranteed)
- Primary use: Basal phosphorus application
- DAP is the most common P source for basal application on Indian farms.

Conversion formula:
- kg DAP = kg P2O5 needed / 0.46
- N contribution from DAP = kg DAP * 0.18

Application note: Apply DAP as basal and incorporate into soil before planting or transplanting.
Do NOT apply DAP as top-dress — its alkaline nature makes surface-applied P inefficient.

---

### MOP — Muriate of Potash

**product**: MOP
**document_type**: fco_specification
**nutrient**: K

- K2O content: 60.0% (minimum guaranteed)
- Form: Potassium chloride (KCl)
- Application timing: Can be applied as basal or split.
  - Avoid large single doses (>50 kg K2O/ha) on light sandy soils — chloride accumulation risk.

Conversion formula: kg MOP = kg K2O needed / 0.60

Application note: For chloride-sensitive crops (potato, onion, tomato), consider SOP (Sulphate of Potash) as an alternative.
FCO specifies SOP at minimum 50% K2O for the sulphate form.

---

### SSP — Single Super Phosphate

**product**: SSP
**document_type**: fco_specification
**nutrients**: [P, S]

- P2O5 content: 16.0% (minimum guaranteed)
- Sulphur (S): 11.0% minimum
- Useful alternative to DAP where sulphur deficiency is also identified.

Conversion formula: kg SSP = kg P2O5 needed / 0.16

---

### Ammonium Sulphate (AS)

**product**: AS
**document_type**: fco_specification
**nutrients**: [N, S]

- N content: 20.8% (minimum guaranteed), ammonium form
- Sulphur (S): 23.5% minimum
- Preferred N source for high-pH soils (Urea volatilises; AS is acidifying and stable).
- Used in sugarcane cultivation where sulphur demand is also present.

Conversion formula: kg AS = kg N needed / 0.208

---

## Legal Notice

These specifications are from the official Fertilizer Control Order (FCO) of India, Government notification.
Any modification to these percentages requires a regulatory amendment.
Using actual bag analysis values is permitted only when a laboratory certificate is attached to the recommendation record.

---

*Source: Fertilizer Control Order, Ministry of Chemicals and Fertilizers, Government of India, 2023.*
*Citation: FCO Schedule I — Nutrient Content Specifications, Annexure 2023.*
