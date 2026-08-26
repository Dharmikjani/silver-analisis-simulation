import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from engine import SimulationEngine
from config import SimConfig

def test_engine_supply_edges(mocker):
    config = SimConfig(
        start_year=2026, start_silver_price=30.0, start_gold_price=2500.0, comex_float=100.0, fed_rate=5.0,
        primary_mine=800, byproduct_mine=200, scrap_refiners=150, ewaste=50,
        solar_pv=150, ev_auto=100, defense=50, ai_tech=50, jewelry=200, other_demand=100, retail=100,
        thresholds=mocker.MagicMock(), capacities=mocker.MagicMock(), vaults=mocker.MagicMock()
    )
    engine = SimulationEngine(config, jitter=0.0)
    
    # Hit line 147: total_hoard <= 0 and price > 250*m2
    for agent in engine.supply_hoarders.sub_agents:
        agent['share'] = 0.0
    engine.physical_price = 300.0
    engine.macro.m2_inflation_index = 1.0
    
    # Hit line 161: scrap_fatigue_days > 3 * TRADING_DAYS
    engine.supply_scrap.scrap_fatigue_days = 1000
    
    engine._process_supply()
    
    assert engine.stats["hoard_depletion_count"] > 0
    assert engine.stats["scrap_fatigue_count"] > 0

def test_engine_demand_edges(mocker):
    config = SimConfig(
        start_year=2026, start_silver_price=30.0, start_gold_price=2500.0, comex_float=100.0, fed_rate=5.0,
        primary_mine=800, byproduct_mine=200, scrap_refiners=150, ewaste=50,
        solar_pv=150, ev_auto=100, defense=50, ai_tech=50, jewelry=200, other_demand=100, retail=100,
        thresholds=mocker.MagicMock(), capacities=mocker.MagicMock(), vaults=mocker.MagicMock()
    )
    engine = SimulationEngine(config, jitter=0.0)
    
    # Hit line 260: etf_flow < 0
    mocker.patch.object(engine.etf_holdings, 'process_day', return_value=-10.0)
    
    # Hit line 267-268: margin_hike_active and force_majeure_active
    engine.comex.margin_hike_active = True
    engine.comex.force_majeure_active = True
    
    engine.macro.base_metal_recession_active = False # prevent missing branches in macro check
    
    engine._process_demand(total_supply=100.0)
    
    assert engine.dynamic_supply_add == 10.0

def test_engine_price_discovery_edges(mocker):
    config = SimConfig(
        start_year=2026, start_silver_price=30.0, start_gold_price=2500.0, comex_float=100.0, fed_rate=5.0,
        primary_mine=800, byproduct_mine=200, scrap_refiners=150, ewaste=50,
        solar_pv=150, ev_auto=100, defense=50, ai_tech=50, jewelry=200, other_demand=100, retail=100,
        thresholds=mocker.MagicMock(), capacities=mocker.MagicMock(), vaults=mocker.MagicMock()
    )
    engine = SimulationEngine(config, jitter=0.0)
    
    # Hit line 363 (paper limit down)
    # Hit line 428: margin hike active during update_price
    engine.exchange_margins.margin_hike_active = True
    engine.dynamic_supply_add = 0.0
    engine.comex_demand_add = 0.0
    
    # Hit line 389: gbm_mult > 1.10
    mocker.patch('engine.random.gauss', return_value=10.0) # huge positive drift
    engine._update_price(lbma_demand=100, comex_demand=200, base_supply=100)
    
    # Hit line 456: total demand <= 0
    engine._update_exchanges_and_stats(day=1, lbma_demand=-100, comex_demand=50, base_supply=10)

    # Hit 500: squeeze days < 30
    engine.comex.vault_float = 0.0
    engine.squeeze_triggered = True
    engine.stats["squeeze_days"] = 10
    mocker.patch('engine.random.random', return_value=0.0)
    engine._update_exchanges_and_stats(day=1, lbma_demand=100, comex_demand=100, base_supply=10)

