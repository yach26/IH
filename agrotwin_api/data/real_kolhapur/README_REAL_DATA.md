# Real Kolhapur Data Sources

This directory contains real data from Kolhapur district, Maharashtra, India.

## Nutrient Dashboard (`nutrient_dashboard/`)

Block-wise Soil Health Card nutrient distribution for Kolhapur district.

| File | Cycle | Source |
|------|-------|--------|
| `2023-24.csv` | 2023-24 | Official SHC Dashboard |
| `2024-25.csv` | 2024-25 | Official SHC Dashboard |
| `2025-26.csv` | 2025-26 | Official SHC Dashboard |

Columns: State, District, Block, Scheme, Cycle, n_High, n_Medium, n_Low, p_High, p_Medium, p_Low, k_High, k_Medium, k_Low, OC_High, OC_Medium, OC_Low, pH_Alkaline, pH_Acidic, pH_Neutral, EC_NonSaline, EC_Saline, S_Sufficient, S_Deficient, Fe_Sufficient, Fe_Deficient, Zn_Sufficient, Zn_Deficient, Cu_Sufficient, Cu_Deficient, B_Sufficient, B_Deficient, Mn_Sufficient, Mn_Deficient

## Soil Tests (`soil_tests/`)

### `polgaon_soil_health.csv`
Real soil test point data from Polgaon village, Kolhapur district.
- Years: 2016-2024
- Fields: pH, EC, OC, N, P, K, S, Zn, Fe, Cu, Mn, B, Longitude, Latitude, Farmer Name, Land Area
- Source: ToySoil Health Dataset Polgaon (Updated)

### `field_nutrient_2016_2020.csv`
Village-level nutrient data for Kolhapur villages (2016-2020).
- Fields: PH, EC, ORGANIC_CARBON, PHOSPHOROUS, POTASH, CALCIUM_CARBONATE, FERROUS, MANGANESE, ZINC, COPPER, SAVI, Year
- Villages: Jambhali, Arjunwad, Shirol, Shirati, Sadalga, Udgaon, Takali, Mangavati, Shirguppi, Janwad

### `field_nutrient_2016_2025.csv`
Extended village-level data with remote sensing indices (2016-2025).
- Fields: latitude, longitude, ndvi, ndwi, evi, savi, ph, ec, organic_carbon, phosphorous, potash, calcium_carbonate, ferrous, manganese, zinc, copper
- 28 records across multiple years

## Farmer Survey (`farmer_survey/`)

### `shirol_farmer_survey.csv`
Real farmer survey from Shirol taluka, Kolhapur district.
- Source: SOIL SURVEY (1).xlsx
- Contents: Farmer names, land area, crop (mostly Sugarcane), fertilizer practices, irrigation source, problems faced

## Villages (`villages/`)

### `village_geocode.csv`
Village geocodes for Shirol area.
- 20 villages with Latitude/Longitude
- Villages: Akiwat, Arjunwad, Borgaon, Chand-Shiradwad, Chinchwad, Dharangutti, Jambhali, Janwad, Kurundwad, Mangavati, Nandani, Rajapur, Sadalga, Shahapur, Shirati, Shirguppi, Shirol, Takali, Terwad, Udgaon

## Usage

The seed data system can now use these real values instead of synthetic ones. The `seed_data.py` script reads from the `polgaon_soil_health.csv` to populate soil_tests with real N, P, K, pH, OC values.

The nutrient dashboard CSVs are used by the `get_kolhapur_soil_context()` helper to provide regional grounding for recommendations.
