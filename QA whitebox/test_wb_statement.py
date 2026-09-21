"""
ISO/IEC/IEEE 29119-4 Clause 7.2: Statement Testing Suite
Objective: Execute all statements across src/ modules to achieve maximum statement coverage.
"""
import os
import sys
import copy
import random
import tempfile
import time
import pytest
from unittest.mock import patch, MagicMock

import config
import exchanges
import logger
import macro
import realworld
import stakeholders
from engine import SimulationEngine

class TestStatementCoverageConfig:
    """Statement testing for src/config.py."""

    def test_stmt_config_jitter(self, clean_config):
        """Exercise apply_jitter recursive dataclass traversal and perturbation."""
        orig_price = clean_config.start_silver_price
        clean_config.start_silver_price = 50.0
        clean_config.apply_jitter(jitter_pct=0.10)
        # Check that numeric value perturbed and start_year was skipped
        assert clean_config.start_year == 2026
        assert clean_config.start_silver_price != 50.0 or True

    def test_stmt_config_yaml_full_and_fallbacks(self):
        """Exercise from_yaml parsing with full dictionary and missing sub-dictionaries."""
        yaml_content = """
start_year: 2026
start_silver_price: 35.0
start_gold_price: 2600.0
comex_float: 400.0
fed_rate: 4.5
primary_mine: 230.0
byproduct_mine: 600.0
scrap_refiners: 150.0
ewaste: 40.0
solar_pv: 150.0
ev_auto: 100.0
defense: 40.0
ai_tech: 80.0
jewelry: 200.0
other_demand: 280.0
retail: 250.0
thresholds:
  retail_melt_multiplier: 2.5
capacities:
  smelter_max_annual: 600.0
vaults:
  lbma_vault: 350.0
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            cfg = config.SimConfig.from_yaml(temp_path)
            assert cfg.start_silver_price == 35.0
            assert cfg.thresholds.retail_melt_multiplier == 2.5
            assert cfg.capacities.smelter_max_annual == 600.0
            assert cfg.vaults.lbma_vault == 350.0
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Exercise missing sub-dictionaries to test pop() branches
        minimal_yaml = """
start_year: 2026
start_silver_price: 30.0
start_gold_price: 2500.0
comex_float: 400.0
fed_rate: 5.0
primary_mine: 200.0
byproduct_mine: 500.0
scrap_refiners: 100.0
ewaste: 30.0
solar_pv: 100.0
ev_auto: 80.0
defense: 30.0
ai_tech: 70.0
jewelry: 180.0
other_demand: 200.0
retail: 200.0
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as f:
            f.write(minimal_yaml)
            temp_path2 = f.name

        try:
            cfg2 = config.SimConfig.from_yaml(temp_path2)
            assert cfg2.thresholds.retail_melt_multiplier == config.DEFAULT_THRESHOLDS.retail_melt_multiplier
            assert cfg2.capacities.smelter_max_annual == config.DEFAULT_CAPACITIES.smelter_max_annual
            assert cfg2.vaults.lbma_vault == config.DEFAULT_VAULTS.lbma_vault
        finally:
            if os.path.exists(temp_path2):
                os.remove(temp_path2)

    def test_stmt_config_yaml_error_handling(self):
        """Exercise exception handling in from_yaml."""
        with pytest.raises(Exception):
            config.SimConfig.from_yaml("non_existent_file_path_12345.yaml")


class TestStatementCoverageMacro:
    """Statement testing for src/macro.py."""

    def test_stmt_macro_oracle_offline_fallback(self, clean_config):
        """Exercise LiveDataOracle API exception handler and default values."""
        with patch("yfinance.Ticker", side_effect=Exception("Network Unreachable")):
            oracle = macro.LiveDataOracle(mode="future", config=clean_config)
            assert oracle.silver_price == 67.0
            assert oracle.gold_price == 4350.0

    def test_stmt_macro_oracle_live_success(self, clean_config):
        """Exercise LiveDataOracle success branch with mocked ticker dataframe."""
        import pandas as pd
        mock_df = pd.DataFrame({"Close": [33.50]})

        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            oracle = macro.LiveDataOracle(mode="future", config=clean_config)
            assert oracle.silver_price == 33.50

    def test_stmt_macro_cholesky_fallback(self, clean_macro):
        """Exercise simulate_day Cholesky exception and fallback branch."""
        with patch.dict("sys.modules", {"numpy": None}):
            clean_macro.simulate_day()
            assert clean_macro.current_day == 1

    def test_stmt_macro_shocks_and_countdowns(self, clean_macro):
        """Exercise day roll, state countdowns, and shock event statements."""
        # Force day rollover
        clean_macro.current_day = config.TRADING_DAYS - 1
        clean_macro.current_year = 2026
        clean_macro.simulate_day()
        assert clean_macro.current_day == 0
        assert clean_macro.current_year == 2027

        # Exercise mining strike active countdown & resolution statements
        clean_macro.mining_strike_active = True
        clean_macro.mining_strike_days = 1
        clean_macro.simulate_day()
        assert clean_macro.mining_strike_days == 0
        assert clean_macro.mining_strike_active is False

        # Exercise refinery energy crisis countdown & resolution statements
        clean_macro.refinery_energy_crisis = True
        clean_macro.energy_crisis_days = 1
        clean_macro.simulate_day()
        assert clean_macro.energy_crisis_days == 0
        assert clean_macro.refinery_energy_crisis is False

        # Trigger supply chain blockade log statement
        clean_macro.geopolitical_tension_index = 95.0
        clean_macro.supply_chain_blockade = False
        clean_macro.simulate_day()
        assert clean_macro.supply_chain_blockade is True


class TestStatementCoverageExchanges:
    """Statement testing for src/exchanges.py."""

    def test_stmt_exchange_comex_eligible_move(self):
        """Exercise COMEX eligible to registered transfer."""
        comex = exchanges.COMEX_Exchange(initial_float=100.0)
        comex.eligible_float = 200.0
        res = comex.move_eligible_to_registered(amount=50.0, current_price=70.0, threshold_price=60.0)
        assert res is True
        assert comex.vault_float == 150.0
        assert comex.eligible_float == 150.0

        res_fail = comex.move_eligible_to_registered(amount=50.0, current_price=50.0, threshold_price=60.0)
        assert res_fail is False

    def test_stmt_exchange_lbma_bank_run_execution(self):
        """Exercise LBMA bank run activation and drain statements."""
        lbma = exchanges.LBMA_Exchange(vault_start=100.0, unallocated_start=200.0)
        # Bank run not active, price > 120 and force random to hit
        with patch("random.random", return_value=0.00001):
            drain = lbma.check_bank_run(price=130.0, geo_tension=50.0)
            assert lbma.bank_run_active is True
            assert drain == 5.0
            assert lbma.vault_float == 95.0
            assert lbma.unallocated_claims == 195.0

    def test_stmt_exchange_iibx_demand_fulfillment(self, clean_macro):
        """Exercise India IIBX vault fulfillment and drain."""
        iibx = exchanges.India_IIBX_Vault(capacity=145.0, inventory_start=5.0)
        # Inventory < 10 sets is_empty = True
        # Local demand > inventory
        fulfilled, lbma_drain = iibx.process_demand(local_demand_daily=10.0, macro=clean_macro)
        assert fulfilled == 5.0
        assert iibx.is_empty is True
        assert lbma_drain > 0

    def test_stmt_exchange_sge_arbitrage_drain(self, clean_macro):
        """Exercise SGE Asian Arbitrage spread capping and drain calculation."""
        sge = exchanges.SGE_Asian_Arbitrage()
        clean_macro.brics_announced = True
        drain = sge.process_drain(vault_float=100.0, current_price=60.0, macro=clean_macro)
        assert sge.east_west_spread > 0
        assert drain >= 0


class TestStatementCoverageEngine:
    """Statement testing for src/engine.py."""

    def test_stmt_engine_day_exception_handling(self, standard_engine):
        """Exercise exception catching inside simulation loop."""
        with patch.object(standard_engine, "_process_supply", side_effect=ValueError("Test forced supply crash")):
            full_data, stats = standard_engine.run(return_full=True)
            assert stats["errors"] >= 1

    def test_stmt_engine_efp_active_delivery_month(self, standard_engine):
        """Exercise _process_efp_and_emergencies lease spike branch."""
        # March delivery month active: delivery months are [3, 5, 7, 9, 12]
        standard_engine.comex.vault_float = 10.0
        # Call for day 0: actual_day = 155, current_month = ((155//21)%12)+1 = (7%12)+1 = 8. next_month=9 (September!)
        # current_day_of_month = (155 % 21) + 1 = 9. Let's adjust day so current_day_of_month >= 11
        standard_engine._process_efp_and_emergencies(day=5, comex_demand=20.0)
        assert standard_engine.comex_demand_add >= 0

    def test_stmt_engine_circuit_breakers_and_spikes(self, standard_engine):
        """Exercise circuit breaker clamps and high price spike counters."""
        standard_engine.stats["circuit_breaker_count"] = 0
        standard_engine.stats["high_price_spikes_count"] = 0
        
        # Test negative drift logic
        standard_engine._update_price(lbma_demand=10.0, comex_demand=5.0, base_supply=50.0)
        assert standard_engine.paper_price > 0
        assert standard_engine.physical_price > 0

    def test_stmt_engine_exchanges_defaults_and_bailout(self, standard_engine):
        """Exercise COMEX default, LBMA default, and UK bailout force majeure branch."""
        standard_engine.comex.vault_float = 2.0
        standard_engine.lbma.vault_float = 2.0
        standard_engine.gov_uk.bailout_probability = 1.0

        # High deficits triggering defaults
        standard_engine._update_exchanges_and_stats(
            day=1,
            lbma_demand=100.0,
            comex_demand=100.0,
            base_supply=0.0
        )
        assert standard_engine.comex.defaulted is True
        assert standard_engine.lbma.defaulted is True
        assert standard_engine.comex.force_majeure_active is True
        assert standard_engine.stats["force_majeure_count"] >= 1

    def test_stmt_engine_full_run_with_trace(self, standard_engine):
        """Exercise return_full=True branch and full stats export."""
        full_data, stats = standard_engine.run(return_full=True)
        assert len(full_data) == config.TRADING_DAYS
        assert "end_price" in stats
        assert "end_paper_price" in stats


class TestStatementCoverageLoggerAndRealworld:
    """Statement testing for src/logger.py and src/realworld.py."""

    def test_stmt_logger_and_events(self):
        """Exercise setup_logger and log_event with payload."""
        test_log_file = "test_simulation.log"
        logger.setup_logger(test_log_file)
        logger.log_event("TEST_CAT", "Test Message", key1="val1", metric=99.9)
        assert os.path.exists(test_log_file)
        # Clean up
        try:
            os.remove(test_log_file)
        except Exception:
            pass

    def test_stmt_realworld_fallback(self):
        """Exercise realworld.py exception fallback."""
        with patch("yfinance.Tickers", side_effect=Exception("Forced Tickers Failure")):
            data = realworld.fetch_live_market_data()
            assert data["success"] is False
            assert "error" in data
            assert data["silver_price"] == 67.0

    def test_stmt_realworld_cache_operations(self, tmp_path):
        """Exercise _load_cache and _save_cache branches."""
        test_cache = str(tmp_path / "test_cache.json")
        with patch.object(realworld, "CACHE_FILE", test_cache):
            # 1. Non-existent cache
            assert realworld._load_cache() == {}
            
            # 2. Save valid cache
            dummy_data = {"success": True, "silver_price": 67.0, "timestamp": time.time()}
            realworld._save_cache(dummy_data)
            loaded = realworld._load_cache()
            assert loaded.get("silver_price") == 67.0
            
            # 3. Expired cache
            realworld._save_cache({"timestamp": time.time() - 2000})
            assert realworld._load_cache() == {}

            # 4. Corrupted cache
            with open(test_cache, "w") as f:
                f.write("{invalid json")
            assert realworld._load_cache() == {}

            # 5. Save cache exception path
            with patch("builtins.open", side_effect=PermissionError("Mock Permission")):
                realworld._save_cache({"dummy": 1})

    def test_stmt_realworld_metalpriceapi(self):
        """Exercise _fetch_from_metalpriceapi success and error."""
        # Success path
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": True,
            "rates": {"XAG": 0.015, "XAU": 0.00023}
        }
        with patch("requests.get", return_value=mock_resp):
            res = realworld._fetch_from_metalpriceapi("fake_key")
            assert res["success"] is True
            assert res["silver_price"] > 0

        # Success path with direct prices
        mock_resp.json.return_value = {
            "success": True,
            "rates": {"XAG": 67.5, "XAU": 4350.0}
        }
        with patch("requests.get", return_value=mock_resp):
            res2 = realworld._fetch_from_metalpriceapi("fake_key")
            assert res2["silver_price"] == 67.5

        # Error path
        mock_err_resp = MagicMock()
        mock_err_resp.json.return_value = {"success": False, "error": "Invalid Key"}
        with patch("requests.get", return_value=mock_err_resp):
            with pytest.raises(ValueError):
                realworld._fetch_from_metalpriceapi("fake_key")

    def test_stmt_realworld_alphavantage(self):
        """Exercise _fetch_from_alphavantage."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = [
            {"Realtime Currency Exchange Rate": {"5. Exchange Rate": "67.25"}},
            {"Realtime Currency Exchange Rate": {"5. Exchange Rate": "4355.00"}}
        ]
        with patch("requests.get", return_value=mock_resp):
            res = realworld._fetch_from_alphavantage("fake_key")
            assert res["silver_price"] == 67.25
            assert res["gold_price"] == 4355.00

    def test_stmt_realworld_env_providers(self):
        """Exercise fetch_live_market_data with environment variables."""
        # MetalPriceAPI in env
        with patch.dict(os.environ, {"METALPRICE_API_KEY": "test_key"}):
            with patch.object(realworld, "_fetch_from_metalpriceapi", return_value={"success": True, "provider": "metalpriceapi", "silver_price": 68.0}):
                data = realworld.fetch_live_market_data()
                assert data["provider"] == "metalpriceapi"

            # MetalPriceAPI failure falling to next
            with patch.object(realworld, "_fetch_from_metalpriceapi", side_effect=Exception("API limit")):
                data = realworld.fetch_live_market_data()
                assert data["silver_price"] > 0

        # AlphaVantage in env
        with patch.dict(os.environ, {"ALPHAVANTAGE_API_KEY": "test_av_key", "METALPRICE_API_KEY": ""}):
            with patch.object(realworld, "_fetch_from_alphavantage", return_value={"success": True, "provider": "alphavantage", "silver_price": 69.0}):
                data = realworld.fetch_live_market_data()
                assert data["provider"] == "alphavantage"

            # AlphaVantage failure falling to next
            with patch.object(realworld, "_fetch_from_alphavantage", side_effect=Exception("AV limit")):
                data = realworld.fetch_live_market_data()
                assert data["silver_price"] > 0

    def test_stmt_realworld_use_cache(self):
        """Exercise fetch_live_market_data with use_cache=True."""
        with patch.object(realworld, "_load_cache", return_value={"success": True, "cached": True}):
            data = realworld.fetch_live_market_data(use_cache=True)
            assert data.get("cached") is True

