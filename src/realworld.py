import os
import json
import time
from typing import Dict, Any
import yfinance as yf
import requests

CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'live_market_cache.json'))
CACHE_TTL_SECONDS = 900  # 15 minutes cache to avoid rate limits and save API quota

def _load_cache() -> Dict[str, Any]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if time.time() - cached.get('timestamp', 0) < CACHE_TTL_SECONDS:
                    return cached
        except Exception:
            pass
    return {}

def _save_cache(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _fetch_from_metalpriceapi(api_key: str) -> Dict[str, Any]:
    """Fetch live rates from MetalPriceAPI (https://metalpriceapi.com/)."""
    url = f"https://api.metalpriceapi.com/v1/latest?api_key={api_key}&base=USD&currencies=XAU,XAG"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("success"):
        rates = payload.get("rates", {})
        xag = rates.get("XAG", 0)
        xau = rates.get("XAU", 0)
        silver = (1.0 / xag) if (xag and xag < 1.0) else float(xag)
        gold = (1.0 / xau) if (xau and xau < 1.0) else float(xau)
        return {
            "success": True,
            "provider": "metalpriceapi",
            "silver_price": round(silver, 2),
            "gold_price": round(gold, 2),
            "fed_rate_proxy": 4.50,
            "timestamp": time.time()
        }
    raise ValueError(f"MetalPriceAPI error: {payload.get('error')}")

def _fetch_from_alphavantage(api_key: str) -> Dict[str, Any]:
    """Fetch live rates from Alpha Vantage (https://www.alphavantage.co/)."""
    url_si = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAG&to_currency=USD&apikey={api_key}"
    resp_si = requests.get(url_si, timeout=5)
    resp_si.raise_for_status()
    data_si = resp_si.json()
    rate_si = float(data_si["Realtime Currency Exchange Rate"]["5. Exchange Rate"])

    url_gc = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=USD&apikey={api_key}"
    resp_gc = requests.get(url_gc, timeout=5)
    resp_gc.raise_for_status()
    data_gc = resp_gc.json()
    rate_gc = float(data_gc["Realtime Currency Exchange Rate"]["5. Exchange Rate"])

    return {
        "success": True,
        "provider": "alphavantage",
        "silver_price": round(rate_si, 2),
        "gold_price": round(rate_gc, 2),
        "fed_rate_proxy": 4.50,
        "timestamp": time.time()
    }

def _fetch_from_yfinance() -> Dict[str, Any]:
    """Fetch from Yahoo Finance using yfinance library."""
    tickers = yf.Tickers("SI=F GC=F ^TNX")
    si_hist = tickers.tickers["SI=F"].history(period="5d")
    gc_hist = tickers.tickers["GC=F"].history(period="5d")
    tnx_hist = tickers.tickers["^TNX"].history(period="5d")
    
    si_price = float(si_hist['Close'].iloc[-1]) if (not si_hist.empty and 'Close' in si_hist) else 67.0
    gc_price = float(gc_hist['Close'].iloc[-1]) if (not gc_hist.empty and 'Close' in gc_hist) else 4350.0
    tnx_rate = float(tnx_hist['Close'].iloc[-1]) if (not tnx_hist.empty and 'Close' in tnx_hist) else 4.50
    
    return {
        "success": True,
        "provider": "yfinance",
        "silver_price": si_price,
        "gold_price": gc_price,
        "fed_rate_proxy": tnx_rate,
        "timestamp": time.time()
    }

def fetch_live_market_data(use_cache: bool = False) -> Dict[str, Any]:
    """
    Multi-Provider live market data fetcher:
    1. Checks local cache (15 min TTL) if use_cache=True to avoid quota burn.
    2. MetalPriceAPI (if METALPRICE_API_KEY set).
    3. AlphaVantage (if ALPHAVANTAGE_API_KEY set).
    4. Yahoo Finance (SI=F, GC=F, ^TNX).
    5. Calibrated Real-World Baseline ($67.00 Silver, $4,350.00 Gold, 4.50% Fed Rate).
    """
    if use_cache:
        cached = _load_cache()
        if cached:
            return cached

    # Check for dedicated API keys in environment
    metalprice_key = os.environ.get("METALPRICE_API_KEY")
    if metalprice_key:
        try:
            data = _fetch_from_metalpriceapi(metalprice_key)
            _save_cache(data)
            return data
        except Exception as e:
            print(f"[LiveMarket] MetalPriceAPI failed: {e}. Trying next provider...")

    alphavantage_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if alphavantage_key:
        try:
            data = _fetch_from_alphavantage(alphavantage_key)
            _save_cache(data)
            return data
        except Exception as e:
            print(f"[LiveMarket] AlphaVantage failed: {e}. Trying next provider...")

    # Default provider: Yahoo Finance
    try:
        data = _fetch_from_yfinance()
        _save_cache(data)
        return data
    except Exception as e:
        print(f"[RealWorld Data] Failed to fetch live data: {e}. Using fallback defaults.")
        fallback = {
            "success": False,
            "provider": "calibrated_fallback",
            "silver_price": 67.0,
            "gold_price": 4350.0,
            "fed_rate_proxy": 4.50,
            "error": str(e),
            "timestamp": time.time()
        }
        return fallback

if __name__ == "__main__":
    data = fetch_live_market_data()
    print("Live Market Data:", data)
