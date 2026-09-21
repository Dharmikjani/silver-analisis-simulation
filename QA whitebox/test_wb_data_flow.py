"""
ISO/IEC/IEEE 29119-4 Clause 7.7: Data Flow Testing Suite
Objective: Verify variable definitions, computation-uses (c-use), predicate-uses (p-use),
and validate absence of data flow anomalies (uninitialized reads, dead definitions).
"""
import math
import pytest

import config
import exchanges
import macro
from engine import SimulationEngine

class TestDataFlowPhysicalPrice:
    """Data flow DU-chain verification for self.physical_price."""

    def test_df_physical_price_lifecycle(self, standard_engine):
        """Verify definition -> c-use -> p-use -> re-definition chain."""
        # 1. Definition (d) at initialization
        initial_price = standard_engine.physical_price
        assert initial_price > 0 and not math.isnan(initial_price)

        # 2. Computation-Use (c-use) in supply & demand
        supply = standard_engine._process_supply()
        assert supply > 0

        # 3. Predicate-Use (p-use) in ewaste and AISC checks
        # Force price high to test p-use in ewaste threshold
        standard_engine.physical_price = 150.0
        standard_engine._process_demand(total_supply=supply)

        # 4. Re-definition (d) in _update_price
        standard_engine._update_price(lbma_demand=50.0, comex_demand=50.0, base_supply=50.0)
        new_price = standard_engine.physical_price

        # Check absence of numerical anomalies
        assert not math.isnan(new_price)
        assert not math.isinf(new_price)
        assert new_price > 0.0

    def test_df_physical_price_lbma_default_multiplier(self, standard_engine):
        """Verify LBMA default redefinition DU-chain (engine.py:521)."""
        standard_engine.lbma.vault_float = 1.0
        standard_engine.lbma.defaulted = False
        old_price = standard_engine.physical_price

        # Force LBMA deficit > vault -> triggers default & 2x price jump
        standard_engine._update_exchanges_and_stats(
            day=1, lbma_demand=50.0, comex_demand=0.0, base_supply=0.0
        )
        assert standard_engine.lbma.defaulted is True
        assert standard_engine.physical_price == pytest.approx(old_price * 2.0, rel=1e-3)


class TestDataFlowPaperPrice:
    """Data flow DU-chain verification for self.paper_price."""

    def test_df_paper_price_lifecycle(self, standard_engine):
        """Verify paper_price definition -> retail demand c-use -> gbm redefinition."""
        # 1. Definition
        assert standard_engine.paper_price > 0

        # 2. Computation-Use in retail demand
        retail_flow = standard_engine.demand_retail.process_day(
            standard_engine.paper_price, standard_engine.macro
        )
        assert retail_flow >= 0

        # 3. Re-definition in _update_price
        standard_engine._update_price(lbma_demand=40.0, comex_demand=40.0, base_supply=40.0)
        assert not math.isnan(standard_engine.paper_price)
        assert standard_engine.paper_price >= 0.10


class TestDataFlowVaultInventories:
    """Data flow DU-chain verification for COMEX & LBMA vault floats."""

    def test_df_vault_floats_clearing_and_bounds(self, standard_engine):
        """Verify definition -> deficit c-use -> inventory mutation -> zero floor clamping."""
        # 1. Definition in exchange initializers
        assert standard_engine.comex.vault_float > 0
        assert standard_engine.lbma.vault_float > 0

        # 2. Mutate with deficit larger than float (depletion)
        initial_comex = standard_engine.comex.vault_float
        standard_engine._update_exchanges_and_stats(
            day=1, lbma_demand=10.0, comex_demand=initial_comex + 50.0, base_supply=0.0
        )
        # Vault must be clamped at exactly 0, not negative
        assert standard_engine.comex.vault_float == 0.0
        assert standard_engine.comex.defaulted is True

    def test_df_vault_efp_conservation(self, standard_engine):
        """Verify mass conservation across trans-Atlantic EFP transfer."""
        standard_engine.lbma.vault_float = 40.0 # Under 50, requests transfer
        standard_engine.comex.vault_float = 100.0
        standard_engine.lbma.defaulted = False
        standard_engine.comex.defaulted = False

        total_before = standard_engine.lbma.vault_float + standard_engine.comex.vault_float

        standard_engine._update_exchanges_and_stats(
            day=1, lbma_demand=0.0, comex_demand=0.0, base_supply=0.0
        )

        total_after = standard_engine.lbma.vault_float + standard_engine.comex.vault_float
        assert total_after == pytest.approx(total_before, rel=1e-5)


class TestDataFlowSGESpread:
    """Data flow DU-chain verification for SGE Asian Arbitrage spread."""

    def test_df_sge_spread_bounds_and_reversion(self, clean_macro):
        """Verify definition -> boost -> cap -> decay -> drain calculation."""
        sge = exchanges.SGE_Asian_Arbitrage()
        assert sge.east_west_spread == 0.0

        # Feed macro triggers to push spread to upper bound
        clean_macro.brics_announced = True
        for _ in range(100):
            sge.process_drain(vault_float=100.0, current_price=100.0, macro=clean_macro)

        # Spread must be strictly capped at 5.0
        assert sge.east_west_spread <= 5.0

        # Inactive macro -> spread must decay toward 0.0
        clean_macro.brics_announced = False
        for _ in range(300):
            sge.process_drain(vault_float=100.0, current_price=30.0, macro=clean_macro)

        assert sge.east_west_spread >= 0.0
        assert sge.east_west_spread < 1.0
