import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from engine import SimulationEngine
from stakeholders import Stakeholder, PrimaryMiners, UnallocatedAccountHolders
import macro
from config import SimConfig

class MockConfig(SimConfig):
    def __init__(self):
        super().__init__(
            start_year=2026, start_silver_price=30.0, start_gold_price=2500.0, comex_float=100.0, fed_rate=5.0,
            primary_mine=800, byproduct_mine=200, scrap_refiners=150, ewaste=50,
            solar_pv=150, ev_auto=100, defense=50, ai_tech=50, jewelry=200, other_demand=100, retail=100,
            thresholds=None, capacities=None, vaults=None
        )

def test_stakeholder_base():
    """Hit the base Stakeholder process_day."""
    s = Stakeholder("test", 100)
    s.process_day(30.0, None)

def test_primary_miners_expansion():
    """Hit lines 39-40 in stakeholders.py"""
    m = PrimaryMiners("Miners", 100)
    m.capex_expansion_cycle = 0.6
    
    class DummyMacro:
        oil_price = 75.0
        m2_inflation_index = 1.0
        tech_deflation_index = 1.0
        mining_strike_active = False
        retail_capitulation = False
        base_metal_recession_active = False
        defense_stockpile_active = False
        refinery_energy_crisis = False
        brics_announced = False
        geopolitical_tension_index = 50.0
    
    m.process_day(100.0, DummyMacro())
    assert m.capex_expansion_cycle < 0.6

def test_unallocated_bank_run():
    """Hit lines 854-870 in stakeholders.py"""
    u = UnallocatedAccountHolders()
    u.vault_confidence = 25.0
    
    # Hit vault_float < 100 (decreases confidence)
    u.check_bank_run(50.0)
    assert u.vault_confidence == 24.0
    
    # Drop below 20.0 to trigger bank run
    u.vault_confidence = 19.0
    u.check_bank_run(50.0)
    assert u.bank_run_active is True
    assert u._bank_run_logged is True
    
    # Hit again to trigger the already logged path
    u.check_bank_run(50.0)
    
    # Recover vault
    u.vault_confidence = 49.0
    u.check_bank_run(250.0)
    assert u.vault_confidence == 49.5
    assert u.bank_run_active is True # Not recovered fully yet (>50)
    
    u.check_bank_run(250.0)
    u.check_bank_run(250.0)
    assert u.bank_run_active is False
    assert u._bank_run_logged is False
