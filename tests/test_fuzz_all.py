import sys
import os
import math
import copy
import pytest
from hypothesis import given, strategies as st

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import stakeholders
from config import FUTURE_2026_STATE

class MockMacro:
    def __init__(self, inflation=1.0):
        self.config = copy.deepcopy(FUTURE_2026_STATE)
        self.config.start_silver_price = 65.0
        self.m2_inflation_index = inflation
        self.brics_currency_gold_backed = False
        self.energy_crisis_active = False
        self.geopolitical_tension_index = 50.0
        self.india_duty_active = False
        self.oil_price = 75.0
        self.tech_deflation_index = 1.0
        self.brics_vault_drain_daily = 0.0
        self.brics_announced = False
        
    def __getattr__(self, name):
        if 'active' in name or 'burst' in name or 'capitulation' in name or 'announced' in name:
            return False
        return 1.0

def check_valid_float(val):
    if math.isnan(val) or math.isinf(val):
        return False
    return True

# Fuzz standard stakeholders
@given(
    price=st.floats(min_value=-1e6, max_value=1e6),
    inflation=st.floats(min_value=-1e6, max_value=1e6),
    volume=st.floats(min_value=-1e6, max_value=1e6)
)
def test_all_base_stakeholders(price, inflation, volume):
    macro = MockMacro(inflation=inflation)
    base_classes = [
        stakeholders.PrimaryMiners, stakeholders.ByproductMiners,
        stakeholders.ScrapRefiners, stakeholders.EWasteRecyclers,
        stakeholders.SolarPV, stakeholders.DefenseAerospace,
        stakeholders.EV_Auto, stakeholders.Tech_AI,
        stakeholders.JewelrySilverware, stakeholders.OtherIndustrial,
        stakeholders.RetailInvestors, stakeholders.Gov_China,
        stakeholders.Gov_CentralBanks, stakeholders.CentralBankReserve,
        stakeholders.DeepPrivateHoarders, stakeholders.BlackMarketSmugglers
    ]
    
    for cls in base_classes:
        obj = cls(name=cls.__name__, annual_base_volume=volume)
        try:
            res = obj.process_day(price=price, macro=macro)
            assert isinstance(res, (int, float)), f"{cls.__name__} returned non-float!"
        except OverflowError:
            pass

# Fuzz vault stakeholders
@given(
    price=st.floats(min_value=-1e6, max_value=1e6),
    inflation=st.floats(min_value=-1e6, max_value=1e6),
    vault=st.floats(min_value=-1e6, max_value=1e6)
)
def test_vault_stakeholders(price, inflation, vault):
    macro = MockMacro(inflation=inflation)
    classes = [
        stakeholders.Billionaire_Family_Offices,
        stakeholders.Global_ETF_Holdings
    ]
    
    for cls in classes:
        obj = cls(vault_float=vault)
        try:
            if cls == stakeholders.Billionaire_Family_Offices:
                obj.process_day(price, macro, current_gsr=80.0)
            elif cls == stakeholders.Global_ETF_Holdings:
                obj.process_day(price, price_momentum=1.0)
        except OverflowError:
            pass

# Fuzz standalone specific stakeholders
@given(
    price=st.floats(min_value=-1e6, max_value=1e6),
    val=st.floats(min_value=-1e6, max_value=1e6),
    val2=st.floats(min_value=-1e6, max_value=1e6)
)
def test_misc_stakeholders(price, val, val2):
    macro = MockMacro()
    # BullionBankShorts
    bbs = stakeholders.BullionBankShorts()
    try: 
        bbs.check_forced_covering(price, macro, False, current_sigma=val)
    except OverflowError: pass
    
    sge = stakeholders.SGE_Asian_Arbitrage()
    try: sge.process_drain(val, price, macro)
    except OverflowError: pass
    
    ind = stakeholders.Gov_India()
    try: ind.process_jewelry_demand(price, val, macro)
    except OverflowError: pass

    ref = stakeholders.SmelterRefineryBottleneck()
    try: ref.process_supply(val, price, macro)
    except OverflowError: pass
    
    phf = stakeholders.PredatoryHedgeFund()
    try: phf.process_attack(comex_float=val, physical_price=price, macro=macro)
    except OverflowError: pass
    
    omm = stakeholders.OptionsMarketMakers()
    try: omm.process_delta_hedge(retail_demand=val, price_momentum=val2)
    except OverflowError: pass
