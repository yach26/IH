# Yield model deployment

This directory is the canonical runtime bundle inside the repository. `models/yield_model.joblib`, `models/model_metadata.json`, `src/inference.py`, and `src/features.py` were copied unchanged from the supplied local `temp/agrotwin_ml` component. Its original README is retained as `README_SOURCE.md` for provenance; its illustrative integration code is not the API adapter. The API uses actual product quantities, not RDF requirements, for applied nutrients.

`worker.py` loads this bundle in a disposable subprocess. No dependency on the original external temp folder remains. `AGROTWIN_ML_ROOT` optionally selects a complete replacement bundle with the same layout. There is one runtime artifact location, not separate model copies per crop or API module. No retraining was performed.

The original component did not record training dependency versions. `../requirements.txt` pins the exact local runtime used for compatibility testing: NumPy 1.26.4, pandas 2.2.3, joblib 1.5.3, scikit-learn 1.8.0, XGBoost 3.2.0. These are not asserted to be original training versions. XGBoost emits an older-serialization warning when loading this supplied joblib; predictions passed local inference tests, but cross-version portability is not guaranteed. Keep the original artifact and obtain the training environment for a future native-format export. The warning remains in server logs rather than being suppressed.

## Honest limitations

- All training records are synthetic, calibrated to published averages. Held-out R2/MAE measure recovery of a synthetic process, not actual farm prediction accuracy.
- Jalgaon soil ranges were extrapolated from the available Kolhapur-Ajara information.
- Exact fitted STCR coefficients were unavailable; the generator uses general nutrient response principles instead.
- Uptake efficiencies are approximate general figures, not measurements for these pilot fields.
- Water response uses a season total and irrigation category. It omits rainfall timing, drainage, and soil moisture retention.
- Four crop models cover Banana, Sugarcane, Cotton, and Soybean; accepted districts are Kolhapur and Jalgaon. Unsupported crops, districts, and irrigation categories abstain.
- Training fertilizer rates span 40–130% of RDF. Ledger gap plans can lie outside this range, particularly zero K; the adapter explicitly flags extrapolation. Out-of-range seasonal rainfall is also flagged.
- Yield confidence is a coarse score derived from synthetic held-out R2, not a probability or the ledger's confidence. The yield band compares with the training mean, not the farmer's target.
- Retrain and validate on real paired soil, fertilizer, weather, and harvested-yield records when available.
