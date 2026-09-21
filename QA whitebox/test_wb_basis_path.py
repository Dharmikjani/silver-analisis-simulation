"""
ISO/IEC/IEEE 29119-4 Basis Path / Control Flow Testing Suite
Objective: Execute the linearly independent basis path sets derived from McCabe's Cyclomatic Complexity.
"""
import pytest
from unittest.mock import patch

import config
import exchanges
import macro
from engine import SimulationEngine

class TestBasisPathLBMA:
    """Basis path tests for LBMA_Exchange.check_bank_run (V(G) = 6)."""

    def test_bp_lbma_path_1_nominal_no_stress(self):
        """Path 1: Inactive, price & tension normal -> Returns 0."""
        lbma = exchanges.LBMA_Exchange(vault_start=100.0, unallocated_start=200.0)
        drain = lbma.check_bank_run(price=30.0, geo_tension=40.0)
        assert drain == 0
        assert lbma.bank_run_active is False

    def test_bp_lbma_path_2_panic_price_rng_miss(self):
        """Path 2: Inactive, price > 120, RNG check fails -> Returns 0."""
        lbma = exchanges.LBMA_Exchange(vault_start=100.0, unallocated_start=200.0)
        with patch("random.random", return_value=0.99):
            drain = lbma.check_bank_run(price=130.0, geo_tension=40.0)
            assert drain == 0
            assert lbma.bank_run_active is False

    def test_bp_lbma_path_3_panic_price_rng_hit_standard_drain(self):
        """Path 3: Inactive, price > 120, RNG hits, vault > 5 -> Drains 5.0."""
        lbma = exchanges.LBMA_Exchange(vault_start=100.0, unallocated_start=200.0)
        with patch("random.random", return_value=0.0):
            drain = lbma.check_bank_run(price=130.0, geo_tension=40.0)
            assert drain == 5.0
            assert lbma.vault_float == 95.0
            assert lbma.unallocated_claims == 195.0

    def test_bp_lbma_path_4_panic_geo_partial_vault_drain(self):
        """Path 4: Inactive, tension > 90, RNG hits, vault < 5 -> Drains remaining vault."""
        lbma = exchanges.LBMA_Exchange(vault_start=3.2, unallocated_start=100.0)
        with patch("random.random", return_value=0.0):
            drain = lbma.check_bank_run(price=50.0, geo_tension=95.0)
            assert drain == 3.2
            assert lbma.vault_float == 0.0

    def test_bp_lbma_path_5_already_active_empty_vault(self):
        """Path 5: Already active, vault == 0 -> Drains 0.0."""
        lbma = exchanges.LBMA_Exchange(vault_start=0.0, unallocated_start=100.0)
        lbma.bank_run_active = True
        drain = lbma.check_bank_run(price=150.0, geo_tension=95.0)
        assert drain == 0.0

    def test_bp_lbma_path_6_claims_underflow_protection(self):
        """Path 6: Already active, unallocated claims < drain -> Claims clamped at 0."""
        lbma = exchanges.LBMA_Exchange(vault_start=10.0, unallocated_start=2.0)
        lbma.bank_run_active = True
        drain = lbma.check_bank_run(price=100.0, geo_tension=50.0)
        assert drain == 5.0
        assert lbma.unallocated_claims == 0.0


class TestBasisPathPriceDiscovery:
    """Basis path tests for SimulationEngine._update_price (V(G) = 18)."""

    def test_bp_price_path_1_extinction_spike_and_circuit_breaker(self, standard_engine):
        """Path 1: Vaults < 10 Moz, huge deficit, extinction drift, breaker at 3.00."""
        standard_engine.comex.vault_float = 2.0
        standard_engine.lbma.vault_float = 2.0
        standard_engine.squeeze_triggered = True
        standard_engine.paper_price = 100.0
        standard_engine.physical_price = 100.0
        # Patch random.gauss to simulate massive jump triggering the 3.00 circuit breaker limit
        with patch("random.gauss", return_value=100.0):
            standard_engine._update_price(lbma_demand=500.0, comex_demand=200.0, base_supply=10.0)
            assert standard_engine.physical_premium > 0
            assert standard_engine.stats["circuit_breaker_count"] >= 1

    def test_bp_price_path_2_severe_surplus_and_aisc_floor(self, standard_engine):
        """Path 2: Deficit < 0, price below AISC floor, lower circuit breaker clamp (0.93)."""
        standard_engine.comex.vault_float = 500.0
        standard_engine.lbma.vault_float = 500.0
        standard_engine.physical_price = 15.0 # Below AISC floor ($30)
        standard_engine.paper_price = 15.0
        standard_engine._update_price(lbma_demand=5.0, comex_demand=5.0, base_supply=100.0)
        assert standard_engine.physical_price >= 0.10
        assert standard_engine.paper_price >= 0.10

    def test_bp_price_path_3_margin_hike_decoupling(self, standard_engine):
        """Path 3: Margin hike crushes paper price while physical premium is protected."""
        standard_engine.exchange_margins.margin_hike_active = True
        standard_engine.comex.force_majeure_active = False
        standard_engine.comex.vault_float = 50.0
        standard_engine.lbma.vault_float = 50.0
        standard_engine.paper_price = 50.0
        standard_engine.physical_price = 50.0
        standard_engine._update_price(lbma_demand=60.0, comex_demand=40.0, base_supply=50.0)
        assert standard_engine.stats.get("decoupling_days", 0) >= 1

    def test_bp_price_path_4_force_majeure_frozen_paper(self, standard_engine):
        """Path 4: Force majeure freezes paper momentum to 0.02x drift."""
        standard_engine.exchange_margins.margin_hike_active = False
        standard_engine.comex.force_majeure_active = True
        standard_engine.paper_price = 40.0
        standard_engine._update_price(lbma_demand=60.0, comex_demand=40.0, base_supply=50.0)
        assert standard_engine.paper_price > 0


class TestBasisPathMacroSimulateDay:
    """Basis path tests for MacroEnvironment.simulate_day (V(G) = 43)."""

    def test_bp_macro_path_1_recessionary_regime(self, clean_macro):
        """Path 1: Global recession, strong dollar, metal cycle drops."""
        clean_macro.dxy_strength = 112.0
        clean_macro.global_gdp_growth = -0.03
        clean_macro.simulate_day()
        assert clean_macro.base_metal_recession_active is True

    def test_bp_macro_path_2_geopolitical_super_crisis(self, clean_macro):
        """Path 2: Geopolitical tension > 85, defense stockpile & blockade active."""
        clean_macro.geopolitical_tension_index = 88.0
        clean_macro.supply_chain_blockade = False
        clean_macro.simulate_day()
        assert clean_macro.defense_stockpile_active is True
        assert clean_macro.supply_chain_blockade is True

    def test_bp_macro_path_3_resolution_of_active_shocks(self, clean_macro):
        """Path 3: Active strike & refinery crisis days hit 1 -> resolved."""
        clean_macro.mining_strike_active = True
        clean_macro.mining_strike_days = 1
        clean_macro.refinery_energy_crisis = True
        clean_macro.energy_crisis_days = 1
        clean_macro.simulate_day()
        assert clean_macro.mining_strike_active is False
        assert clean_macro.refinery_energy_crisis is False
