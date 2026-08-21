import math
import random
import yfinance as yf
from config import FUTURE_2026_STATE, SCENARIOS_OVERRIDE, TRADING_DAYS
from logger import log_event

class LiveDataOracle:
    def __init__(self, mode="future", config=FUTURE_2026_STATE):
        self.silver_price = config.start_silver_price
        self.gold_price = config.start_gold_price
        self.fed_rate = config.fed_rate
        self.dxy = 100.0
        self.copper = 4.0
        
        if mode == "future":
            self.fetch_live_data()
        
    def fetch_live_data(self):
        try:
            print("[LiveDataOracle] Fetching live macro APIs...")
            tickers = {
                "Silver": "SI=F",
                "Gold": "GC=F",
                "DXY": "DX-Y.NYB",
                "FedRate": "^IRX",
                "Copper": "HG=F"
            }
            
            data = {}
            for name, symbol in tickers.items():
                t = yf.Ticker(symbol)
                hist = t.history(period="1d")
                if not hist.empty:
                    data[name] = float(hist["Close"].iloc[-1])
            
            if "Silver" in data: self.silver_price = data["Silver"]
            if "Gold" in data and data["Gold"] > 0: self.gold_price = data["Gold"]
            if "DXY" in data and data["DXY"] > 0: self.dxy = data["DXY"]
            if "FedRate" in data: self.fed_rate = data["FedRate"]
            if "Copper" in data and data["Copper"] > 0: self.copper = data["Copper"]
            log_event("LiveDataOracle", "Loaded live data", silver=self.silver_price, gold=self.gold_price, dxy=self.dxy, fed_rate=self.fed_rate, copper=self.copper)
            print(f"[LiveDataOracle] Loaded | Silver: ${self.silver_price:.2f} | Gold: ${self.gold_price:.2f} | DXY: {self.dxy:.2f} | Fed: {self.fed_rate:.2f}% | Copper: ${self.copper:.2f}")
            
        except Exception as e:
            print(f"[LiveDataOracle] API Error: {e}. Using defaults.")
            self.silver_price = 30.0
            self.gold_price = 2500.0

class MacroEnvironment:
    def __init__(self, config=None, gold_price=2500.0, fed_rate=5.0, dxy=100.0, copper=4.0, start_year=2026):
        self.config = config
        self.dxy_strength = dxy
        self.fed_funds_rate = fed_rate
        self.m2_inflation_index = 1.0
        self.tech_deflation_index = 1.0
        self.supply_chain_blockade = False
        self.brics_vault_drain_daily = 0
        self.gold_price = gold_price
        
        self.current_year = start_year
        self.current_day = 0
        
        self.copper_price_index = copper / 4.0
        self.base_metal_cycle = 1.0  
        self.brics_announced = False
        self.cbdc_launched = False
        self.india_duty_active = False 
        self.real_yields = 1.5 
        self.global_gdp_growth = 0.02 
        self.geopolitical_tension_index = 50.0 
        self.oil_price = 75.0  
        
        self.ai_bubble_burst = False
        self.mining_strike_active = False
        self.mining_strike_days = 0
        self.retail_capitulation = False
        self.refinery_energy_crisis = False
        self.energy_crisis_days = 0
        
        self.base_metal_recession_active = False
        self.defense_stockpile_active = False
        self.export_ban_active = False
        
    def simulate_day(self):
        self.current_day += 1
        if self.current_day >= TRADING_DAYS:
            self.current_year += 1
            self.current_day = 0
            
        dt = 1.0 / TRADING_DAYS
        
        Z1 = random.gauss(0,1)
        Z2 = random.gauss(0,1)
        Z3 = random.gauss(0,1)
        
        dW_dxy = Z1
        dW_metal = -0.3 * Z1 + 0.9539 * Z2  
        dW_geo = 0.4 * Z1 + 0.1 * Z2 + 0.911 * Z3
        
        self.dxy_strength *= math.exp(-0.5 * 0.05**2 * dt + 0.05 * math.sqrt(dt) * dW_dxy)
        self.base_metal_cycle = max(0.6, min(1.4, self.base_metal_cycle * math.exp(-0.5 * 0.1**2 * dt + 0.1 * math.sqrt(dt) * dW_metal)))
        
        geo_theta = 0.5  
        self.geopolitical_tension_index += geo_theta * (50.0 - self.geopolitical_tension_index) * dt + 15 * math.sqrt(dt) * dW_geo
        self.geopolitical_tension_index = max(10.0, min(100.0, self.geopolitical_tension_index))
        
        gold_drift = 0.03 + (self.m2_inflation_index - 1.0) * 0.02
        self.gold_price *= math.exp((gold_drift - 0.5 * 0.15**2) * dt + 0.15 * math.sqrt(dt) * random.gauss(0,1))
        
        if self.global_gdp_growth < 0:
            self.copper_price_index *= math.exp(-0.5 * 0.3**2 * dt - 0.1*dt + 0.3 * math.sqrt(dt) * random.gauss(0,1))
        else:
            self.copper_price_index = min(1.2, self.copper_price_index * math.exp(-0.5 * 0.1**2 * dt + 0.05*dt + 0.1 * math.sqrt(dt) * random.gauss(0,1)))
        
        oil_drift = 0.02
        if self.geopolitical_tension_index > 75: oil_drift = 0.20
        elif self.global_gdp_growth < -0.01: oil_drift = -0.20
        self.oil_price = max(40.0, min(200.0, self.oil_price * math.exp((oil_drift - 0.5 * 0.25**2) * dt + 0.25 * math.sqrt(dt) * random.gauss(0,1))))
        
        self.m2_inflation_index *= math.exp(0.03 * dt)
        self.tech_deflation_index *= math.exp(-0.02 * dt)
        
        gdp_theta = 0.3  
        self.global_gdp_growth += gdp_theta * (0.02 - self.global_gdp_growth) * dt + 0.015 * math.sqrt(dt) * random.gauss(0,1)
        self.global_gdp_growth = max(-0.04, min(0.06, self.global_gdp_growth))
        
        if not self.brics_announced and self.config and random.random() < (self.config.thresholds.prob_brics_announce / TRADING_DAYS):
            self.brics_announced = True
            log_event("Macro", "BRICS Gold-Reserve Announcement", gold_price=self.gold_price)
            self.brics_vault_drain_daily = 0
            self.gold_price *= random.uniform(1.05, 1.15) 
            
        if self.dxy_strength > 105 and self.global_gdp_growth < 0:
            self.base_metal_recession_active = True
        else:
            self.base_metal_recession_active = False
            
        if self.geopolitical_tension_index > 85:
            self.defense_stockpile_active = True
        else:
            self.defense_stockpile_active = False
            
        if self.geopolitical_tension_index > 75:
            if random.random() < (0.10 / TRADING_DAYS):
                self.export_ban_active = True
        elif self.brics_announced:
            self.brics_vault_drain_daily = 0
            
        if self.geopolitical_tension_index > 85:
            if not self.supply_chain_blockade:
                log_event("Macro", "Supply Chain Blockade Hit", tension=self.geopolitical_tension_index)
            self.supply_chain_blockade = True
        else:
            self.supply_chain_blockade = False
            
        if not self.cbdc_launched and self.config and random.random() < (self.config.thresholds.prob_cbdc_launch / TRADING_DAYS):
            self.cbdc_launched = True
            log_event("Macro", "CBDC Launched")
            
        if not SCENARIOS_OVERRIDE["no_ai_burst"] and not self.ai_bubble_burst and self.config and random.random() < (0.03 / TRADING_DAYS):
            self.ai_bubble_burst = True
            log_event("Macro", "AI Bubble Burst", year=self.current_year)
            
        if not SCENARIOS_OVERRIDE["no_strikes"] and not self.mining_strike_active and self.config and random.random() < (self.config.thresholds.prob_mining_strike / TRADING_DAYS):
            self.mining_strike_active = True
            self.mining_strike_days = 60
            log_event("Macro", "Mining Strike Active", duration_days=60)
            
        if self.mining_strike_active:
            self.mining_strike_days -= 1
            if self.mining_strike_days <= 0:
                self.mining_strike_active = False
                log_event("Macro", "Mining strikes resolved")
                
        if not SCENARIOS_OVERRIDE["no_retail_cap"] and not self.retail_capitulation and self.config and random.random() < (self.config.thresholds.prob_retail_capitulation / TRADING_DAYS):
            self.retail_capitulation = True
            log_event("Macro", "Retail Capitulation", year=self.current_year)
            
        if not SCENARIOS_OVERRIDE["no_energy_crisis"] and not self.refinery_energy_crisis and self.config and random.random() < (self.config.thresholds.prob_energy_crisis / TRADING_DAYS):
            self.refinery_energy_crisis = True
            self.energy_crisis_days = 90
            log_event("Macro", "Smelter Energy Crisis", duration_days=90)
            
        if self.refinery_energy_crisis:
            self.energy_crisis_days -= 1
            if self.energy_crisis_days <= 0:
                self.refinery_energy_crisis = False
                log_event("Macro", "Smelter energy crisis resolved")
