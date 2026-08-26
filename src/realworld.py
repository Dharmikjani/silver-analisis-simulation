import yfinance as yf
from typing import Dict, Any

def fetch_live_market_data() -> Dict[str, Any]:
    """
    Fetches live real-world market data for the silver simulation.
    Uses yfinance to get:
    - Silver Futures (SI=F)
    - Gold Futures (GC=F)
    - 10-Year Treasury Yield (TNX) as a proxy for rates.
    """
    try:
        # Tickers for Silver, Gold, and 10-Year Treasury
        tickers = yf.Tickers("SI=F GC=F ^TNX")
        
        # Get latest price
        si_price = tickers.tickers["SI=F"].history(period="1d")['Close'].iloc[-1]
        gc_price = tickers.tickers["GC=F"].history(period="1d")['Close'].iloc[-1]
        tnx_rate = tickers.tickers["^TNX"].history(period="1d")['Close'].iloc[-1]
        
        return {
            "success": True,
            "silver_price": float(si_price),
            "gold_price": float(gc_price),
            "fed_rate_proxy": float(tnx_rate)
        }
    except Exception as e:
        print(f"[RealWorld Data] Failed to fetch live data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    data = fetch_live_market_data()
    print("Live Market Data:", data)
