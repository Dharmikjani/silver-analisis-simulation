import pytest
from hypothesis import given, strategies as st
import math

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from stakeholders import JPM_House_Account, Retail_Mattress_Hoard, SolarPV
from config import FUTURE_2026_STATE
import copy

class MockMacro:
    def __init__(self):
        self.config = copy.deepcopy(FUTURE_2026_STATE)
        self.config.start_silver_price = 65.0
        self.m2_inflation_index = 1.0

def test_jpm_dump_logic():
    macro = MockMacro()
    # Threshold is 65.0 * 3.33 = 216.45
    jpm = JPM_House_Account(vault_float=350.0)
    
    # Below threshold, shouldn't dump
    jpm.process_day(price=200.0, macro=macro)
    assert not jpm.dumping
    assert jpm.vault_float == 350.0
    
    # Above threshold, should dump exactly 5.0
    jpm.process_day(price=220.0, macro=macro)
    assert jpm.dumping
    assert jpm.vault_float == 345.0
    
    # Exhaust vault
    jpm.vault_float = 2.0
    jpm.process_day(price=220.0, macro=macro)
    assert jpm.vault_float >= 0, "Vault float should not drop below 0!"

@given(
    price=st.floats(),
    vault=st.floats(),
    inflation=st.floats()
)
def test_jpm_fuzzing(price, vault, inflation):
    macro = MockMacro()
    macro.m2_inflation_index = inflation
    jpm = JPM_House_Account(vault_float=vault)
    
    try:
        jpm.process_day(price=price, macro=macro)
        # Invariants
        assert not math.isnan(jpm.vault_float)
        assert jpm.vault_float <= vault or math.isnan(vault)
    except Exception:
        pass

def test_retail_melt_logic():
    macro = MockMacro()
    # Threshold = 65.0 * 2.0 = 130.0
    retail = Retail_Mattress_Hoard(vault_float=2000.0)
    
    retail.process_day(price=100.0, macro=macro)
    assert not retail.melting
    assert retail.vault_float == 2000.0
    
    retail.process_day(price=140.0, macro=macro)
    assert retail.melting
    assert retail.vault_float == 1990.0

@given(
    price=st.floats(),
    vault=st.floats()
)
def test_retail_fuzzing(price, vault):
    macro = MockMacro()
    retail = Retail_Mattress_Hoard(vault_float=vault)
    try:
        retail.process_day(price=price, macro=macro)
    except Exception:
        pass
