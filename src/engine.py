import math
import random
import copy
from collections import defaultdict
from config import TRADING_DAYS, FUTURE_2026_STATE, SCENARIOS_OVERRIDE
from logger import log_event
from macro import LiveDataOracle, MacroEnvironment
from stakeholders import *
from exchanges import COMEX_Exchange, LBMA_Exchange, India_IIBX_Vault, SGE_Asian_Arbitrage

class SimulationEngine:
    def __init__(self, mode="future", config=FUTURE_2026_STATE, years=10, seed=None, jitter=0.10):
        if seed is not None:
            random.seed(seed)
            
        self.config = copy.deepcopy(config)
        if jitter > 0:
            self.config.apply_jitter(jitter)
            
        self.years = years
        self.total_sim_days = TRADING_DAYS * years
        
        self.oracle = LiveDataOracle(mode=mode, config=self.config)
        
        # FIX: The oracle fetches live prices, but config.start_silver_price (used by stakeholders for thresholds)
        # remains 0.0 in FUTURE_2026_STATE. We must update the config with the actual fetched prices!
        if self.config.start_silver_price == 0.0:
            self.config.start_silver_price = self.oracle.silver_price
        if self.config.start_gold_price == 0.0:
            self.config.start_gold_price = self.oracle.gold_price
            
        self.macro = MacroEnvironment(
            config=self.config,
            gold_price=self.oracle.gold_price, 
            fed_rate=self.oracle.fed_rate, 
            dxy=self.oracle.dxy, 
            copper=self.oracle.copper, 
            start_year=self.config.start_year
        )
        
        self._init_stakeholders()
        self._init_dark_inventory()
        self._init_exchanges()
        
        self.squeeze_triggered = False
        self.physical_price = self.oracle.silver_price
        self.paper_price = self.oracle.silver_price
        
        self.current_sigma = 0.25
        self.prev_day_price = self.oracle.silver_price
        self.dt = 1.0 / TRADING_DAYS
        
        self.stats = defaultdict(int)
        self.daily_data = []
        self.ACTIVE_DELIVERY_MONTHS = {3, 5, 7, 9, 12}
        
    def _init_stakeholders(self):
        c = self.config
        self.supply_primary = PrimaryMiners("Primary", c.primary_mine)
        self.supply_byproduct = ByproductMiners("Byproduct", c.byproduct_mine)
        self.supply_scrap = ScrapRefiners("Scrap", c.scrap_refiners)
        self.supply_ewaste = EWasteRecyclers("EWaste", c.ewaste)
        self.supply_hoarders = DeepPrivateHoarders("Hoarders", 0)
        self.supply_smugglers = BlackMarketSmugglers("BlackMarket", 5.0)
        self.refinery_bottleneck = SmelterRefineryBottleneck(500.0)
        
        self.demand_solar = SolarPV("Solar", c.solar_pv)
        self.demand_defense = DefenseAerospace("Defense", c.defense)
        self.demand_ev = EV_Auto("EV", c.ev_auto)
        self.demand_ai = Tech_AI("AI", c.ai_tech)
        self.demand_jewelry = JewelrySilverware("Jewelry", c.jewelry)
        self.demand_other = OtherIndustrial("Other", c.other_demand)
        self.demand_retail = RetailInvestors("Retail", c.retail)
        
        self.gov_india = Gov_India()
        self.gov_china = Gov_China("China", 20.0)
        self.gov_usa = Gov_USA()
        self.gov_uk = Gov_UK()
        self.cb_hoarders = Gov_CentralBanks("CentralBanks", 0.0)
        
        self.whale_syndicate = WhaleSyndicate()
        self.predatory_hedge_fund = PredatoryHedgeFund()
        self.options_mm = OptionsMarketMakers()
        self.bullion_bank_shorts = BullionBankShorts(self.config.start_silver_price)
        self.sge_arb = SGE_Asian_Arbitrage()
        self.unallocated_holders = UnallocatedAccountHolders()
        self.cb_reserve = CentralBankReserve("CentralBank", 50.0)
        self.gsr_gravity = GSR_Gravity()
        self.exchange_margins = ExchangeMarginControls()
        
    def _init_dark_inventory(self):
        c = self.config
        self.jpm = JPM_House_Account(vault_float=c.vaults.jpm_house)
        self.billionaire_syndicate = Billionaire_Family_Offices(vault_float=c.vaults.billionaire_vault)
        self.retail_melt = Retail_Mattress_Hoard(vault_float=c.vaults.retail_mattress)
        self.etf_holdings = Global_ETF_Holdings(vault_float=c.vaults.etf_holdings)

    def _init_exchanges(self):
        c = self.config
        self.comex = COMEX_Exchange(initial_float=c.vaults.comex_eligible)
        self.lbma = LBMA_Exchange(vault_start=c.vaults.lbma_vault, unallocated_start=c.vaults.lbma_unallocated)
        self.india_vault = India_IIBX_Vault(capacity=c.vaults.india_capacity, inventory_start=c.vaults.india_inventory)

    def run(self, return_full=False):
        for day in range(self.total_sim_days):
            self.macro.simulate_day()
            
            # Track macro events for stats
            if getattr(self.macro, 'ai_bubble_burst', False): self.stats["ai_bubble_burst_count"] = 1
            if getattr(self.macro, 'retail_capitulation', False): self.stats["retail_cap_count"] = 1
            if self.macro.mining_strike_active: self.stats["mining_strike_count"] = 1
            if self.macro.refinery_energy_crisis: self.stats["energy_crisis_count"] = 1
            if self.demand_solar.substitution_triggered: self.stats["substitution_trigger_count"] = 1
            if getattr(self.macro, 'cbdc_launched', False): self.stats["cbdc_count"] = 1
            
            total_supply = self._process_supply()
            lbma_demand, comex_demand = self._process_demand(total_supply)
            
            # EXTREME INVARIANT CHECK: No negative supply or NaN allowed
            assert total_supply >= 0, f"BUG: Negative supply generated: {total_supply}"
            assert not math.isnan(total_supply) and not math.isnan(lbma_demand)
            
            self._process_efp_and_emergencies(day, comex_demand)
            self._update_price(lbma_demand, comex_demand, total_supply)
            
            assert self.physical_price > 0, f"BUG: Price dropped to {self.physical_price}"
            assert not math.isnan(self.physical_price), "BUG: Price became NaN!"
            
            self._update_exchanges_and_stats(day, lbma_demand, comex_demand, total_supply)
            
            # VAULT INVARIANT CHECKS
            assert self.comex.vault_float >= 0, "BUG: COMEX float dropped below zero!"
            assert self.lbma.vault_float >= 0, "BUG: LBMA float dropped below zero!"
            
        self.stats["end_price"] = self.physical_price
        self.stats["end_paper_price"] = self.paper_price
        return self.daily_data if return_full else [], self.stats

    def _process_supply(self):
        s_prim = self.supply_primary.process_day(self.physical_price, self.macro)
        s_by = self.supply_byproduct.process_day(self.physical_price, self.macro)
        mine_supply = s_prim + s_by
                      
        hoarder_supply = self.supply_hoarders.process_day(self.physical_price, self.macro)
        if self.supply_hoarders.total_hoard <= 0 and self.physical_price > (250 * self.macro.m2_inflation_index):
            self.stats["hoard_depletion_count"] += 1
            
        jpm_dump = self.jpm.process_day(self.physical_price, self.macro)
        if self.jpm.dumping: self.stats["jpm_dump_count"] += 1
            
        retail_melt = self.retail_melt.process_day(self.physical_price, self.macro)
        if self.retail_melt.melting: self.stats["retail_melt_count"] += 1
            
        s_scrap = self.supply_scrap.process_day(self.physical_price, self.macro)
        s_ewaste = self.supply_ewaste.process_day(self.physical_price, self.macro)
        s_smuggle = self.supply_smugglers.process_day(self.physical_price, self.macro)
        secondary_raw = (s_scrap + s_ewaste + hoarder_supply + s_smuggle + retail_melt)
                         
        if self.supply_scrap.scrap_fatigue_days > (3 * TRADING_DAYS):
            self.stats["scrap_fatigue_count"] += 1
            
        processed_sec = self.refinery_bottleneck.process_supply(secondary_raw, self.physical_price, self.macro)
        
        self.trace_data = {
            "sup_primary": s_prim, "sup_byprod": s_by, "sup_hoard": hoarder_supply,
            "sup_scrap": s_scrap, "sup_ewaste": s_ewaste, "sup_smuggle": s_smuggle,
            "jpm_dump": jpm_dump, "retail_melt": retail_melt
        }
        return mine_supply + processed_sec + jpm_dump
        
    def _process_demand(self, total_supply):
        bank_panic_cover = self.bullion_bank_shorts.check_forced_covering(self.physical_price, self.macro, self.comex.force_majeure_active, current_sigma=self.current_sigma)
        if bank_panic_cover > 0: self.stats["short_squeeze_count"] += 1
        
        d_jewel = self.demand_jewelry.process_day(self.physical_price, self.macro)
        d_other = self.demand_other.process_day(self.physical_price, self.macro)
        
        raw_jewelry = d_jewel + d_other
        india_share, row_jewelry = self.gov_india.process_jewelry_demand(self.physical_price, raw_jewelry, self.macro)
        regulated_jewelry = india_share + row_jewelry
        
        if self.gov_india.import_duty_level > 0: self.stats["india_duty_trigger_count"] += 1
        self.macro.india_duty_active = self.gov_india.import_duty_level > 5.0
        
        d_solar = self.demand_solar.process_day(self.physical_price, self.macro)
        d_def = self.demand_defense.process_day(self.physical_price, self.macro)
        d_ev = self.demand_ev.process_day(self.physical_price, self.macro)
        d_ai = self.demand_ai.process_day(self.physical_price, self.macro)
        d_cb = self.cb_hoarders.process_day(self.physical_price, self.macro)
        
        base_demand = d_solar + d_def + d_ev + d_ai + regulated_jewelry + d_cb
                       
        retail_daily = self.demand_retail.process_day(self.physical_price, self.macro)
        base_demand -= india_share
        
        india_domestic, lbma_drain_iibx = self.india_vault.process_demand(india_share, self.macro)
        india_unfulfilled = india_share - india_domestic
        base_demand += india_unfulfilled
        
        if self.india_vault.is_empty: self.stats["india_vault_empty_count"] += 1
        china_daily = self.gov_china.process_day(self.physical_price, self.macro)
        
        if hasattr(self, 'trace_data'):
            self.trace_data.update({
                "dem_solar": d_solar, "dem_defense": d_def, "dem_ev": d_ev, "dem_ai": d_ai,
                "dem_jewelry": d_jewel, "dem_retail": retail_daily, "dem_other": d_other,
                "dem_india_share": india_share, "dem_china": china_daily, "bank_panic": bank_panic_cover,
                "dem_cb_hoarders": d_cb
            })
        
        usa_dpa = self.gov_usa.check_defense_production_act(self.comex.vault_float + self.lbma.vault_float)
        if usa_dpa > 0: self.stats["dpa_trigger_count"] += 1
        
        sge_drain = self.sge_arb.process_drain(self.lbma.vault_float, self.physical_price, self.macro)
        if self.gov_usa.export_ban_active: sge_drain = 0.0
        
        whale_acc = 0.0 if SCENARIOS_OVERRIDE["no_whales"] else self.whale_syndicate.process_accumulation(self.lbma.vault_float, self.bullion_bank_shorts.short_position)
        if whale_acc > 0: self.stats["whale_buy_count"] += 1
        
        hedge_fund_squeeze = self.predatory_hedge_fund.process_attack(self.comex.vault_float, self.physical_price, self.macro)
        if self.predatory_hedge_fund.is_squeezing: self.stats["predatory_attack_count"] += 1
        
        current_gsr = self.oracle.gold_price / self.physical_price if self.physical_price > 0 else 80.0
        bill_flow = self.billionaire_syndicate.process_day(self.physical_price, self.macro, current_gsr)
        if self.billionaire_syndicate.is_buying: self.stats["billionaire_raid_count"] += 1
        
        if bill_flow < 0:
            total_supply += abs(bill_flow) # Need to propagate this up or just handle it here
            self.dynamic_supply_add = abs(bill_flow)
            bill_flow = 0.0
        else:
            self.dynamic_supply_add = 0.0
            
        cb_acc = self.cb_reserve.process_day(self.physical_price, self.macro)
        hoarder_acc = (10.0 / TRADING_DAYS) if self.macro.geopolitical_tension_index > 80 else 0.0
        
        price_mom = self.physical_price / self.prev_day_price if self.prev_day_price > 0 else 1.0
        self.prev_day_price = self.physical_price
        
        etf_flow = self.etf_holdings.process_day(self.physical_price, price_mom)
        if self.etf_holdings.is_drained: self.stats["etf_depletion_count"] += 1
        if etf_flow < 0:
            self.dynamic_supply_add += abs(etf_flow)
            
        opt_hedge = self.options_mm.process_delta_hedge(retail_daily, price_mom)
        margin_liquidation = self.exchange_margins.process_day(price_mom, self.options_mm.implied_volatility)
        
        if getattr(self.comex, 'margin_hike_active', False) and self.comex.force_majeure_active:
            retail_daily *= 0.10
            opt_hedge *= 0.10
            
        gsr_demand = self.gsr_gravity.process_day(self.physical_price, self.macro)
        
        if hasattr(self, 'trace_data'):
            self.trace_data.update({
                "usa_dpa": usa_dpa, "sge_drain": sge_drain, "whale_acc": whale_acc,
                "hedge_fund_attack": hedge_fund_squeeze, "billionaire_net_flow": bill_flow,
                "etf_net_flow": etf_flow, "opt_hedge": opt_hedge, "margin_liq": margin_liquidation,
                "cb_reserve_acc": cb_acc, "geopol_hoarder_acc": hoarder_acc, "gsr_algo_demand": gsr_demand,
                # Add boolean flags as 1/0 for easy analysis
                "flag_export_ban": 1 if self.macro.export_ban_active else 0,
                "flag_base_metal_recession": 1 if self.macro.base_metal_recession_active else 0,
                "flag_comex_default": 1 if getattr(self.comex, 'defaulted', False) else 0,
                "flag_lbma_default": 1 if getattr(self.lbma, 'defaulted', False) else 0,
                "flag_force_majeure": 1 if self.comex.force_majeure_active else 0,
                "flag_india_empty": 1 if self.india_vault.is_empty else 0
            })
            
        lbma_demand = (base_demand + (retail_daily * 0.5) + china_daily + lbma_drain_iibx + 
                       sge_drain + usa_dpa + self.macro.brics_vault_drain_daily + whale_acc + cb_acc + 
                       hoarder_acc + bank_panic_cover + bill_flow + max(0, etf_flow) + gsr_demand)
                       
        if self.physical_price > 100.0:
            destruction_factor = 1.0 - min(0.95, ((self.physical_price - 100.0) / 100.0) * 0.20)
            lbma_demand *= destruction_factor
            
        comex_demand = (retail_daily * 0.5) + hedge_fund_squeeze + opt_hedge + margin_liquidation
        
        if self.exchange_margins.margin_hike_active: self.stats["margin_hikes_count"] += 1
        
        if self.macro.base_metal_recession_active: self.stats["base_metal_shock_count"] += 1
        if self.macro.export_ban_active: self.stats["export_ban_count"] += 1
        if self.macro.defense_stockpile_active: self.stats["defense_stockpile_count"] += 1
        if self.predatory_hedge_fund.is_squeezing: self.stats["predatory_attack_count"] += 1
        
        return lbma_demand, comex_demand

    def _process_efp_and_emergencies(self, day, comex_demand):
        actual_day = day + 155
        current_month = ((actual_day // 21) % 12) + 1
        current_day_of_month = (actual_day % 21) + 1
        next_month = (current_month % 12) + 1
        
        if next_month in self.ACTIVE_DELIVERY_MONTHS and current_day_of_month >= 11:
            if self.comex.vault_float < 15.0:
                lease_spike = max(0, (15.0 - self.comex.vault_float) / 2.0)
                self.comex_demand_add = lease_spike
            else:
                self.comex_demand_add = 0.0
        else:
            self.comex_demand_add = 0.0

    def _update_price(self, lbma_demand, comex_demand, base_supply):
        total_supply = base_supply + self.dynamic_supply_add
        comex_demand += self.comex_demand_add
        
        actual_deficit = (lbma_demand - total_supply) + comex_demand
        total_vaults = self.comex.vault_float + self.lbma.vault_float
        
        raw_drift = actual_deficit / (total_vaults + 50.0)
        if raw_drift > 0:
            drift = min(0.15, raw_drift * 1.5)
        else:
            # FIX: Allow downward drift up to 50% per year during massive oversupply/post-squeeze crash.
            # Previously this was erroneously max(-0.05, ...) which capped crashes at a tiny 5% per year!
            drift = max(-0.50, math.tanh(raw_drift) * 0.5)
            
        aisc_floor = 30.0 * self.macro.m2_inflation_index
        if self.physical_price < aisc_floor and actual_deficit < 0:
            drift += 0.20
            
        margin_impact = False
        target_sigma = 0.25
        if self.squeeze_triggered: 
            target_sigma = 0.70
        elif margin_impact: 
            target_sigma = 0.55
        self.current_sigma = self.current_sigma * 0.95 + target_sigma * 0.05
        
        gbm_mult = math.exp((drift - 0.5 * self.current_sigma**2) * self.dt + self.current_sigma * math.sqrt(self.dt) * random.gauss(0,1))
        
        if gbm_mult > 1.07:
            self.stats["circuit_breaker_count"] += 1
            gbm_mult = 1.07
        elif gbm_mult < 0.93:
            self.stats["circuit_breaker_count"] += 1
            gbm_mult = 0.93
            
        if gbm_mult > 1.10:
            self.stats["high_price_spikes_count"] += 1
            
        self.physical_price = max(0.10, self.physical_price * gbm_mult)
        
        paper_drift = drift * 0.8
        paper_sigma = self.current_sigma * 0.7
        if self.comex.force_majeure_active:
            paper_drift = drift * 0.05
            paper_sigma = self.current_sigma * 0.1
        paper_gbm = math.exp((paper_drift - 0.5 * paper_sigma**2) * self.dt + paper_sigma * math.sqrt(self.dt) * random.gauss(0,1))
        
        # Decoupling: If COMEX defaults, the paper price is frozen and irrelevant. Physical continues parabolic.
        if not getattr(self.comex, 'defaulted', False):
            self.paper_price = max(0.10, self.paper_price * paper_gbm)

    def _update_exchanges_and_stats(self, day, lbma_demand, comex_demand, base_supply):
        total_supply = base_supply + self.dynamic_supply_add
        comex_demand += self.comex_demand_add
        
        total_demand = lbma_demand + comex_demand
        if total_demand > 0:
            lbma_supply_alloc = total_supply * (lbma_demand / total_demand)
            comex_supply_alloc = total_supply * (comex_demand / total_demand)
        else:
            lbma_supply_alloc = total_supply
            comex_supply_alloc = 0.0
            
        lbma_deficit = lbma_demand - lbma_supply_alloc
        comex_deficit = comex_demand - comex_supply_alloc
        
        if self.comex.force_majeure_active:
            comex_deficit = min(0.0, comex_deficit)
            self.stats["fm_days"] += 1
                
        if self.comex.vault_float - comex_deficit < 0:
            self.comex.vault_float = 0
            if not self.comex.defaulted:
                self.comex.defaulted = True
                self.stats["squeeze_count"] += 1
                self.stats["comex_default_count"] += 1
            if not self.squeeze_triggered:
                self.squeeze_triggered = True
                self.stats["squeeze_days"] = 0
            else:
                self.stats["squeeze_days"] += 1
                if self.stats["squeeze_days"] < 30 and random.random() < 0.10:
                    self.physical_price *= random.uniform(1.10, 1.25)
        else:
            if comex_deficit < 0:
                self.comex.vault_float += abs(comex_deficit)
            else:
                self.comex.vault_float -= comex_deficit
                
        if self.lbma.vault_float - lbma_deficit < 0:
            self.lbma.vault_float = 0
            if not self.lbma.defaulted:
                self.lbma.defaulted = True
                self.stats["lbma_default_count"] += 1
                self.physical_price *= 2.0
        else:
            if lbma_deficit < 0:
                self.lbma.vault_float += abs(lbma_deficit)
            else:
                self.lbma.vault_float -= lbma_deficit
                
        if self.comex.defaulted and self.lbma.defaulted and not self.comex.force_majeure_active:
            if self.gov_uk.check_lbma_bailout(self.lbma.vault_float):
                self.comex.force_majeure_active = True
                self.stats["force_majeure_count"] += 1
                self.stats["decoupled_count"] += 1
                
        if self.squeeze_triggered:
            if "peak_price" not in self.stats or self.physical_price > self.stats["peak_price"]:
                self.stats["peak_price"] = self.physical_price
        
        if self.physical_price > self.stats.get("max_price", 0):
            self.stats["max_price"] = self.physical_price
        if "min_price" not in self.stats or self.physical_price < self.stats["min_price"]:
            self.stats["min_price"] = self.physical_price
            
        actual_day = day + 155
        daily_record = {
            "day_index": day + 1,
            "year": 2026 + (actual_day // 252),
            "month": ((actual_day // 21) % 12) + 1,
            "day_of_month": (actual_day % 21) + 1,
            "avg_physical": self.physical_price,
            "avg_paper": self.paper_price,
            "supply": total_supply,
            "demand": lbma_demand + comex_demand,
            "vault": self.comex.vault_float + self.lbma.vault_float
        }
        if hasattr(self, 'trace_data'):
            daily_record.update(self.trace_data)
        self.daily_data.append(daily_record)

def run_simulation_core(*args, **kwargs):
    return_full = kwargs.pop('return_full', False)
    engine = SimulationEngine(*args, **kwargs)
    return engine.run(return_full=return_full)
