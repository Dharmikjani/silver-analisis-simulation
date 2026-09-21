import os
import sys
import copy
import pytest
import random
import numpy as np

# Ensure src/ is on Python search path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config
import exchanges
import logger
import macro
import stakeholders
from engine import SimulationEngine

@pytest.fixture(autouse=True)
def reset_random_seed():
    """Ensure determinism across test executions."""
    random.seed(42)
    np.random.seed(42)

@pytest.fixture
def clean_config():
    """Returns a deep-copied SimConfig with preset prices."""
    cfg = copy.deepcopy(config.FUTURE_2026_STATE)
    cfg.start_silver_price = 30.0
    cfg.start_gold_price = 2500.0
    return cfg

@pytest.fixture
def clean_macro(clean_config):
    """Returns a fresh MacroEnvironment instance."""
    return macro.MacroEnvironment(
        config=clean_config,
        gold_price=2500.0,
        fed_rate=5.0,
        dxy=100.0,
        copper=4.0,
        start_year=2026
    )

@pytest.fixture
def standard_engine(clean_config):
    """Provides a pre-configured SimulationEngine in backtest mode (offline, no jitter)."""
    return SimulationEngine(
        mode="backtest",
        config=clean_config,
        years=1,
        seed=42,
        jitter=0.0
    )
