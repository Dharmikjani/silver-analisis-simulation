"""
ISO/IEC/IEEE 29119-4 Clause 7.3: Branch / Decision Testing Suite
Objective: Ensure both TRUE and FALSE outcomes for all conditional decisions across src/ modules.
"""
import pytest
from unittest.mock import patch

import config
import exchanges
import macro
import stakeholders
from engine import SimulationEngine

class TestBranchCoverageEngine:
    """Branch coverage tests targeting SimulationEngine decision points."""

    def test_br_hoard_depletion(self, standard_engine):
        """Branch test for hoard_depletion_count trigger (engine.py:155)."""
        standard_engine.stats["hoard_depletion_count"] = 0
        standard_engine.macro.m2_inflation_index = 1.0

        # Branch FALSE: hoard > 0
        standard_engine.supply_hoarders.total_hoard = 100.0
        standard_engine.physical_price = 300.0
        standard_engine._process_supply()
        assert standard_engine.stats["hoard_depletion_count"] == 0

        # Branch TRUE: hoard <= 0 and price > 250
        for agent in standard_engine.supply_hoarders.sub_agents:
            agent['share'] = 0.0
        standard_engine.supply_hoarders.total_hoard = 0.0
        standard_engine.physical_price = 300.0
        standard_engine._process_supply()
        assert standard_engine.stats["hoard_depletion_count"] == 1

    def test_br_scrap_fatigue(self, standard_engine):
        """Branch test for scrap fatigue trigger (engine.py:169)."""
        standard_engine.stats["scrap_fatigue_count"] = 0

        # Branch FALSE: fatigue days low
        standard_engine.supply_scrap.scrap_fatigue_days = 10
        standard_engine._process_supply()
        assert standard_engine.stats["scrap_fatigue_count"] == 0

        # Branch TRUE: fatigue days > 3 * TRADING_DAYS
        standard_engine.supply_scrap.scrap_fatigue_days = 3 * config.TRADING_DAYS + 5
        standard_engine._process_supply()
        assert standard_engine.stats["scrap_fatigue_count"] == 1

    def test_br_ewaste_ratio_threshold(self, standard_engine):
        """Branch test for ewaste recovery ratio (engine.py:211)."""
        # Branch FALSE: physical price <= 100 -> ratio 0.20
        standard_engine.physical_price = 90.0
        standard_engine.macro.global_ewaste_pool = 100.0
        standard_engine._process_demand(total_supply=100.0)
        pool_after_low = standard_engine.macro.global_ewaste_pool

        # Branch TRUE: physical price > 100 -> ratio 0.50
        standard_engine.physical_price = 150.0
        standard_engine.macro.global_ewaste_pool = 100.0
        standard_engine._process_demand(total_supply=100.0)
        pool_after_high = standard_engine.macro.global_ewaste_pool

        # Higher recovery ratio results in higher pool additions
        assert pool_after_high > pool_after_low

    def test_br_billionaire_dynamic_supply(self, standard_engine):
        """Branch test for billionaire syndication flow (engine.py:251)."""
        # Branch TRUE: flow < 0 (Billionaires liquidating inventory adds supply)
        with patch.object(standard_engine.billionaire_syndicate, "process_day", return_value=-5.0):
            standard_engine._process_demand(total_supply=50.0)
            assert standard_engine.dynamic_supply_add == 5.0

        # Branch FALSE: flow >= 0 (Buying silver)
        with patch.object(standard_engine.billionaire_syndicate, "process_day", return_value=5.0):
            standard_engine._process_demand(total_supply=50.0)
            assert standard_engine.dynamic_supply_add == 0.0

    def test_br_drift_extinction_branch(self, standard_engine):
        """Branch test for drift calculation with vaults < 10 vs >= 10 (engine.py:356)."""
        # Branch TRUE: total_vaults < 10.0 (extinction drift cap 5.0)
        standard_engine.comex.vault_float = 2.0
        standard_engine.lbma.vault_float = 2.0
        standard_engine._update_price(lbma_demand=100.0, comex_demand=50.0, base_supply=10.0)
        p_price_extinct = standard_engine.physical_price

        # Branch FALSE: total_vaults >= 10.0 (normal drift cap 0.25)
        standard_engine.comex.vault_float = 100.0
        standard_engine.lbma.vault_float = 100.0
        standard_engine.physical_price = 30.0
        standard_engine.paper_price = 30.0
        standard_engine._update_price(lbma_demand=100.0, comex_demand=50.0, base_supply=10.0)
        p_price_normal = standard_engine.physical_price

        assert p_price_extinct > p_price_normal

    def test_br_paper_drift_margin_vs_fm(self, standard_engine):
        """Branch test for paper drift under margin hike vs force majeure (engine.py:408)."""
        # Branch 1: Margin hike active
        standard_engine.exchange_margins.margin_hike_active = True
        standard_engine.comex.force_majeure_active = False
        standard_engine.paper_price = 50.0
        standard_engine._update_price(lbma_demand=50.0, comex_demand=50.0, base_supply=50.0)
        assert standard_engine.stats.get("decoupling_days", 0) >= 1

        # Branch 2: Force majeure active
        standard_engine.exchange_margins.margin_hike_active = False
        standard_engine.comex.force_majeure_active = True
        standard_engine._update_price(lbma_demand=50.0, comex_demand=50.0, base_supply=50.0)
        assert standard_engine.paper_price > 0

    def test_br_comex_force_majeure_deficit(self, standard_engine):
        """Branch test for COMEX force majeure deficit zeroing (engine.py:471)."""
        standard_engine.stats["fm_days"] = 0
        standard_engine.comex.force_majeure_active = True
        standard_engine._update_exchanges_and_stats(
            day=1, lbma_demand=50.0, comex_demand=50.0, base_supply=20.0
        )
        assert standard_engine.stats["fm_days"] == 1

    def test_br_efp_cross_atlantic_arbitrage(self, standard_engine):
        """Branch test for EFP flow: NY to London vs London to NY (engine.py:488)."""
        standard_engine.lbma.defaulted = False
        standard_engine.comex.defaulted = False

        # Branch 1: NY to London (London stressed, NY has silver)
        standard_engine.lbma.vault_float = 40.0
        standard_engine.comex.vault_float = 100.0
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=20.0)
        # Transferred from COMEX to LBMA
        assert standard_engine.comex.vault_float < 100.0

        # Branch 2: London to NY (NY stressed, London has silver)
        standard_engine.comex.vault_float = 40.0
        standard_engine.lbma.vault_float = 100.0
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=20.0)
        # Transferred from LBMA to COMEX
        assert standard_engine.lbma.vault_float < 100.0

    def test_br_vault_deficit_positive_vs_negative(self, standard_engine):
        """Branch test for positive vs negative deficits on vaults (engine.py:511 & 523)."""
        standard_engine.comex.vault_float = 50.0
        standard_engine.lbma.vault_float = 50.0

        # Surplus (Supply > Demand) -> Deficit < 0 -> Vault increases
        standard_engine._update_exchanges_and_stats(
            day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=100.0
        )
        assert standard_engine.comex.vault_float > 50.0
        assert standard_engine.lbma.vault_float > 50.0


class TestBranchCoverageMacroAndExchanges:
    """Branch coverage tests targeting MacroEnvironment and Exchanges."""

    def test_br_copper_recession_dynamics(self, clean_macro):
        """Branch test for GDP growth < 0 vs >= 0 on copper price (macro.py:130)."""
        # Branch TRUE: global_gdp_growth < 0
        clean_macro.global_gdp_growth = -0.02
        clean_macro.simulate_day()
        assert clean_macro.copper_price_index > 0

        # Branch FALSE: global_gdp_growth >= 0
        clean_macro.global_gdp_growth = 0.03
        clean_macro.simulate_day()
        assert clean_macro.copper_price_index <= 1.2

    def test_br_oil_drift_tension_vs_recession(self, clean_macro):
        """Branch test for oil drift: tension > 75 vs recession < -0.01 vs nominal (macro.py:136)."""
        # Branch 1: High tension > 75
        clean_macro.geopolitical_tension_index = 80.0
        clean_macro.global_gdp_growth = 0.02
        clean_macro.simulate_day()
        assert clean_macro.oil_price > 10.0

        # Branch 2: Severe recession < -0.01
        clean_macro.geopolitical_tension_index = 50.0
        clean_macro.global_gdp_growth = -0.03
        clean_macro.simulate_day()
        assert clean_macro.oil_price > 10.0

    def test_br_iibx_vault_inventory_exhaustion(self, clean_macro):
        """Branch test for IIBX inventory exhaustion (exchanges.py:51 & 57)."""
        # Branch FALSE: inventory >= 10
        iibx_full = exchanges.India_IIBX_Vault(capacity=100.0, inventory_start=20.0)
        fulfilled, _ = iibx_full.process_demand(local_demand_daily=5.0, macro=clean_macro)
        assert fulfilled == 5.0
        assert iibx_full.is_empty is False

        # Branch TRUE: inventory < 10
        iibx_empty = exchanges.India_IIBX_Vault(capacity=100.0, inventory_start=5.0)
        fulfilled2, _ = iibx_empty.process_demand(local_demand_daily=30.0, macro=clean_macro)
        assert fulfilled2 == 5.0
        assert iibx_empty.is_empty is True
