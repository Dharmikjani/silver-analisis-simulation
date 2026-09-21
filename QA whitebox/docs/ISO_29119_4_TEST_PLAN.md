# ISO/IEC/IEEE 29119-4 White-Box Test Plan & Strategy
**Document Identifier:** TP-ISO-29119-WB-001  
**Standard Reference:** ISO/IEC/IEEE 29119-2 (Test Processes), ISO/IEC/IEEE 29119-3 (Test Documentation), ISO/IEC/IEEE 29119-4 (Test Techniques)  
**System Under Test (SUT):** Silver Analisis Simulation Engine (`src/`)  
**Status:** Approved & Baseline  
**Version:** 1.0.0  

---

## 1. Introduction & Purpose

This document constitutes the formal **White-Box Test Plan** for the Silver Analisis Simulation Engine. The objective is to rigorously verify the internal structural logic, control flows, data integrity, mathematical boundary conditions, and decision criteria of the simulation engine using standard white-box test design techniques defined in **ISO/IEC/IEEE 29119-4:2015 / 2021 (Clause 7: White-Box Test Design Techniques)**.

---

## 2. Test Items & Scope

The scope encompasses all core structural modules within `src/`:
| Module Identifier | Source File | Description / Structural Role | Cyclomatic Complexity ($V(G)$ Max) |
|---|---|---|---|
| **MOD-01** | `src/config.py` | Simulation configuration, state models, jitter perturbation, YAML serialization | 9 (Grade B) |
| **MOD-02** | `src/macro.py` | MacroEnvironment, LiveDataOracle, Cholesky correlated Wiener processes, CIR processes | 43 (Grade F) |
| **MOD-03** | `src/exchanges.py` | COMEX, LBMA, SGE Arbitrage, India IIBX Vault physical liquidity dynamics | 6 (Grade B) |
| **MOD-04** | `src/stakeholders.py` | 24+ market participants (miners, hoarders, banks, hedge funds, sovereign buyers) | 16 (Grade C) |
| **MOD-05** | `src/engine.py` | Core simulation loop, supply-demand matching, dual-price discovery (paper vs physical) | 33 (Grade E) |
| **MOD-06** | `src/logger.py` | Structured event logging and file persistence | 4 (Grade A) |
| **MOD-07** | `src/realworld.py` | External market data ingestion and network fallback mechanisms | 2 (Grade A) |

---

## 3. White-Box Test Design Techniques (ISO/IEC/IEEE 29119-4)

The test suite in `QA whitebox/` implements the following structural techniques specified in **ISO/IEC/IEEE 29119-4 Clause 7**:

### 3.1 Statement Testing (Clause 7.2)
- **Objective:** Exercise every executable statement in the target codebase.
- **Coverage Item:** Executable code statements.
- **Metric:** Statement Coverage ($SC\% = \frac{\text{Statements Executed}}{\text{Total Executable Statements}} \times 100\%$).
- **Target:** $>95\%$ across all non-external modules; $100\%$ feasible coverage.

### 3.2 Branch / Decision Testing (Clause 7.3)
- **Objective:** Verify both outcomes (`TRUE` and `FALSE`) of all control flow decisions (if/elif/else conditions, loop exit conditions, exception handlers).
- **Coverage Item:** Control flow edges and decision branches.
- **Metric:** Branch Coverage ($BC\% = \frac{\text{Branches Executed}}{\text{Total Decision Outcomes}} \times 100\%$).
- **Target:** $>90\%$ across modules, verifying all nominal and corner branch paths.

### 3.3 Modified Condition/Decision Coverage (MC/DC) (Clause 7.6)
- **Objective:** Prove that each atomic Boolean condition in multi-condition compound decisions independently affects the decision outcome.
- **Requirement:** For each atomic condition $C_i$ in decision $D$, identify an **Independence Pair** of test cases:
  - In one test case, $C_i = \text{True}$ and $D = \text{Outcome}_1$.
  - In the paired test case, $C_i = \text{False}$ and $D = \text{Outcome}_2$.
  - All other atomic conditions $C_j$ ($j \ne i$) remain fixed or masked such that only $C_i$'s variation causes $D$'s outcome to change.
- **Target:** 100% of safety-critical compound decisions (e.g. LBMA bank runs, COMEX defaults, EFP cross-Atlantic arbitrage, margin controls).

### 3.4 Basis Path / Control Flow Testing
- **Objective:** Execute a linearly independent set of execution paths derived from McCabe's Cyclomatic Complexity:
  $$V(G) = E - N + 2P$$
  where $E$ = edges, $N$ = nodes, $P$ = connected components.
- **Target:** All high-complexity methods ($V(G) \ge 10$) must have distinct basis path test cases exercising each basis vector.

### 3.5 Data Flow Testing (Clause 7.7)
- **Objective:** Verify definition-use associations (DU-pairs: All-Defs, All-Uses, All-DU-Paths) for key numerical state variables.
- **Target Variables:** `physical_price`, `paper_price`, `vault_float`, `comex_deficit`, `lbma_deficit`, `scrap_fatigue_days`, `east_west_spread`.
- **Integrity Assertion:** Ensure no variable is used before definition (UR-anomaly), defined twice without intermediate use (DD-anomaly), or defined but never used (DU-dead anomaly).

---

## 4. Test Environment & Toolchain

- **Runtime:** Python 3.13.6 (64-bit) on Windows.
- **Test Framework:** `pytest` (>= 9.0) with `pytest-cov` (>= 7.0).
- **Branch Profiler:** `coverage.py` configured with `branch = true`.
- **Complexity Analyzer:** `radon` (>= 6.0) calculating McCabe's Cyclomatic Complexity.
- **Mocking & Isolation:** In-memory mocks for external APIs (`yfinance`, realworld oracles) to guarantee deterministic, offline-capable test execution.

---

## 5. Pass/Fail Criteria & Quality Gates

| Quality Metric | Standard Threshold | Project Target | Gate Verification Mechanism |
|---|---|---|---|
| **Test Case Pass Rate** | $100\%$ | $100\%$ (0 failures, 0 errors) | Automated pytest execution |
| **Statement Coverage (SC)** | $\ge 85\%$ | $\ge 90\%$ | `pytest --cov=src` |
| **Branch Coverage (BC)** | $\ge 75\%$ | $\ge 85\%$ | `pytest --cov-branch` |
| **MC/DC Critical Pairs** | $100\%$ | $100\%$ for target compound decisions | Dedicated MC/DC Truth Table test suite |
| **Data Flow Anomalies** | 0 detected | 0 detected | Static inspection & dynamic DU assert tests |
| **Execution Determinism** | $100\%$ | Identical seeded outcomes | Controlled pseudo-RNG fixture |

---

## 6. Deliverables & Organization

All white-box artifacts reside within the dedicated `QA whitebox/` directory:
- `docs/ISO_29119_4_TEST_PLAN.md` (This document)
- `docs/ISO_29119_4_TEST_DESIGN_SPECIFICATION.md` (Control flow graphs, truth tables, DU pairs)
- `docs/ISO_29119_4_TRACEABILITY_MATRIX.md` (Bi-directional requirements to tests mapping)
- `docs/ISO_29119_4_TEST_SUMMARY_REPORT.md` (Execution results and formal sign-off)
- `test_wb_statement.py` (Clause 7.2 Statement testing)
- `test_wb_branch_decision.py` (Clause 7.3 Branch/decision testing)
- `test_wb_mcdc.py` (Clause 7.6 MC/DC testing)
- `test_wb_basis_path.py` (Basis path execution)
- `test_wb_data_flow.py` (Clause 7.7 Data flow DU verification)
- `run_whitebox_suite.py` (Automated CLI runner and reporter)
