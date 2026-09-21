# ISTQB / ISO 29119-3 Formal Defect Report
**Document Identifier:** DR-ISO-29119-001  
**Standard Reference:** ISTQB Certified Tester Advanced Level (Technical Test Analyst) & ISO/IEC/IEEE 29119-3:2021 Clause 12 (Incident Report)  
**System Under Test:** Silver Analisis Simulation Engine (`src/`, `api/`)  
**Verification Date:** 2026-09-21  
**Verification Harness:** [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py)  
**Verification Status:** **All 16 Defects 100% Verified & Reproducible (0 False Negatives, 0 False Positives)**  

---

## Master Defect Summary Table

| Defect ID | Component & Lines | Severity | Priority | ISTQB Defect Classification | Summary / Description | Status |
|---|---|---|---|---|---|---|
| **DEF-01** | `src/realworld.py:17-19` | **Critical** | **High** | Runtime Crash / Boundary Exception | Unchecked `.iloc[-1]` on empty DataFrame crashes `/api/live` and `test_api_e2e.py` | **Verified** |
| **DEF-02** | `src/engine.py:275-277` | **Major** | **High** | Data Flow Anomaly / Dead Code | `getattr(self.comex, 'margin_hike_active', False)` queries wrong object; lines 276-277 dead | **Verified** |
| **DEF-03** | `src/engine.py:247` | **Major** | **Medium** | Algorithmic Defect / Stale Data | `current_gsr` uses static frozen `oracle.gold_price` instead of dynamic `macro.gold_price` | **Verified** |
| **DEF-04** | `src/stakeholders.py:930-945` | **Major** | **Medium** | State Corruption / Data Overwrite | `Billionaire_Family_Offices` sequential `if` overwrites `net_flow = -3.0`, erasing buy volume | **Verified** |
| **DEF-05** | `src/macro.py:57, 158, 175` | **Medium** | **Medium** | Inert Feature / Dead Variable | `brics_vault_drain_daily` initialized and reassigned to 0; zero physical drain produced | **Verified** |
| **DEF-06** | `src/exchanges.py:13` | **Medium** | **High** | Boundary Value Off-by-One | Strict inequality `eligible_float > amount` traps last 10 Moz in COMEX Eligible vault | **Verified** |
| **DEF-07** | `src/macro.py:171-176` | **Low** | **Low** | Control Flow Shadowing / Syntax Trap | `elif self.brics_announced` coupled to `if tension > 75`, permanently shadowed during crisis | **Verified** |
| **DEF-08** | `src/engine.py:54, 540` | **Medium** | **Medium** | Type Invariant Hazard / Autovivification | `self.stats = defaultdict(int)` zeroes `min_price` permanently if accessed before minimum | **Verified** |
| **DEF-09** | `src/macro.py:9, 36-38` | **Critical** | **High** | Silent Zero-Price Initialization | When yfinance returns empty history, oracle prices stay $0.00; entire 10-year sim runs at $0 | **Verified** |
| **DEF-10** | `src/engine.py:384-398, 417` | **Major** | **High** | Dead Computation & Bypass | `gbm_mult` Merton Jump-Diffusion & circuit breaker are computed but completely bypassed | **Verified** |
| **DEF-11** | `src/stakeholders.py:689` & `src/engine.py:310, 512` | **Major** | **High** | Physical/Paper Domain Inversion | Predatory hedge fund paper futures dump routed to physical demand; replenishes physical vault | **Verified** |
| **DEF-12** | `src/stakeholders.py:852` & `src/engine.py:87` | **Major** | **Medium** | Abandoned Architecture / Inert Agent | `UnallocatedAccountHolders` instantiated but `check_bank_run` is never invoked anywhere | **Verified** |
| **DEF-13** | `src/engine.py:241` | **Medium** | **Medium** | Parameter Inversion / Wrong Metric | Passes `self.lbma.vault_float` into WhaleSyndicate parameter `comex_float` | **Verified** |
| **DEF-14** | `src/engine.py:521, 450` | **Medium** | **Medium** | Ephemeral Price State Overwrite | LBMA default 2.0x physical price jump is completely overwritten and erased on Day T+1 | **Verified** |
| **DEF-15** | `src/engine.py:251` | **Low** | **Low** | Unpropagated Local Mutation | `total_supply += abs(bill_flow)` mutates local primitive float inside `_process_demand` | **Verified** |
| **DEF-16** | `src/macro.py:88` & `src/engine.py:329, 546` | **Medium** | **Medium** | Calendar De-synchronization | 155-day offset advances recorded output year to 2027 at Day 97, but Macro stays 2026 until Day 252 | **Verified** |

---

## Detailed ISTQB Incident Specifications

### DEF-01: Runtime Crash on Empty DataFrame in `src/realworld.py`
- **Component:** `src/realworld.py:17-19` (consumed by `api/main.py:75` and `tests/test_api_e2e.py:13`)
- **Severity:** Critical (Blocks API endpoint `/api/live` and causes test suite failure)
- **Priority:** High
- **Preconditions:** US market closed, weekend, holiday, or yfinance rate-limited.
- **Steps to Reproduce:**
  1. Call `fetch_live_market_data()` outside US trading hours or with empty history.
  2. Execute `pytest tests/test_api_e2e.py::test_api_live_endpoint`.
- **Expected Result:** Graceful fallback to cached/default market prices (`silver_price > 0`, `gold_price > 0`, `fed_rate_proxy > 0`).
- **Actual Result:** `IndexError: single positional indexer is out-of-bounds`. Function returns `{'success': False, 'error': 'single positional indexer is out-of-bounds'}`. Assertion `assert 'silver_price' in data` fails.
- **Root Cause:** Direct subscripting `tickers.tickers["SI=F"].history(period="1d")['Close'].iloc[-1]` without validating `if not hist.empty`.
- **Remediation:** Guard with `if not hist.empty: ... else fallback defaults` ($30.0 / $2500.0 / 4.5%).
- **Verification Proof:** Executable test `test_verify_def01_realworld_iloc_crash` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L30-L50).

---

### DEF-02: Dead Code & Mismatched Object in `src/engine.py:275-277`
- **Component:** `src/engine.py:275-277`
- **Severity:** Major (Structural Logic Defect)
- **Priority:** High
- **Preconditions:** Force majeure active and margin hike active.
- **Steps to Reproduce:**
  1. Inspect `src/exchanges.py:5` (`COMEX_Exchange`). Note attributes: `vault_float`, `eligible_float`, `defaulted`, `force_majeure_active`.
  2. Inspect `src/stakeholders.py:731` (`ExchangeMarginControls`). Note attribute: `margin_hike_active`.
  3. Inspect `src/engine.py:275`: `if getattr(self.comex, 'margin_hike_active', False) and self.comex.force_majeure_active:`.
- **Expected Result:** Liquidations and volume dampening execute during force majeure margin hike.
- **Actual Result:** `getattr(self.comex, 'margin_hike_active', False)` evaluates to `False` 100% of the time. Lines 276-277 (`retail_daily *= 0.10; opt_hedge *= 0.10`) are dead code.
- **Root Cause:** Developer passed `self.comex` instead of `self.exchange_margins`.
- **Remediation:** Change condition to `if self.exchange_margins.margin_hike_active and self.comex.force_majeure_active:`.
- **Verification Proof:** Executable test `test_verify_def02_comex_margin_hike_dead_code` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L53-L70).

---

### DEF-03: Stale Day-0 Gold Price Used in 10-Year Dynamic GSR Calculation
- **Component:** `src/engine.py:247`
- **Severity:** Major (Macro Modeling Defect)
- **Priority:** Medium
- **Preconditions:** Multi-year simulation run where gold price appreciates.
- **Steps to Reproduce:**
  1. Run 10-year simulation.
  2. Inspect `self.macro.gold_price` at year 10 (e.g., $4,500).
  3. Inspect line 247: `current_gsr = self.oracle.gold_price / self.physical_price`.
- **Expected Result:** `current_gsr` reflects simulated macroeconomic gold price `self.macro.gold_price / self.physical_price`.
- **Actual Result:** `current_gsr` is calculated using frozen Day-0 static price `self.oracle.gold_price` ($2,500), distorting billionaire portfolio rebalancing and algorithmic demand.
- **Root Cause:** Variable reference mismatch between static oracle snapshot and simulated macro environment.
- **Remediation:** Replace `self.oracle.gold_price` with `self.macro.gold_price`.
- **Verification Proof:** Executable test `test_verify_def03_stale_gold_price_in_gsr` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L73-L93).

---

### DEF-04: Intraday Inventory Churn & Net Flow Overwrite in Billionaire Family Offices
- **Component:** `src/stakeholders.py:930-945`
- **Severity:** Major (Data Flow & Mass Balance Defect)
- **Priority:** Medium
- **Preconditions:** `macro.geopolitical_tension_index > 80` AND `current_gsr < 30.0`.
- **Steps to Reproduce:**
  1. Set `geopolitical_tension_index = 85.0`, `current_gsr = 25.0`, `vault_float = 100.0`.
  2. Execute `Billionaire_Family_Offices.process_day(price=40.0, macro=macro, current_gsr=25.0)`.
- **Expected Result:** Net flow should be calculated as $+2.0 - 3.0 = -1.0$ Moz.
- **Actual Result:** Vault increases by 2.0, then decreases by 3.0 (ending at 99.0). But `net_flow` is overwritten to `-3.0`. The $+2.0$ Moz buy demand is erased from market demand routing.
- **Root Cause:** Sequential `if` statements overwriting `net_flow` variable instead of accumulating.
- **Remediation:** Accumulate net changes: `net_flow += ...` or prioritize mutually exclusive trading regimes.
- **Verification Proof:** Executable test `test_verify_def04_billionaire_net_flow_overwrite` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L96-L117).

---

### DEF-05: Inert Feature - BRICS Vault Drain Always Zero
- **Component:** `src/macro.py:57, 158, 175` & `src/engine.py:299`
- **Severity:** Medium (Dead Feature)
- **Priority:** Medium
- **Preconditions:** BRICS gold-backed reserve announcement triggers.
- **Steps to Reproduce:**
  1. Trigger BRICS announcement: `clean_macro.brics_announced = True`.
  2. Inspect `clean_macro.brics_vault_drain_daily`.
- **Expected Result:** Physical vault drain added to London LBMA demand (`self.macro.brics_vault_drain_daily > 0`).
- **Actual Result:** `self.brics_vault_drain_daily` is initialized to 0 and explicitly set to 0 on line 158 and line 175. Term contributes 0.0 Moz to `lbma_demand`.
- **Root Cause:** Hardcoded placeholder `0` never replaced with calibrated parameter (e.g., `20.0 / TRADING_DAYS`).
- **Remediation:** Assign calibrated physical drain rate (e.g. `20.0 / TRADING_DAYS`).
- **Verification Proof:** Executable test `test_verify_def05_brics_vault_drain_always_zero` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L120-L132).

---

### DEF-06: Off-by-One Strict Inequality Traps Last 10 Moz in COMEX Eligible
- **Component:** `src/exchanges.py:13` & `src/engine.py:479`
- **Severity:** Medium (Boundary Defect)
- **Priority:** High
- **Preconditions:** Registered vaults under stress (<30 Moz), Eligible float $\le 10.0$ Moz.
- **Steps to Reproduce:**
  1. Set `comex.eligible_float = 10.0`.
  2. Call `comex.move_eligible_to_registered(amount=10.0, current_price=70.0, threshold_price=60.0)`.
- **Expected Result:** Transfer succeeds, eligible becomes 0.0, registered increases by 10.0.
- **Actual Result:** Condition `self.eligible_float > amount` tests `10.0 > 10.0` $\implies$ `False`. Transfer fails and returns `False`.
- **Root Cause:** Strict inequality `>` instead of inclusive `>=`.
- **Remediation:** Change to `if current_price > threshold_price and self.eligible_float >= amount:`.
- **Verification Proof:** Executable test `test_verify_def06_eligible_strict_inequality_traps_metal` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L135-L149).

---

### DEF-07: Control Flow Shadowing in `src/macro.py:171-176`
- **Component:** `src/macro.py:171-176`
- **Severity:** Low (Faulty Control Flow)
- **Priority:** Low
- **Steps to Reproduce:**
  1. Set `geopolitical_tension_index = 80.0` and `brics_announced = True`.
  2. Observe execution of lines 171-176.
- **Expected Result:** Independent evaluation of export ban risk and BRICS vault drain reset.
- **Actual Result:** `elif self.brics_announced:` is an alternate branch of `if self.geopolitical_tension_index > 75:`. Whenever tension is $>75$, the `elif` branch is completely unreachable.
- **Root Cause:** Incorrect indentation / coupling of two unrelated state checks.
- **Remediation:** De-couple into separate `if` statements.
- **Verification Proof:** Executable test `test_verify_def07_control_flow_shadowing_macro` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L152-L171).

---

### DEF-08: `defaultdict(int)` Traps `min_price` at Zero in `src/engine.py:54, 540`
- **Component:** `src/engine.py:54, 540`
- **Severity:** Medium (Data Invariant Hazard)
- **Priority:** Medium
- **Steps to Reproduce:**
  1. Access `self.stats["min_price"]` before first minimum price comparison.
  2. `defaultdict(int)` assigns default value `0`.
  3. Condition `if "min_price" not in self.stats or self.physical_price < self.stats["min_price"]:` executes.
- **Expected Result:** `min_price` captures the true lowest silver price (e.g. $28.50).
- **Actual Result:** `self.physical_price < 0` is `False`. `min_price` stays stuck at `0.0`.
- **Root Cause:** Using `defaultdict(int)` for metrics that require non-zero initial minimums (like prices).
- **Remediation:** Initialize `self.stats["min_price"] = self.oracle.silver_price` explicitly in `__init__`.
- **Verification Proof:** Executable test `test_verify_def08_defaultdict_min_price_zero` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L174-L192).

---

### DEF-09: Silent Zero-Price Initialization in `src/macro.py:9, 36-38`
- **Component:** `src/macro.py:9, 36-38` & `src/engine.py:27-30`
- **Severity:** Critical (Corrupts Simulation Pricing Model)
- **Priority:** High
- **Preconditions:** Running simulation when yfinance returns empty history (e.g. market closed, offline, API rate limit).
- **Steps to Reproduce:**
  1. Run `SimulationEngine(mode="future")` when `SI=F` returns empty DataFrame.
  2. Observe `self.oracle.silver_price` and `self.oracle.gold_price`.
- **Expected Result:** Fallback to reasonable defaults ($30.0 silver, $2500.0 gold).
- **Actual Result:** No exception is thrown, so `except Exception:` does not trigger. `data` dictionary is empty. Oracle retains `config.start_silver_price` which is `0.0` in `FUTURE_2026_STATE`. Entire simulation runs with $0.00 silver and $0.00 gold.
- **Root Cause:** Fallbacks are placed only inside `except Exception:` block; missing check for empty `data`.
- **Remediation:** Check `if self.silver_price <= 0: self.silver_price = 30.0` and `if self.gold_price <= 0: self.gold_price = 2500.0`.
- **Verification Proof:** Executable test `test_verify_def09_silent_zero_price_initialization` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L195-L218).

---

### DEF-10: Dead Computation of `gbm_mult` & Bypassed Circuit Breaker in `src/engine.py:384-450`
- **Component:** `src/engine.py:384-398, 417, 450`
- **Severity:** Major (Core Pricing Engine Bypass)
- **Priority:** High
- **Preconditions:** Normal simulation day price update.
- **Steps to Reproduce:**
  1. Trace lines 384-398 in `SimulationEngine._update_price()`.
  2. Note calculation of Merton Jump-Diffusion (`jump_mult`), `gbm_mult`, and circuit breaker clamping (`0.93` to `1.07`).
  3. Trace line 417: `paper_gbm = math.exp(...)`.
  4. Trace line 450: `self.physical_price = max(0.10, self.paper_price * (1.0 + self.physical_premium) * physical_noise)`.
- **Expected Result:** `gbm_mult` (with jumps and circuit breaker clamps) drives the paper or physical price.
- **Actual Result:** `gbm_mult` is never multiplied into `paper_price` or `physical_price`. `paper_gbm` is computed separately with no jumps and no circuit breakers. The entire Merton Jump-Diffusion model is dead computation.
- **Root Cause:** Incomplete refactoring during dual-price separation.
- **Remediation:** Apply `jump_mult` and circuit breaker limits to `paper_gbm`.
- **Verification Proof:** Executable test `test_verify_def10_dead_computation_gbm_mult` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L221-L239).

---

### DEF-11: Paper Futures Dump Placed in Physical Demand & Inverts Flow in `src/engine.py:310-314`
- **Component:** `src/stakeholders.py:689` & `src/engine.py:310, 512`
- **Severity:** Major (Domain Inversion & Mass Conservation)
- **Priority:** High
- **Preconditions:** `PredatoryHedgeFund` reaches target price and enters `is_dumping = True`.
- **Steps to Reproduce:**
  1. `PredatoryHedgeFund` sells paper futures: `return -dump_amt` (-4.0 Moz).
  2. Line 310 adds this to `comex_physical_demand`: `comex_physical_demand = (retail_daily * 0.1) + hedge_fund_squeeze`.
  3. `comex_physical_demand` becomes negative (e.g. -3.9 Moz).
  4. `comex_deficit` becomes negative.
  5. Line 512 executes: `self.comex.vault_float += abs(comex_deficit)`.
- **Expected Result:** Paper futures dump affects paper price and paper demand; physical registered metal is untouched.
- **Actual Result:** Paper sell order reduces physical demand below zero, causing COMEX to register negative deficit and INCREASE physical vault float. Paper futures sell orders manufacture physical silver bars in the vault.
- **Root Cause:** Placing paper derivative hedge fund cash-out into `comex_physical_demand` instead of `comex_paper_demand`.
- **Remediation:** Move `hedge_fund_squeeze` to `comex_paper_demand` (line 311).
- **Verification Proof:** Executable test `test_verify_def11_paper_dump_creates_physical_bars` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L242-L274).

---

### DEF-12: Abandoned Architecture: `UnallocatedAccountHolders` Completely Inert
- **Component:** `src/stakeholders.py:852` & `src/engine.py:87` & `src/exchanges.py:27`
- **Severity:** Major (Feature Disconnect)
- **Priority:** Medium
- **Preconditions:** LBMA vault under extreme drain stress (<100 Moz).
- **Steps to Reproduce:**
  1. Inspect `SimulationEngine._init_stakeholders()`: `self.unallocated_holders = UnallocatedAccountHolders()`.
  2. Search entire engine codebase for `self.unallocated_holders.check_bank_run` or `self.lbma.check_bank_run`.
- **Expected Result:** Unallocated account confidence drops during vault exhaustion, triggering London bank run.
- **Actual Result:** Neither method is ever called in `SimulationEngine`. London bank runs on unallocated silver are 100% inert and disconnected from the simulation.
- **Root Cause:** Abandoned stakeholder integration during engine development.
- **Remediation:** Call `self.unallocated_holders.check_bank_run(self.lbma.vault_float)` in `_process_demand` and route bank run demand to `lbma_demand`.
- **Verification Proof:** Executable test `test_verify_def12_abandoned_unallocated_bank_run` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L277-L295).

---

### DEF-13: Parameter Inversion: Whale Syndicate Passed LBMA Instead of COMEX
- **Component:** `src/engine.py:241` & `src/stakeholders.py:617`
- **Severity:** Medium (Parameter Mismatch)
- **Priority:** Medium
- **Preconditions:** Evaluating whale accumulation attacks.
- **Steps to Reproduce:**
  1. Inspect `WhaleSyndicate.process_accumulation(self, comex_float, bank_short_position)`.
  2. Inspect `src/engine.py:241`: `self.whale_syndicate.process_accumulation(self.lbma.vault_float, self.bullion_bank_shorts.short_position)`.
- **Expected Result:** COMEX registered float is passed to check if COMEX float < 150 Moz.
- **Actual Result:** `self.lbma.vault_float` is passed instead. Whales track London vault size instead of COMEX float.
- **Root Cause:** Variable name typo passing `self.lbma.vault_float` instead of `self.comex.vault_float`.
- **Remediation:** Change parameter to `self.comex.vault_float`.
- **Verification Proof:** Executable test `test_verify_def13_parameter_inversion_whale_syndicate` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L298-L315).

---

### DEF-14: Ephemeral Price Shock: LBMA Default 2.0x Multiplier Erased on Next Day
- **Component:** `src/engine.py:521, 450`
- **Severity:** Medium (Transient State Defect)
- **Priority:** Medium
- **Preconditions:** LBMA vault float drops to 0, triggering default.
- **Steps to Reproduce:**
  1. On Day T, `self.lbma.vault_float` reaches 0.
  2. Line 521 executes: `self.physical_price *= 2.0` (e.g. jumps from $33 to $66).
  3. Advance to Day T+1 and call `_update_price()`.
  4. Line 450 executes: `self.physical_price = max(0.10, self.paper_price * (1.0 + self.physical_premium) * physical_noise)`.
- **Expected Result:** The 2.0x physical price repricing persists across subsequent days.
- **Actual Result:** `self.physical_price` is overwritten from `paper_price * (1 + premium)`. The price drops right back down to ~$33-35. The default doubling lasted exactly 1 tick.
- **Root Cause:** Physical price is computed as a state-less formula from `paper_price` on line 450, ignoring modifications to `self.physical_price`.
- **Remediation:** Represent LBMA default via permanent physical premium expansion (`self.physical_premium += 1.0`) rather than direct multiplication of `physical_price`.
- **Verification Proof:** Executable test `test_verify_def14_ephemeral_price_shock_overwrite` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L318-L345).

---

### DEF-15: Unpropagated Local Supply Modification in `src/engine.py:251`
- **Component:** `src/engine.py:251-255`
- **Severity:** Low (Code Smells & Dead Local Mutation)
- **Priority:** Low
- **Preconditions:** Billionaires net selling silver (`bill_flow < 0`).
- **Steps to Reproduce:**
  1. Inspect line 251: `total_supply += abs(bill_flow) # Need to propagate this up or just handle it here`.
  2. Check return of `_process_demand`: `return lbma_demand, comex_demand`.
- **Expected Result:** `total_supply` updated in `run()` loop.
- **Actual Result:** `total_supply` is an immutable float passed by value. The local variable inside `_process_demand` changes, but the caller's variable in `run()` is unchanged.
- **Root Cause:** Incomplete propagation acknowledged by author comment.
- **Remediation:** Rely cleanly on `self.dynamic_supply_add` (line 253) which is already handled in `_update_price` and `_update_exchanges_and_stats`. Remove dead local modification.
- **Verification Proof:** Executable test `test_verify_def15_unpropagated_local_supply_modification` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L348-L362).

---

### DEF-16: 155-Day Calendar De-synchronization Between Engine and Macro
- **Component:** `src/macro.py:88` & `src/engine.py:329, 546`
- **Severity:** Medium (Temporal Temporal Inconsistency)
- **Priority:** Medium
- **Preconditions:** Running simulation past day 97.
- **Steps to Reproduce:**
  1. Run simulation to day 97.
  2. Inspect output record: `actual_day = 97 + 155 = 252`. `year = 2026 + (252 // 252) = 2027`.
  3. Inspect `self.macro.current_year`. `macro.current_day` is 97, so `macro.current_year` is STILL 2026.
- **Expected Result:** Macro simulation year and output daily record year advance synchronously.
- **Actual Result:** Engine output marks records as Year 2027 starting at Day 97 (~4.5 months into simulation), but MacroEnvironment stakeholder triggers (`current_year >= 2027`) remain locked in 2026 until Day 252.
- **Root Cause:** Calendar offset of 155 days applied in `engine.py` without synchronizing `macro.current_day = 155`.
- **Remediation:** Initialize `self.macro.current_day = 155` in `SimulationEngine.__init__`.
- **Verification Proof:** Executable test `test_verify_def16_calendar_desynchronization` in [`QA whitebox/verify_all_bugs_istqb.py`](file:///c:/Users/Dell/Downloads/silver%20analisis/QA%20whitebox/verify_all_bugs_istqb.py#L365-L389).
