"""
ISO/IEC/IEEE 29119-4 White-Box Testing Suite for Stakeholder Agents (src/stakeholders.py)
Objective: Maximize statement, branch, and edge-case coverage across all market participants.
"""
import pytest
from unittest.mock import patch

import config
import macro
import stakeholders

class TestStakeholdersWhiteBox:
    """White-box structural test suite for stakeholders.py."""

    def test_primary_miners_branches(self, clean_macro):
        """Test capex cycle, bankruptcy, withholding inventory, strikes, and military orders."""
        miner = stakeholders.PrimaryMiners(name="PrimaryMiners", annual_base_volume=230.0)

        # 1. High margin capex expansion cycle buildup
        miner.process_day(price=100.0, macro=clean_macro)
        assert miner.capex_expansion_cycle > 0

        # 2. Delayed supply bonus release when capex_expansion_cycle > 0.5
        miner.capex_expansion_cycle = 0.6
        out_capex = miner.process_day(price=100.0, macro=clean_macro)
        assert out_capex > 0

        # 3. Low price withholding inventory
        clean_macro.m2_inflation_index = 1.0
        miner.process_day(price=20.0, macro=clean_macro) # price < aisc ($25)
        assert miner.withheld_inventory > 0
        assert miner.mines_shutdown >= 1

        # 4. Severe depression price < aisc * 0.80
        miner.process_day(price=15.0, macro=clean_macro)

        # 5. Bankruptcy shutdown threshold
        miner.mines_shutdown = int(config.TRADING_DAYS * 1.5) + 5
        out_bankrupt = miner.process_day(price=15.0, macro=clean_macro)
        assert out_bankrupt == 0.0
        assert miner.daily_volume == 0

        # 6. Inventory release when price > aisc * 1.20
        miner_recovery = stakeholders.PrimaryMiners(name="PrimaryMiners", annual_base_volume=230.0)
        miner_recovery.withheld_inventory = 50.0
        out_recovery = miner_recovery.process_day(price=50.0, macro=clean_macro)
        assert out_recovery > miner_recovery.daily_volume

        # 7. Mining strike scenario
        clean_macro.mining_strike_active = True
        out_strike = miner_recovery.process_day(price=50.0, macro=clean_macro)
        assert out_strike < out_recovery

        # 8. Geopolitical high tension emergency production
        clean_macro.mining_strike_active = False
        clean_macro.geopolitical_tension_index = 90.0
        out_geo = miner_recovery.process_day(price=50.0, macro=clean_macro)
        assert out_geo > 0

    def test_byproduct_miners_shocks(self, clean_macro):
        """Test byproduct miners under base metal recession and copper crash."""
        byproduct = stakeholders.ByproductMiners(name="ByproductMiners", annual_base_volume=600.0)

        # Base metal recession active
        clean_macro.base_metal_recession_active = True
        clean_macro.copper_price_index = 0.70
        out_recession = byproduct.process_day(price=30.0, macro=clean_macro)
        assert out_recession < byproduct.initial_capacity

    def test_scrap_and_ewaste_refiners(self, clean_macro):
        """Test scrap fatigue when pool dries up and above-ground pool depletion."""
        scrap = stakeholders.ScrapRefiners(name="ScrapRefiners", annual_base_volume=150.0)
        # Dried up scrap pool triggers fatigue days counter
        clean_macro.global_scrap_pool = 0.0
        for _ in range(5):
            scrap.process_day(price=120.0, macro=clean_macro)
        assert scrap.scrap_fatigue_days > 0

        ewaste = stakeholders.EWasteRecyclers(name="EWasteRecyclers", annual_base_volume=40.0)
        clean_macro.global_ewaste_pool = 1.0 # Pool depleted
        out_ewaste = ewaste.process_day(price=50.0, macro=clean_macro)
        assert out_ewaste <= 1.0

    def test_deep_private_hoarders_buying(self, clean_macro):
        """Test deep private hoarders fundamentalist buying when price is low."""
        hoarders = stakeholders.DeepPrivateHoarders(name="DeepPrivateHoarders", annual_base_volume=0.0)
        hoarders.process_day(price=5.0, macro=clean_macro)
        assert hoarders.total_hoard > 0

    def test_solar_pv_substitution_and_thrifting(self, clean_macro):
        """Test solar PV thrifting, copper substitution, and high-price penalty."""
        solar = stakeholders.SolarPV(name="SolarPV", annual_base_volume=150.0)
        solar.substitution_triggered = True
        out_sub = solar.process_day(price=300.0, macro=clean_macro)
        assert out_sub < (solar.daily_volume * 0.5)

    def test_tech_ai_bubble_burst(self, clean_macro):
        """Test Tech AI demand collapse during bubble burst."""
        tech = stakeholders.Tech_AI(name="Tech_AI", annual_base_volume=80.0)
        clean_macro.ai_bubble_burst = True
        out_burst = tech.process_day(price=30.0, macro=clean_macro)
        assert out_burst < tech.daily_volume

    def test_gov_usa_defense_production_act(self):
        """Test Gov_USA Defense Production Act physical seizure."""
        usa = stakeholders.Gov_USA()
        # Reserves > 75: Normal
        assert usa.check_defense_production_act(vault_float=100.0) == 0.0
        # Reserves < 75: DPA triggered
        seizure = usa.check_defense_production_act(vault_float=60.0)
        assert seizure > 0.0
        assert usa.export_ban_active is True

    def test_gov_uk_bailout(self):
        """Test Gov_UK LBMA bailout execution and rejection."""
        uk = stakeholders.Gov_UK()
        assert uk.check_lbma_bailout(vault_float=10.0) is False
        assert uk.check_lbma_bailout(vault_float=0.0) is True
        assert uk.fiat_injections == 10.0

    def test_retail_investors_capitulation(self, clean_macro):
        """Test retail investors panic capitulation selling (80% volume collapse)."""
        retail = stakeholders.RetailInvestors(name="RetailInvestors", annual_base_volume=250.0)
        clean_macro.retail_capitulation = True
        out_cap = retail.process_day(price=30.0, macro=clean_macro)
        # Capitulation crushes retail volume to 20%
        assert out_cap < (retail.daily_volume * 0.5)

    def test_whale_syndicate_accumulation_and_halts(self):
        """Test whale syndicate buying and stopping when shorts are covered."""
        whale = stakeholders.WhaleSyndicate()
        whale.bank_vulnerability_score = 100.0
        # Trigger attack with forced random
        with patch("random.random", return_value=0.0):
            buy = whale.process_accumulation(comex_float=100.0, bank_short_position=250.0)
            assert buy > 0.0

    def test_predatory_hedge_fund_attack_lifecycle(self, clean_macro):
        """Test predatory hedge fund COMEX raid and squeeze."""
        phf = stakeholders.PredatoryHedgeFund()
        # Trigger attack with forced random
        with patch("random.random", return_value=0.0):
            attack = phf.process_attack(comex_float=60.0, physical_price=35.0, macro=clean_macro)
            assert attack > 0.0
            assert phf.is_squeezing is True

    def test_options_market_makers_gamma_squeeze(self):
        """Test options dealer delta hedging during high implied volatility."""
        omm = stakeholders.OptionsMarketMakers()
        omm.implied_volatility = 0.60 # > 0.40 generates positive gamma demand
        hedge_buy = omm.process_delta_hedge(retail_demand=1.0, price_momentum=1.3)
        assert hedge_buy > 0.0

        # Unwind hedges when IV drops and momentum breaks
        omm.implied_volatility = 0.25
        hedge_sell = omm.process_delta_hedge(retail_demand=0.1, price_momentum=0.8)
        assert hedge_sell < 0.0

    def test_exchange_margin_controls_hike(self):
        """Test exchange margin hike trigger on sustained run."""
        margin_ctrl = stakeholders.ExchangeMarginControls()
        # Process 10 days of strong momentum (>20% run)
        for _ in range(10):
            margin_ctrl.process_day(price_momentum=1.25, implied_volatility=0.60)
        assert margin_ctrl.margin_hike_active is True

    def test_bullion_bank_shorts_panic_and_recovery(self, clean_macro):
        """Test bullion bank shorts margin call, forced covering panic, and relief."""
        bbs = stakeholders.BullionBankShorts()
        bbs.average_short_entry = 30.0
        bbs.short_position = 300.0

        # Force majeure clears position
        bbs.check_forced_covering(price=50.0, macro=clean_macro, force_majeure_active=True)
        assert bbs.short_position == 0

        # Re-initialize and test panic cover when risk tolerance drops
        bbs2 = stakeholders.BullionBankShorts()
        bbs2.risk_tolerance = 10.0 # Under 20.0 triggers panic cover
        cover = bbs2.check_forced_covering(price=80.0, macro=clean_macro, force_majeure_active=False)
        assert cover > 0.0

        # Price relief increases risk tolerance
        bbs3 = stakeholders.BullionBankShorts()
        bbs3.average_short_entry = 50.0
        bbs3.risk_tolerance = 50.0
        bbs3.check_forced_covering(price=20.0, macro=clean_macro, force_majeure_active=False)
        assert bbs3.risk_tolerance > 50.0

    def test_unallocated_account_holders_run(self):
        """Test unallocated account holders confidence drop on low vaults."""
        uah = stakeholders.UnallocatedAccountHolders()
        # Drop vault below 100
        for _ in range(85):
            uah.check_bank_run(vault_float=50.0)
        # When confidence drops below 20, bank run triggers
        is_run = uah.check_bank_run(vault_float=50.0)
        assert is_run is True
        assert uah.bank_run_active is True
