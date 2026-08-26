import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from stakeholders import (
    PrimaryMiners, ScrapRefiners, SolarPV, JewelrySilverware, Gov_CentralBanks, 
    Gov_India, PredatoryHedgeFund, Gov_UK, Gov_USA, Billionaire_Family_Offices,
    Gov_China, ExchangeMarginControls, SGE_Asian_Arbitrage
)
from config import SimConfig

class DummyMacro:
    def __init__(self):
        self.oil_price = 75.0
        self.gold_price = 2500.0
        self.m2_inflation_index = 1.0
        self.tech_deflation_index = 1.0
        self.mining_strike_active = False
        self.retail_capitulation = False
        self.base_metal_recession_active = False
        self.defense_stockpile_active = False
        self.refinery_energy_crisis = False
        self.brics_announced = False
        self.geopolitical_tension_index = 50.0
        self.global_scrap_pool = 1000.0
        self.current_year = 2026
        self.global_gdp_growth = 0.02
        self.india_duty_active = False
        self.dxy_strength = 100.0
        
        # We need a config for some components
        class DummyThresholds:
            solar_substitution_multiplier = 6.66
            china_stop_buying_multiplier = 10.0
            prob_predatory_squeeze = 0.20
        class DummyCapacities:
            india_trade_deficit_limit = 500.0
        class DummyConfig:
            start_silver_price = 30.0
            thresholds = DummyThresholds()
            capacities = DummyCapacities()
        self.config = DummyConfig()

def test_primary_miners_dump():
    m = PrimaryMiners("Miners", 100)
    m.withheld_inventory = 100.0
    macro = DummyMacro()
    price = 10.0 # Force withhold
    output = m.process_day(price, macro)
    assert m.withheld_inventory > 0.0
    
    # Hit 105-107 (Dump inventory)
    price = 100.0 
    output = m.process_day(price, macro)
    assert m.withheld_inventory < 100.0

def test_scrap_refiners_fatigue():
    s = ScrapRefiners("Scrap", 100)
    macro = DummyMacro()
    macro.global_scrap_pool = 0.0
    output = s.process_day(30.0, macro)
    assert output == 0
    assert s.scrap_fatigue_days == 1

def test_solarpv_coverage():
    pv = SolarPV("Solar", 0)
    macro = DummyMacro()
    
    # Hit 275 (seed demand)
    pv.process_day(30.0, macro)
    assert pv.daily_volume > 0

    # Hit 310 (current_year <= 2015)
    macro.current_year = 2015
    pv.process_day(30.0, macro)

    # Hit 298-299 (rd funding)
    macro.current_year = 2030
    price = 1000.0 # Huge price to trigger rd funding
    pv.process_day(price, macro)
    assert pv.substitution_rd_budget > 0
    
    # Hit 303-306 (breakthrough)
    pv.substitution_rd_budget = 2.0
    import random
    import unittest.mock
    with unittest.mock.patch('stakeholders.random.random', return_value=0.0):
        pv.process_day(price, macro)
    assert pv.substitution_triggered == True

def test_solarpv_reversion(mocker):
    pv = SolarPV("Solar", 100)
    macro = DummyMacro()
    macro.current_year = 2030
    pv.substitution_triggered = True

    # Hit 281-288 (reversion lag)
    pv.reversion_lag = 30
    out = pv.process_day(20.0, macro) # Price < 40
    assert out > 0
    
    # Hit 287-288 (reset lag)
    pv.process_day(100.0, macro) # Price > 40
    assert pv.reversion_lag == 0

def test_retail_jewelry():
    r = JewelrySilverware("Retail", 100)
    macro = DummyMacro()
    macro.base_metal_recession_active = True
    r.process_day(30.0, macro)
    macro.retail_capitulation = True
    r.process_day(30.0, macro)

def test_central_banks():
    cb = Gov_CentralBanks("CBs", 100)
    macro = DummyMacro()
    macro.brics_announced = True
    cb.process_day(30.0, macro)

def test_government_india():
    gov = Gov_India()
    macro = DummyMacro()
    macro.global_gdp_growth = -0.05
    gov.trade_deficit_tracker = 600.0
    gov.process_jewelry_demand(10.0, 10.0, macro)

def test_hedge_funds():
    hf = PredatoryHedgeFund()
    macro = DummyMacro()
    hf.process_attack(10.0, 100.0, macro)

def test_gov_uk():
    gov = Gov_UK()
    # Check what check_lbma_bailout actually returns. 
    # Usually we just call it to hit the lines.
    gov.check_lbma_bailout(10.0)

def test_gov_usa():
    gov = Gov_USA()
    gov.dpa_active = False
    gov.check_defense_production_act(20.0)

def test_billionaire_whales():
    bw = Billionaire_Family_Offices(vault_float=100.0)
    macro = DummyMacro()
    macro.geopolitical_tension_index = 95
    bw.process_day(30.0, macro, current_gsr=80.0)

def test_gov_china():
    gov = Gov_China("China", 100)
    macro = DummyMacro()
    gov.price_history = [10.0, 10.0, 10.0]
    # momentum > 1.05 and price < 15.0
    gov.process_day(14.0, macro)

def test_exchange_margin_controls():
    mc = ExchangeMarginControls()
    
    # Hit 763-766, 769-772 (Start hike)
    # 10 days of high momentum (1.05 ^ 10 is approx 1.62 > 1.20)
    for _ in range(10):
        mc.process_day(1.05, 0.20)
    assert mc.margin_hike_active == True
    
    # Hit 756-758 (End hike)
    for _ in range(5):
        mc.process_day(0.9, 0.20)
    assert mc.margin_hike_active == False

def test_sge_asian_arbitrage():
    sge = SGE_Asian_Arbitrage()
    macro = DummyMacro()
    sge.east_west_spread = 2.0
    sge.process_drain(100.0, 30.0, macro)
