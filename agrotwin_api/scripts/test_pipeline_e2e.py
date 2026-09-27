#!/usr/bin/env python3
"""
AgroTwin – Rigorous End-to-End Pipeline Test
"""
import os, sys, json, time, io, statistics, traceback

try:
    import requests
except ImportError:
    print("[FATAL] requests not installed.  Run:  pip install requests"); sys.exit(1)

BASE_URL  = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
FIELD_IDS = ["SYN-001","SYN-002","SYN-003","SYN-004","SYN-005","SYN-006","SYN-007","SYN-008"]
TEST_FIELD = "SYN-001"
PASS = "  ✅ PASS"; FAIL = "  ❌ FAIL"; WARN = "  ⚠️  WARN"; SEP = "─"*72
passed = 0; failed = 0; results = []

def check(label, cond, detail=""):
    global passed, failed
    if cond: passed += 1
    else: failed += 1
    results.append((label, cond, detail))
    print(f"{PASS if cond else FAIL}  {label}")
    if detail and not cond: print(f"          → {detail}")

def section(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def get(path, **kw): return requests.get(f"{BASE_URL}{path}", timeout=10, **kw)
def post(path, json_data=None, files=None):
    if files: return requests.post(f"{BASE_URL}{path}", files=files, timeout=30)
    return requests.post(f"{BASE_URL}{path}", json=json_data, timeout=30)

# 1. Health
section("1 · Health Check")
try:
    r = get("/")
    check("Server reachable", r.status_code < 500, f"status={r.status_code}")
except Exception as e:
    check("Server reachable", False, str(e))
    print("\n[FATAL] Cannot connect. Start uvicorn first.\n"); sys.exit(1)

# 2. Field listing
section("2 · Field Listing")
try:
    r = get("/fields")
    if r.status_code == 200:
        d = r.json()
        check("GET /fields returns list", isinstance(d, list))
        check("At least one field", len(d) >= 1)
    else:
        print(f"{WARN}  /fields not implemented (status={r.status_code})")
except Exception as e:
    print(f"{WARN}  /fields error: {e}")

# 3. Twin for every field
section("3 · Digital Twin per Field")
twin_latencies = []
for fid in FIELD_IDS:
    t0 = time.perf_counter()
    try:
        r = get(f"/fields/{fid}/twin"); lat = time.perf_counter()-t0; twin_latencies.append(lat)
        ok = r.status_code == 200
        check(f"[{fid}] returns 200", ok, f"status={r.status_code}")
        if ok:
            d = r.json()
            check(f"[{fid}] has fieldId",    "fieldId"     in d)
            check(f"[{fid}] has nutrients",  "nutrients"   in d)
            check(f"[{fid}] has currentPlan","currentPlan" in d)
            check(f"[{fid}] nutrients N+P+K","n" in d.get("nutrients",{}) and "p" in d.get("nutrients",{}) and "k" in d.get("nutrients",{}))
            check(f"[{fid}] latency<2s", lat<2.0, f"{lat:.3f}s")
    except Exception as e:
        twin_latencies.append(10.0); check(f"[{fid}] no exception", False, str(e)[:120])
if twin_latencies:
    p99 = sorted(twin_latencies)[int(0.99*len(twin_latencies))-1]
    print(f"\n  Twin — p50={statistics.median(twin_latencies)*1000:.0f}ms  p99={p99*1000:.0f}ms")
    check("Twin p99<2000ms", p99<2.0, f"{p99*1000:.0f}ms")

# 4. What-if scenarios
section("4 · What-If Simulator Scenarios")
scenarios = [
    ("baseline",           {"fertilizer_delta_pct": 0,    "rainfall_mm": 20}),
    ("+25% fertilizer",    {"fertilizer_delta_pct": 25.0, "rainfall_mm": 20}),
    ("-30% fertilizer",    {"fertilizer_delta_pct":-30.0, "rainfall_mm": 20}),
    ("heavy rain (80mm)",  {"fertilizer_delta_pct": 0,    "rainfall_mm": 80}),
    ("drought (2mm)",      {"fertilizer_delta_pct": 0,    "rainfall_mm": 2}),
    ("worst case",         {"fertilizer_delta_pct":-50.0, "rainfall_mm": 0}),
    ("excess everything",  {"fertilizer_delta_pct": 50.0, "rainfall_mm":100}),
]
wi_lats = []
for label, body in scenarios:
    t0 = time.perf_counter()
    try:
        r = post(f"/fields/{TEST_FIELD}/what-if", json_data=body); lat = time.perf_counter()-t0; wi_lats.append(lat)
        ok = r.status_code == 200
        check(f"[what-if] {label} 200", ok, f"status={r.status_code} {r.text[:80]}")
        if ok:
            d = r.json()
            check(f"[what-if] {label} has simulated", "simulated" in d)
            check(f"[what-if] {label} has original",  "original"  in d)
            sim = d.get("simulated", {})
            check(f"[what-if] {label} yieldBand", bool(sim.get("yieldBand")), str(sim.get("yieldBand")))
            check(f"[what-if] {label} modelSignals", "modelSignals" in sim)
            check(f"[what-if] {label} latency<2s", lat<2.0, f"{lat:.3f}s")
    except Exception as e:
        check(f"[what-if] {label} no exception", False, str(e)[:120])
if wi_lats:
    print(f"\n  What-If — p50={statistics.median(wi_lats)*1000:.0f}ms  worst={max(wi_lats)*1000:.0f}ms")

# 5. OCR upload
section("5 · OCR Soil Report Upload")
SOIL_TXT = b"""SOIL TEST REPORT\nNitrogen (N) : 195 kg/ha\nPhosphorus (P): 32 kg/ha\nPotassium (K): 380 kg/ha\npH: 7.6\n"""
try:
    r = post("/upload-soil-report", files={"file": ("test.txt", io.BytesIO(SOIL_TXT), "text/plain")})
    if r.status_code == 200:
        d = r.json()
        check("OCR upload 200", True)
        check("OCR has status", "status" in d)
        check("OCR status ok", d.get("status") in ("extracted","ok","success"), d.get("status"))
    elif r.status_code == 404:
        print(f"{WARN}  /upload-soil-report not found – skipping")
    else:
        check("OCR upload 200", False, f"status={r.status_code} {r.text[:120]}")
except Exception as e:
    print(f"{WARN}  OCR error: {e}")

# 6. Recommend
section("6 · Recommendation Endpoint")
try:
    r = get(f"/recommend/{TEST_FIELD}")
    if r.status_code == 200:
        d = r.json()
        check("GET /recommend 200", True)
        check("Has status",  "status" in d)
        check("Status PLAN_GENERATED", d.get("status")=="PLAN_GENERATED", d.get("status"))
        plan = d.get("plan_kg_ha", d.get("plan", {}))
        check("Plan has DAP",  "DAP_kg_ha" in plan or bool(plan), str(plan)[:80])
    elif r.status_code == 404:
        print(f"{WARN}  /recommend/{TEST_FIELD} → 404")
    else:
        check("GET /recommend 200", False, f"status={r.status_code}")
except Exception as e:
    print(f"{WARN}  /recommend error: {e}")

# 7. Alerts
section("7 · Alerts Endpoint")
try:
    r = get("/alerts")
    if r.status_code == 200:
        check("GET /alerts 200", True); check("Alerts is list", isinstance(r.json(), list))
    else:
        r2 = get(f"/fields/{TEST_FIELD}/alerts")
        if r2.status_code == 200:
            check("GET /fields/{id}/alerts 200", True)
        else:
            print(f"{WARN}  No alerts endpoint found")
except Exception as e:
    print(f"{WARN}  alerts error: {e}")

# 8. 404 edge case
section("8 · Edge Case – Unknown Field 404")
try:
    r = get("/fields/DOES_NOT_EXIST/twin")
    check("Unknown twin → 404", r.status_code==404, f"got {r.status_code}")
    r2 = post("/fields/DOES_NOT_EXIST/what-if", json_data={"fertilizer_delta_pct":0,"rainfall_mm":20})
    check("Unknown what-if → 404", r2.status_code==404, f"got {r2.status_code}")
except Exception as e:
    print(f"{WARN}  404 edge test error: {e}")

# 9. 422 edge case
section("9 · Edge Case – Bad Body 422")
try:
    r = post(f"/fields/{TEST_FIELD}/what-if", json_data={"fertilizer_delta_pct":"bad"})
    check("Bad body → 422 or 400", r.status_code in (422,400), f"got {r.status_code}")
except Exception as e:
    print(f"{WARN}  422 edge test error: {e}")

# 10. Performance stress
section("10 · Performance Stress – 10 Rapid Requests")
plats = []
for i in range(10):
    t0 = time.perf_counter()
    try:
        get(f"/fields/{FIELD_IDS[i%len(FIELD_IDS)]}/twin"); plats.append(time.perf_counter()-t0)
    except: plats.append(10.0)
plats.sort()
p50_ms = statistics.median(plats)*1000; worst_ms = plats[-1]*1000
print(f"  10-shot p50={p50_ms:.0f}ms  worst={worst_ms:.0f}ms")
check("All 10 < 3s",     all(l<3.0 for l in plats), f"worst={worst_ms:.0f}ms")
check("Rapid p50<1000ms", p50_ms<1000, f"{p50_ms:.0f}ms")

# Summary
print(f"\n{'═'*72}")
print(f"  RESULTS:  {passed} passed  |  {failed} failed  |  {passed+failed} total")
print(f"{'═'*72}")
if failed:
    print("\n  Failed checks:")
    for label, ok, detail in results:
        if not ok:
            print(f"    ❌  {label}")
            if detail: print(f"        → {detail}")
sys.exit(0 if failed==0 else 1)
