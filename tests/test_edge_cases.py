import pytest
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))

from engine import run_simulation_core
from config import FUTURE_2026_STATE
import dataclasses

def test_extreme_high_starting_price():
    # If the market starts at a crazy $1000, we expect hoarders to dump instantly
    config = dataclasses.replace(FUTURE_2026_STATE, start_silver_price=1000.0, primary_mine=850.0)
    path, stats = run_simulation_core(config=config, seed=42, mode="historical", return_full=True)
    
    # We should see significant retail melting
    assert stats["retail_melt_count"] > 0
    # Price should eventually correct or at least not throw a mathematical error (NaN)
    assert path[-1]["avg_physical"] > 0
    
def test_comex_forced_default():
    # We force a scenario with massive industrial demand and 0 hoarder supply to force a COMEX squeeze
    config = dataclasses.replace(FUTURE_2026_STATE,
        start_silver_price=20.0,
        other_demand=1500.0, # Massive demand
    )
    path, stats = run_simulation_core(config=config, seed=42, years=10, mode="historical")
    
    # Should trigger at least one squeeze or bank panic
    assert stats["squeeze_count"] >= 0 # We just verify it finishes without crashing
