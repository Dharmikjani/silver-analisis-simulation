import os
import json
import csv
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Cache to hold the simulation results in memory
simulation_cache: Dict[str, Dict[str, Any]] = {}

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")
WEB_DIR = os.path.join(ROOT_DIR, "web")

def load_simulation_data() -> Dict[str, Dict[str, Any]]:
    scenarios = ["base", "bull", "bear"]
    result = {}
    
    for s in scenarios:
        data = []
        path_file = os.path.join(OUTPUT_DIR, f"ultimate_simulation_path_{s}.csv")
        stats_file = os.path.join(OUTPUT_DIR, f"simulation_stats_{s}.json")
        
        if os.path.exists(path_file):
            with open(path_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append({
                        "day_index": int(row["DayIndex"]),
                        "year": int(row["Year"]),
                        "month": int(row["Month"]),
                        "day": int(row["Day"]),
                        "avg_physical": float(row["Avg_Physical_Price"]),
                        "avg_paper": float(row["Avg_Paper_Price"]),
                        "supply": float(row["Supply"]),
                        "demand": float(row["Demand"]),
                        "vault": float(row["Vault_Float"])
                    })
                    
        stats = {}
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as sf:
                stats = json.load(sf)
                
        result[s] = {"data": data, "stats": stats}
        
    return result

@app.on_event("startup")
def startup_event():
    # Pre-load data into memory on server start to prevent reading disk on every API call
    global simulation_cache
    simulation_cache = load_simulation_data()
    print("Simulation data loaded into cache.")

@app.get("/api/simulate")
def simulate() -> Dict[str, Dict[str, Any]]:
    # Simply return the in-memory cache instead of reading disk
    # Fallback to load on the fly if cache is somehow empty (e.g., deleted files during runtime)
    global simulation_cache
    if not simulation_cache:
        simulation_cache = load_simulation_data()
    return simulation_cache

# Mount static files (css, js)
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 for production-readiness instead of 127.0.0.1
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
