import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from realworld import fetch_live_market_data
import runpy

def test_fetch_live_market_data_exception(mocker, capsys):
    """Test that connection errors to yfinance are caught and handled gracefully."""
    # Mock yfinance.Tickers to raise an Exception
    mocker.patch('realworld.yf.Tickers', side_effect=Exception("Connection refused"))
    
    result = fetch_live_market_data()
    
    assert result["success"] is False
    assert "Connection refused" in result["error"]
    
    captured = capsys.readouterr()
    assert "[RealWorld Data] Failed to fetch live data: Connection refused" in captured.out

def test_realworld_main_block(mocker, capsys):
    """Test the __main__ execution block of realworld.py."""
    # Mock the fetch_live_market_data so we don't actually hit the API
    mock_data = {"success": True, "silver_price": 31.0, "gold_price": 2500.0, "fed_rate_proxy": 4.5}
    mocker.patch('realworld.fetch_live_market_data', return_value=mock_data)
    
    # Execute the file as __main__
    module_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'realworld.py')
    runpy.run_path(module_path, run_name="__main__")
    
    captured = capsys.readouterr()
    assert "Live Market Data:" in captured.out
