import pytest
from fastapi.testclient import TestClient
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from api.main import app

client = TestClient(app)

def test_api_live_endpoint():
    # Hit the real yfinance API through our FastAPI endpoint
    response = client.get("/api/live")
    assert response.status_code == 200
    data = response.json()
    assert "silver_price" in data
    assert "gold_price" in data
    assert "fed_rate_proxy" in data
    assert data["silver_price"] > 0
    assert data["gold_price"] > 0

def test_api_simulate_endpoint():
    # This might return empty if no outputs exist, but we should just ensure a 200 response
    response = client.get("/api/simulate")
    assert response.status_code == 200
    data = response.json()
    assert "base" in data
    assert "bull" in data
    assert "bear" in data
