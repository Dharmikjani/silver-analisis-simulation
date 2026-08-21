import math
import random
from config import TRADING_DAYS, SCENARIOS_OVERRIDE
from logger import log_event

class Stakeholder:
    def __init__(self, name, annual_base_volume):
        self.name = name
        self.daily_volume = annual_base_volume / TRADING_DAYS
        
    def process_day(self, price, macro):
        pass

class PrimaryMiners(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.mines_shutdown = 0 
        self.capex_expansion_cycle = 0 # Delayed supply from high margins
        self.ore_grade_difficulty_multiplier = 1.0 # Geological difficulty increases over time (higher = harder/costlier)
        self.withheld_inventory = 0.0 # Hoarded silver when prices are below cost
    def process_day(self, price, macro):
        # AI Logic: Geological decay makes mining harder every year (1.5% annual decay penalty)
        self.ore_grade_difficulty_multiplier *= math.exp(0.015 / TRADING_DAYS)
        
        # AI Logic: AISC is inflated by M2, deflated by Tech, but permanently penalized by geological difficulty
        aisc = 22.0 * (macro.oil_price / 75.0) * macro.m2_inflation_index * macro.tech_deflation_index * self.ore_grade_difficulty_multiplier
        aisc = max(0.01, aisc) # Prevent division by zero
        dt = 1.0 / TRADING_DAYS
        
        aisc_margin = (price - aisc) / aisc
        
        # AI Logic: Invest Capex if margin is very high
        if aisc_margin > 0.5:
            self.capex_expansion_cycle += (0.05 / TRADING_DAYS) # Gradual buildup
        
        # Release delayed capex supply
        delayed_supply_bonus = 0.0
        if self.capex_expansion_cycle > 0.5: # Takes years to hit this
            delayed_supply_bonus = self.capex_expansion_cycle * 0.1
            self.capex_expansion_cycle -= (0.1 / TRADING_DAYS)
        
        # Long-term base growth/decay
        growth_rate = 0.01 if price > aisc else -0.02
        self.daily_volume *= math.exp(growth_rate * dt)
        
        # BUG FIX 1 (User Domain Expertise): Primary Miners do not shut down, they withhold sales!
        production = self.daily_volume + delayed_supply_bonus
        output = production
        
        if price < aisc:
            self.mines_shutdown = 0 # Miners don't shutdown, they just hoard
            if price < aisc * 0.80:
                withhold_ratio = 0.90 # Withhold 90% of sales
            else:
                withhold_ratio = 0.50 # Withhold 50% of sales
                
            withheld_amount = production * withhold_ratio
            self.withheld_inventory += withheld_amount
            output = production - withheld_amount
        else:
            self.mines_shutdown = 0
            if self.withheld_inventory > 0 and price > aisc * 1.20:
                dump_amount = min(self.withheld_inventory, production * 0.50)
                self.withheld_inventory -= dump_amount
                output = production + dump_amount
            
        # Scenario: South American mining strike slashes supply by 40%
        if macro.mining_strike_active:
            output *= 0.60
            
        # AI Logic: Blockades/Strikes happen in normal times.
        # But if the price is extremely high (Squeeze), governments use military/emergency powers to force mines open.
        if macro.geopolitical_tension_index > 85 and price < (100 * macro.m2_inflation_index):
            output *= random.uniform(0.90, 0.95) # Only 5-10% of global primary production goes offline (realistic single-country impact)
            
        return output
        
class ByproductMiners(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.initial_capacity = self.daily_volume
        self.withheld_inventory = 0.0
        
    def process_day(self, price, macro):
        dt = 1.0 / TRADING_DAYS
        self.initial_capacity *= math.exp(0.005 * dt)
        production = self.initial_capacity * macro.base_metal_cycle * macro.copper_price_index
        output = production
        
        # User Domain Expertise: Base metal mines won't shut down for silver, and they almost never hoard it.
        # They mine copper/zinc and sell the silver byproduct at market value regardless of price.
        hoard_threshold = 15.0 * macro.m2_inflation_index
        if price < hoard_threshold:
            withhold_ratio = 0.10 # Only a tiny 10% friction withholding, mostly they just sell it
            withheld_amount = production * withhold_ratio
            self.withheld_inventory += withheld_amount
            output = production - withheld_amount
        else:
            if self.withheld_inventory > 0 and price > hoard_threshold * 1.5:
                dump_amount = min(self.withheld_inventory, production * 0.50)
                self.withheld_inventory -= dump_amount
                output = production + dump_amount
                
        self.daily_volume = production
        return output

class ScrapRefiners(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.scrap_fatigue_days = 0
        self.total_scrap_inventory = 1500.0 # Global above-ground meltable scrap pool
        self.price_history = []
        
    def process_day(self, price, macro):
        dt = 1.0 / TRADING_DAYS
        self.daily_volume *= math.exp(0.015 * dt) 
        
        # AI Momentum tracking
        self.price_history.append(price)
        if len(self.price_history) > 30: self.price_history.pop(0)
        
        price_momentum = 1.0
        if len(self.price_history) == 30:
            momentum_ratio = price / self.price_history[0]
            # FIX: Reversed order so high-momentum branch (2.5x) is reachable
            if momentum_ratio > 1.5: price_momentum = 2.5
            elif momentum_ratio > 1.2: price_momentum = 1.5
        
        if self.total_scrap_inventory <= 0:
            self.scrap_fatigue_days += 1
            return 0 # Completely dried up
            
        actual_output = self.daily_volume * price_momentum
        
        # EXTREME SCRAP AVALANCHE: High prices cure high prices
        if price > 100:
            # For every $10 over $100, daily scrap output increases by 10%
            scrap_multiplier = 1.0 + ((price - 100) / 10.0) * 0.10
            actual_output *= scrap_multiplier
            
        if price_momentum > 1.0 or price > 100:
            dump_amount = min(self.total_scrap_inventory, actual_output)
            self.total_scrap_inventory -= dump_amount
            return dump_amount
            
        # User Domain Expertise: If price is too low, people stop selling scrap
        hoard_threshold = 15.0 * macro.m2_inflation_index
        if price < hoard_threshold:
            return 0.0
            
        return actual_output

class EWasteRecyclers(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.tech_obsolescence_rate = 1.0
        
    def process_day(self, price, macro):
        self.tech_obsolescence_rate *= math.exp(0.02 / TRADING_DAYS) # More electronics die over time
        
        # User Domain Expertise: E-waste isn't recycled if it costs more than the silver is worth
        hoard_threshold = 15.0 * macro.m2_inflation_index
        if price < hoard_threshold:
            return 0.0
            
        refining_margin = price / (40.0 * max(0.01, macro.m2_inflation_index)) # Needs high prices to be profitable
        if refining_margin > 1.0:
            return min((120.0 / TRADING_DAYS), self.daily_volume * self.tech_obsolescence_rate * refining_margin)
        return self.daily_volume

class DeepPrivateHoarders(Stakeholder):
    """FIX #7 (Competitor): Split hoarder hive-mind into N independent sub-agents
    with randomized thresholds and staggered reaction delays."""
    def __init__(self, name, annual_base_volume, num_agents=5):
        super().__init__(name, annual_base_volume)
        self.total_hoard = 2500.0 
        self.price_history = []
        self.num_agents = num_agents
        # Each sub-agent has a different dump threshold multiplier and reaction lag
        self.sub_agents = []
        for i in range(num_agents):
            self.sub_agents.append({
                'share': self.total_hoard / num_agents,
                'dump_threshold_mult': random.uniform(0.85, 1.15),  # ±15% around $150 base
                'momentum_lag': random.randint(5, 30),  # 5-30 day reaction delay
                'price_buffer': [],
            })
        
    def process_day(self, price, macro):
        self.price_history.append(price)
        if len(self.price_history) > 60: self.price_history.pop(0)
        
        total_dump = 0.0
        
        for agent in self.sub_agents:
            agent['price_buffer'].append(price)
            if len(agent['price_buffer']) > agent['momentum_lag']:
                agent['price_buffer'].pop(0)
            
            # AI Accumulation: High fear = Hoard more (all agents agree on this)
            if macro.geopolitical_tension_index > 80:
                accumulation = (10.0 / TRADING_DAYS) / self.num_agents
                agent['share'] += accumulation
                continue
            
            # AI Dumping: Each agent has its own threshold and checks its own lagged momentum
            threshold_base = macro.config.start_silver_price * macro.config.thresholds.hoarder_dump_multiplier if macro.config else 150
            threshold = threshold_base * macro.m2_inflation_index * agent['dump_threshold_mult']
            if agent['share'] > 0 and price > threshold:
                if len(agent['price_buffer']) == agent['momentum_lag']:
                    if price < agent['price_buffer'][0] * 0.95:
                        dump = min(agent['share'], random.uniform(200, 500) / TRADING_DAYS / self.num_agents)
                        agent['share'] -= dump
                        total_dump += dump
        
        self.total_hoard = sum(a['share'] for a in self.sub_agents)
        return total_dump

class BlackMarketSmugglers(Stakeholder):
    def process_day(self, price, macro):
        # AI Arb: Smugglers only act if India import duty is high
        # FIX #3: Now uses macro.india_duty_active flag (set from Gov_India's duty level in main loop)
        if macro.india_duty_active:
            return random.uniform(10.0, 30.0) / TRADING_DAYS
        return 5.0 / TRADING_DAYS

class SmelterRefineryBottleneck:
    def __init__(self, max_annual_capacity=500.0): 
        self.max_daily_capacity = max_annual_capacity / TRADING_DAYS
        self.backlog = 0.0
        
    def process_supply(self, secondary_supply, price, macro):
        # FIX #10: Capacity expansion is now reversible — decays when price drops
        max_annual = macro.config.capacities.smelter_max_annual if macro.config else 500.0
        if price > 200:
            self.max_daily_capacity = min((max_annual * 1.2) / TRADING_DAYS, self.max_daily_capacity * 1.001)  # Slow ramp up
        elif price < 100:
            self.max_daily_capacity = max(max_annual / TRADING_DAYS, self.max_daily_capacity * 0.999)  # Slow decay back
        
        working_capacity = self.max_daily_capacity
        if macro.supply_chain_blockade: working_capacity *= 0.85
        
        total_to_process = secondary_supply + self.backlog
        processed = min(working_capacity, total_to_process)
        self.backlog = total_to_process - processed
        
        return processed

class SolarPV(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.substitution_rd_budget = 0.0 # Tracks how much money is spent trying to replace silver
        self.substitution_triggered = False
        self._panic_days = 0  # FIX: Track panic hoarding duration for decay
        self.loading_factor = 1.0  # FIX #7: Silver loading per cell (thrifting reduces this ~3%/year)
        self.reversion_lag = 0
        
    def process_day(self, price, macro):
        dt = 1.0 / TRADING_DAYS
        
        if macro.current_year < 2005:
            return 0
        if self.daily_volume == 0:
            self.daily_volume = 5.0 / TRADING_DAYS # Seed demand
            
        if self.substitution_triggered:
            # AI Logic: Reversible Substitution (User Insight)
            # Even if they retooled to copper, if silver price crashes, they switch back 
            # because silver has superior thermal & electrical conductivity.
            competitive_threshold = 40.0 * macro.m2_inflation_index
            if price < competitive_threshold:
                self.reversion_lag += 1
                if self.reversion_lag > 30: # 30 trading days lag to switch back
                    return self.daily_volume * self.loading_factor  # Demand fully restored (but still thrifted)
            else:
                self.reversion_lag = 0
            return self.daily_volume * self.loading_factor * 0.10  # Still using copper
            
        # AI Logic: The "Assembly Line Shutdown Paradox"
        # Industry can't substitute easily. R&D only gets seriously funded at threshold (adjusted for inflation)
        sub_base = macro.config.start_silver_price * macro.config.thresholds.solar_substitution_multiplier if macro.config else 200.0
        substitution_threshold = sub_base * macro.m2_inflation_index
        
        # AI Logic: Bear Case Threat Matrix - Copper substitution is physically impossible at scale before 2029
        if not SCENARIOS_OVERRIDE["no_solar_sub"] and price > substitution_threshold and macro.current_year >= 2029:
            # Probabilistic substitution based on user requirement (not hard 100% budget)
            rd_funding_rate = ((price - substitution_threshold) / 100.0) * (1.0 / TRADING_DAYS)
            self.substitution_rd_budget += rd_funding_rate
            
        if self.substitution_rd_budget >= 1.0: 
            # Breakthrough achieved probabilistically (e.g., 5% chance once budget is full)
            if random.random() < (0.05 / TRADING_DAYS):
                self.substitution_triggered = True
                print(f"[SolarPV] Copper-retooling breakthrough achieved! Massive demand destruction.")
                return self.daily_volume * self.loading_factor * 0.10
        
        # Epoch scaling
        if macro.current_year <= 2015:
            self.daily_volume *= math.exp((macro.global_gdp_growth) * dt)
        else:
            self.daily_volume *= math.exp((macro.global_gdp_growth + 0.05) * dt)
        
        # FIX #7: Silver loading thrifting — cells use ~3% less silver per year (industry trend since 2015)
        if macro.current_year >= 2015:
            self.loading_factor *= math.exp(-0.03 * dt)
            self.loading_factor = max(0.20, self.loading_factor)  # Floor: can't go below 20% of original loading
            
        # FIX: Panic Hoarding (Bullwhip Effect) — now decays over ~2 years instead of permanent 2x
        if price > 50.0 and macro.current_year >= 2025:
            self._panic_days += 1
            panic_mult = 1.0 + max(0.0, 1.0 - self._panic_days / (TRADING_DAYS * 2))
            return self.daily_volume * self.loading_factor * panic_mult
        else:
            self._panic_days = max(0, self._panic_days - 1)  # Decay panic counter when price drops
            
        return self.daily_volume * self.loading_factor

class DefenseAerospace(Stakeholder):
    def process_day(self, price, macro):
        self.daily_volume *= math.exp(0.03 / TRADING_DAYS)
        # AI Logic: Completely inelastic to price. Tracks geopolitics.
        if macro.geopolitical_tension_index > 80: return self.daily_volume * 1.5 
        return self.daily_volume

class Tech_AI(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.datacenter_buildout_rate = 1.0
        # FIX: Logistic saturation cap
        self.max_annual_capacity = 800.0
        
    def process_day(self, price, macro):
        max_daily_capacity = (macro.config.capacities.ai_tech_max_annual if macro.config else self.max_annual_capacity) / TRADING_DAYS
        if macro.current_year < 2020:
            self.daily_volume *= math.exp(0.02 / TRADING_DAYS) # Standard electronics growth
            return min(max_daily_capacity, self.daily_volume)
        else:
            self.datacenter_buildout_rate *= math.exp(0.05 / TRADING_DAYS)
            self.daily_volume *= math.exp(0.10 / TRADING_DAYS)
            # FIX: Logistic saturation — compound growth is capped at physical maximum
            self.daily_volume = min(max_daily_capacity, self.daily_volume)
            self.datacenter_buildout_rate = min(3.0, self.datacenter_buildout_rate)  # Cap buildout rate at 3x
            
            # AI Logic: Highly elastic unless in a massive AI boom (which we assume here)
            safe_price = max(1.0, price)
            
            # Panic Hoarding (Bullwhip Effect)
            base_vol = self.daily_volume * self.datacenter_buildout_rate
            if safe_price > 50.0 and macro.current_year >= 2025:
                base_vol *= 1.5
                
            # Scenario: AI valuation bubble burst slows capital expenditure. Real physical demand contracts by 25% (not 70%) as hyperscalers slow buildout.
            if macro.ai_bubble_burst:
                base_vol *= 0.75
                
            if safe_price > (2000 * macro.m2_inflation_index): return base_vol * 0.80
            return min(max_daily_capacity * 3.0, base_vol)  # Hard cap including buildout

class EV_Auto(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.battery_tech_cycle = 1.0
        
    def process_day(self, price, macro):
        if macro.current_year < 2012:
            return 0
        if self.daily_volume == 0:
            self.daily_volume = 5.0 / TRADING_DAYS # Seed demand
            
        # AI Logic: Thrifting over time, but overall demand scales with GDP
        self.battery_tech_cycle *= math.exp(-0.01 / TRADING_DAYS) # Thrifting silver out slowly
        
        if macro.current_year < 2018:
            self.daily_volume *= math.exp(macro.global_gdp_growth / TRADING_DAYS)
        else:
            self.daily_volume *= math.exp(0.08 / TRADING_DAYS)
            
        return self.daily_volume * self.battery_tech_cycle

class JewelrySilverware(Stakeholder):
    def process_day(self, price, macro):
        # AI Logic: Consumer discretionary is highly elastic and inverse to inflation
        safe_price = max(1.0, price) # Prevent division by zero
        purchasing_power = min(5.0, 1.0 / max(0.01, macro.m2_inflation_index)) 
        # FIX #11: Thresholds inflation-adjusted from $35/$60 base (historically jewelry demand drops at ~$35+)
        high_threshold = 60.0 * macro.m2_inflation_index
        extreme_threshold = 120.0 * macro.m2_inflation_index
        dip_buy_threshold = 15.0 * macro.m2_inflation_index
        
        # User Domain Expertise: If silver is dirt cheap, Indians and Chinese buy everything (Hyper-elasticity)
        if price < dip_buy_threshold:
            return self.daily_volume * purchasing_power * 10.0
            
        if safe_price > extreme_threshold: return self.daily_volume * 0.40 * purchasing_power
        elif safe_price > high_threshold: return self.daily_volume * 0.80 * purchasing_power
        else:
            self.daily_volume *= math.exp(0.01 / TRADING_DAYS) # Cap infinite compounding, 1% annual growth
            return self.daily_volume * purchasing_power

class OtherIndustrial(Stakeholder):
    """FIX: Separate class for 'Other' industrial demand (photography, brazing, electronics).
    Less price-elastic than jewelry — these are industrial inputs, not discretionary purchases."""
    def process_day(self, price, macro):
        dt = 1.0 / TRADING_DAYS
        safe_price = max(1.0, price)
        # Slow structural decline (photography shrinking, but brazing/medical growing)
        self.daily_volume *= math.exp(0.005 * dt)
        # Industrial demand is moderately elastic — only responds to extreme prices
        if safe_price > (300 * macro.m2_inflation_index):
            return self.daily_volume * 0.60  # Severe demand destruction at extreme prices
        elif safe_price > (150 * macro.m2_inflation_index):
            return self.daily_volume * 0.85  # Moderate thrifting
        return self.daily_volume

class Gov_CentralBanks(Stakeholder):
    def process_day(self, price, macro):
        # FIX (Competitor): Removed arbitrary Cantillon multiplier on physical volume.
        # Inflation/M2 expands purchasing power for price thresholds, but shouldn't arbitrarily 
        # multiply physical tons of metal demanded independently of price.
        
        # AI Logic: Tracks Gold/Silver Ratio (GSR)
        gsr = macro.gold_price / max(0.01, price)
        if gsr > 85.0: # Silver is historically cheap vs gold
            self.daily_volume += (0.2 / TRADING_DAYS) # FIX #1: Slower accumulation (was 5.0)
        elif gsr < 40.0: # Silver is expensive vs gold
            self.daily_volume = max(0, self.daily_volume - (0.2 / TRADING_DAYS))
            
        if macro.brics_announced:
            self.daily_volume += (10.0 / TRADING_DAYS) # Gradually ramp up
        
        # BUG FIX 3: Cap raw daily_volume 
        self.daily_volume = min(self.daily_volume, 150.0 / TRADING_DAYS)
            
        return self.daily_volume

class Gov_India:
    """FIX #9 (Competitor): Policy inertia — duty changes evaluated quarterly, not daily."""
    def __init__(self):
        self.import_duty_level = 0.0 # 0% to 15%
        self.trade_deficit_tracker = 0.0
        self._policy_review_counter = 0  # Days until next policy review
        self._pending_duty_change = 0.0  # Accumulated pressure
        
    def process_jewelry_demand(self, price, base_jewelry_demand, macro=None):
        indian_share = base_jewelry_demand * 0.33
        rest_of_world = base_jewelry_demand * 0.67
        
        # AI Logic: Track Trade Deficit (Price * Volume)
        daily_import_cost = price * indian_share
        self.trade_deficit_tracker += (daily_import_cost - self.trade_deficit_tracker) * 0.1 # Exponential moving average
        
        # FIX #9: Accumulate pressure daily but only ACT on it quarterly (63 trading days)
        # FIX (Trade Deficit limit): Scaled limit to be realistic for daily moving average in Moz
        limit = macro.config.capacities.india_trade_deficit_limit if macro.config else 500.0
        
        # User Feedback Fix: India should drop duties dynamically if trade deficit shrinks or price crashes
        if self.trade_deficit_tracker > limit:
            self._pending_duty_change += 0.1
        elif self.trade_deficit_tracker < limit * 0.7 or price < (20.0 * macro.m2_inflation_index):
            self._pending_duty_change -= 0.5 # Drop duty aggressively
        
        self._policy_review_counter += 1
        if self._policy_review_counter >= 63:  # Quarterly review
            self._policy_review_counter = 0
            if self._pending_duty_change > 0:
                self.import_duty_level = min(15.0, self.import_duty_level + min(self._pending_duty_change, 3.0))
            else:
                self.import_duty_level = max(0.0, self.import_duty_level + max(self._pending_duty_change, -3.0))
            self._pending_duty_change = 0.0
            
        # Reduce demand based on duty
        duty_impact = 1.0 - (self.import_duty_level / 100.0) * 2.0 # 15% duty kills 30% of demand
        indian_share *= max(0.2, duty_impact)
        
        return indian_share, rest_of_world

class Gov_China(Stakeholder):
    """FIX #9 (Competitor): Policy inertia — accumulation strategy reviewed quarterly."""
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.yuan_reserves = 5000000.0 # FIX #8: Scaled budget to match actual purchase costs
        self._policy_review_counter = 0
        self._current_accumulation_rate = 20.0  # Moz/year baseline, set quarterly
        
    def process_day(self, price, macro):
        # User Feedback Fix: China is a black hole. They DO NOT dump silver at high prices.
        # They only stop buying if they run out of reserves.
        if self.yuan_reserves <= 0: return 0 
        
        # FIX #9: Re-evaluate accumulation strategy quarterly
        self._policy_review_counter += 1
        if self._policy_review_counter >= 63:
            self._policy_review_counter = 0
            # Set quarterly accumulation target based on macro conditions
            base = random.uniform(15.0, 25.0)
            if macro.geopolitical_tension_index > 80: base += random.uniform(10.0, 20.0)
            if macro.dxy_strength < 90: base *= 2.0 # Massive buying if USD is weak
            elif macro.dxy_strength > 105: base *= 0.5
            self._current_accumulation_rate = base
            
        # User Domain Expertise: If silver is dirt cheap, Sovereign wealth funds drain the market
        dip_buy_threshold = 15.0 * macro.m2_inflation_index
        if price < dip_buy_threshold:
            self._current_accumulation_rate = 1000.0 # 1000 Moz/year (Hyper-elasticity black hole)
        
        daily_accumulation = self._current_accumulation_rate / TRADING_DAYS
        cost = daily_accumulation * price
        self.yuan_reserves -= cost
        return daily_accumulation

class Gov_USA:
    def __init__(self):
        self.dpa_stockpile = 0.0
        self.national_security_threshold = 75.0 # Critical float level
        self.export_ban_active = False
        
    def check_defense_production_act(self, vault_float):
        # AI Logic: Seize metal for national security if float is too low
        # FIX: DPA is a one-time emergency seizure, not a daily trickle
        if vault_float > 0 and vault_float < self.national_security_threshold and self.dpa_stockpile == 0.0:
            seizure = min(vault_float, 50.0)
            self.dpa_stockpile += seizure
            self.export_ban_active = True
            log_event("Gov", f"US seized {seizure:.1f} Moz under DPA", seizure_moz=seizure, export_ban=True)
            return seizure
        return 0

class Gov_UK:
    def __init__(self):
        self.fiat_injections = 0.0
        
    def check_lbma_bailout(self, vault_float):
        # AI Logic: Bailout LBMA if it defaults
        if vault_float <= 0: 
            self.fiat_injections += 10.0
            log_event("Gov", "UK Bailed out LBMA/Banks", total_injections=self.fiat_injections)
            return True 
        return False

class RetailInvestors(Stakeholder):
    def __init__(self, name, annual_base_volume):
        super().__init__(name, annual_base_volume)
        self.price_history = []
        
    def process_day(self, price, macro):
        self.price_history.append(price)
        if len(self.price_history) > 200: self.price_history.pop(0)
        
        vol = self.daily_volume
        fomo_multiplier = 1.0
        
        # User Domain Expertise: Buy the absolute dip. If price < $15, physical drain happens
        dip_buy_threshold = 15.0 * macro.m2_inflation_index
        if price < dip_buy_threshold:
            return vol * 20.0 # 20x demand when silver crashes to $10-$15
        
        # AI Logic: FOMO Index based on 50 SMA and 200 SMA
        if len(self.price_history) == 200:
            sma_50 = sum(self.price_history[-50:]) / 50.0
            sma_200 = sum(self.price_history) / 200.0
            
            if sma_50 > sma_200 and price > sma_50:
                # FIX #3: Continuous FOMO scaling based on distance above 50 SMA
                distance = (price - sma_50) / sma_50
                fomo_multiplier = 1.0 + min(4.0, distance * 10.0) # Scales smoothly up to 5.0
            elif sma_50 < sma_200:
                fomo_multiplier = 0.5 # Death Cross Fear
        
        if macro.fed_funds_rate < 1.0: vol *= 1.2
        safe_price = max(1.0, price)
        if safe_price > (300 * macro.m2_inflation_index):
            purchasing_power_ratio = (100.0 * macro.m2_inflation_index) / safe_price
            vol *= max(0.1, min(2.0, purchasing_power_ratio))
            
        # Scenario: Retail Capitulation shifts retail capital into gold/crypto (80% drop)
        if macro.retail_capitulation:
            vol *= 0.20
            
        return vol * fomo_multiplier

class WhaleSyndicate:
    def __init__(self):
        self.bank_vulnerability_score = 0.0
        self.attack_volume_remaining = 0.0
        
    def process_accumulation(self, comex_float, bank_short_position):
        # AI Logic: Whales hunt for weakness.
        # If COMEX float drops and bank shorts are high, vulnerability spikes.
        if comex_float < 150.0 and bank_short_position > 200.0:
            self.bank_vulnerability_score += 10.0
        else:
            # FIX #9: Vulnerability decays when conditions normalize
            self.bank_vulnerability_score = max(0.0, self.bank_vulnerability_score - 5.0)
            
        if self.bank_vulnerability_score > 100.0 and self.attack_volume_remaining <= 0:
            # Execute coordinated squeeze attack
            self.bank_vulnerability_score = 0.0 # Reset after attack
            self.attack_volume_remaining = random.uniform(100.0, 250.0)
            print(f"[WhaleSyndicate] Blood in the water! Coordinated buy attack executed! Target: {self.attack_volume_remaining:.1f} Moz")
            
        if self.attack_volume_remaining > 0:
            daily_drain = min(self.attack_volume_remaining, 10.0) # Drain up to 10 Moz/day
            self.attack_volume_remaining -= daily_drain
            return daily_drain
            
        return 0

class PredatoryHedgeFund:
    def __init__(self):
        self.is_squeezing = False
        self.is_dumping = False
        self.holdings = 0.0
        self.target_price = 0.0
        
    def process_attack(self, comex_float, physical_price, macro=None):
        # Trigger condition: Vulnerable float
        if not self.is_squeezing and not self.is_dumping and comex_float < 100.0:
            prob = macro.config.thresholds.prob_predatory_squeeze if (macro and macro.config) else 0.20
            if random.random() < (prob / TRADING_DAYS): 
                self.is_squeezing = True
                self.target_price = physical_price * 1.5 # Target 50% gain
                print(f"[PredatoryHedgeFund] Squeeze initiated! Target: ${self.target_price:.2f}")
                
        if self.is_squeezing:
            if physical_price >= self.target_price or self.holdings >= 40.0:
                self.is_squeezing = False
                self.is_dumping = True
                print(f"[PredatoryHedgeFund] Target reached! Initiating massive PAPER DUMP to cash out!")
                return 0.0
            buy_amt = 2.0 # Buys 2 Moz per day
            self.holdings += buy_amt
            return buy_amt
            
        if self.is_dumping:
            if self.holdings <= 0:
                self.is_dumping = False
                self.holdings = 0.0
                return 0.0
            dump_amt = min(self.holdings, 4.0) # Sells 4 Moz per day
            self.holdings -= dump_amt
            return -dump_amt # Negative demand (supply)
            
        return 0.0
class OptionsMarketMakers:
    """FIX #8 (Competitor): Continuous gamma exposure instead of binary 80% IV trigger."""
    def __init__(self):
        self.implied_volatility = 0.20 # 20% IV base
        self.hedge_sensitivity = 200.0  # Scaling factor for gamma demand (Moz/year equivalent)
        
    def process_delta_hedge(self, retail_demand, price_momentum):
        # AI Logic: IV expands dynamically with retail FOMO and price momentum
        if retail_demand > (150 / TRADING_DAYS) or price_momentum > 1.2:
            self.implied_volatility = min(1.50, self.implied_volatility + 0.05)
        elif price_momentum < 0.95:
            # FIX #4: Vol Crush — IV drops rapidly when momentum breaks
            self.implied_volatility = max(0.20, self.implied_volatility - 0.10)
        else:
            self.implied_volatility = max(0.20, self.implied_volatility - 0.01)
            
        # Delta hedging unwinds when IV drops below base + 10%
        if self.implied_volatility < 0.30 and price_momentum < 1.0:
            return -10.0 / TRADING_DAYS # Unwind hedges
            
        # FIX #8 (Competitor): Continuous gamma exposure calculation
        # Instead of binary trigger at 80%, gamma demand scales continuously above 40% IV
        gamma_demand = max(0.0, (self.implied_volatility - 0.40) * self.hedge_sensitivity) / TRADING_DAYS
        
        return gamma_demand

class ExchangeMarginControls:
    def __init__(self):
        self.margin_hike_active = False
        self.days_since_hike = 0
        
    def process_day(self, price_momentum, implied_volatility):
        # Exchange intervenes when things get out of control (like 2011 or 1980)
        # We trigger forced liquidation paper dumping
        if price_momentum > 1.4 or implied_volatility > 0.80:
            if not self.margin_hike_active:
                self.margin_hike_active = True
                print("[Exchange] CRITICAL: COMEX raised margin requirements! Forced liquidation triggered!")
        
        if self.margin_hike_active:
            self.days_since_hike += 1
            if self.days_since_hike > 10:
                self.margin_hike_active = False
                self.days_since_hike = 0
            return -50.0 # Dump 50 Moz paper equivalent DAILY to crush the momentum
            
        return 0.0

class BullionBankShorts:
    """FIX #4 (Competitor): Dynamic margin-based forced covering instead of arbitrary $2B threshold."""
    def __init__(self, start_price=25.0):
        self.short_position = 400.0 
        self.risk_tolerance = 100.0
        self.realized_pnl = 0.0
        # Bug Fix: Set initial short entry slightly below current market price
        # so they aren't instantly bankrupt if the simulation starts at $60+
        self.average_short_entry = start_price * 0.90 
        self.maintenance_margin_pct = 0.10  # 10% initial maintenance margin
        
    def check_forced_covering(self, price, macro, force_majeure_active, current_sigma=0.25):
        if force_majeure_active:
            self.short_position = 0 
            return 0
            
        # AI Logic: PnL tracking
        unrealized_loss = (price - self.average_short_entry) * self.short_position
        
        # FIX #4 (Competitor): Dynamic margin requirement scales with volatility
        # When volatility spikes, margin requirements increase, forcing earlier covering
        dynamic_margin_pct = self.maintenance_margin_pct * (1.0 + current_sigma * 2.0)
        margin_required = price * self.short_position * dynamic_margin_pct
        
        # Margin call triggers when unrealized loss exceeds margin capacity
        if unrealized_loss > margin_required:
            self.risk_tolerance -= 5.0
            
        # Allow shorts to regain some composure if the market crashes and provides relief
        if unrealized_loss < 0 or (margin_required > 0 and unrealized_loss < margin_required * 0.8):
            self.risk_tolerance = min(100.0, self.risk_tolerance + 2.0)
            
        if self.risk_tolerance < 20.0:
            # Panic Cover
            # FIX #2: Fast liquidation (up to 50 Moz/day) instead of slow trickle
            cover_panic = min(self.short_position, 50.0) 
            # BUG FIX 2: short_position floored at 0 — cannot go negative
            self.short_position = max(0.0, self.short_position - cover_panic)
            return cover_panic 
            
        # If price drops, they gain confidence and short more
        if price < self.average_short_entry:
            self.risk_tolerance = min(100.0, self.risk_tolerance + 1.0)
            # FIX #2: Slowly mark entry price to market when rebuilding confidence
            self.average_short_entry = self.average_short_entry * 0.99 + price * 0.01
            
        return 0

class SGE_Asian_Arbitrage:
    def __init__(self):
        self.east_west_spread = 0.0 # Premium of SGE over COMEX
        
    def process_drain(self, vault_float, current_price, macro):
        # AI Logic: Drain COMEX only if SGE premium > shipping/insurance costs
        shipping_insurance_cost = 0.50 # 50 cents/oz
        
        # BUG FIX 4: Spread is capped at 5.0 to prevent unbounded daily vault drain
        if macro.brics_announced: self.east_west_spread += 0.05
        if current_price > 50: self.east_west_spread += 0.10
        self.east_west_spread = min(5.0, self.east_west_spread)  # Hard cap
        
        # FIX #7: Spread mean-reverts constantly, not trapped behind a return
        self.east_west_spread = max(0.0, self.east_west_spread - 0.02)
        
        if self.east_west_spread > shipping_insurance_cost and vault_float > 0:
            drain = min(vault_float, (self.east_west_spread * 10.0) / TRADING_DAYS)
            return drain
            
        return 0

class UnallocatedAccountHolders:
    """FIX #2 (Competitor): Bank run logged once per episode, not every tick."""
    def __init__(self):
        self.vault_confidence = 100.0
        self.bank_run_active = False
        self._bank_run_logged = False  # FIX #2: Prevent log spam
        
    def check_bank_run(self, vault_float):
        # AI Logic: Confidence drops as float drops
        if vault_float < 100:
            self.vault_confidence -= 1.0
        # BUG FIX 5: Confidence recovers when vault refills — bank run is not permanent
        elif vault_float > 200:
            self.vault_confidence = min(100.0, self.vault_confidence + 0.5)
            if self.bank_run_active and self.vault_confidence > 50.0:
                self.bank_run_active = False  # Bank run ends when confidence recovers
                self._bank_run_logged = False  # Reset log flag for next episode
                log_event("Demand", "Bank run ended, confidence recovered", confidence=self.vault_confidence)
            
        if self.vault_confidence < 20.0 and vault_float > 0:
            self.bank_run_active = True
            if not self._bank_run_logged:  # FIX #2: Log ONCE per episode
                log_event("Demand", "Bank Run on unallocated metal", confidence=self.vault_confidence, vault=vault_float)
                self._bank_run_logged = True
            return True # Trigger massive physical delivery demands (Bank Run)
        return self.bank_run_active  # Sustain run until confidence recovers

class CentralBankReserve(Stakeholder):
    def process_day(self, price, macro):
        if macro.current_year < 2027: return 0
        # AI Logic: Central banks slowly accumulate silver as a strategic solar reserve
        # 50 Moz per year = ~0.198 Moz/day
        return 50.0 / TRADING_DAYS

class GSR_Gravity:
    def __init__(self):
        self.liquidity_momentum = 1.0
        
    def process_day(self, silver_price, macro):
        # AI Logic: GSR gravity gets stronger if liquidity is tight
        current_gsr = macro.gold_price / silver_price
        
        if macro.fed_funds_rate > 5.0: self.liquidity_momentum = 1.05 # Tight liquidity hurts silver
        else: self.liquidity_momentum = 0.95 # Loose liquidity helps silver outpace gold
        
        if current_gsr > (85.0 * self.liquidity_momentum):
            return 5.0 / TRADING_DAYS # Add 5 Moz/year of physical demand
        elif current_gsr < (40.0 / self.liquidity_momentum):
            return -5.0 / TRADING_DAYS # Add 5 Moz/year of physical supply
        return 0.0
        
class JPM_House_Account:
    def __init__(self, vault_float=350.0):
        self.vault_float = vault_float
        self.dumping = False

    def process_day(self, price, macro=None):
        dump_amount = 0.0
        threshold = macro.config.start_silver_price * macro.config.thresholds.jpm_dump_multiplier if (macro and macro.config) else 100.0
        if price > threshold and self.vault_float > 0:
            self.dumping = True
            dump_amount = min(5.0, self.vault_float) # Dump 5 Moz per day to crush the price
            self.vault_float -= dump_amount
        else:
            self.dumping = False
        return dump_amount

class Billionaire_Family_Offices:
    def __init__(self, vault_float=400.0):
        self.vault_float = vault_float
        self.is_buying = False
        self.is_selling = False

    def process_day(self, price, macro, current_gsr):
        net_flow = 0.0
        dip_buy_threshold = 15.0 * macro.m2_inflation_index
        
        # User Domain Expertise: Billionaires will buy everything if silver is dirt cheap
        if price < dip_buy_threshold:
            self.is_buying = True
            net_flow = 5.0 # Drain 5 Moz/day
            self.vault_float += net_flow
            return net_flow
            
        # Buy during extreme geopolitical tension
        if macro.geopolitical_tension_index > 80:
            self.is_buying = True
            net_flow = 2.0 # Drain 2 Moz/day
            self.vault_float += net_flow
        else:
            self.is_buying = False
            
        # Sell if GSR drops below 30 (trading silver for gold)
        if current_gsr < 30.0 and self.vault_float > 0:
            self.is_selling = True
            sell_amount = min(3.0, self.vault_float) # Supply 3 Moz/day
            self.vault_float -= sell_amount
            net_flow = -sell_amount
        else:
            self.is_selling = False
            
        return net_flow # Positive = Demand/Drain, Negative = Supply

class Retail_Mattress_Hoard:
    def __init__(self, vault_float=2000.0):
        self.vault_float = vault_float
        self.melting = False
        self.all_time_high = 0.0

    def process_day(self, price, macro=None):
        melt_supply = 0.0
        
        # Track ATH
        if price > self.all_time_high:
            self.all_time_high = price
            
        # User Feedback Fix: Aam janta doesn't melt at a flat $60.
        # They only melt during a Parabolic FOMO event (price is 4x the inflation-adjusted norm)
        # AND when price is near an All-Time High.
        base_norm = 30.0 * (macro.m2_inflation_index if macro else 1.0)
        
        if price > (base_norm * 4.0) and price >= (self.all_time_high * 0.9) and self.vault_float > 0:
            self.melting = True
            melt_supply = min(10.0, self.vault_float) # Massive 10 Moz/day scrap wave
            self.vault_float -= melt_supply
        else:
            self.melting = False
        return melt_supply

class Global_ETF_Holdings:
    def __init__(self, vault_float=1270.0):
        self.vault_float = vault_float
        self.is_drained = False

    def process_day(self, price, price_momentum):
        # The user specified that ETFs should act purely as an emergency reserve
        # and not casually trade daily. They only get raided when COMEX is dying.
        if self.vault_float <= 0:
            self.is_drained = True
            
        return 0.0

