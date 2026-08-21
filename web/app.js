document.addEventListener('DOMContentLoaded', () => {
    // 1. DATASET DEFINITIONS
    const silverData = {
        historical: [
            { year: 2019, supply: 1018.3, demand: 991.4, balance: 26.9, price: 16.20 },
            { year: 2020, supply: 958.0, demand: 907.0, balance: 51.0, price: 20.55 },
            { year: 2021, supply: 997.4, demand: 1067.0, balance: -69.6, price: 25.14 },
            { year: 2022, supply: 985.1, demand: 1225.5, balance: -240.4, price: 21.73 },
            { year: 2023, supply: 1015.9, demand: 1185.8, balance: -169.9, price: 23.35 },
            { year: 2024, supply: 1024.0, demand: 1195.0, balance: -171.0, price: 28.27 },
            { year: 2025, supply: 1031.0, demand: 1236.0, balance: -40.3, price: 31.50 },
            { year: 2026, supply: 1038.0, demand: 1284.3, balance: -46.3, price: 58.00 }
        ],
        byproduct: {
            "Lead & Zinc": 30.0,
            "Copper": 27.0,
            "Primary Silver": 26.0,
            "Gold": 16.0,
            "Other": 1.0
        },
        solarTech: {
            "PERC (Legacy)": 10.5,
            "TOPCon (Current)": 13.8,
            "HJT (Next-Gen)": 21.5,
            "Copper Plated": 0.0
        },
        scenarios: {
            years: [2025, 2026, 2027, 2028, 2029, 2030, 2035],
            Base_Case: [-40.3, -46.3, -80.0, -115.0, -149.0, -185.0, -210.0],
            Bull_Case: [-95.0, -130.0, -165.0, -195.0, -215.0, -245.0, -290.0],
            Bear_Case: [-15.0, 5.0, 15.0, 25.0, 30.0, 35.0, 45.0],
            Supply_Crunch_Case: [-110.0, -150.0, -190.0, -230.0, -260.0, -290.0, -350.0]
        }
    };

    const vaultHistoryData = [
        { year: 2019, supply: 1018.3, demand: 991.4, stocks: 1780.0, freeFloat: 790.0 },
        { year: 2020, supply: 958.0, demand: 907.0, stocks: 1831.0, freeFloat: 830.0 },
        { year: 2021, supply: 997.4, demand: 1067.0, stocks: 1761.4, freeFloat: 760.0 },
        { year: 2022, supply: 985.1, demand: 1225.5, stocks: 1521.0, freeFloat: 610.0 },
        { year: 2023, supply: 1015.9, demand: 1185.8, stocks: 1351.1, freeFloat: 510.0 },
        { year: 2024, supply: 1024.0, demand: 1195.0, stocks: 1180.1, freeFloat: 450.0 },
        { year: 2025, supply: 1031.0, demand: 1236.0, stocks: 1139.8, freeFloat: 420.0 },
        { year: 2026, supply: 1038.0, demand: 1284.3, stocks: 1093.5, freeFloat: 400.0 },
        { year: 2027, supply: 1045.0, demand: 1325.0, stocks: 1013.5, freeFloat: 320.0 },
        { year: 2028, supply: 1052.0, demand: 1368.0, stocks: 897.5, freeFloat: 204.0 },
        { year: 2029, supply: 1060.0, demand: 1410.0, stocks: 747.5, freeFloat: 95.0 },
        { year: 2030, supply: 1070.0, demand: 1455.0, stocks: 562.5, freeFloat: 15.0 }
    ];

    let simPhysicalPrices = [];
    let simPaperPrices = [];
    let simYears = [];

    const miningAuditData = [
        { company: "Fresnillo plc", aisc: 22.20, output: 44.0 },
        { company: "KGHM Polska", aisc: 6.50, output: 41.5 },
        { company: "Newmont Corp", aisc: 12.80, output: 31.0 },
        { company: "Glencore plc", aisc: 11.50, output: 29.5 },
        { company: "Pan American Ag", aisc: 15.75, output: 26.0 },
        { company: "Polymetal", aisc: 16.50, output: 21.0 },
        { company: "Southern Copper", aisc: 8.20, output: 19.0 },
        { company: "Hindustan Zinc", aisc: 9.80, output: 18.5 },
        { company: "Hecla Mining", aisc: 11.28, output: 17.0 },
        { company: "First Majestic", aisc: 25.68, output: 14.0 }
    ];

    const chartInstances = {};
    let liveSpot = 58.00; // Updated by API

    // Fetch Live Simulation Data from FastAPI Backend
    let scenarioSimulationData = null;

    fetch('/api/simulate')
        .then(response => response.json())
        .then(apiResponse => {
            scenarioSimulationData = apiResponse;
            const baseScenario = apiResponse.base || { data: [], stats: {} };
            const simulatedData = baseScenario.data;
            
            // Group monthly data to yearly for Overview tab
            const yearlyDataMap = {};
            simulatedData.forEach(d => {
                const yr = d.year;
                if (!yearlyDataMap[yr]) {
                    yearlyDataMap[yr] = { year: yr, sum_physical: 0, sum_paper: 0, sum_supply: 0, sum_demand: 0, sum_vault: 0, count: 0 };
                }
                yearlyDataMap[yr].sum_physical += d.avg_physical;
                yearlyDataMap[yr].sum_paper += d.avg_paper;
                yearlyDataMap[yr].sum_supply += d.supply;
                yearlyDataMap[yr].sum_demand += d.demand;
                yearlyDataMap[yr].sum_vault += d.vault;
                yearlyDataMap[yr].count += 1;
            });
            
            const aggregatedYearlyData = Object.values(yearlyDataMap).map(yrData => ({
                year: yrData.year,
                avg_physical: yrData.sum_physical / yrData.count,
                avg_paper: yrData.sum_paper / yrData.count,
                supply: yrData.sum_supply / yrData.count,
                demand: yrData.sum_demand / yrData.count,
                vault: yrData.sum_vault / yrData.count
            }));

            // Merge Historical (2019-2025) with Simulated (2026-2035)
            const combinedVaultData = vaultHistoryData.filter(d => d.year < 2026);
            
            // Clear existing simulated arrays
            simYears.length = 0;
            simPhysicalPrices.length = 0;
            simPaperPrices.length = 0;
            
            aggregatedYearlyData.forEach(d => {
                simYears.push(d.year.toString());
                simPhysicalPrices.push(d.avg_physical);
                simPaperPrices.push(d.avg_paper);
                
                combinedVaultData.push({
                    year: d.year,
                    supply: d.supply * 12, // Annualized
                    demand: d.demand * 12, // Annualized
                    stocks: d.vault + 650, // Approximation of total above ground reserves
                    freeFloat: d.vault
                });
            });
            
            // Replace old array
            vaultHistoryData.length = 0;
            vaultHistoryData.push(...combinedVaultData);
            
            if (simulatedData && simulatedData.length > 0) {
                liveSpot = simulatedData[0].avg_physical || 58.00;
                
                const overviewSpotEl = document.getElementById('overviewLiveSpot');
                if (overviewSpotEl) overviewSpotEl.textContent = `$${liveSpot.toFixed(2)} / oz`;
                
                const priceTabSpotEl = document.getElementById('priceTabLiveSpot');
                if (priceTabSpotEl) priceTabSpotEl.textContent = `$${liveSpot.toFixed(2)} / oz`;
            }
            
            // Populate God-Tier Event Stats if available (using base case as overview stats)
            if (baseScenario.stats) {
                const s = baseScenario.stats;
                const squeezeEl = document.getElementById('statSqueezeProb');
                const aiBubbleEl = document.getElementById('statAIBubble');
                const mineStrikeEl = document.getElementById('statMineStrike');
                const retailCapEl = document.getElementById('statRetailCap');
                const refineryCrisisEl = document.getElementById('statRefineryCrisis');
                const solarEl = document.getElementById('statSolarSub');
                const baseMetalEl = document.getElementById('statBaseMetalShock');
                const exportBanEl = document.getElementById('statExportBan');
                const defenseEl = document.getElementById('statDefenseStockpile');
                const attackEl = document.getElementById('statPredatoryAttack');
                const comexDefaultEl = document.getElementById('statComexDefault');
                const lbmaDefaultEl = document.getElementById('statLbmaDefault');
                const etfRaidEl = document.getElementById('statEtfRaid');
                const jpmDumpEl = document.getElementById('statJpmDump');
                const billionaireRaidEl = document.getElementById('statBillionaireRaid');
                const retailMeltEl = document.getElementById('statRetailMelt');
                
                const iterations = s.iterations || 500;
                
                if (squeezeEl) squeezeEl.textContent = ((s.squeeze_count / iterations) * 100).toFixed(1) + '%';
                if (aiBubbleEl) aiBubbleEl.textContent = ((s.ai_bubble_burst_count / iterations) * 100).toFixed(1) + '%';
                if (mineStrikeEl) mineStrikeEl.textContent = ((s.mining_strike_count / iterations) * 100).toFixed(1) + '%';
                if (retailCapEl) retailCapEl.textContent = ((s.retail_cap_count / iterations) * 100).toFixed(1) + '%';
                if (refineryCrisisEl) refineryCrisisEl.textContent = ((s.energy_crisis_count / iterations) * 100).toFixed(1) + '%';
                if (solarEl) solarEl.textContent = s.substitution_trigger_count || 0;
                if (baseMetalEl) baseMetalEl.textContent = s.base_metal_shock_count || 0;
                if (exportBanEl) exportBanEl.textContent = s.export_ban_count || 0;
                if (defenseEl) defenseEl.textContent = s.defense_stockpile_count || 0;
                if (attackEl) attackEl.textContent = s.predatory_attack_count || 0;
                if (comexDefaultEl) comexDefaultEl.textContent = s.comex_default_count || 0;
                if (lbmaDefaultEl) lbmaDefaultEl.textContent = s.lbma_default_count || 0;
                if (etfRaidEl) etfRaidEl.textContent = s.etf_raid_count || 0;
                if (jpmDumpEl) jpmDumpEl.textContent = s.jpm_dump_count || 0;
                if (billionaireRaidEl) billionaireRaidEl.textContent = s.billionaire_raid_count || 0;
                if (retailMeltEl) retailMeltEl.textContent = s.retail_melt_count || 0;
            }

            // Inject Pure Squeeze Engine Stats
            if (baseScenario.stats) {
                const pStats = baseScenario.stats;
                const formatMoney = (val) => val ? '$' + val.toFixed(2) : 'Loading...';
                
                const avgPeakEl = document.getElementById('ui-avg-peak');
                if (avgPeakEl) avgPeakEl.textContent = formatMoney(pStats.avg_peak);
                
                const maxPeakEl = document.getElementById('ui-max-peak');
                if (maxPeakEl) maxPeakEl.textContent = formatMoney(pStats.max_peak);
                
                const etfRaidsEl = document.getElementById('ui-etf-raids');
                if (etfRaidsEl) etfRaidsEl.textContent = pStats.etf_raid_count || 0;
                
                const indiaArbEl = document.getElementById('ui-india-arb');
                if (indiaArbEl) indiaArbEl.textContent = pStats.india_ny_arbitrage_count || 0;
            }

            // Initialize Default Tab Charts after data is loaded
            initChartsForTab('tab-overview');
        })
        .catch(err => console.error("Error fetching simulation data:", err));


    // 2. LAZY CHART INITIALIZER ENGINE BY TAB
    function initChartsForTab(tabId) {
        setTimeout(() => {
            if (tabId === 'tab-overview') {
                initChart('chartSupplyDemand', () => new Chart(document.getElementById('chartSupplyDemand').getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: silverData.historical.map(d => d.year),
                        datasets: [
                            { label: 'Total Supply (Moz)', data: silverData.historical.map(d => d.supply), backgroundColor: 'rgba(56, 189, 248, 0.4)', borderColor: '#38bdf8', borderWidth: 1.5 },
                            { label: 'Total Demand (Moz)', data: silverData.historical.map(d => d.demand), backgroundColor: 'rgba(192, 132, 252, 0.4)', borderColor: '#c084fc', borderWidth: 1.5 },
                            { label: 'Market Balance (Moz)', data: silverData.historical.map(d => d.balance), type: 'line', borderColor: '#f87171', backgroundColor: '#f87171', borderWidth: 3, yAxisID: 'y1' }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } } }, scales: { x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }, y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }, y1: { position: 'right', ticks: { color: '#f87171' }, grid: { drawOnChartArea: false } } } }
                }));

                initChart('chartVaultAndFreeFloat', () => new Chart(document.getElementById('chartVaultAndFreeFloat').getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: vaultHistoryData.map(d => d.year),
                        datasets: [
                            { label: 'Annual Supply (Moz)', data: vaultHistoryData.map(d => d.supply), backgroundColor: 'rgba(56, 189, 248, 0.45)', borderColor: '#38bdf8', borderWidth: 1.5, yAxisID: 'ySupply' },
                            { label: 'Annual Demand (Moz)', data: vaultHistoryData.map(d => d.demand), backgroundColor: 'rgba(192, 132, 252, 0.45)', borderColor: '#c084fc', borderWidth: 1.5, yAxisID: 'ySupply' },
                            { label: 'Above-Ground Reserves (Moz)', data: vaultHistoryData.map(d => d.stocks), type: 'line', borderColor: '#fbbf24', backgroundColor: 'transparent', borderWidth: 3.5, pointRadius: 4, pointBackgroundColor: '#fbbf24', tension: 0.3, yAxisID: 'yVault' },
                            { label: 'Liquid Free Float Silver (Moz)', data: vaultHistoryData.map(d => d.freeFloat), type: 'line', borderColor: '#f87171', backgroundColor: 'rgba(248, 113, 113, 0.15)', fill: true, borderWidth: 3.5, pointRadius: 5, pointBackgroundColor: '#f87171', tension: 0.3, yAxisID: 'yVault' }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f0f4fc', font: { family: 'Inter', weight: '600' } } } }, scales: { x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }, ySupply: { position: 'left', title: { display: true, text: 'Annual Supply & Demand (Moz)', color: '#38bdf8' }, ticks: { color: '#94a3b8' } }, yVault: { position: 'right', title: { display: true, text: 'Vault Reserves & Free Float (Moz)', color: '#fbbf24' }, ticks: { color: '#fbbf24' }, grid: { drawOnChartArea: false } } } }
                }));

                initChart('chartPriceForecastOverview', () => new Chart(document.getElementById('chartPriceForecastOverview').getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: simYears,
                        datasets: [
                            { label: 'Physical Squeeze Price ($/oz)', data: simPhysicalPrices, borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: true, borderWidth: 3.5, pointRadius: 6, pointBackgroundColor: '#ef4444', tension: 0.3 },
                            { label: 'Paper Market (COMEX Force Majeure) ($/oz)', data: simPaperPrices, borderColor: '#94a3b8', backgroundColor: 'transparent', borderWidth: 2, borderDash: [3, 3], tension: 0.3 }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f0f4fc', font: { family: 'Inter', weight: '600' } } } }, scales: { x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }, y: { ticks: { color: '#94a3b8', callback: (v) => '$' + v }, grid: { color: 'rgba(255,255,255,0.05)' } } } }
                }));
            }

            if (tabId === 'tab-thesis') {
                initChart('chartMineByproduct', () => new Chart(document.getElementById('chartMineByproduct').getContext('2d'), {
                    type: 'doughnut',
                    data: { labels: Object.keys(silverData.byproduct), datasets: [{ data: Object.values(silverData.byproduct), backgroundColor: ['#38bdf8', '#34d399', '#fbbf24', '#c084fc', '#94a3b8'], borderWidth: 2, borderColor: '#131b2e' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#94a3b8' } } } }
                }));
            }

            if (tabId === 'tab-tech') {
                initChart('chartSolarTech', () => new Chart(document.getElementById('chartSolarTech').getContext('2d'), {
                    type: 'bar',
                    data: { labels: Object.keys(silverData.solarTech), datasets: [{ label: 'Silver Loading Intensity (mg / Wp)', data: Object.values(silverData.solarTech), backgroundColor: ['rgba(148, 163, 184, 0.6)', 'rgba(56, 189, 248, 0.8)', 'rgba(192, 132, 252, 0.8)', 'rgba(52, 211, 153, 0.5)'], borderRadius: 6 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' } } } }
                }));
            }

            if (tabId === 'tab-cot') {
                initChart('chartCotPositioning', () => new Chart(document.getElementById('chartCotPositioning').getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['Swap Dealers (Commercial)', 'Producer/Merchant', 'Managed Money (Funds)', 'Other Reportable', 'Non-Reportable (Retail)'], datasets: [{ label: 'Net Position (Moz Equivalent)', data: [-441.5, -122.0, 399.0, 73.5, 91.0], backgroundColor: ['rgba(248, 113, 113, 0.7)', 'rgba(251, 146, 60, 0.7)', 'rgba(52, 211, 153, 0.7)', 'rgba(56, 189, 248, 0.7)', 'rgba(192, 132, 252, 0.7)'], borderColor: ['#f87171', '#fb923c', '#34d399', '#38bdf8', '#c084fc'], borderWidth: 1.5 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#94a3b8', font: { size: 10 } } }, y: { ticks: { color: '#94a3b8', callback: (v) => v + ' Moz' } } } }
                }));

                initChart('chartEtfFlows', () => new Chart(document.getElementById('chartEtfFlows').getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['24 Q1', '24 Q2', '24 Q3', '24 Q4', '25 Q1', '25 Q2', '25 Q3', '25 Q4', '26 Q1', '26 Q2'], datasets: [{ label: 'Quarterly ETF Net Inflows (Moz)', data: [-6.2, 8.4, 5.1, 11.2, 14.5, 9.8, 10.2, 7.5, 28.5, 30.0], backgroundColor: 'rgba(56, 189, 248, 0.6)', borderColor: '#38bdf8', borderWidth: 1.5, yAxisID: 'yFlow' }, { label: 'Silver Spot Price ($/oz)', data: [22.80, 28.50, 29.10, 30.80, 31.50, 33.20, 35.80, 42.00, 52.50, liveSpot], type: 'line', borderColor: '#fbbf24', borderWidth: 3, pointRadius: 4, yAxisID: 'yPrice' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, yFlow: { position: 'left', ticks: { color: '#38bdf8', callback: (v) => v + ' Moz' } }, yPrice: { position: 'right', ticks: { color: '#fbbf24', callback: (v) => '$' + v }, grid: { drawOnChartArea: false } } } }
                }));
            }

            if (tabId === 'tab-arbitrage') {
                initChart('chartRegionalPrices', () => new Chart(document.getElementById('chartRegionalPrices').getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['London LBMA (Spot)', 'NY COMEX (Futures)', 'Shanghai SGE (Physical)', 'India MCX (Physical)'], datasets: [{ label: 'Equivalent USD Price ($/oz)', data: [liveSpot, liveSpot + 0.25, liveSpot + 5.80, liveSpot + 6.90], backgroundColor: ['rgba(148, 163, 184, 0.7)', 'rgba(56, 189, 248, 0.7)', 'rgba(251, 191, 36, 0.8)', 'rgba(52, 211, 153, 0.8)'], borderColor: ['#94a3b8', '#38bdf8', '#fbbf24', '#34d399'], borderWidth: 1.5 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { min: 45, max: 70, ticks: { color: '#94a3b8', callback: (v) => '$' + v } } } }
                }));

                initChart('chartIndiaImports', () => new Chart(document.getElementById('chartIndiaImports').getContext('2d'), {
                    type: 'bar',
                    data: { labels: [2021, 2022, 2023, 2024, 2025, 2026], datasets: [{ label: 'Physical Silver Imports (Tonnes)', data: [4500, 9450, 5600, 10800, 8900, 9800], backgroundColor: 'rgba(52, 211, 153, 0.6)', borderColor: '#34d399', borderWidth: 1.5, yAxisID: 'yTonnes' }, { label: 'Equivalent Moz Demand', data: [144.7, 303.8, 180.0, 337.2, 286.1, 315.0], type: 'line', borderColor: '#fbbf24', borderWidth: 3, pointRadius: 5, yAxisID: 'yMoz' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, yTonnes: { position: 'left', ticks: { color: '#34d399', callback: (v) => v + ' T' } }, yMoz: { position: 'right', ticks: { color: '#fbbf24', callback: (v) => v + ' Moz' }, grid: { drawOnChartArea: false } } } }
                }));
            }

            if (tabId === 'tab-geopolitics') {
                initChart('chartCountryRisk', () => new Chart(document.getElementById('chartCountryRisk').getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['Mexico', 'China', 'Peru', 'Poland', 'Chile', 'Russia', 'Bolivia'], datasets: [{ label: 'Country Risk Score (1-10)', data: [7.5, 6.0, 7.0, 2.0, 4.5, 8.5, 8.0], backgroundColor: 'rgba(248, 113, 113, 0.7)', borderColor: '#f87171', borderWidth: 1.5, yAxisID: 'yRisk' }, { label: 'Global Mine Supply Share (%)', data: [23.5, 13.0, 12.5, 5.0, 4.8, 5.3, 4.2], type: 'line', borderColor: '#38bdf8', borderWidth: 3, pointRadius: 5, yAxisID: 'yShare' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, yRisk: { position: 'left', min: 0, max: 10, ticks: { color: '#f87171' } }, yShare: { position: 'right', ticks: { color: '#38bdf8', callback: (v) => v + '%' }, grid: { drawOnChartArea: false } } } }
                }));

                initChart('chartSupplyDisruption', () => new Chart(document.getElementById('chartSupplyDisruption').getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['Mexican Open-Pit Ban', 'Peruvian Highway Blockades', 'Russian Sanctions & ENA Trade', 'Bolivian Reserve Nationalization'], datasets: [{ label: 'Estimated Disruption Drag (Moz/yr)', data: [30.0, 12.0, 6.0, 4.0], backgroundColor: ['rgba(248, 113, 113, 0.8)', 'rgba(251, 146, 60, 0.8)', 'rgba(251, 191, 36, 0.8)', 'rgba(192, 132, 252, 0.8)'], borderRadius: 6 }] },
                    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#94a3b8', callback: (v) => v + ' Moz' } }, y: { ticks: { color: '#94a3b8' } } } }
                }));
            }

            if (tabId === 'tab-recycling') {
                initChart('chartScrapBreakdown', () => new Chart(document.getElementById('chartScrapBreakdown').getContext('2d'), {
                    type: 'bar',
                    data: { labels: [2020, 2021, 2022, 2023, 2024, 2025, 2026], datasets: [{ label: 'Industrial & EO Catalysts (Moz)', data: [98.5, 92.4, 95.8, 94.2, 97.5, 100.2, 102.5], backgroundColor: 'rgba(56, 189, 248, 0.7)' }, { label: 'Jewelry & Silverware (Moz)', data: [51.2, 49.5, 51.0, 50.1, 51.8, 53.0, 54.0], backgroundColor: 'rgba(251, 146, 60, 0.7)' }, { label: 'Photographic Recovery (Moz)', data: [21.0, 20.8, 20.5, 20.3, 20.1, 20.4, 20.5], backgroundColor: 'rgba(148, 163, 184, 0.7)' }, { label: 'Urban E-Waste Mining (Moz)', data: [11.4, 12.1, 13.3, 14.0, 14.6, 15.4, 16.0], backgroundColor: 'rgba(52, 211, 153, 0.7)' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { stacked: true, ticks: { color: '#94a3b8' } }, y: { stacked: true, ticks: { color: '#94a3b8', callback: (v) => v + ' Moz' } } } }
                }));

                initChart('chartPriceElasticity', () => new Chart(document.getElementById('chartPriceElasticity').getContext('2d'), {
                    type: 'line',
                    data: { labels: ['$35/oz', '$50/oz (Spot)', '$65/oz', '$85/oz', '$100/oz+'], datasets: [{ label: 'Projected Scrap Supply Output (Moz/yr)', data: [185.0, 193.0, 212.0, 245.0, 275.0], borderColor: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.2)', borderWidth: 3, pointRadius: 5, pointBackgroundColor: '#34d399', fill: true, tension: 0.3 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8', callback: (v) => v + ' Moz' } } } }
                }));
            }

            if (tabId === 'tab-defense') {
                initChart('chartDefenseDemand', () => new Chart(document.getElementById('chartDefenseDemand').getContext('2d'), {
                    type: 'bar',
                    data: { labels: [2024, 2025, 2026], datasets: [{ label: 'Guided Missile Thermal Batteries (Moz)', data: [3.2, 3.8, 4.5], backgroundColor: 'rgba(248, 113, 113, 0.7)' }, { label: 'Satellite Solar Arrays (Moz)', data: [4.2, 5.8, 7.5], backgroundColor: 'rgba(56, 189, 248, 0.7)' }, { label: 'Mil Radar & RF Waveguides (Moz)', data: [2.8, 3.2, 3.8], backgroundColor: 'rgba(251, 146, 60, 0.7)' }, { label: 'Defense Optical & Laser Optics (Moz)', data: [1.5, 1.8, 2.2], backgroundColor: 'rgba(192, 132, 252, 0.7)' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { stacked: true, ticks: { color: '#94a3b8' } }, y: { stacked: true, ticks: { color: '#94a3b8', callback: (v) => v + ' Moz' } } } }
                }));

                initChart('chartSatelliteForecast', () => new Chart(document.getElementById('chartSatelliteForecast').getContext('2d'), {
                    type: 'bar',
                    data: { labels: [2024, 2025, 2026, 2028, 2030], datasets: [{ label: 'Satellites Deployed', data: [3200, 4500, 5800, 8200, 11500], backgroundColor: 'rgba(192, 132, 252, 0.5)', borderColor: '#c084fc', borderWidth: 1.5, yAxisID: 'y' }, { label: 'Satellite Ag Demand (Moz)', data: [4.2, 5.8, 7.5, 10.8, 15.0], type: 'line', borderColor: '#38bdf8', backgroundColor: '#38bdf8', borderWidth: 3, pointRadius: 4, tension: 0.3, yAxisID: 'y1' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8', callback: (v) => v + ' Sat' } }, y1: { position: 'right', ticks: { color: '#38bdf8', callback: (v) => v + ' Moz' }, grid: { drawOnChartArea: false } } } }
                }));
            }

            if (tabId === 'tab-macro') {
                initChart('chartSqueezeIndex', () => new Chart(document.getElementById('chartSqueezeIndex').getContext('2d'), {
                    type: 'line',
                    data: { labels: [2024, 2025, 2026, 2027, 2028], datasets: [{ label: 'Squeeze Probability Index Score (%)', data: [45.0, 68.0, 88.5, 96.0, 99.5], borderColor: '#f87171', backgroundColor: 'rgba(248, 113, 113, 0.2)', borderWidth: 3.5, pointRadius: 6, pointBackgroundColor: '#f87171', fill: true, tension: 0.3 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { min: 0, max: 100, ticks: { color: '#94a3b8', callback: (v) => v + '%' } } } }
                }));

                initChart('chartGsrMatrix', () => new Chart(document.getElementById('chartGsrMatrix').getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['$2,800 Gold', '$3,000 Gold', '$3,500 Gold', '$4,000 Gold'], datasets: [{ label: 'GSR 65:1 (50-Yr Avg)', data: [43.07, 46.15, 53.84, 61.53], backgroundColor: 'rgba(148, 163, 184, 0.6)' }, { label: 'GSR 55:1 (2026 Spot)', data: [50.90, 54.54, 63.63, 72.72], backgroundColor: 'rgba(56, 189, 248, 0.6)' }, { label: 'GSR 35:1 (Bull Target)', data: [80.00, 85.70, 100.00, 114.28], backgroundColor: 'rgba(245, 158, 11, 0.7)' }, { label: 'GSR 25:1 (Squeeze Peak)', data: [112.00, 120.00, 140.00, 160.00], backgroundColor: 'rgba(248, 113, 113, 0.7)' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8', callback: (v) => '$' + v } } } }
                }));
            }

            if (tabId === 'tab-puresqueeze') {
                if (scenarioSimulationData && scenarioSimulationData.base) {
                    const sData = scenarioSimulationData.base.data;
                    const labels = sData.map(d => `Yr ${d.year - 2025} M${d.month} D${d.day || 1}`);
                    const physicalPrices = sData.map(d => d.avg_physical);
                    
                    initChart('chartPureSqueeze', () => new Chart(document.getElementById('chartPureSqueeze').getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Physical Squeeze Peak ($/oz)',
                                data: physicalPrices,
                                borderColor: '#ef4444',
                                backgroundColor: 'rgba(239, 68, 68, 0.25)',
                                borderWidth: 3.5,
                                pointRadius: 0,
                                fill: true,
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { labels: { color: '#94a3b8' } } },
                            scales: {
                                x: { ticks: { color: '#94a3b8', maxTicksLimit: 12 } },
                                y: { ticks: { color: '#ef4444', callback: (v) => '$' + v }, grid: { color: 'rgba(255,255,255,0.05)' } }
                            }
                        }
                    }));
                }
            }

            if (tabId === 'tab-mining') {
                initChart('chartMiningAISC', () => new Chart(document.getElementById('chartMiningAISC').getContext('2d'), {
                    type: 'bar',
                    data: { labels: miningAuditData.map(d => d.company), datasets: [{ label: 'AISC ($ / oz)', data: miningAuditData.map(d => d.aisc), backgroundColor: ['rgba(52, 211, 153, 0.7)', 'rgba(52, 211, 153, 0.7)', 'rgba(56, 189, 248, 0.7)', 'rgba(56, 189, 248, 0.7)', 'rgba(251, 191, 36, 0.7)', 'rgba(248, 113, 113, 0.7)'], borderRadius: 6, yAxisID: 'yAISC' }, { label: 'Annual Output (Moz)', data: miningAuditData.map(d => d.output), type: 'line', borderColor: '#c084fc', borderWidth: 3, pointRadius: 5, pointBackgroundColor: '#c084fc', yAxisID: 'yOutput' }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f0f4fc' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, yAISC: { position: 'left', title: { display: true, text: 'AISC Cost ($ / oz)', color: '#34d399' }, ticks: { color: '#94a3b8', callback: (v) => '$' + v } }, yOutput: { position: 'right', title: { display: true, text: 'Annual Output (Moz)', color: '#c084fc' }, ticks: { color: '#c084fc' }, grid: { drawOnChartArea: false } } } }
                }));
            }

            if (tabId === 'tab-scenarios') {
                const activeBtn = document.querySelector('.sim-scenario-btn.active');
                const activeScenario = activeBtn ? activeBtn.getAttribute('data-sim-scenario') : 'base';
                updateScenarioSimulationCharts(activeScenario);
            }

            if (tabId === 'tab-price') {
                initChart('chartPriceForecast', () => new Chart(document.getElementById('chartPriceForecast').getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: ['2025', '2026', '2027', '2028', '2029', '2030', '2035'],
                        datasets: [
                            { label: '⚡ Pure Physical Squeeze Peak (Zero External Dependency)', data: [45.00, 75.00, 105.00, 155.00, 185.00, 250.00, 280.00], borderColor: '#c084fc', backgroundColor: 'rgba(192, 132, 252, 0.15)', fill: true, borderWidth: 3.5, pointRadius: 6, pointBackgroundColor: '#c084fc', tension: 0.3 },
                            { label: 'Model Projected Macro Squeeze Peak (Gold Dependent)', data: [37.50, 75.00, 105.00, 155.00, 175.00, 205.00, 250.00], borderColor: '#ef4444', backgroundColor: 'transparent', borderWidth: 3, borderDash: [5, 5], pointRadius: 5, pointBackgroundColor: '#ef4444', tension: 0.3 },
                            { label: 'Bull Case Annual Avg ($/oz)', data: [37.50, 58.00, 75.00, 95.00, 110.00, 125.00, 185.00], borderColor: '#f59e0b', backgroundColor: 'transparent', borderWidth: 3, tension: 0.3 },
                            { label: 'Base Case Annual Avg ($/oz)', data: [31.50, 58.00, 64.00, 72.00, 78.00, 85.00, 115.00], borderColor: '#38bdf8', backgroundColor: 'transparent', borderWidth: 3, tension: 0.3 },
                            { label: 'Bear Case Annual Avg ($/oz)', data: [31.50, 58.00, 48.00, 45.00, 43.00, 42.00, 48.00], borderColor: '#94a3b8', backgroundColor: 'transparent', borderWidth: 2, borderDash: [3, 3], tension: 0.3 }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f0f4fc', font: { family: 'Inter', weight: '600' } } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8', callback: (v) => '$' + v } } } }
                }));

                initChart('chartScenarioPriceForecast', () => new Chart(document.getElementById('chartScenarioPriceForecast').getContext('2d'), {
                    type: 'line',
                    data: { 
                        labels: simYears, 
                        datasets: [
                            { label: 'Physical Squeeze Premium Path ($/oz)', data: simPhysicalPrices, borderColor: '#c084fc', backgroundColor: 'transparent', borderWidth: 3, tension: 0.3 }, 
                            { label: 'Paper Market (Force Majeure) ($/oz)', data: simPaperPrices, borderColor: '#94a3b8', backgroundColor: 'transparent', borderWidth: 2, borderDash: [3, 3], tension: 0.3 }
                        ] 
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f0f4fc' } } }, scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8', callback: (v) => '$' + v } } } }
                }));
            }
        }, 80);
    }

    function initChart(canvasId, creatorFn) {
        const el = document.getElementById(canvasId);
        if (!el) return;

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].resize();
            chartInstances[canvasId].update();
        } else {
            chartInstances[canvasId] = creatorFn();
        }
    }

    // 3. TAB SWITCHING LOGIC
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            const targetElem = document.getElementById(targetId);
            if (targetElem) {
                targetElem.classList.add('active');
                initChartsForTab(targetId);
            }
        });
    });

    // 4. INTERACTIVE CALCULATORS SETUP
    // Pure Squeeze Calculator
    const pureFloatSlider = document.getElementById('pureFreeFloatInput');
    const pureDeficitSlider = document.getElementById('pureDeficitInput');
    const pureFloatValDisp = document.getElementById('pureFreeFloatVal');
    const pureDeficitValDisp = document.getElementById('pureDeficitVal');
    const pureOutputDisp = document.getElementById('pureSqueezePeakOutput');
    const pureStatusDisp = document.getElementById('pureSqueezeStatusText');

    function calculatePureSqueezePeak() {
        if (!pureFloatSlider || !pureDeficitSlider) return;

        const floatVal = parseFloat(pureFloatSlider.value);
        const deficitVal = parseFloat(pureDeficitSlider.value);

        if (pureFloatValDisp) pureFloatValDisp.textContent = `${floatVal.toFixed(1)} Moz`;
        if (pureDeficitValDisp) pureDeficitValDisp.textContent = `-${deficitVal.toFixed(1)} Moz`;

        const baselineSpot = liveSpot;
        const ratio = deficitVal / floatVal;
        const scarcityMultiplier = Math.pow(1 + ratio, 1.65);
        const calculatedPeak = baselineSpot * scarcityMultiplier;

        if (pureOutputDisp) pureOutputDisp.textContent = `$${calculatedPeak.toFixed(2)} / oz`;

        if (pureStatusDisp) {
            if (floatVal <= 50) {
                pureStatusDisp.textContent = "🔥 Physical Delivery Default / Vault Exhaustion";
                pureStatusDisp.style.color = "#f87171";
            } else if (floatVal <= 210) {
                pureStatusDisp.textContent = "⚡ Critical Scarcity Threshold Breached";
                pureStatusDisp.style.color = "#fbbf24";
            } else {
                pureStatusDisp.textContent = "🟡 Moderate Free Float Buffer";
                pureStatusDisp.style.color = "#38bdf8";
            }
        }
    }

    if (pureFloatSlider && pureDeficitSlider) {
        pureFloatSlider.addEventListener('input', calculatePureSqueezePeak);
        pureDeficitSlider.addEventListener('input', calculatePureSqueezePeak);
        calculatePureSqueezePeak();
    }

    // Substitution Calculator
    const slider = document.getElementById('silverPriceInput');
    const priceValDisplay = document.getElementById('priceVal');
    const resultBox = document.getElementById('substitutionResult');

    function updateSubstitutionCalculator(price) {
        if (!priceValDisplay || !resultBox) return;
        priceValDisplay.textContent = `$${parseFloat(price).toFixed(2)}`;

        let html = '';
        if (price < 35) {
            html = `<strong>Price Level: $${price} / oz</strong><br><span style="color:#34d399">Low Substitution Pressure</span>: Silver remains economic for standard screen-printed PV paste.`;
        } else if (price >= 35 && price < 50) {
            html = `<strong>Price Level: $${price} / oz</strong><br><span style="color:#38bdf8">Moderate Thrifting Acceleration</span>: Solar module makers mandate SMBB wire technology.`;
        } else if (price >= 50 && price < 70) {
            html = `<strong>Price Level: $${price} / oz</strong><br><span style="color:#fbbf24">High Substitution Threshold</span>: Copper electroplating lines become economically viable.`;
        } else {
            html = `<strong>Price Level: $${price} / oz</strong><br><span style="color:#f87171">Critical Substitution Pressure ($70+ / oz)</span>: Industrial consumers forcefully transition away from pure silver.`;
        }
        resultBox.innerHTML = html;
    }

    if (slider) {
        slider.addEventListener('input', (e) => updateSubstitutionCalculator(e.target.value));
        updateSubstitutionCalculator(slider.value);
    }

    // Dynamic Scenario button clicks
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.sim-scenario-btn');
        if (!btn) return;
        
        document.querySelectorAll('.sim-scenario-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        const scenarioKey = btn.getAttribute('data-sim-scenario');
        updateScenarioSimulationCharts(scenarioKey);
    });

    function updateScenarioSimulationCharts(scenarioKey) {
        if (!scenarioSimulationData || !scenarioSimulationData[scenarioKey]) return;
        
        const sData = scenarioSimulationData[scenarioKey].data;
        const sStats = scenarioSimulationData[scenarioKey].stats;
        
        // Update Chart Titles
        const formattedName = scenarioKey.charAt(0).toUpperCase() + scenarioKey.slice(1) + " Scenario";
        document.getElementById('simChartTitle1').textContent = `${formattedName}: Supply, Demand & Liquid Vault Reserves (Monthly)`;
        document.getElementById('simChartTitle2').textContent = `${formattedName}: Physical vs Paper Price Path (Monthly)`;
        
        // Update Audit Stats
        const den = sStats.iterations || 500;
        const getPct = (val) => val !== undefined ? ((val / den) * 100).toFixed(1) + '%' : '0.0%';
        
        document.getElementById('simSqueezeProb').textContent = getPct(sStats.squeeze_count);
        document.getElementById('simAIBubble').textContent = getPct(sStats.ai_bubble_burst_count);
        document.getElementById('simMineStrike').textContent = getPct(sStats.mining_strike_count);
        document.getElementById('simRetailCap').textContent = getPct(sStats.retail_cap_count);
        document.getElementById('simRefineryCrisis').textContent = getPct(sStats.energy_crisis_count);
        document.getElementById('simSolarSub').textContent = sStats.substitution_trigger_count || 0;
        document.getElementById('simBaseMetalShock').textContent = sStats.base_metal_shock_count || 0;
        document.getElementById('simExportBan').textContent = sStats.export_ban_count || 0;
        document.getElementById('simDefenseStockpile').textContent = sStats.defense_stockpile_count || 0;
        document.getElementById('simPredatoryAttack').textContent = sStats.predatory_attack_count || 0;
        
        document.getElementById('simComexDefault').textContent = sStats.comex_default_count || 0;
        document.getElementById('simLbmaDefault').textContent = sStats.lbma_default_count || 0;
        document.getElementById('simEtfRaid').textContent = sStats.etf_raid_count || 0;
        
        document.getElementById('simJpmDump').textContent = sStats.jpm_dump_count || 0;
        document.getElementById('simBillionaireRaid').textContent = sStats.billionaire_raid_count || 0;
        document.getElementById('simRetailMelt').textContent = sStats.retail_melt_count || 0;
        
        // Scenario Labels & Lines for daily data: "Yr X Mo Y Day Z"
        const labels = sData.map(d => `Yr ${d.year - 2025} M${d.month} D${d.day || 1}`);
        
        const physicalPrices = sData.map(d => d.avg_physical);
        const paperPrices = sData.map(d => d.avg_paper);
        const supplyData = sData.map(d => d.supply);
        const demandData = sData.map(d => d.demand);
        const vaultData = sData.map(d => d.vault);
        
        // Destroy old Chart instances if they exist
        if (chartInstances['chartSimSupplyDemandVault']) {
            chartInstances['chartSimSupplyDemandVault'].destroy();
            chartInstances['chartSimSupplyDemandVault'] = null;
        }
        if (chartInstances['chartSimPricePath']) {
            chartInstances['chartSimPricePath'].destroy();
            chartInstances['chartSimPricePath'] = null;
        }
        
        // Create Chart 1: Supply, Demand & Vault (Dual-Axis)
        const ctx1 = document.getElementById('chartSimSupplyDemandVault').getContext('2d');
        chartInstances['chartSimSupplyDemandVault'] = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Demand (Moz)', data: demandData, borderColor: '#ef4444', backgroundColor: 'transparent', borderWidth: 2, tension: 0.2, yAxisID: 'y' },
                    { label: 'Supply (Moz)', data: supplyData, borderColor: '#38bdf8', backgroundColor: 'transparent', borderWidth: 2, tension: 0.2, yAxisID: 'y' },
                    { label: 'COMEX Free Float (Moz)', data: vaultData, borderColor: '#c084fc', backgroundColor: 'rgba(192, 132, 252, 0.1)', fill: true, borderWidth: 3, tension: 0.2, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#f0f4fc' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8', maxTicksLimit: 12 } },
                    y: { type: 'linear', display: true, position: 'left', ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Supply/Demand (Moz)', color: '#94a3b8' } },
                    y1: { type: 'linear', display: true, position: 'right', ticks: { color: '#94a3b8' }, grid: { drawOnChartArea: false }, title: { display: true, text: 'Vault Reserves (Moz)', color: '#94a3b8' } }
                }
            }
        });
        
        // Create Chart 2: Physical vs Paper Price Path
        const ctx2 = document.getElementById('chartSimPricePath').getContext('2d');
        chartInstances['chartSimPricePath'] = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Physical Price ($/oz)', data: physicalPrices, borderColor: '#c084fc', backgroundColor: 'transparent', borderWidth: 3.5, tension: 0.2 },
                    { label: 'Paper Price ($/oz)', data: paperPrices, borderColor: '#94a3b8', backgroundColor: 'transparent', borderWidth: 2, borderDash: [4, 4], tension: 0.2 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#f0f4fc' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8', maxTicksLimit: 12 } },
                    y: { ticks: { color: '#94a3b8', callback: (v) => '$' + v }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Price ($/oz)', color: '#94a3b8' } }
                }
            }
        });
    }

    // The default tab is now initialized inside the fetch callback above
});
