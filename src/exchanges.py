import random
from config import TRADING_DAYS
from logger import log_event

class COMEX_Exchange:
    def __init__(self, initial_float):
        self.vault_float = initial_float # Moz (Registered)
        self.eligible_float = 200.0 # Moz
        self.defaulted = False
        self.force_majeure_active = False
        
    def move_eligible_to_registered(self, amount, price):
        if price > 50.0 and self.eligible_float > amount:
            self.eligible_float -= amount
            self.vault_float += amount
            log_event("Exchange", "Eligible metal moved to Registered", amount=amount, price=price)
            return True
        return False

class LBMA_Exchange:
    def __init__(self, vault_start=800.0, unallocated_start=1000.0):
        self.vault_float = vault_start
        self.unallocated_claims = unallocated_start
        self.defaulted = False
        self.bank_run_active = False
        
    def check_bank_run(self, price, geo_tension):
        if not self.bank_run_active and (price > 40.0 or geo_tension > 80):
            if random.random() < (0.05 / TRADING_DAYS):
                self.bank_run_active = True
                log_event("Exchange", "Bank run on LBMA unallocated!")
        
        if self.bank_run_active:
            drain = min(self.vault_float, 20.0) 
            self.vault_float -= drain
            self.unallocated_claims = max(0.0, self.unallocated_claims - drain)
            return drain
        return 0

class India_IIBX_Vault:
    def __init__(self, capacity=145.0, inventory_start=50.0):
        self.capacity = capacity
        self.current_inventory = inventory_start
        self.is_empty = False
        
    def process_demand(self, local_demand_daily, macro):
        # Premium/Discount mechanics
        if self.current_inventory < 10.0:
            self.is_empty = True
        else:
            self.is_empty = False
            
        unfulfilled = 0
        if local_demand_daily > self.current_inventory:
            fulfilled_locally = self.current_inventory
            self.current_inventory = 0
        else:
            fulfilled_locally = local_demand_daily
            self.current_inventory -= local_demand_daily
            
        lbma_drain = 0
        if not macro.export_ban_active and not macro.supply_chain_blockade:
            lbma_drain = min(self.capacity - self.current_inventory, 2.0) # Up to 2 Moz/day shipped from LBMA
            self.current_inventory += lbma_drain
            
        return fulfilled_locally, lbma_drain

class SGE_Asian_Arbitrage:
    def __init__(self):
        self.east_west_spread = 0.0 # Premium of SGE over COMEX
        
    def process_drain(self, vault_float, current_price, macro):
        # AI Logic: Drain COMEX/LBMA only if SGE premium > shipping/insurance costs
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
