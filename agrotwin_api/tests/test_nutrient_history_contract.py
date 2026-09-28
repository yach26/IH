import json
from datetime import date, timedelta
import pytest
from app.core.nutrients import normalize, actionable_gap, elemental
from app.core.application_history import residual_credit
from app.ledger import run_field_ledger
from app.api.routes import get_twin


def test_elemental_and_oxide_inputs_normalize_once():
    assert normalize(100, 10, 20) == {"N": 100, "P2O5": 22.919, "K2O": 24.092}
    assert normalize(100, 22.919, 24.092, p_basis="P2O5", k_basis="K2O") == normalize(100, 10, 20)
    p, k = elemental(22.919, 24.092, p_basis="P2O5", k_basis="K2O")
    assert p == pytest.approx(10)
    assert k == pytest.approx(20)
    assert normalize(None, None, None) == dict(N=None, P2O5=None, K2O=None)


@pytest.mark.parametrize("value", [-1, float('nan'), float('inf')])
def test_invalid_nutrients_rejected(value):
    with pytest.raises(ValueError):
        normalize(value, 10, 10)


def test_twin_matches_ledger_units(conn, field_row):
    ledger = run_field_ledger(conn, field_row)
    twin = get_twin('TEST-001', conn)
    for wire, nutrient in [('n','N'), ('p','P2O5'), ('k','K2O')]:
        assert twin['nutrients'][wire]['current'] == ledger['normalized_soil'][nutrient]
        assert twin['nutrients'][wire]['target'] == ledger['required'][nutrient]
    assert ledger['gap'] == actionable_gap(ledger['required'], ledger['normalized_soil'])


def add_application(conn, field_id, applied, qty=100):
    conn.execute('''INSERT INTO applications (field_id, product_id, application_date, quantity_kg_ha,
        n_supplied_kg_ha,p2o5_supplied_kg_ha,k2o_supplied_kg_ha)
        VALUES (?,(SELECT product_id FROM fertilizer_products WHERE product_code='UREA'),?,?,?,0,0)''',
        (field_id, applied.isoformat(), qty, qty*.46))
    conn.commit()


def test_recent_application_without_policy_abstains(conn, field_row, ids):
    conn.execute('UPDATE soil_tests SET test_date=?', ((date.today()-timedelta(days=30)).isoformat(),))
    add_application(conn, ids['field_id'], date.today()-timedelta(days=7))
    result = run_field_ledger(conn, field_row)
    assert result['status'] == 'ABSTAIN'
    assert result['application_history']['credits_kg_ha'] is None


def test_configured_credit_reduces_gap_and_is_traceable(conn, field_row, ids, monkeypatch):
    conn.execute('UPDATE soil_tests SET test_date=?', ((date.today()-timedelta(days=30)).isoformat(),))
    baseline = run_field_ledger(conn, field_row)
    add_application(conn, ids['field_id'], date.today()-timedelta(days=7))
    policy={'source':'TEST ONLY explicit agronomist-reviewed policy', 'crop_code':'SUGARCANE',
            'products': {'UREA': {'max_age_days':30, 'fractions':dict(N=.5,P2O5=.3,K2O=.4)}}}
    monkeypatch.setenv('AGROTWIN_RESIDUAL_POLICY', json.dumps(policy))
    revised=run_field_ledger(conn,field_row)
    assert revised['gap']['N'] == baseline['gap']['N']-23
    assert revised['plan_kg_ha']['UREA_kg_ha'] < baseline['plan_kg_ha']['UREA_kg_ha']
    assert revised['application_history']['source'] == policy['source']


def test_soil_sample_prevents_double_counting_and_field_isolation(conn, field_row, ids):
    before=run_field_ledger(conn,field_row)
    add_application(conn,ids['field_id'],date.today()-timedelta(days=1))
    after=run_field_ledger(conn,field_row)
    assert before['gap'] == after['gap']
    assert after['application_history']['applications'][0]['status'] == 'ALREADY_REFLECTED_IN_SOIL_OR_PRIOR_CROP'
    assert residual_credit(conn, 9999, date.today().isoformat(), None, 'SUGARCANE')['applications'] == []


def test_same_day_application_requires_review(conn, field_row, ids):
    add_application(conn,ids['field_id'],date.today())
    assert run_field_ledger(conn,field_row)['status'] == 'ABSTAIN'


def test_missing_soil_nutrient_abstains_instead_of_zero(conn,field_row):
    conn.execute('UPDATE soil_tests SET p_kg_ha=NULL')
    assert run_field_ledger(conn,field_row)['status']=='ABSTAIN'
    assert get_twin('TEST-001',conn)['nutrients']['p']['current'] is None
