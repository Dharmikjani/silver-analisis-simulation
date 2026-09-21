"""
ISO/IEC/IEEE 29119-4 Clause 7.6: Modified Condition/Decision Coverage (MC/DC) Suite
Objective: Demonstrate that each atomic Boolean condition independently affects decision outcomes.
"""
import pytest
from unittest.mock import patch

import config
import exchanges
import macro
from engine import SimulationEngine

class TestMCDCLBMAExchange:
    """MC/DC for D1: not bank_run_active and (price > 120.0 or geo_tension > 90)."""

    def test_mcdc_d1_condition_a_independence(self):
        """Independence Pair for Condition A (bank_run_active)."""
        # Test 1: A=False, B=True, C=False -> Outcome=True (Bank run activates)
        lbma1 = exchanges.LBMA_Exchange()
        lbma1.bank_run_active = False
        with patch("random.random", return_value=0.0): # Force p-check to pass
            lbma1.check_bank_run(price=130.0, geo_tension=50.0)
            assert lbma1.bank_run_active is True

        # Test 2: A=True, B=True, C=False -> Inner trigger evaluated to False (no re-activation)
        lbma2 = exchanges.LBMA_Exchange()
        lbma2.bank_run_active = True
        # Already active, stays active without trigger event log
        drain = lbma2.check_bank_run(price=130.0, geo_tension=50.0)
        assert drain > 0

    def test_mcdc_d1_condition_b_independence(self):
        """Independence Pair for Condition B (price > 120.0)."""
        # Test 1: A=False, B=True, C=False -> Outcome=True
        lbma1 = exchanges.LBMA_Exchange()
        with patch("random.random", return_value=0.0):
            lbma1.check_bank_run(price=130.0, geo_tension=50.0)
            assert lbma1.bank_run_active is True

        # Test 3: A=False, B=False, C=False -> Outcome=False
        lbma3 = exchanges.LBMA_Exchange()
        with patch("random.random", return_value=0.0):
            lbma3.check_bank_run(price=100.0, geo_tension=50.0)
            assert lbma3.bank_run_active is False

    def test_mcdc_d1_condition_c_independence(self):
        """Independence Pair for Condition C (geo_tension > 90.0)."""
        # Test 4: A=False, B=False, C=True -> Outcome=True
        lbma4 = exchanges.LBMA_Exchange()
        with patch("random.random", return_value=0.0):
            lbma4.check_bank_run(price=100.0, geo_tension=95.0)
            assert lbma4.bank_run_active is True

        # Test 3 (from above): A=False, B=False, C=False -> Outcome=False
        lbma3 = exchanges.LBMA_Exchange()
        with patch("random.random", return_value=0.0):
            lbma3.check_bank_run(price=100.0, geo_tension=50.0)
            assert lbma3.bank_run_active is False


class TestMCDCIndiaIIBX:
    """MC/DC for D2: not export_ban_active and not supply_chain_blockade."""

    def test_mcdc_d2_condition_a_independence(self, clean_macro):
        """Independence Pair for Condition A (export_ban_active)."""
        iibx = exchanges.India_IIBX_Vault(capacity=100.0, inventory_start=20.0)

        # Test 1: A=False, B=False -> Outcome=True (LBMA drain executed)
        clean_macro.export_ban_active = False
        clean_macro.supply_chain_blockade = False
        _, drain1 = iibx.process_demand(local_demand_daily=5.0, macro=clean_macro)
        assert drain1 > 0

        # Test 2: A=True, B=False -> Outcome=False (LBMA drain halted)
        clean_macro.export_ban_active = True
        clean_macro.supply_chain_blockade = False
        _, drain2 = iibx.process_demand(local_demand_daily=5.0, macro=clean_macro)
        assert drain2 == 0

    def test_mcdc_d2_condition_b_independence(self, clean_macro):
        """Independence Pair for Condition B (supply_chain_blockade)."""
        iibx = exchanges.India_IIBX_Vault(capacity=100.0, inventory_start=20.0)

        # Test 1: A=False, B=False -> Outcome=True (LBMA drain executed)
        clean_macro.export_ban_active = False
        clean_macro.supply_chain_blockade = False
        _, drain1 = iibx.process_demand(local_demand_daily=5.0, macro=clean_macro)
        assert drain1 > 0

        # Test 3: A=False, B=True -> Outcome=False (LBMA drain halted)
        clean_macro.export_ban_active = False
        clean_macro.supply_chain_blockade = True
        _, drain3 = iibx.process_demand(local_demand_daily=5.0, macro=clean_macro)
        assert drain3 == 0


class TestMCDCCOMEXTransfer:
    """MC/DC for D3: current_price > threshold_price and eligible_float > amount."""

    def test_mcdc_d3_independence(self):
        """Independence Pairs for Conditions A and B."""
        comex = exchanges.COMEX_Exchange(initial_float=100.0)
        comex.eligible_float = 50.0

        # Test 1: A=True, B=True -> Outcome=True
        assert comex.move_eligible_to_registered(amount=20.0, current_price=70.0, threshold_price=60.0) is True

        # Test 2: A=False, B=True -> Outcome=False (Condition A independent)
        assert comex.move_eligible_to_registered(amount=20.0, current_price=50.0, threshold_price=60.0) is False

        # Test 3: A=True, B=False -> Outcome=False (Condition B independent)
        assert comex.move_eligible_to_registered(amount=100.0, current_price=70.0, threshold_price=60.0) is False


class TestMCDCSGEArbitrage:
    """MC/DC for D4: east_west_spread > shipping_insurance_cost and vault_float > 0."""

    def test_mcdc_d4_independence(self, clean_macro):
        """Independence Pairs for Conditions A and B."""
        sge = exchanges.SGE_Asian_Arbitrage()

        # Test 1: A=True (spread 1.0 > 0.50), B=True (vault 100 > 0) -> Outcome=True
        sge.east_west_spread = 1.02 # after -0.02 decay = 1.00
        drain1 = sge.process_drain(vault_float=100.0, current_price=40.0, macro=clean_macro)
        assert drain1 > 0

        # Test 2: A=False (spread 0.30 <= 0.50), B=True (vault 100 > 0) -> Outcome=False
        sge.east_west_spread = 0.32 # after decay = 0.30
        drain2 = sge.process_drain(vault_float=100.0, current_price=40.0, macro=clean_macro)
        assert drain2 == 0

        # Test 3: A=True (spread 1.0 > 0.50), B=False (vault 0 <= 0) -> Outcome=False
        sge.east_west_spread = 1.02
        drain3 = sge.process_drain(vault_float=0.0, current_price=40.0, macro=clean_macro)
        assert drain3 == 0


class TestMCDCMacroRecession:
    """MC/DC for D5: dxy_strength > 105 and global_gdp_growth < 0."""

    def test_mcdc_d5_independence(self, clean_macro):
        """Independence Pairs for Conditions A and B."""
        # Test 1: A=True (110 > 105), B=True (-0.02 < 0) -> Outcome=True
        clean_macro.dxy_strength = 110.0
        clean_macro.global_gdp_growth = -0.02
        clean_macro.simulate_day()
        assert clean_macro.base_metal_recession_active is True

        # Test 2: A=False (100 <= 105), B=True (-0.02 < 0) -> Outcome=False
        clean_macro.dxy_strength = 100.0
        clean_macro.global_gdp_growth = -0.02
        clean_macro.simulate_day()
        assert clean_macro.base_metal_recession_active is False

        # Test 3: A=True (110 > 105), B=False (0.02 >= 0) -> Outcome=False
        clean_macro.dxy_strength = 110.0
        clean_macro.global_gdp_growth = 0.02
        clean_macro.simulate_day()
        assert clean_macro.base_metal_recession_active is False


class TestMCDCDualDefaultForceMajeure:
    """MC/DC for D6: comex.defaulted and lbma.defaulted and not comex.force_majeure_active."""

    def test_mcdc_d6_independence(self, standard_engine):
        """Independence Pairs for Conditions A, B, and C."""
        standard_engine.gov_uk.bailout_probability = 1.0

        # Test 1: A=True, B=True, C=False -> Outcome=True (FM activated)
        standard_engine.comex.defaulted = True
        standard_engine.lbma.defaulted = True
        standard_engine.lbma.vault_float = 0.0 # Required for UK bailout to trigger
        standard_engine.comex.force_majeure_active = False
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=10.0)
        assert standard_engine.comex.force_majeure_active is True

        # Test 2: A=False, B=True, C=False -> Outcome=False
        standard_engine.comex.defaulted = False
        standard_engine.comex.vault_float = 500.0 # Prevents comex defaulting
        standard_engine.lbma.defaulted = True
        standard_engine.lbma.vault_float = 0.0
        standard_engine.comex.force_majeure_active = False
        standard_engine.stats["force_majeure_count"] = 0
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=100.0)
        assert standard_engine.stats["force_majeure_count"] == 0

        # Test 3: A=True, B=False, C=False -> Outcome=False
        standard_engine.comex.defaulted = True
        standard_engine.comex.vault_float = 0.0
        standard_engine.lbma.defaulted = False
        standard_engine.lbma.vault_float = 500.0 # Prevents lbma defaulting
        standard_engine.comex.force_majeure_active = False
        standard_engine.stats["force_majeure_count"] = 0
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=100.0)
        assert standard_engine.stats["force_majeure_count"] == 0

        # Test 4: A=True, B=True, C=True -> Outcome=False (Already in FM, no re-trigger)
        standard_engine.comex.defaulted = True
        standard_engine.comex.vault_float = 0.0
        standard_engine.lbma.defaulted = True
        standard_engine.lbma.vault_float = 0.0
        standard_engine.comex.force_majeure_active = True
        standard_engine.stats["force_majeure_count"] = 0
        standard_engine._update_exchanges_and_stats(day=1, lbma_demand=10.0, comex_demand=10.0, base_supply=100.0)
        assert standard_engine.stats["force_majeure_count"] == 0
