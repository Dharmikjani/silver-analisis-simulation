"""
ISO/IEC/IEEE 29119-4 Comprehensive 100% Coverage Completion Suite
Objective: Exercise every remaining branch and statement across src/ modules to achieve maximum feasible coverage.
"""
import os
import sys
import copy
import random
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

import config
import exchanges
import logger
import macro
import realworld
import stakeholders
from engine import SimulationEngine, run_simulation_core


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class TestCoveragePushEngine:
    """Target remaining uncovered branches in src/engine.py."""

    def test_cov_engine_init_zeros_and_jitter(self):
        """Cover lines 18, 28, 30 in engine.py: start_silver_price == 0, start_gold_price == 0, jitter > 0."""
        cfg = copy.deepcopy(config.FUTURE_2026_STATE)
        cfg.start_silver_price = 0.0
        cfg.start_gold_price = 0.0
        with patch.object(macro.LiveDataOracle, "fetch_live_data", lambda self: setattr(self, 'silver_price', 30.0) or setattr(self, 'gold_price', 2500.0)):
            eng = SimulationEngine(mode="future", config=cfg, years=1, seed=123, jitter=0.05)
            assert eng.config.start_silver_price == 30.0
            assert eng.config.start_gold_price == 2500.0

    def test_cov_engine_run_simulation_core_entrypoint(self):
        """Cover lines 562-566 in engine.py: run_simulation_core function."""
        cfg = copy.deepcopy(config.FUTURE_2026_STATE)
        cfg.start_silver_price = 30.0
        cfg.start_gold_price = 2500.0
        daily_data, stats = run_simulation_core(mode="backtest", config=cfg, years=1, seed=42, return_full=True)
        assert len(daily_data) == config.TRADING_DAYS
        assert "end_price" in stats

    def test_cov_engine_etf_outflow_dynamic_supply(self, standard_engine):
        """Cover line 269 in engine.py: etf_flow < 0 dynamic supply addition."""
        with patch.object(standard_engine.etf_holdings, "process_day", return_value=-15.0):
            standard_engine._process_demand(total_supply=50.0)
            assert standard_engine.dynamic_supply_add >= 15.0

    def test_cov_engine_margin_hike_and_bank_run(self, standard_engine):
        """Cover lines 282-283 and 290-291 in engine.py."""
        # 1. Margin hike dampening
        standard_engine.exchange_margins.margin_hike_active = True
        standard_engine.comex.force_majeure_active = True
        standard_engine._process_demand(total_supply=50.0)
        
        # 2. Bank run drain
        standard_engine.unallocated_holders.vault_confidence = 10.0
        standard_engine.lbma.vault_float = 50.0
        standard_engine._process_demand(total_supply=50.0)
        assert standard_engine.stats.get("bank_run_count", 0) >= 1

    def test_cov_engine_squeeze_price_multiplier_random(self, standard_engine):
        """Cover lines 507-509 in engine.py: squeeze_days < 30 and price multiplier."""
        standard_engine.comex.vault_float = 0.0
        standard_engine.squeeze_triggered = True
        standard_engine.stats["squeeze_days"] = 10
        old_price = standard_engine.physical_price

        with patch("random.random", return_value=0.01): # Force random < 0.10
            standard_engine._update_exchanges_and_stats(day=1, lbma_demand=100.0, comex_demand=50.0, base_supply=10.0)
            assert standard_engine.physical_price > old_price

    def test_cov_engine_comex_eligible_to_registered_transfer_branch(self, standard_engine):
        """Cover lines 479-481 in engine.py: eligible to registered transfer."""
        standard_engine.comex.vault_float = 20.0
        standard_engine.comex.eligible_float = 50.0
        standard_engine.physical_price = 100.0
        standard_engine.config.start_silver_price = 30.0
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=0.0)
        assert standard_engine.comex.eligible_float <= 50.0


class TestCoveragePushMacro:
    """Target remaining uncovered branches in src/macro.py."""

    def test_cov_macro_all_stochastic_shocks(self, clean_macro):
        """Cover lines 156-159, 173, 185-186, 189-190, 193-195, 204-205, 208-210 in macro.py."""
        clean_macro.brics_announced = False
        clean_macro.cbdc_launched = False
        clean_macro.ai_bubble_burst = False
        clean_macro.mining_strike_active = False
        clean_macro.retail_capitulation = False
        clean_macro.refinery_energy_crisis = False
        clean_macro.geopolitical_tension_index = 80.0

        with patch("random.random", return_value=0.0):
            clean_macro.simulate_day()
            assert clean_macro.brics_announced is True
            assert clean_macro.cbdc_launched is True
            assert clean_macro.ai_bubble_burst is True
            assert clean_macro.mining_strike_active is True
            assert clean_macro.retail_capitulation is True
            assert clean_macro.refinery_energy_crisis is True
            assert clean_macro.export_ban_active is True

    def test_cov_macro_line_175_brics_drain_active(self, clean_macro):
        """Cover line 175 in macro.py: tension <= 75 and brics_announced == True."""
        clean_macro.geopolitical_tension_index = 50.0
        clean_macro.brics_announced = True
        clean_macro.brics_vault_drain_daily = 0.0
        clean_macro.simulate_day()
        assert clean_macro.brics_vault_drain_daily > 0


class TestCoveragePushConfig:
    """Target lines 119-120 in src/config.py."""

    def test_cov_config_yaml_import_error(self):
        """Cover lines 119-120: PyYAML not installed exception path."""
        orig_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("No module named 'yaml'")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(ImportError):
                config.SimConfig.from_yaml("some_path.yaml")


class TestCoveragePushRealWorld:
    """Target lines 18-21 and 35-36 in src/realworld.py."""

    def test_cov_realworld_successful_fetch(self):
        """Cover lines 18-21 in realworld.py: successful non-empty history fetch."""
        with patch("yfinance.Tickers") as mock_tickers:
            mock_inst = MagicMock()
            t_si = MagicMock()
            t_si.history.return_value = pd.DataFrame({"Close": [33.50]})
            t_gc = MagicMock()
            t_gc.history.return_value = pd.DataFrame({"Close": [2550.00]})
            t_tnx = MagicMock()
            t_tnx.history.return_value = pd.DataFrame({"Close": [4.25]})
            mock_inst.tickers = {"SI=F": t_si, "GC=F": t_gc, "^TNX": t_tnx}
            mock_tickers.return_value = mock_inst

            res = realworld.fetch_live_market_data()
            assert res["success"] is True
            assert res["silver_price"] == 33.50
            assert res["gold_price"] == 2550.00
            assert res["fed_rate_proxy"] == 4.25

    def test_cov_realworld_main_block(self):
        """Cover lines 35-36 in realworld.py: if __name__ == '__main__': block."""
        import runpy
        realworld_path = os.path.join(ROOT_DIR, "src", "realworld.py")
        with patch("realworld.fetch_live_market_data", return_value={"success": True, "silver_price": 30.0}):
            runpy.run_path(realworld_path, run_name="__main__")


class TestCoveragePushStakeholders:
    """Target remaining uncovered branches in src/stakeholders.py."""

    def test_cov_stakeholders_base_class(self):
        """Cover line 12: Stakeholder.process_day abstract pass."""
        sh = stakeholders.Stakeholder("Generic", 100.0)
        assert sh.process_day(30.0, None) is None

    def test_cov_stakeholders_byproduct_miners_hoard_and_dump(self, clean_macro):
        """Cover lines 99-102 and 105-107 in stakeholders.py."""
        miner = stakeholders.ByproductMiners("Byproduct", 600.0)
        # 1. Price < hoard_threshold (15.0) -> withhold
        out_withheld = miner.process_day(price=10.0, macro=clean_macro)
        assert miner.withheld_inventory > 0
        assert out_withheld > 0

        # 2. Price > hoard_threshold * 1.5 with withheld inventory -> dump
        out_dump = miner.process_day(price=30.0, macro=clean_macro)
        assert out_dump > 0

    def test_cov_stakeholders_scrap_and_ewaste_low_price_hoard(self, clean_macro):
        """Cover line 148 and 166: price < hoard_threshold."""
        scrap = stakeholders.ScrapRefiners("Scrap", 150.0)
        assert scrap.process_day(price=10.0, macro=clean_macro) == 0.0

        ewaste = stakeholders.EWasteRecyclers("EWaste", 40.0)
        assert ewaste.process_day(price=10.0, macro=clean_macro) == 0.0

    def test_cov_stakeholders_smugglers_duty_active(self, clean_macro):
        """Cover line 235: macro.india_duty_active == True."""
        smugglers = stakeholders.BlackMarketSmugglers("Smugglers", 5.0)
        clean_macro.india_duty_active = True
        rate = smugglers.process_day(price=30.0, macro=clean_macro)
        assert rate > 0

    def test_cov_stakeholders_solar_pv_early_year_and_substitution(self, clean_macro):
        """Cover lines 273, 275, 298-299, 303-306 in SolarPV."""
        solar = stakeholders.SolarPV("Solar", 150.0)
        # Year < 2005
        clean_macro.current_year = 2000
        assert solar.process_day(price=30.0, macro=clean_macro) == 0

        # daily_volume == 0 seed
        clean_macro.current_year = 2010
        solar.daily_volume = 0
        solar.process_day(price=30.0, macro=clean_macro)
        assert solar.daily_volume > 0

        # Breakthrough substitution trigger
        clean_macro.current_year = 2030
        solar.substitution_rd_budget = 1.0
        with patch("random.random", return_value=0.0001):
            out = solar.process_day(price=300.0, macro=clean_macro)
            assert solar.substitution_triggered is True
            assert out > 0

    def test_cov_stakeholders_tech_ai_early_year(self, clean_macro):
        """Cover lines 349-350 in Tech_AI."""
        ai = stakeholders.Tech_AI("AI", 80.0)
        clean_macro.current_year = 2018
        out = ai.process_day(price=30.0, macro=clean_macro)
        assert out > 0

    def test_cov_stakeholders_ev_auto_early_years(self, clean_macro):
        """Cover lines 380, 382, 388 in EV_Auto."""
        ev = stakeholders.EV_Auto("EV", 100.0)
        # Year < 2012
        clean_macro.current_year = 2010
        assert ev.process_day(price=30.0, macro=clean_macro) == 0

        # Seed daily_volume == 0
        clean_macro.current_year = 2015
        ev.daily_volume = 0
        out = ev.process_day(price=30.0, macro=clean_macro)
        assert ev.daily_volume > 0
        assert out > 0

    def test_cov_stakeholders_jewelry_extreme_dip_buy(self, clean_macro):
        """Cover line 409 in JewelrySilverware."""
        jewel = stakeholders.JewelrySilverware("Jewelry", 200.0)
        out = jewel.process_day(price=10.0, macro=clean_macro) # price < 15.0
        assert out > 0

    def test_cov_stakeholders_other_industrial_price_tiers(self, clean_macro):
        """Cover lines 428 and 430 in OtherIndustrial."""
        other = stakeholders.OtherIndustrial("Other", 280.0)
        # Severe destruction > 300
        out_severe = other.process_day(price=350.0, macro=clean_macro)
        assert out_severe > 0
        # Moderate thrifting > 150
        out_mod = other.process_day(price=180.0, macro=clean_macro)
        assert out_mod > 0

    def test_cov_stakeholders_gov_central_banks_brics(self, clean_macro):
        """Cover line 447 in Gov_CentralBanks."""
        cb = stakeholders.Gov_CentralBanks("CB", 10.0)
        clean_macro.brics_announced = True
        out = cb.process_day(price=30.0, macro=clean_macro)
        assert out > 0

    def test_cov_stakeholders_gov_india_trade_deficit_and_quarterly(self, clean_macro):
        """Cover lines 476 and 484 in Gov_India."""
        india = stakeholders.Gov_India()
        clean_macro.config = config.FUTURE_2026_STATE
        # High price * high jewelry demand ensures daily import cost > 500 limit
        for _ in range(65):
            india.process_jewelry_demand(price=250.0, base_jewelry_demand=20.0, macro=clean_macro)
        assert india.import_duty_level > 0

    def test_cov_stakeholders_solar_reversion_restored(self, clean_macro):
        """Cover lines 283-285 in SolarPV: reversion after 30 days under competitive threshold."""
        solar = stakeholders.SolarPV("Solar", 100.0)
        solar.substitution_triggered = True
        for _ in range(35):
            ret = solar.process_day(price=20.0, macro=clean_macro)
        assert ret == solar.daily_volume * solar.loading_factor

    def test_cov_stakeholders_gov_china_momentum_branches(self, clean_macro):
        """Cover lines 526 and 528 in Gov_China."""
        china = stakeholders.Gov_China("China", 20.0)
        # Momentum > 1.05
        china.price_history = [8.0]
        china.process_day(price=10.0, macro=clean_macro)
        assert china._current_accumulation_rate == 50.0

        # Momentum < 0.95
        china.price_history = [12.0]
        china.process_day(price=10.0, macro=clean_macro)
        assert china._current_accumulation_rate == 1000.0

    def test_cov_stakeholders_margin_controls_reset_on_down_days(self):
        """Cover lines 756-758 in ExchangeMarginControls: end hike on 5 down days."""
        mc = stakeholders.ExchangeMarginControls()
        mc.margin_hike_active = True
        mc.consecutive_down_days = 4
        # 5th down day
        ret = mc.process_day(price_momentum=0.98, implied_volatility=0.30)
        assert mc.margin_hike_active is False
        assert ret == 0.0

    def test_cov_stakeholders_sge_asian_arb_drain_positive(self, clean_macro):
        """Cover lines 840-841 in stakeholders.SGE_Asian_Arbitrage: spread > 0.50 and drain > 0."""
        sge = stakeholders.SGE_Asian_Arbitrage()
        sge.east_west_spread = 2.0
        drain = sge.process_drain(vault_float=100.0, current_price=55.0, macro=clean_macro)
        assert drain > 0

    def test_cov_stakeholders_unallocated_bank_run_end(self):
        """Cover lines 857-862 in UnallocatedAccountHolders: confidence recovery and log reset."""
        uah = stakeholders.UnallocatedAccountHolders()
        uah.bank_run_active = True
        uah.vault_confidence = 49.0
        # Refill with vault_float > 200
        for _ in range(5):
            uah.check_bank_run(vault_float=250.0)
        assert uah.vault_confidence > 50.0
        assert uah.bank_run_active is False

    def test_cov_stakeholders_gov_china_momentum_neutral(self, clean_macro):
        """Cover line 530 in Gov_China."""
        china = stakeholders.Gov_China("China", 20.0)
        china.price_history = [10.0]
        # Price = 10.0 -> momentum = 1.0 (between 0.95 and 1.05)
        china.process_day(price=10.0, macro=clean_macro)
        assert china._current_accumulation_rate == 250.0

    def test_cov_stakeholders_retail_extreme_price_power(self, clean_macro):
        """Cover lines 604-605 in RetailInvestors."""
        retail = stakeholders.RetailInvestors("Retail", 250.0)
        out = retail.process_day(price=400.0, macro=clean_macro)
        assert out > 0

    def test_cov_stakeholders_retail_golden_cross(self, clean_macro):
        """Cover lines 589-593 in RetailInvestors: Golden cross momentum buying."""
        retail = stakeholders.RetailInvestors("Retail", 250.0)
        # 150 days at $20, then 50 days at $30: sma_50 = 30, sma_200 = 22.5
        retail.price_history = [20.0] * 150 + [30.0] * 50
        out = retail.process_day(price=35.0, macro=clean_macro)
        assert out > retail.daily_volume

    def test_cov_stakeholders_predatory_hedge_fund_dump_lifecycle(self, clean_macro):
        """Cover lines 674-677 and 683-689 in PredatoryHedgeFund."""
        fund = stakeholders.PredatoryHedgeFund()
        fund.is_squeezing = True
        fund.holdings = 39.0
        fund.target_price = 50.0

        # Trigger target reached transition to dumping (lines 674-677)
        ret1 = fund.process_attack(comex_float=100.0, physical_price=55.0, macro=clean_macro)
        assert fund.is_squeezing is False
        assert fund.is_dumping is True
        assert ret1 == 0.0

        # Execute dump until empty (lines 683-689)
        while fund.is_dumping:
            fund.process_attack(comex_float=100.0, physical_price=55.0, macro=clean_macro)
        assert fund.holdings == 0.0

    def test_cov_stakeholders_options_mm_steady_decay(self):
        """Cover line 706 in OptionsMarketMakers."""
        omm = stakeholders.OptionsMarketMakers()
        omm.implied_volatility = 0.50
        # price_momentum between 0.95 and 1.2, retail_demand low
        omm.process_delta_hedge(retail_demand=0.1, price_momentum=1.05)
        assert omm.implied_volatility == 0.49

    def test_cov_stakeholders_duplicate_sge_arbitrage(self, clean_macro):
        """Cover lines 825, 829-843 in stakeholders.py duplicate SGE_Asian_Arbitrage."""
        sge = stakeholders.SGE_Asian_Arbitrage()
        clean_macro.brics_announced = True
        drain = sge.process_drain(vault_float=100.0, current_price=60.0, macro=clean_macro)
        assert drain >= 0

    def test_cov_stakeholders_billionaire_dip_buy_and_geopolitics(self, clean_macro):
        """Cover lines 924-927 and 931-933 in Billionaire_Family_Offices."""
        fam = stakeholders.Billionaire_Family_Offices(vault_float=400.0)
        # Dip buy below $15
        flow_dip = fam.process_day(price=10.0, macro=clean_macro, current_gsr=80.0)
        assert flow_dip == 5.0

        # Geopolitical buy
        clean_macro.geopolitical_tension_index = 85.0
        flow_geo = fam.process_day(price=30.0, macro=clean_macro, current_gsr=50.0)
        assert flow_geo == 2.0

    def test_cov_stakeholders_global_etf_holdings_drained(self):
        """Cover line 983 in Global_ETF_Holdings."""
        etf = stakeholders.Global_ETF_Holdings(vault_float=0.0)
        etf.process_day(price=30.0, price_momentum=1.0)
        assert etf.is_drained is True
