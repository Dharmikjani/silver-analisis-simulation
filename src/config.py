import random
from dataclasses import dataclass, fields

TRADING_DAYS = 252
TOTAL_YEARS = 10
TOTAL_DAYS = TRADING_DAYS * TOTAL_YEARS

# Global Scenario Overrides
SCENARIOS_OVERRIDE = {
    "no_strikes": False,
    "no_whales": False,
    "no_ai_burst": False,
    "no_solar_sub": False,
    "no_energy_crisis": False,
    "no_retail_cap": False,
}

@dataclass
class Thresholds:
    retail_melt_multiplier: float
    jpm_dump_multiplier: float
    solar_substitution_multiplier: float
    hoarder_dump_multiplier: float
    china_stop_buying_multiplier: float
    prob_brics_announce: float
    prob_cbdc_launch: float
    prob_mining_strike: float
    prob_retail_capitulation: float
    prob_energy_crisis: float
    prob_predatory_squeeze: float

@dataclass
class Capacities:
    smelter_max_annual: float
    ai_tech_max_annual: float
    india_trade_deficit_limit: float

@dataclass
class VaultStarts:
    lbma_vault: float
    lbma_unallocated: float
    comex_eligible: float
    india_capacity: float
    india_inventory: float
    jpm_house: float
    billionaire_vault: float
    retail_mattress: float
    etf_holdings: float
    deep_hoarders: float

@dataclass
class SimConfig:
    start_year: int
    start_silver_price: float
    start_gold_price: float
    comex_float: float
    fed_rate: float
    
    # Base Supply
    primary_mine: float
    byproduct_mine: float
    scrap_refiners: float
    ewaste: float
    
    # Base Demand
    solar_pv: float
    ev_auto: float
    defense: float
    ai_tech: float
    jewelry: float
    other_demand: float
    retail: float
    
    thresholds: Thresholds
    capacities: Capacities
    vaults: VaultStarts

    def apply_jitter(self, jitter_pct: float = 0.10):
        """Apply random ±jitter_pct perturbation to all numeric fields."""
        skip_fields = {'start_year'}
        def jitter_obj(obj):
            for f in fields(obj):
                if f.name in skip_fields:
                    continue
                val = getattr(obj, f.name)
                if isinstance(val, (int, float)) and val != 0.0:
                    perturbed = val * random.uniform(1.0 - jitter_pct, 1.0 + jitter_pct)
                    setattr(obj, f.name, perturbed)
                elif hasattr(val, '__dataclass_fields__'):
                    jitter_obj(val)
        
        jitter_obj(self)
        return self

    @classmethod
    def from_yaml(cls, path: str):
        try:
            import yaml
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                
            if 'thresholds' in data and isinstance(data['thresholds'], dict):
                data['thresholds'] = Thresholds(**data['thresholds'])
            if 'capacities' in data and isinstance(data['capacities'], dict):
                data['capacities'] = Capacities(**data['capacities'])
            if 'vaults' in data and isinstance(data['vaults'], dict):
                data['vaults'] = VaultStarts(**data['vaults'])
                
            return cls(**data)
        except ImportError:
            print("[Config] PyYAML not installed. Install with: pip install pyyaml")
            raise
        except Exception as e:
            print(f"[Config] Error loading YAML config: {e}")
            raise

# Shared defaults for the hardcoded magic numbers we pulled out
DEFAULT_THRESHOLDS = Thresholds(
    retail_melt_multiplier=2.0,       # $60 / $30
    jpm_dump_multiplier=3.33,         # $100 / $30
    solar_substitution_multiplier=6.66, # $200 / $30
    hoarder_dump_multiplier=5.0,      # $150 / $30
    china_stop_buying_multiplier=10.0, # $300 / $30
    prob_brics_announce=0.05,
    prob_cbdc_launch=0.05,
    prob_mining_strike=0.10,
    prob_retail_capitulation=0.05,
    prob_energy_crisis=0.05,
    prob_predatory_squeeze=0.20
)

DEFAULT_CAPACITIES = Capacities(
    smelter_max_annual=500.0,
    ai_tech_max_annual=800.0,
    india_trade_deficit_limit=500.0 # Normalized limit based on Moz volume
)

DEFAULT_VAULTS = VaultStarts(
    lbma_vault=300.0,
    lbma_unallocated=1000.0,
    comex_eligible=200.0,
    india_capacity=145.0,
    india_inventory=70.0,
    jpm_house=350.0,
    billionaire_vault=400.0,
    retail_mattress=2000.0,
    etf_holdings=1270.0,
    deep_hoarders=2500.0
)

HISTORICAL_2005_STATE = SimConfig(
    start_year=2005, start_silver_price=7.00, start_gold_price=430.00, comex_float=180.0,
    fed_rate=3.0, primary_mine=200.0, byproduct_mine=450.0, scrap_refiners=150.0, ewaste=5.0,
    solar_pv=5.0, ev_auto=5.0, defense=25.0, ai_tech=150.0, jewelry=180.0, other_demand=150.0, retail=100.0,
    thresholds=DEFAULT_THRESHOLDS, capacities=DEFAULT_CAPACITIES, vaults=DEFAULT_VAULTS
)

HISTORICAL_1990_STATE = SimConfig(
    start_year=1990, start_silver_price=4.00, start_gold_price=380.00, comex_float=250.0,
    fed_rate=8.0, primary_mine=130.0, byproduct_mine=300.0, scrap_refiners=100.0, ewaste=0.0,
    solar_pv=0.0, ev_auto=0.0, defense=35.0, ai_tech=80.0, jewelry=150.0, other_demand=150.0, retail=50.0,
    thresholds=DEFAULT_THRESHOLDS, capacities=DEFAULT_CAPACITIES, vaults=DEFAULT_VAULTS
)

FUTURE_2026_STATE = SimConfig(
    start_year=2026, start_silver_price=0.0, start_gold_price=0.0, comex_float=415.0,
    fed_rate=5.0, primary_mine=232.0, byproduct_mine=610.0, scrap_refiners=150.0, ewaste=40.0,
    solar_pv=151.0, ev_auto=100.0, defense=40.0, ai_tech=80.0, jewelry=200.0, other_demand=280.0, retail=250.0,
    thresholds=DEFAULT_THRESHOLDS, capacities=DEFAULT_CAPACITIES, vaults=DEFAULT_VAULTS
)
