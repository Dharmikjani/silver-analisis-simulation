import sys
import os
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from engine import run_simulation_core
from config import FUTURE_2026_STATE

def analyze_gsr_5_years():
    print("Running simulation for 5 years to project Gold/Silver Ratio (GSR)...")
    import copy
    collapse_config = copy.deepcopy(FUTURE_2026_STATE)
    # Simulate Paper Collapse / Zero Inventory Event
    collapse_config.comex_float = 0.0
    collapse_config.vaults.lbma_vault = 0.0
    collapse_config.solar_pv = 350.0 
    
    # Run the core simulation for 5 years
    daily_data, stats = run_simulation_core(return_full=True, years=5, seed=42, config=collapse_config)
    
    # Extract data
    days = [d["day_index"] for d in daily_data]
    gsr = [d.get("gold_silver_ratio", 0) for d in daily_data]
    
    if not gsr or gsr[0] == 0:
        print("Error: GSR not found in daily data.")
        return
        
    avg_gsr = sum(gsr) / len(gsr)
    max_gsr = max(gsr)
    min_gsr = min(gsr)
    
    print("\n--- 5-YEAR GSR PROJECTIONS ---")
    print(f"Average GSR: {avg_gsr:.2f}")
    print(f"Maximum GSR: {max_gsr:.2f}")
    print(f"Minimum GSR: {min_gsr:.2f}")
    
    print("\n--- SUB-AGENT OBSERVATIONS (GSR IMPACT) ---")
    for d in daily_data:
        day = d["day_index"]
        gsr_val = d.get("gold_silver_ratio", 0)
        
        # Central Bank Actions (Gov_China / Gov_BRICS logic based on GSR thresholds)
        if gsr_val > 85.0:
            if day % 252 == 0: # Print once a year to avoid spam
                print(f"Day {day}: GSR hit {gsr_val:.2f} (> 85.0). Central Banks & Sovereigns activated VALUE BUYING (Silver is cheap).")
        elif gsr_val < 40.0:
            if day % 252 == 0:
                print(f"Day {day}: GSR dropped to {gsr_val:.2f} (< 40.0). Central Banks halted buying (Silver is expensive).")
                
        # Billionaire Swap Logic
        if gsr_val < 30.0:
            if day % 100 == 0:
                print(f"Day {day}: GSR dropped below 30.0! Billionaire Family Offices are aggressively SWAPPING silver for gold.")
                
        # Hedge Fund Squeeze Tracking
        if d.get("hedge_fund_attack", 0) > 0:
            print(f"Day {day}: PREDATORY HEDGE FUND ATTACK DETECTED! Squeezing market... GSR violently dropped to {gsr_val:.2f}.")
    
    # Plotting
    os.makedirs('outputs', exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(days, gsr, color='gold', label='Gold/Silver Ratio (GSR)')
    
    # Add trend line or average line
    plt.axhline(y=avg_gsr, color='r', linestyle='--', label=f'Average ({avg_gsr:.2f})')
    
    plt.title('Projected Gold/Silver Ratio (Next 5 Years)')
    plt.xlabel('Trading Days')
    plt.ylabel('Ratio (Gold Price / Silver Price)')
    plt.legend()
    plt.grid(True)
    
    output_path = 'outputs/gsr_projection.png'
    plt.savefig(output_path)
    print(f"\nChart saved successfully to: {output_path}")

if __name__ == "__main__":
    analyze_gsr_5_years()
