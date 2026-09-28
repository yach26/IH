"""Field-scoped residual accounting; no assumed recovery percentages.

AGROTWIN_RESIDUAL_POLICY is an explicit reviewed JSON configuration:
{source, crop_code, products: {UREA: {max_age_days, fractions: {N,P2O5,K2O}}}}.
Fractions are retained fractions within the configured age window, not a
prediction. Outside its scope the ledger abstains. No policy is shipped.
"""
import json
import os
from datetime import date
from math import isfinite


def residual_credit(conn, field_id, soil_date, sowing_date, crop_code, *, today=None, policy=None):
    today = today or date.today()
    result = {"status": "NO_RECORDED_APPLICATIONS", "credits_kg_ha": dict.fromkeys(("N", "P2O5", "K2O"), 0.0),
              "applications": [], "assumptions": [], "source": None}
    rows = conn.execute("""SELECT a.*, p.product_code FROM applications a
        LEFT JOIN fertilizer_products p ON p.product_id = a.product_id
        WHERE a.field_id = ? ORDER BY a.application_date, a.application_id""", (field_id,)).fetchall()
    if not rows:
        result["assumptions"].append("No applications are recorded; this does not prove no fertilizer was applied. Confirm history before use.")
        return result
    try:
        sampled = date.fromisoformat(str(soil_date))
        sown = date.fromisoformat(str(sowing_date)) if sowing_date else None
        policy = policy if policy is not None else json.loads(os.getenv("AGROTWIN_RESIDUAL_POLICY", "null"))
        for raw in rows:
            row = dict(raw)
            applied = date.fromisoformat(str(row["application_date"]))
            item = {"application_id": row["application_id"], "application_date": str(applied), "product": row["product_code"]}
            result["applications"].append(item)
            if applied < sampled or (sown and applied < sown):
                item["status"] = "ALREADY_REFLECTED_IN_SOIL_OR_PRIOR_CROP"
                continue
            if applied == sampled:
                raise ValueError("Application and soil sample share a date; sampling order must be resolved with a new soil test")
            if applied > today:
                raise ValueError("Application date is in the future")
            if not policy or not policy.get("source") or policy.get("crop_code") != crop_code:
                raise ValueError("Post-sample fertilizer application needs a sourced residual policy for this crop or a newer soil test")
            rule = policy.get("products", {}).get(row["product_code"])
            age = (today - applied).days
            if not rule or age > int(rule["max_age_days"]):
                raise ValueError("Application is outside the configured product/age scope; residual availability is unknown")
            credits = {}
            for nutrient, column in (("N", "n_supplied_kg_ha"), ("P2O5", "p2o5_supplied_kg_ha"), ("K2O", "k2o_supplied_kg_ha")):
                fraction = float(rule["fractions"][nutrient])
                supplied = float(row[column])
                if not isfinite(fraction) or not 0 <= fraction <= 1 or not isfinite(supplied) or supplied < 0:
                    raise ValueError("Invalid residual fraction or application nutrient quantity")
                credits[nutrient] = round(supplied * fraction, 4)
                result["credits_kg_ha"][nutrient] += credits[nutrient]
            item.update(status="CREDITED", age_days=age, retained_fractions=rule["fractions"], credits_kg_ha=credits)
            result["source"] = policy["source"]
        result["status"] = "ACCOUNTED"
        result["assumptions"].append("Applications before the soil sample are not added again; post-sample credits use the cited configured retained fractions.")
    except (ValueError, TypeError, KeyError) as exc:
        result.update(status="REVIEW_REQUIRED", reason=str(exc), credits_kg_ha=None)
    return result
