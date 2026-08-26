import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import SimConfig, Thresholds, Capacities, VaultStarts

def test_config_from_yaml(tmp_path, mocker):
    """Test loading valid YAML into dataclass."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("dummy")
    
    # Mock yaml.safe_load to return a complete dictionary
    mock_data = {
        'start_year': 2026, 'start_silver_price': 30.0, 'start_gold_price': 2500.0,
        'comex_float': 100.0, 'fed_rate': 5.0,
        'primary_mine': 800.0, 'byproduct_mine': 200.0, 'scrap_refiners': 150.0, 'ewaste': 50.0,
        'solar_pv': 150.0, 'ev_auto': 100.0, 'defense': 50.0, 'ai_tech': 50.0, 
        'jewelry': 200.0, 'other_demand': 100.0, 'retail': 100.0,
        'thresholds': {
            'retail_melt_multiplier': 2.5, 'jpm_dump_multiplier': 3.33, 'solar_substitution_multiplier': 6.66,
            'hoarder_dump_multiplier': 5.0, 'china_stop_buying_multiplier': 10.0, 'prob_brics_announce': 0.05,
            'prob_cbdc_launch': 0.05, 'prob_mining_strike': 0.10, 'prob_retail_capitulation': 0.05,
            'prob_energy_crisis': 0.05, 'prob_predatory_squeeze': 0.20
        },
        'capacities': {
            'smelter_max_annual': 500.0, 'ai_tech_max_annual': 800.0, 'india_trade_deficit_limit': 500.0
        },
        'vaults': {
            'lbma_vault': 300.0, 'lbma_unallocated': 1000.0, 'comex_eligible': 200.0,
            'india_capacity': 200.0, 'india_inventory': 100.0, 'jpm_house': 100.0,
            'billionaire_vault': 50.0, 'retail_mattress': 100.0, 'etf_holdings': 800.0, 'deep_hoarders': 2500.0
        }
    }
    mocker.patch('yaml.safe_load', return_value=mock_data)
    
    cfg = SimConfig.from_yaml(str(config_file))
    assert cfg.start_silver_price == 30.0
    assert cfg.thresholds.retail_melt_multiplier == 2.5
    assert cfg.capacities.smelter_max_annual == 500.0
    assert cfg.vaults.jpm_house == 100.0

def test_config_from_yaml_exception(tmp_path, capsys):
    """Test catching exceptions when loading bad YAML."""
    bad_yaml_content = "start_silver_price: : bad yaml {"
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(bad_yaml_content)
    
    with pytest.raises(Exception):
        SimConfig.from_yaml(str(config_file))
        
    captured = capsys.readouterr()
    assert "[Config] Error loading YAML config" in captured.out

def test_config_from_yaml_import_error(tmp_path, mocker, capsys):
    """Test handling of missing PyYAML."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("start_silver_price: 30.0")
    
    # Mock __import__ to raise ImportError when importing yaml
    original_import = __builtins__['__import__']
    def mock_import(name, *args, **kwargs):
        if name == 'yaml':
            raise ImportError("No module named 'yaml'")
        return original_import(name, *args, **kwargs)
        
    mocker.patch('builtins.__import__', side_effect=mock_import)
    
    with pytest.raises(ImportError):
        SimConfig.from_yaml(str(config_file))
        
    captured = capsys.readouterr()
    assert "[Config] PyYAML not installed" in captured.out
