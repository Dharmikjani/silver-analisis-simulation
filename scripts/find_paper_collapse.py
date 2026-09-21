import sys
import os
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from engine import run_simulation_core
from config import FUTURE_2026_STATE

def find_paper_collapse():
    print("Running Mathematical Vault Runout Simulation (Max 15 Years)...")
    
    import copy
    collapse_config = copy.deepcopy(FUTURE_2026_STATE)
    # Simulate the "Zero Inventory Event" (Report 32)
    collapse_config.comex_float = 0.0
    collapse_config.vaults.lbma_vault = 0.0
    collapse_config.solar_pv = 350.0 # Force a massive deficit to trigger default immediately
    collapse_config.start_silver_price = 100.0 # Price is already elevated going into the collapse
    
    # Run the core simulation for 15 years under Paper Collapse conditions
    daily_data, stats = run_simulation_core(return_full=True, years=15, seed=42, config=collapse_config)
    
    fm_day = -1
    fm_price = 0
    gsr_15_day = -1
    
    print("\n--- ZERO INVENTORY EVENT TRACKER ---")
    
    for d in daily_data:
        day = d["day_index"]
        vault = d["vault"]
        gsr = d.get("gold_silver_ratio", 0)
        flag_fm = d.get("flag_force_majeure", 0)
        flag_comex = d.get("flag_comex_default", 0)
        flag_lbma = d.get("flag_lbma_default", 0)
        
        if flag_comex == 1 and flag_lbma == 1 and fm_day == -1:
            fm_day = day
            fm_price = d["avg_physical"]
            print(f"!!! PAPER COLLAPSE DETECTED (COMEX+LBMA = 0) !!!")
            print(f"Day {fm_day}: COMEX and LBMA Vaults hit ZERO. Force Majeure Declared.")
            print(f"Silver Physical Price at Default: ${fm_price:.2f}")
            print(f"GSR at Default: {gsr:.2f}")
            print("Physical market is now decoupled from paper suppression...\n")
            
        # Track if GSR hits 15
        if gsr > 0 and gsr <= 15.0 and gsr_15_day == -1:
            gsr_15_day = day
            print(f"!!! TARGET REACHED !!!")
            print(f"Day {gsr_15_day}: GSR has violently compressed to {gsr:.2f} (1:15 or lower)!")
            print(f"Silver Price: ${d['avg_physical']:.2f}")
            print(f"COMEX Vault: {d['comex_vault']:.2f} Moz | LBMA Vault: {d['lbma_vault']:.2f} Moz")
            
    if fm_day == -1:
        print("Result: Paper Collapse (Force Majeure) did NOT occur within 15 years in the base scenario.")
        print(f"Min COMEX Vault: {min(d['comex_vault'] for d in daily_data):.2f}")
        print(f"Min LBMA Vault: {min(d['lbma_vault'] for d in daily_data):.2f}")
        print(f"Min GSR: {min(d.get('gold_silver_ratio', 999) for d in daily_data):.2f}")
    elif gsr_15_day == -1:
        min_gsr_after = min([d.get("gold_silver_ratio", 999) for d in daily_data if d["day_index"] >= fm_day])
        print(f"Result: Paper Collapse occurred on Day {fm_day}, but GSR only dropped to {min_gsr_after:.2f}. The 1:15 target was not reached.")

if __name__ == "__main__":
    find_paper_collapse()
