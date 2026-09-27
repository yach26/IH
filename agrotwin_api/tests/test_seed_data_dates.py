"""
Regression test for a real bug found during the dashboard dynamic-UI rewrite:
seed_data.py's real-Kolhapur branch stored soil_tests.test_date verbatim from
the source CSV (DD-MM-YYYY), while every `/twin`-adjacent query does
`ORDER BY test_date DESC LIMIT 1` as a plain string sort. A DD-MM-YYYY string
sorts ahead of any real ISO date (e.g. "24-10-2016" > "2026-09-27"
lexicographically), which meant a farmer confirming a new OCR soil test for
one of the real demo fields would never actually show up on the dashboard —
the 2016 seed row would silently keep winning forever.
"""

from __future__ import annotations

from seed_data import _to_iso_date


def test_converts_ddmmyyyy_to_iso():
    assert _to_iso_date("24-10-2016") == "2016-10-24"
    assert _to_iso_date("01-01-2024") == "2024-01-01"


def test_passes_through_already_iso_or_unknown_format():
    assert _to_iso_date("2026-09-27") == "2026-09-27"
    assert _to_iso_date("not-a-date") == "not-a-date"


def test_falls_back_on_empty():
    assert _to_iso_date("") == "2024-01-01"
    assert _to_iso_date(None) == "2024-01-01"


def test_iso_dates_sort_correctly_against_old_seed_dates():
    """The actual bug: a converted seed date must sort BEFORE a later real date."""
    seed_date = _to_iso_date("24-10-2016")
    new_confirmed_date = "2026-09-27"
    assert sorted([seed_date, new_confirmed_date])[-1] == new_confirmed_date
