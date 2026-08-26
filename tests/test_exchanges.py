import pytest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from exchanges import COMEX_Exchange, LBMA_Exchange, India_IIBX_Vault, SGE_Asian_Arbitrage
from logger import setup_logger

# Dummy Macro class to satisfy dependencies
class DummyMacro:
    def __init__(self):
        self.export_ban_active = False
        self.supply_chain_blockade = False
        self.brics_announced = False

@pytest.fixture(autouse=True)
def isolate_logger(tmp_path):
    """Ensure tests don't write to the real outputs folder."""
    setup_logger(output_dir=str(tmp_path))

def test_comex_move_eligible_to_registered_boundaries():
    """Boundary value analysis on the price threshold."""
    comex = COMEX_Exchange(initial_float=100.0)
    comex.eligible_float = 50.0
    
    # Test boundary 1: Exactly at threshold (should fail)
    assert not comex.move_eligible_to_registered(10.0, current_price=30.0, threshold_price=30.0)
    assert comex.vault_float == 100.0
    
    # Test boundary 2: Slightly above threshold (should pass)
    assert comex.move_eligible_to_registered(10.0, current_price=30.01, threshold_price=30.0)
    assert comex.vault_float == 110.0
    assert comex.eligible_float == 40.0
    
    # Test boundary 3: Try to move more than we have (should fail)
    assert not comex.move_eligible_to_registered(50.0, current_price=40.0, threshold_price=30.0)

def test_lbma_bank_run_mocked(mocker):
    """Mock the random number generator to force a bank run deterministically."""
    lbma = LBMA_Exchange(vault_start=10.0, unallocated_start=50.0)
    
    # Mock random to return 0.0 (always triggers the < 0.02 condition)
    mocker.patch('exchanges.random.random', return_value=0.0)
    
    # Trigger the run (price > 120.0)
    drain = lbma.check_bank_run(price=120.01, geo_tension=50)
    assert lbma.bank_run_active is True
    assert drain == 5.0
    assert lbma.vault_float == 5.0
    assert lbma.unallocated_claims == 45.0
    
    # Drain again, vault hits 0
    drain = lbma.check_bank_run(price=120.01, geo_tension=50)
    assert drain == 5.0
    assert lbma.vault_float == 0.0
    
    # Drain again, vault is 0, shouldn't go negative
    drain = lbma.check_bank_run(price=120.01, geo_tension=50)
    assert drain == 0.0
    assert lbma.vault_float == 0.0
    assert lbma.unallocated_claims == 40.0 # Unallocated still drained even if vault empty based on current code logic

def test_india_iibx_is_empty_flag():
    """Verify is_empty flag flips correctly at the exact boundary of 10.0"""
    vault = India_IIBX_Vault(inventory_start=10.0)
    macro = DummyMacro()
    
    # Exactly 10.0 -> is_empty should be False
    vault.process_demand(0.0, macro)
    assert vault.is_empty is False
    
    # Drop slightly below 10.0
    vault.current_inventory = 9.99
    vault.process_demand(0.0, macro)
    assert vault.is_empty is True

def test_sge_arbitrage_spread_caps_and_reversion():
    """Test hard caps and mean reversion of the east/west spread."""
    sge = SGE_Asian_Arbitrage()
    macro = DummyMacro()
    
    # Force the spread very high
    sge.east_west_spread = 10.0
    
    # process_drain should cap it at 5.0, then subtract 0.02 for mean reversion (4.98)
    drain = sge.process_drain(vault_float=100.0, current_price=30.0, macro=macro)
    assert sge.east_west_spread == 4.98
    
    # Test lower bound (should not go below 0)
    sge.east_west_spread = 0.01
    sge.process_drain(vault_float=100.0, current_price=30.0, macro=macro)
    assert sge.east_west_spread == 0.0
