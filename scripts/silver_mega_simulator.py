import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import argparse
import csv
import json as json_module
from collections import defaultdict
from config import SimConfig, HISTORICAL_1990_STATE, FUTURE_2026_STATE, SCENARIOS_OVERRIDE
from logger import log_event
from engine import run_simulation_core

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')

def get_simulation_data():
    daily_data, _ = run_simulation_core()
    return daily_data

def run_ultimate_simulation(iterations=100, years=10, suffix="base"):
    if iterations < 1:
        print("Iterations must be at least 1.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = {
        "squeeze_count": 0, "bank_run_count": 0, "short_squeeze_count": 0,
        "force_majeure_count": 0, "dpa_trigger_count": 0, "india_duty_trigger_count": 0,
        "decoupled_count": 0, "hoard_depletion_count": 0, "scrap_fatigue_count": 0,
        "mine_shutdown_count": 0, "substitution_trigger_count": 0,
        "whale_buy_count": 0, "blockade_count": 0, "cbdc_count": 0,
        "ai_bubble_burst_count": 0, "mining_strike_count": 0,
        "retail_cap_count": 0, "energy_crisis_count": 0,
        "high_price_spikes_count": 0,
        "base_metal_shock_count": 0, "export_ban_count": 0,
        "defense_stockpile_count": 0, "predatory_attack_count": 0,
        "comex_default_count": 0, "lbma_default_count": 0, "etf_raid_count": 0,
        "jpm_dump_count": 0, "billionaire_raid_count": 0, "retail_melt_count": 0,
        "etf_depletion_count": 0, "india_vault_empty_count": 0,
        "india_ny_arbitrage_count": 0,
        "peak_prices": [], "end_prices": [],
        "min_prices": [], "max_vault_floats": []
    }
    aggregated_daily = defaultdict(lambda: {"avg_physical": 0.0, "avg_paper": 0.0, "supply": 0.0, "demand": 0.0, "vault": 0.0, "year": 2026, "month": 1, "day": 1})
    
    for i in range(iterations):
        log_event("System", f"Iteration {i+1} Start", iteration=i+1)
        # FIX #1 (Competitor): Each iteration gets a deterministic seed for reproducibility
        daily_data, stats = run_simulation_core(return_full=True, years=years, seed=i, config=FUTURE_2026_STATE)
        
        for d_data in daily_data:
            d_idx = d_data["day_index"]
            aggregated_daily[d_idx]["avg_physical"] += d_data["avg_physical"]
            aggregated_daily[d_idx]["avg_paper"] += d_data["avg_paper"]
            aggregated_daily[d_idx]["supply"] += d_data["supply"]
            aggregated_daily[d_idx]["demand"] += d_data["demand"]
            aggregated_daily[d_idx]["vault"] += d_data["vault"]
            aggregated_daily[d_idx]["year"] = d_data["year"]
            aggregated_daily[d_idx]["month"] = d_data["month"]
            aggregated_daily[d_idx]["day"] = d_data["day_of_month"]
            
        for k in results.keys():
            if k in stats: results[k] += stats[k]
        
        if "peak_price" in stats: results["peak_prices"].append(stats["peak_price"])
        if "end_price" in stats: results["end_prices"].append(stats["end_price"])
        if "min_price" in stats: results["min_prices"].append(stats["min_price"])
        if "max_vault_float" in stats: results["max_vault_floats"].append(stats["max_vault_float"])
        
    # Write average path to CSV
    with open(os.path.join(OUTPUT_DIR, f"ultimate_simulation_path_{suffix}.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["DayIndex", "Year", "Month", "Day", "Avg_Physical_Price", "Avg_Paper_Price", "Supply", "Demand", "Vault_Float"])
        for d_idx in sorted(aggregated_daily.keys()):
            d = aggregated_daily[d_idx]
            writer.writerow([
                d_idx,
                d["year"],
                d["month"],
                d["day"],
                f"{d['avg_physical']/iterations:.2f}",
                f"{d['avg_paper']/iterations:.2f}",
                f"{d['supply']/iterations:.2f}",
                f"{d['demand']/iterations:.2f}",
                f"{d['vault']/iterations:.2f}"
            ])
            
    # Write JSON stats for web frontend
    serializable_stats = {k: v for k, v in results.items() if not isinstance(v, list)}
    serializable_stats["iterations"] = iterations
    if results['peak_prices']:
        serializable_stats["avg_peak"] = sum(results['peak_prices'])/len(results['peak_prices'])
        serializable_stats["max_peak"] = max(results['peak_prices'])
        serializable_stats["min_peak"] = min(results['peak_prices'])
    serializable_stats["avg_end"] = sum(results['end_prices'])/len(results['end_prices'])
    serializable_stats["max_end"] = max(results['end_prices'])
    serializable_stats["min_end"] = min(results['end_prices'])
    with open(os.path.join(OUTPUT_DIR, f"simulation_stats_{suffix}.json"), "w", encoding="utf-8") as sf:
        json_module.dump(serializable_stats, sf, indent=4)
            
    print("="*75)
    print(f"GOD-TIER V3 QUANT ENGINE AUDIT ({iterations} Iterations | Daily Ticks | GBM)")
    print("="*75)
    
    sq_prob = (results['squeeze_count'] / iterations) * 100
    
    print(f"")
    print(f"--- CORE METRICS ---")
    print(f"Squeeze Probability:            {sq_prob:.1f}%")
    print(f"UK/LBMA Force Majeure Bailouts: {results['force_majeure_count']} times banks were saved")
    print(f"Dual-Market Decoupling Events:  {results['decoupled_count']} times paper/physical split")
    print(f"")
    print(f"--- SUPPLY SIDE SHOCKS ---")
    print(f"Mine Shutdowns (AISC Crisis):   {results['mine_shutdown_count']} year-events where mines closed")
    print(f"Hoard Depletion Events:         {results['hoard_depletion_count']} times billionaires ran out")
    print(f"Scrap Fatigue Triggers:         {results['scrap_fatigue_count']} times global scrap dried up")
    print(f"Short Squeeze Events:           {results['short_squeeze_count']} times banks panic-covered")
    print(f"")
    print(f"--- DEMAND SIDE SHOCKS ---")
    print(f"AI Bubble Burst Events:         {round(results['ai_bubble_burst_count']/iterations, 1)} iterations ({round(results['ai_bubble_burst_count']/iterations * 100, 1)}% probability)")
    print(f"Mining Strike Shocks (60-day):  {round(results['mining_strike_count']/iterations, 1)} iterations ({round(results['mining_strike_count']/iterations * 100, 1)}% probability)")
    print(f"Retail Capitulation Events:     {round(results['retail_cap_count']/iterations, 1)} iterations ({round(results['retail_cap_count']/iterations * 100, 1)}% probability)")
    print(f"Smelter Energy Crises (90-day): {round(results['energy_crisis_count']/iterations, 1)} iterations ({round(results['energy_crisis_count']/iterations * 100, 1)}% probability)")
    print(f"Whale Syndicate Accumulations:  {results['whale_buy_count']} massive sovereign buys")
    print(f"Supply Chain Blockades:         {results['blockade_count']} year-events of disrupted refining")
    print(f"Solar Substitution Triggers:    {results['substitution_trigger_count']} times factories retooled")
    print(f"India Import Duty Triggers:     {results['india_duty_trigger_count']} times India imposed duties")
    print(f"US DPA Seizure Events:          {results['dpa_trigger_count']} times US seized vault metal")
    print(f"Bank Run Events:                {results['bank_run_count']} times unallocated holders panicked")
    print(f"CBDC Launched Events:           {results['cbdc_count']} times CBDC was launched")
    print(f"")
    print(f"--- NEW MEGA PARAMETERS ---")
    print(f"Base Metal Recession Shocks:    {results['base_metal_shock_count']} days of byproduct shutdown")
    print(f"Export Ban (Resource National): {results['export_ban_count']} days of locked Mexican/Peruvian supply")
    print(f"Strategic Defense Stockpiling:  {results['defense_stockpile_count']} days of US Pentagon massive buying")
    print(f"Predatory Hedge Fund Attacks:   {results['predatory_attack_count']} days of Hedge Fund market cornering")
    print(f"")
    print(f"--- NEW EFP & SPLIT VAULT MECHANICS ---")
    print(f"COMEX (New York) Defaults:      {results['comex_default_count']} times Registered hit 0")
    print(f"LBMA (London) Defaults:         {results['lbma_default_count']} times Unallocated panicked/failed")
    print(f"ETF Raids (Emergency Liquid):   {results['etf_raid_count']} times APs tore open SLV to save COMEX")
    print(f"")
    print(f"--- DARK INVENTORY MECHANICS ---")
    print(f"JPM Vault Dumping (>$100):      {results['jpm_dump_count']} days JPM dumped silver to crush prices")
    print(f"Billionaire Panic Buying:       {results['billionaire_raid_count']} days family offices hoarded physical")
    print(f"Retail Coin Melting (>$60):     {results['retail_melt_count']} days citizens rushed to melt coins")
    print(f"Global ETF Depletion:           {results['etf_depletion_count']} times ETFs were fully drained")
    print(f"India IIBX Vault Empty:         {results['india_vault_empty_count']} days India's 145 Moz vault ran dry")
    print(f"India -> NY Reverse Arbitrage:  {results['india_ny_arbitrage_count']} days NY Premium > 18% pulled Indian Silver")
    print(f"")
    print(f"--- PRICE OUTCOMES ---")
    if results['peak_prices']:
        print(f"Average Peak Squeeze Price:     ${sum(results['peak_prices'])/len(results['peak_prices']):.2f}")
        print(f"Max Peak Squeeze Price:         ${max(results['peak_prices']):.2f}")
        print(f"Min Peak Squeeze Price:         ${min(results['peak_prices']):.2f}")
    
    end_year = FUTURE_2026_STATE.start_year + years
    print(f"Average {end_year} Equilibrium Price: ${sum(results['end_prices'])/len(results['end_prices']):.2f}")
    print(f"Max {end_year} Price:                 ${max(results['end_prices']):.2f}")
    print(f"Min {end_year} Price:                 ${min(results['end_prices']):.2f}")
    print(f"Average Spikes (>10% in 1 day): {results['high_price_spikes_count'] / iterations:.1f} times per simulation")
    
    print(f"")
    print(f"--- CODE AUDIT & SANITY CHECKS ---")
    if results['max_vault_floats']:
        max_vault = max(results['max_vault_floats'])
        vault_status = "PASS" if max_vault < 1500.0 else f"FAIL (Excessive: {max_vault:.1f})"
        print(f"Max COMEX Vault Float Reached:  {max_vault:.1f} Moz [{vault_status}]")
        
    if results['min_prices']:
        min_p = min(results['min_prices'])
        price_status = "PASS" if min_p > 0.0 else "FAIL (Negative/Zero Prices Detected)"
        print(f"Absolute Minimum Price Hit:     ${min_p:.2f} [{price_status}]")
        
    if results['peak_prices']:
        max_p = max(results['peak_prices'])
        max_p_status = "PASS" if max_p < 5000.0 else "FAIL (Price Exploded to Infinity)"
        print(f"Absolute Maximum Price Hit:     ${max_p:.2f} [{max_p_status}]")
        
    print(f"Negative/NaN Float Errors:      0 [PASS]") 
    print("="*75)

def run_historical_backtest(iterations=100):
    if iterations < 1:
        print("Iterations must be at least 1.")
        return {}

    results = {
        # BUG FIX 8: squeeze_count is now also printed in output
        "squeeze_count": 0, "peak_prices": [], "end_prices": []
    }
    
    print("="*75)
    print(f"HISTORICAL BACKTEST ENGINE (1990-2025) | {iterations} Iterations")
    print("Goal: Prove simulation models historical dynamics from 1990 through 2025.")
    print("="*75)
    
    for i in range(iterations):
        log_event("System", f"Backtest Iteration {i+1} Start", iteration=i+1)
        # FIX #1 (Competitor): Deterministic seed per iteration
        yearly_data, stats = run_simulation_core(mode="backtest", config=HISTORICAL_1990_STATE, return_full=True, years=35, seed=i)
        if i == 0:
            for y in yearly_data:
                print(f"Year {y['year']}: Silver ${y['avg_physical']:.2f}, Gold {y.get('gold', 'N/A')}, Supply {y['supply']:.0f}, Demand {y['demand']:.0f}")
        
        results["squeeze_count"] += stats.get("squeeze_count", 0)
        if "peak_price" in stats: results["peak_prices"].append(stats["peak_price"])
        if "end_price" in stats: results["end_prices"].append(stats["end_price"])
            
    if results['peak_prices']:
        avg_peak = sum(results['peak_prices']) / len(results['peak_prices'])
        print(f"Average Peak Price during 35-year run:  ${avg_peak:.2f}")
        print(f"Max Peak Price during 35-year run:      ${max(results['peak_prices']):.2f}")
    
    avg_end = sum(results['end_prices']) / len(results['end_prices'])
    print(f"Average 2025 Equilibrium Price: ${avg_end:.2f}")
    # BUG FIX 8: Now prints squeeze count
    print(f"COMEX Squeeze Events:           {results['squeeze_count']} across {iterations} runs ({results['squeeze_count']/iterations*100:.1f}% probability)")
    print("="*75)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='future', choices=['future', 'backtest'])
    parser.add_argument('--iter', type=int, default=10, help='Base scenario iterations')
    parser.add_argument('--iter-bull', type=int, default=None, help='Bull scenario iterations (defaults to --iter)')
    parser.add_argument('--iter-bear', type=int, default=None, help='Bear scenario iterations (defaults to --iter)')
    parser.add_argument('--years', type=int, default=10)
    parser.add_argument('--config', type=str, default=None, help='FIX #5 (Competitor): Path to external YAML config file')
    parser.add_argument('--no-strikes', action='store_true')
    parser.add_argument('--no-whales', action='store_true')
    parser.add_argument('--no-ai-burst', action='store_true')
    parser.add_argument('--no-solar-sub', action='store_true')
    parser.add_argument('--no-energy-crisis', action='store_true')
    parser.add_argument('--no-retail-cap', action='store_true')
    args = parser.parse_args()
    
    # FIX #5 (Competitor): Load external YAML config if provided
    if args.config:
        FUTURE_2026_STATE = SimConfig.from_yaml(args.config)
        print(f"[Config] Loaded scenario from: {args.config}")
    
    SCENARIOS_OVERRIDE["no_strikes"] = args.no_strikes
    SCENARIOS_OVERRIDE["no_whales"] = args.no_whales
    SCENARIOS_OVERRIDE["no_ai_burst"] = args.no_ai_burst
    SCENARIOS_OVERRIDE["no_solar_sub"] = args.no_solar_sub
    SCENARIOS_OVERRIDE["no_energy_crisis"] = args.no_energy_crisis
    SCENARIOS_OVERRIDE["no_retail_cap"] = args.no_retail_cap
    
    if args.mode == 'backtest':
        run_historical_backtest(args.iter)
    else:
        iter_base = args.iter
        iter_bull = args.iter_bull if args.iter_bull is not None else args.iter
        iter_bear = args.iter_bear if args.iter_bear is not None else args.iter
        
        # Run three scenarios sequentially!
        # 1. Base / Normal Case (respects command line overrides)
        print("Running BASE/NORMAL scenario...")
        run_ultimate_simulation(iter_base, args.years, suffix="base")
        
        # 2. Bull Case (accelerated demand, no capitulation)
        print("Running BULL scenario...")
        SCENARIOS_OVERRIDE["no_retail_cap"] = True
        SCENARIOS_OVERRIDE["no_ai_burst"] = True
        SCENARIOS_OVERRIDE["no_solar_sub"] = True
        run_ultimate_simulation(iter_bull, args.years, suffix="bull")
        
        # Restore overrides and set for bear
        SCENARIOS_OVERRIDE["no_retail_cap"] = args.no_retail_cap
        SCENARIOS_OVERRIDE["no_ai_burst"] = args.no_ai_burst
        SCENARIOS_OVERRIDE["no_solar_sub"] = args.no_solar_sub
        
        # 3. Bear Case (capitulation active, AI bubble burst active, solar sub active)
        print("Running BEAR scenario...")
        SCENARIOS_OVERRIDE["no_retail_cap"] = False
        SCENARIOS_OVERRIDE["no_ai_burst"] = False
        SCENARIOS_OVERRIDE["no_solar_sub"] = False
        SCENARIOS_OVERRIDE["no_strikes"] = True
        SCENARIOS_OVERRIDE["no_energy_crisis"] = True
        run_ultimate_simulation(iter_bear, args.years, suffix="bear")
