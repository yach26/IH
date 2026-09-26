"""Unit tests for HeuristicOptimizer + RuleEngine (doc 07)."""

from app.core.optimizer import HeuristicOptimizer, estimate_cost
from app.core.rules import RuleEngine
from app.ledger import convert_gap_to_products, get_products


class TestHeuristicOptimizer:
    def test_matches_ledger_convert_gap_to_products(self, conn, field_row):
        from app.ledger import run_field_ledger

        ledger = run_field_ledger(conn, field_row)
        products = get_products(conn)
        expected = convert_gap_to_products(
            ledger["gap"]["N"], ledger["gap"]["P2O5"], ledger["gap"]["K2O"], products
        )
        twin = {
            "region_id": "MH",
            "products": products,
            "gap": ledger["gap"],
            "current_plan": ledger,
        }
        plan = HeuristicOptimizer().optimize(twin)
        assert plan.optimizer_id == "heuristic_dap_urea_mop"
        assert plan.plan_kg_ha["DAP_kg_ha"] == expected["DAP_kg_ha"]
        assert plan.plan_kg_ha["UREA_kg_ha"] == expected["UREA_kg_ha"]
        assert plan.plan_kg_ha["MOP_kg_ha"] == expected["MOP_kg_ha"]
        assert plan.cost_estimate is not None
        assert "ENGINEERING_DEFAULT" in plan.cost_citation

    def test_zero_gap_is_zero_products(self, conn):
        products = get_products(conn)
        twin = {"products": products, "gap": {"N": 0, "P2O5": 0, "K2O": 0}}
        plan = HeuristicOptimizer().optimize(twin)
        assert plan.plan_kg_ha["DAP_kg_ha"] == 0
        assert plan.plan_kg_ha["UREA_kg_ha"] == 0
        assert plan.plan_kg_ha["MOP_kg_ha"] == 0

    def test_estimate_cost_uses_config_prices(self):
        total, currency, cite = estimate_cost({"UREA_kg_ha": 10, "DAP_kg_ha": 0, "MOP_kg_ha": 0})
        assert currency == "INR"
        assert total == 60.0  # 10 * 6.0
        assert "Gap #8" in cite


class TestRuleEngine:
    def _plan(self, **how):
        return {
            "plan_kg_ha": how,
            "how_much": how,
            "gap": {"N": 50, "P2O5": 20, "K2O": 10},
            "required": {"N": 340, "P2O5": 170, "K2O": 170},
        }

    def test_weather_window_fails_on_heavy_rain_with_n_gap(self, conn):
        products = get_products(conn)
        twin = {
            "products": products,
            "soil": {"ph": 7.0, "is_stale": False},
            "weather": {"heavy_rain_alert": True, "alert_details": "80mm"},
        }
        v = RuleEngine().hard_failures(self._plan(UREA_kg_ha=50, DAP_kg_ha=10, MOP_kg_ha=5), twin)
        assert any("WEATHER_CONFLICT" in x.message for x in v)

    def test_weather_ok_when_dry(self, conn):
        products = get_products(conn)
        twin = {
            "products": products,
            "soil": {"ph": 7.0, "is_stale": False},
            "weather": {"heavy_rain_alert": False},
        }
        v = RuleEngine().hard_failures(self._plan(UREA_kg_ha=50, DAP_kg_ha=10, MOP_kg_ha=5), twin)
        assert v == []

    def test_compatibility_urea_ssp(self, conn):
        products = get_products(conn)
        twin = {
            "products": products,
            "soil": {"ph": 7.0},
            "weather": {},
        }
        plan = self._plan(UREA_kg_ha=20, SSP_kg_ha=20)
        fails = RuleEngine().hard_failures(plan, twin)
        assert any(x.rule_id == "PRODUCT_COMPATIBILITY" for x in fails)

    def test_high_ph_is_warning_not_hard(self, conn):
        products = get_products(conn)
        twin = {
            "products": products,
            "soil": {"ph": 8.6, "is_stale": False},
            "weather": {},
        }
        engine = RuleEngine()
        hard = engine.hard_failures(self._plan(UREA_kg_ha=10), twin)
        allv = engine.check(self._plan(UREA_kg_ha=10), twin)
        assert hard == []
        assert any("HIGH_PH" in v.message for v in allv if not v.passed)

    def test_stale_soil_is_warning(self, conn):
        products = get_products(conn)
        twin = {
            "products": products,
            "soil": {"ph": 7.0, "is_stale": True, "days_since_test": 400},
            "weather": {},
        }
        engine = RuleEngine()
        assert engine.hard_failures(self._plan(UREA_kg_ha=10), twin) == []
        assert any("STALE_SOIL" in v.message for v in engine.check(self._plan(UREA_kg_ha=10), twin) if not v.passed)

    def test_max_rates_flags_overshoot(self, conn):
        products = get_products(conn)
        twin = {"products": products, "soil": {"ph": 7.0}, "weather": {}}
        # 10000 kg DAP would wildly exceed RDF
        plan = self._plan(DAP_kg_ha=10000)
        fails = RuleEngine().hard_failures(plan, twin)
        assert any(x.rule_id == "MAX_RATES_RDF" for x in fails)
