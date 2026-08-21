from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json
import csv

app = FastAPI()

# API endpoint to run the simulation and get data
@app.get("/api/simulate")
def simulate():
    scenarios = ["base", "bull", "bear"]
    result = {}
    
    for s in scenarios:
        data = []
        path_file = f"outputs/ultimate_simulation_path_{s}.csv"
        stats_file = f"outputs/simulation_stats_{s}.json"
        
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

# Mount static files (css, js)
app.mount("/", StaticFiles(directory="web", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
