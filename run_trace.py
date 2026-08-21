import sys
import os
import csv
sys.path.append('src')
from engine import run_simulation_core
from config import FUTURE_2026_STATE

os.makedirs('outputs', exist_ok=True)

print("Running 5-year single iteration...")
daily_data, stats = run_simulation_core(years=5, config=FUTURE_2026_STATE, return_full=True)

if daily_data:
    keys = daily_data[0].keys()
    with open('outputs/trace_5yr.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(daily_data)
    print(f"Saved {len(daily_data)} days of trace data to outputs/trace_5yr.csv")
    print(f"Final Price: ${stats['end_price']:.2f}")
else:
    print("No daily data generated.")
