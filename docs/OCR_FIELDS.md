# OCR Field Extraction Guide

## Overview

The AgroTwin OCR pipeline extracts soil nutrient values from Maharashtra Soil Health Card (SHC) images, PDFs, and text files. This document describes exactly which fields are extracted, how they are parsed, and which fields remain manual.

## Pipeline Stages

1. **Preprocessing** — OpenCV CLAHE contrast enhancement (images only)
2. **OCR Engine** — EasyOCR (images) or pypdf (digital PDFs) or direct decode (text files)
3. **Regex Parsing** — Three-pass extraction (inline, multi-line table, spatial adjacency)
4. **LLM Refinement** — Optional Groq/xAI fallback for missing fields (confidence capped at 0.80)
5. **Confidence Scoring** — Per-field confidence based on OCR engine scores

## Extracted Fields

### Macronutrients (Required for Digital Twin)

| Field | Unit | Regex Patterns | Confidence Source |
|-------|------|----------------|-------------------|
| `n_kg_ha` | kg/ha | "available nitrogen", "N", "available n", "नायट्रोजन" | OCR block score |
| `p_kg_ha` | kg/ha | "phosphorus", "p2o5", "P", "available p", "फॉस्फरस" | OCR block score |
| `k_kg_ha` | kg/ha | "potassium", "potash", "k2o", "K", "available k", "पोटॅश" | OCR block score |
| `ph` | pH | "pH", "reaction (ph)", "पीएच" | OCR block score |
| `oc_percent` | % | "organic carbon", "OC", "सेंद्रिय कर्बन" | OCR block score |
| `ec_ds_m` | dS/m | "electrical conductivity", "EC", "विद्युत चालकता" | OCR block score |

### Micronutrients (Extracted but not written to soil_tests)

| Field | Unit | Regex Patterns |
|-------|------|----------------|
| `s_ppm` | ppm | "sulphur", "S", "गंधक" |
| `zn_ppm` | ppm | "zinc", "Zn", "जस्त" |
| `fe_ppm` | ppm | "iron", "Fe", "लोह" |
| `cu_ppm` | ppm | "copper", "Cu", "तांबे" |
| `mn_ppm` | ppm | "manganese", "Mn", "मग्नेशियम" |
| `b_ppm` | ppm | "boron", "B", "बोरॉन" |

### Metadata (Extracted but mostly discarded)

| Field | Regex Patterns | Notes |
|-------|----------------|-------|
| `farmer_name` | "farmer name", "name of farmer", "शेतकरी नाव" | Not stored |
| `sample_id` | "sample id/no", "shc no", "नमुना क्रमांक" | Not stored |
| `test_date` | "date of test", "sampled", "तपासणी दिनांक" | Used if present |
| `lab_name` | "soil testing lab", "lab name", "प्रयोगशाळा" | Not stored |

## Fields That Remain Manual

The following fields are **NOT extracted** and must be entered manually by the farmer or agronomist:

1. **Micronutrients** — S, Zn, Fe, Cu, Mn, B are extracted by OCR but the `soil_tests` table has no columns for them. They are stored in `extracted_json` in the `soil_report_uploads` table but never written to the Digital Twin.
2. **Farmer name** — Extracted but not stored (privacy by design).
3. **Sample ID** — Extracted but not stored.
4. **Lab name** — Extracted but not stored.
5. **Soil type** — Not present on SHC cards; must be entered manually.
6. **Cation Exchange Capacity (CEC)** — Not present on standard SHC cards.
7. **Soil texture** — Not present on SHC cards.

## Confidence Thresholds

| Source | Confidence | Action |
|--------|-----------|--------|
| Plain text file (.txt, .csv, .md) | 0.98 | Auto-accept |
| Digital PDF (pypdf text extraction) | 0.96 | Auto-accept |
| EasyOCR inline match | OCR score (floored at 0.51) | Review if < 0.85 |
| EasyOCR multi-line table | Weakest block score (floored at 0.51) | Review if < 0.85 |
| EasyOCR spatial adjacency | min(label_conf, value_conf) (floored at 0.51) | Review if < 0.85 |
| LLM-refined value | 0.80 (fixed) | Always requires review |
| Missing field | 0.0 | Always requires review |

**Review threshold: 0.85** — Any field below this threshold appears in `fields_needing_review` and must be confirmed by the farmer before being written to the Digital Twin.

## Farmer Confirmation Flow

1. **Upload** — `POST /fields/{field_id}/soil-report/upload` runs OCR and stores results in `soil_report_uploads` with status `PENDING_CONFIRMATION`. **No data is written to `soil_tests`.**
2. **Review** — Farmer reviews extracted values in the UI, edits any incorrect values.
3. **Confirm** — `POST /fields/{field_id}/soil-report/confirm` writes confirmed values to `soil_tests` and updates the upload status to `CONFIRMED`.

**Critical safety rule**: LLM-suggested values (confidence 0.80) can never be auto-accepted. They always require explicit farmer confirmation.

## Supported Card Layouts

The OCR pipeline has been tested against these Maharashtra SHC layouts:

1. **Standard English** — "Available Nitrogen (N): 210 kg/ha"
2. **Bilingual Marathi/English** — "उपलब्ध नायट्रोजन / Available N: 180 kg/ha"
3. **Compact English** — "Nitrogen (N): 95.5 kg/ha"
4. **Table format** — Pipe-delimited tables with "Parameter | Value | Unit"
5. **Mixed format** — Combinations of the above

## Test Fixtures

Five sample SHC fixtures are available in `agrotwin_api/tests/fixtures/`:

| File | Layout | District |
|------|--------|----------|
| `shc_sample_1.txt` | Standard English | Kolhapur |
| `shc_sample_2.txt` | Bilingual Marathi/English | Kolhapur |
| `shc_sample_3.txt` | Compact English | Jalgaon |
| `shc_sample_4.txt` | Bilingual with different labels | Kolhapur |
| `shc_sample_5.txt` | Table format | Jalgaon |

These are synthetic fixtures created for testing purposes. Real SHC cards may have additional layout variations.
