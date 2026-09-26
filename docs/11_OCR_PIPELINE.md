# 11 — Soil Report OCR Pipeline

## Flow

```
Farmer uploads soil report (image / PDF)
        ↓
   OCR / Parser (PaddleOCR or EasyOCR)
        ↓
Key-value extraction (N, P, K, pH, OC, EC, ...)
        ↓
Confidence validation (per field)
        ↓
Farmer confirms / corrects extracted values
        ↓
Digital Twin updated → event SOIL_REPORT_UPDATED
```

**Never** silently accept low-confidence OCR values.

---

## Implementation Details

1. Endpoint `POST /fields/{id}/soil-report` accepts multipart file.
2. Store original file in object storage / local uploads folder.
3. Run OCR → structured dict with confidence scores per field.
4. Return the extraction to the frontend for confirmation.
5. Only after farmer confirmation write to `soil_tests` table and emit `SOIL_REPORT_UPDATED`.

### Suggested libraries

- **PaddleOCR** (good for Indian languages and tables)
- or **EasyOCR** + custom post-processing
- `pdf2image` if PDF input is required

### Confidence handling

```python
extracted = {
  "n_kg_ha": {"value": 45.2, "confidence": 0.92},
  "p_kg_ha": {"value": 12.1, "confidence": 0.78},
  ...
}
# Frontend highlights low-confidence fields (< 0.85) and forces review
```

---

## Checklist

- [x] Upload endpoint + storage of original file
- [x] OCR → structured fields with confidence
- [x] Confirmation UI that shows original image + extracted values side-by-side
- [x] Only confirmed values update the twin
- [x] Event emission after successful update
- [x] Graceful fallback when OCR fails completely (manual entry form)
