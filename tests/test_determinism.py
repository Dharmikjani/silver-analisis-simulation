import pytest
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))

from engine import run_simulation_core
from config import FUTURE_2026_STATE
import dataclasses

def test_determinism_identical_seeds():
    config1 = dataclasses.replace(FUTURE_2026_STATE, start_silver_price=30.0)
    config2 = dataclasses.replace(FUTURE_2026_STATE, start_silver_price=30.0)
    
    # Run first time with seed 42
    path1, stats1 = run_simulation_core(config=config1, seed=42, mode="historical", return_full=True)
    
    # Run second time with same seed
    path2, stats2 = run_simulation_core(config=config2, seed=42, mode="historical", return_full=True)
    
    # Assert exact match
    assert stats1["squeeze_count"] == stats2["squeeze_count"]
    assert path1[-1]["avg_physical"] == path2[-1]["avg_physical"]
    assert stats1["retail_melt_count"] == stats2["retail_melt_count"]
