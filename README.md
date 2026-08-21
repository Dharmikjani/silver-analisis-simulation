# Silver Analisis Simulation Engine 📈🪙

A highly advanced quantitative simulation engine designed to model the global silver market dynamics, physical squeezes, and macroeconomic shocks. This project features a robust backtesting core and a FastAPI-driven web dashboard to visualize simulation paths for Base, Bull, and Bear scenarios.

## 🚀 Features

- **Mega Simulator Engine**: Capable of running thousands of Monte Carlo iterations.
- **Deep Supply/Demand Metrics**: Accurately models primary mining, scrap refining, solar PV, AI tech, EV auto, and defense consumption.
- **Extreme Macro Shocks**: Simulates black swan events like LBMA/COMEX defaults, AI bubble bursts, mining strikes, ETF raids, and retail capitulation.
- **Historical Backtesting**: Validate the engine against historical silver data (1990 - 2025).
- **FastAPI Dashboard**: In-memory cached API serving an interactive frontend visualization.

## 📂 Project Structure

- `api/`: Contains `main.py`, the FastAPI backend that serves the simulation data and web UI.
- `scripts/`: Contains executable scripts like `silver_mega_simulator.py` and `run_trace.py`.
- `src/`: The core engine logic (`config.py`, `engine.py`, `macro.py`, `stakeholders.py`, etc.).
- `docs/`: Extensive research reports, factual data audits, and monetary education material.
- `web/`: The frontend UI (HTML, CSS, JS) served by the API.
- `tests/`: Pytest suite for fuzzing and stakeholder logic verification.

## ⚙️ Installation

Make sure you have Python installed, then install the dependencies:

```bash
pip install -r requirements.txt
```

## 🎮 How to Run

### 1. Run the Simulator
To generate the simulation outputs (CSVs and JSON stats) for all scenarios (base, bull, bear), run:

```bash
python scripts/silver_mega_simulator.py --iter 10 --years 10
```
*Note: Results are saved automatically to the `outputs/` folder.*

### 2. Start the Web Dashboard
To view the results on the web dashboard, start the FastAPI server:

```bash
python api/main.py
```
*Then open your browser and navigate to: `http://localhost:8000`*

### 3. Run Historical Backtest
To backtest the model against historical data:

```bash
python scripts/silver_mega_simulator.py --mode backtest --iter 10
```

## 🧪 Testing

To run the unit and fuzzing tests, use pytest:

```bash
pytest tests/
```
