import pytest
import sys
import os
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from macro import LiveDataOracle, MacroEnvironment
from config import SimConfig

def test_livedataoracle_exception(mocker, capsys):
    """Test fallback when oracle hits an exception."""
    # Mock yfinance to fail during init
    mocker.patch('macro.yf.Ticker', side_effect=Exception("Timeout"))
    
    oracle = LiveDataOracle()
    assert oracle.silver_price == 30.0
    assert oracle.gold_price == 2500.0
    
    captured = capsys.readouterr()
    assert "[LiveDataOracle] API Error: Timeout. Using defaults." in captured.out

def test_macro_numpy_fallback(mocker):
    """Test the fallback random paths when numpy is missing."""
    macro = MacroEnvironment()
    
    # Mock numpy import to fail
    original_import = __builtins__['__import__']
    def mock_import(name, *args, **kwargs):
        if name == 'numpy':
            raise ImportError("No module named 'numpy'")
        return original_import(name, *args, **kwargs)
        
    mocker.patch('builtins.__import__', side_effect=mock_import)
    
    # Run a day, it should use the random.gauss fallback
    macro.simulate_day()
    assert macro.current_day == 1

def test_macro_brics_announcement_and_logic(mocker):
    """Test the BRICS announcement random trigger and downstream effects."""
    config = SimConfig(
        start_year=2026, start_silver_price=30.0, start_gold_price=2500.0, comex_float=100.0, fed_rate=5.0,
        primary_mine=800, byproduct_mine=200, scrap_refiners=150, ewaste=50,
        solar_pv=150, ev_auto=100, defense=50, ai_tech=50, jewelry=200, other_demand=100, retail=100,
        thresholds=None, capacities=None, vaults=None
    )
    config.thresholds = mocker.MagicMock()
    config.thresholds.prob_brics_announce = 0.10
    config.thresholds.prob_cbdc_launch = 0.0
    config.thresholds.prob_mining_strike = 0.0
    config.thresholds.prob_retail_capitulation = 0.0
    config.thresholds.prob_energy_crisis = 0.0
    config.thresholds.prob_predatory_squeeze = 0.0
    
    macro = MacroEnvironment(config=config)
    
    # Mock random to force BRICS announcement (needs < prob / TRADING_DAYS)
    # prob is ~0.10, so random < 0.0003
    mocker.patch('macro.random.random', return_value=0.0)
    # Mock uniform to return 1.10
    mocker.patch('macro.random.uniform', return_value=1.10)
    
    macro.simulate_day()
    
    assert macro.brics_announced is True
    assert macro.brics_vault_drain_daily == 0
    # Gold price should be 2500 * drift * 1.10, let's just assert it went up significantly
    assert macro.gold_price > 2600.0

    # Also test line 175 logic: geo_tension <= 75 and brics_announced
    macro.geopolitical_tension_index = 50.0
    macro.simulate_day()
    assert macro.brics_vault_drain_daily == 0
