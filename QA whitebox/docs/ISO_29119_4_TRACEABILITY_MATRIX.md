# ISO/IEC/IEEE 29119-4 Traceability Matrix
**Document Identifier:** TM-ISO-29119-WB-001  
**Standard Reference:** ISO/IEC/IEEE 29119-3 & 29119-4  
**System Under Test:** Silver Analisis Simulation Engine  

---

## 1. Traceability Overview

This document provides bi-directional traceability linking source code control constructs, decision logic, and data flow paths to specific test cases across the structural testing suites implemented in `QA whitebox/`.

---

## 2. Master Traceability Matrix

| Requirement / Decision Item | Source Module & Lines | ISO 29119-4 Technique | Test Case ID | Test Script | Target Verification |
|---|---|---|---|---|---|
| **ST-CFG-01** | `src/config.py:78-93` | Clause 7.2 (Statement) | `test_stmt_config_jitter` | `test_wb_statement.py` | Full execution of `apply_jitter` recursion & perturbation |
| **ST-CFG-02** | `src/config.py:96-124` | Clause 7.2 (Statement) | `test_stmt_config_yaml_parser` | `test_wb_statement.py` | Full execution of YAML parsing & fallback branch handling |
| **ST-ENG-01** | `src/engine.py:140-144` | Clause 7.2 (Statement) | `test_stmt_engine_day_exception` | `test_wb_statement.py` | Catch loop exceptions, increment error stats |
| **ST-ENG-02** | `src/engine.py:328-341` | Clause 7.2 (Statement) | `test_stmt_engine_efp_active_month` | `test_wb_statement.py` | Trigger delivery month EFP lease spike |
| **ST-ENG-03** | `src/engine.py:386-398` | Clause 7.2 (Statement) | `test_stmt_engine_circuit_breakers` | `test_wb_statement.py` | Upper clamp (1.07/3.00), lower clamp (0.93), spike counter |
| **ST-ENG-04** | `src/engine.py:534-545` | Clause 7.2 (Statement) | `test_stmt_engine_peak_stats` | `test_wb_statement.py` | Verify peak_price, max_price, min_price updates |
| **ST-MAC-01** | `src/macro.py:18-48` | Clause 7.2 (Statement) | `test_stmt_macro_oracle_offline_fallback` | `test_wb_statement.py` | API failure handler, fallback default assignment |
| **ST-MAC-02** | `src/macro.py:108-114` | Clause 7.2 (Statement) | `test_stmt_macro_cholesky_fallback` | `test_wb_statement.py` | NumPy import failure / linear algebra fallback branch |
| **ST-MAC-03** | `src/macro.py:184-216` | Clause 7.2 (Statement) | `test_stmt_macro_shocks_lifecycles` | `test_wb_statement.py` | CBDC launch, mining strikes, energy crisis countdown |
| **ST-EXC-01** | `src/exchanges.py:35-41`| Clause 7.2 (Statement) | `test_stmt_exchange_bank_run_drain` | `test_wb_statement.py` | Unallocated drain, vault floor, claims reduction |
| **ST-EXC-02** | `src/exchanges.py:57-63`| Clause 7.2 (Statement) | `test_stmt_exchange_iibx_empty` | `test_wb_statement.py` | Domestic demand unfulfilled, inventory exhaustion |
| **BR-ENG-01** | `src/engine.py:155` | Clause 7.3 (Branch) | `test_br_hoard_depletion` | `test_wb_branch_decision.py` | True & False outcomes for hoard depletion threshold |
| **BR-ENG-02** | `src/engine.py:211` | Clause 7.3 (Branch) | `test_br_ewaste_ratio_threshold` | `test_wb_branch_decision.py` | True ($P>100$) and False ($P \le 100$) ewaste recovery ratio |
| **BR-ENG-03** | `src/engine.py:251` | Clause 7.3 (Branch) | `test_br_billionaire_dynamic_supply`| `test_wb_branch_decision.py` | True ($flow < 0$) dynamic supply add, False ($flow \ge 0$) |
| **BR-ENG-04** | `src/engine.py:356` | Clause 7.3 (Branch) | `test_br_drift_extinction_branch` | `test_wb_branch_decision.py` | Vaults $<10$ Moz (500% drift cap) vs $\ge 10$ Moz (25% cap) |
| **BR-ENG-05** | `src/engine.py:408` | Clause 7.3 (Branch) | `test_br_paper_drift_margin_vs_fm` | `test_wb_branch_decision.py` | Margin hike vs Force Majeure vs nominal paper drift |
| **BR-ENG-06** | `src/engine.py:471` | Clause 7.3 (Branch) | `test_br_comex_force_majeure` | `test_wb_branch_decision.py` | True & False for COMEX force majeure deficit clamping |
| **BR-ENG-07** | `src/engine.py:488` | Clause 7.3 (Branch) | `test_br_efp_arbitrage_flow` | `test_wb_branch_decision.py` | Trans-Atlantic flow: NY $\to$ London vs London $\to$ NY vs none |
| **BR-MAC-01** | `src/macro.py:130` | Clause 7.3 (Branch) | `test_br_copper_recession` | `test_wb_branch_decision.py` | GDP growth $<0$ vs $\ge 0$ copper dynamics |
| **BR-MAC-02** | `src/macro.py:136` | Clause 7.3 (Branch) | `test_br_oil_drift_tension` | `test_wb_branch_decision.py` | Geo tension $>75$ vs GDP $<-0.01$ vs baseline oil drift |
| **MC-EXC-01** | `src/exchanges.py:30` | Clause 7.6 (MC/DC) | `test_mcdc_lbma_bank_run` | `test_wb_mcdc.py` | Independence pairs for $\neg A \land (B \lor C)$ |
| **MC-EXC-02** | `src/exchanges.py:65` | Clause 7.6 (MC/DC) | `test_mcdc_iibx_lbma_drain` | `test_wb_mcdc.py` | Independence pairs for $\neg A \land \neg B$ |
| **MC-EXC-03** | `src/exchanges.py:13` | Clause 7.6 (MC/DC) | `test_mcdc_comex_eligible_transfer` | `test_wb_mcdc.py` | Independence pairs for $A \land B$ |
| **MC-EXC-04** | `src/exchanges.py:87` | Clause 7.6 (MC/DC) | `test_mcdc_sge_arbitrage` | `test_wb_mcdc.py` | Independence pairs for $A \land B$ |
| **MC-MAC-01** | `src/macro.py:161` | Clause 7.6 (MC/DC) | `test_mcdc_base_metal_recession` | `test_wb_mcdc.py` | Independence pairs for $A \land B$ |
| **MC-ENG-01** | `src/engine.py:528` | Clause 7.6 (MC/DC) | `test_mcdc_dual_default_bailout` | `test_wb_mcdc.py` | Independence pairs for $A \land B \land \neg C$ |
| **MC-ENG-02** | `src/engine.py:487` | Clause 7.6 (MC/DC) | `test_mcdc_efp_alive_check` | `test_wb_mcdc.py` | Independence pairs for $\neg A \land \neg B$ |
| **BP-ENG-01** | `src/engine.py:181` | Basis Path | `test_bp_demand_routing` | `test_wb_basis_path.py` | Exercise linearly independent basis paths in `_process_demand` |
| **BP-ENG-02** | `src/engine.py:456` | Basis Path | `test_bp_exchange_clearing` | `test_wb_basis_path.py` | Exercise linearly independent basis paths in `_update_exchanges_and_stats` |
| **BP-MAC-01** | `src/macro.py:86` | Basis Path | `test_bp_macro_simulate_day` | `test_wb_basis_path.py` | Exercise linearly independent basis paths in `simulate_day` |
| **BP-EXC-01** | `src/exchanges.py:27`| Basis Path | `test_bp_lbma_bank_run` | `test_wb_basis_path.py` | Exercise all 5 basis paths through `check_bank_run` |
| **DF-VAR-01** | `src/engine.py:32` | Clause 7.7 (Data Flow) | `test_df_physical_price_lifecycle` | `test_wb_data_flow.py` | All-Defs, All-Uses, All-DU-Paths for `physical_price` |
| **DF-VAR-02** | `src/engine.py:33` | Clause 7.7 (Data Flow) | `test_df_paper_price_lifecycle` | `test_wb_data_flow.py` | All-Defs, All-Uses for `paper_price` |
| **DF-VAR-03** | `src/exchanges.py:7` | Clause 7.7 (Data Flow) | `test_df_vault_floats_clearing` | `test_wb_data_flow.py` | All-Defs, All-Uses for COMEX & LBMA vault floats |
| **DF-VAR-04** | `src/engine.py:34` | Clause 7.7 (Data Flow) | `test_df_physical_premium_dynamics` | `test_wb_data_flow.py` | All-Defs, All-Uses for `physical_premium` |
| **DF-VAR-05** | `src/exchanges.py:73`| Clause 7.7 (Data Flow) | `test_df_sge_spread_bounds` | `test_wb_data_flow.py` | Definition, mutation, bounds clamp, reversion of `east_west_spread` |
