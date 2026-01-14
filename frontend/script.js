// ===== การตั้งค่า Configuration =====
const API_URL = "http://127.0.0.1:8000";

// ===== ตัวแปรสถานะ (State) =====
let selectedCoin = "BTC";
let priceChart = null;
let predictionChart = null;
let autoSyncInterval = null;
let syncCountdownInterval = null;
let isAutoSyncOn = false;
let nextSyncTime = 0;

// ===== ข้อมูลเหรียญ (Coin Data) =====
const COINS = {
    BTC: { name: "Bitcoin", pair: "BTC/USDT", color: "#F7931A" },
    ETH: { name: "Ethereum", pair: "ETH/USDT", color: "#627EEA" }
};

// ===== การนำทางหน้าเว็บ (Page Navigation) =====
function showPage(pageName) {
    // ซ่อนทุกหน้า
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // แสดงหน้าที่เลือก
    document.getElementById(`page-${pageName}`).classList.add('active');

    // อัปเดตสถานะเมนูนำทาง
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) {
            item.classList.add('active');
        }
    });

    // เริ่มต้นกราฟเมื่อเปลี่ยนหน้ามาที่ prediction
    if (pageName === 'prediction' && !predictionChart) {
        initPredictionChart();
    }
}

// ===== ตัวจัดการ Tooltip =====
const getOrCreateTooltip = (chart) => {
    let tooltipEl = chart.canvas.parentNode.querySelector('div.chartjs-tooltip');
    if (!tooltipEl) {
        tooltipEl = document.createElement('div');
        tooltipEl.id = 'chartjs-tooltip';
        tooltipEl.className = 'chartjs-tooltip';
        chart.canvas.parentNode.appendChild(tooltipEl);
    }
    return tooltipEl;
};

const externalTooltipHandler = (context) => {
    const { chart, tooltip } = context;
    const tooltipEl = getOrCreateTooltip(chart);

    if (tooltip.opacity === 0) {
        tooltipEl.style.opacity = 0;
        return;
    }

    if (tooltip.body) {
        const titleLines = tooltip.title || [];
        const bodyLines = tooltip.body.map(b => b.lines);

        let innerHtml = '';

        titleLines.forEach(title => {
            const clockIcon = '<svg class="tooltip-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
            innerHtml += '<div class="tooltip-header">' + clockIcon + ' Time: ' + title + '</div>';
        });

        innerHtml += '<div class="tooltip-body">';
        bodyLines.forEach((body, i) => {
            const colors = tooltip.labelColors[i];
            const style = 'background:' + colors.backgroundColor + '; border-color:' + colors.borderColor;
            const span = '<span class="tooltip-color" style="' + style + '"></span>';
            const text = body[0];
            innerHtml += '<div class="tooltip-item">' + span + text + '</div>';
        });
        innerHtml += '</div>';

        tooltipEl.innerHTML = innerHtml;
    }

    const { offsetLeft: positionX, offsetTop: positionY } = chart.canvas;

    tooltipEl.style.opacity = 1;
    tooltipEl.style.left = positionX + tooltip.caretX + 'px';
    tooltipEl.style.top = positionY + tooltip.caretY + 'px';
    tooltipEl.style.font = tooltip.options.bodyFont.string;
};

// ===== เริ่มต้นกราฟหลัก (Main Chart) =====
function initChart() {
    const ctx = document.getElementById("priceChart").getContext("2d");

    const gradientWhite = ctx.createLinearGradient(0, 0, 0, 320);
    gradientWhite.addColorStop(0, "rgba(255, 255, 255, 0.15)");
    gradientWhite.addColorStop(1, "rgba(255, 255, 255, 0)");

    const gradientGreen = ctx.createLinearGradient(0, 0, 0, 320);
    gradientGreen.addColorStop(0, "rgba(34, 197, 94, 0.15)");
    gradientGreen.addColorStop(1, "rgba(34, 197, 94, 0)");

    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Actual Price",
                    data: [],
                    borderColor: "#ffffff",
                    backgroundColor: gradientWhite,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: "#ffffff"
                },
                {
                    label: "Predicted Price",
                    data: [],
                    borderColor: "#22c55e",
                    backgroundColor: gradientGreen,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: "#22c55e"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: "index"
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: false,
                    external: externalTooltipHandler,
                    callbacks: {
                        title: function (context) {
                            return context[0].label;
                        },
                        label: function (context) {
                            const value = context.raw;
                            const formattedValue = "$" + value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                            return " " + context.dataset.label + ": " + formattedValue;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(42, 42, 42, 0.4)" },
                    ticks: {
                        color: "#6b7280",
                        maxTicksLimit: 8,
                        maxRotation: 0
                    }
                },
                y: {
                    grid: { color: "rgba(42, 42, 42, 0.4)" },
                    ticks: { color: "#6b7280" }
                }
            }
        }
    });
}

// ===== เริ่มต้นกราฟทำนาย (Prediction Chart) =====
function initPredictionChart() {
    const ctx = document.getElementById("predictionChart").getContext("2d");

    predictionChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "Actual", data: [], borderColor: "#ffffff", borderWidth: 2, tension: 0.4, pointRadius: 0 },
                { label: "Predicted", data: [], borderColor: "#22c55e", borderWidth: 2, tension: 0.4, pointRadius: 0 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, labels: { color: "#9ca3af" } } },
            scales: {
                x: {
                    grid: { color: "rgba(42, 42, 42, 0.4)" },
                    ticks: {
                        color: "#6b7280",
                        maxTicksLimit: 8,
                        maxRotation: 0
                    }
                },
                y: { grid: { color: "rgba(42, 42, 42, 0.4)" }, ticks: { color: "#6b7280" } }
            }
        }
    });
}

// ===== โหลดข้อมูลทำนาย (หน้า Dashboard) =====
async function loadPrediction() {
    const timeframe = document.getElementById("timeframe").value;
    const predictBtn = document.querySelector(".predict-btn");

    predictBtn.innerHTML = '<span class="loading">Loading...</span>';
    predictBtn.disabled = true;

    try {
        const [predRes, btRes] = await Promise.all([
            fetch(`${API_URL}/predict?coin=${selectedCoin}&timeframe=${timeframe}`),
            fetch(`${API_URL}/backtest?coin=${selectedCoin}&timeframe=${timeframe}`)
        ]);

        const predData = await predRes.json();
        const btData = await btRes.json();

        updateChartWithHistory(predData);
        updateStats(predData, btData, timeframe);
        updateTrend(predData);

    } catch (error) {
        console.error("Error:", error);
        alert("Failed to load prediction. Check if backend is running.");
    } finally {
        predictBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>PREDICTION`;
        predictBtn.disabled = false;
    }
}

function updateChartWithHistory(data) {
    if (!data.times) return;
    priceChart.data.labels = data.times;
    priceChart.data.datasets[0].data = data.actual_prices;
    priceChart.data.datasets[1].data = data.predicted_prices;
    priceChart.update("default");
}

function updateStats(predData, btData, timeframe) {
    const formatPrice = (n) => "$" + n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const formatError = (n) => n.toLocaleString(undefined, { maximumFractionDigits: 0 });

    document.getElementById("currentPrice").textContent = formatPrice(predData.current);
    document.getElementById("predictedPrice").textContent = formatPrice(predData.predicted);
    document.getElementById("maeValue").textContent = formatError(btData.mae);
    document.getElementById("rmseValue").textContent = formatError(btData.rmse);
    document.getElementById("currentCoinLabel").textContent = COINS[selectedCoin].pair;

    const tfLabels = { "5m": "Next 5 Minutes", "1h": "Next 1 Hour", "4h": "Next 4 Hours" };
    document.getElementById("predictionLabel").textContent = tfLabels[timeframe] || "Prediction";
}

function updateTrend(data) {
    const indicator = document.getElementById("trendIndicator");
    const text = document.getElementById("trendText");

    if (data.predicted > data.current) {
        indicator.classList.remove("downtrend");
        text.textContent = "Uptrend";
    } else {
        indicator.classList.add("downtrend");
        text.textContent = "Downtrend";
    }
}

function updateCoinUI() {
    document.getElementById("coinName").textContent = COINS[selectedCoin].name;
    document.getElementById("coinPair").textContent = COINS[selectedCoin].pair;

    document.querySelectorAll(".coin-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.coin === selectedCoin);
    });
}

function setupCoinSelector() {
    document.querySelectorAll(".coin-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            selectedCoin = btn.dataset.coin;
            updateCoinUI();
            loadPrediction();
        });
    });
}

// ===== รันการทำนาย (หน้า Prediction) =====
async function runPrediction() {
    const coin = document.getElementById("pred-coin").value;
    const timeframe = document.getElementById("pred-timeframe").value;

    try {
        const [predRes, btRes] = await Promise.all([
            fetch(`${API_URL}/predict?coin=${coin}&timeframe=${timeframe}`),
            fetch(`${API_URL}/backtest?coin=${coin}&timeframe=${timeframe}`)
        ]);

        const pred = await predRes.json();
        const bt = await btRes.json();

        // อัปเดตกราฟ
        if (predictionChart && pred.times) {
            predictionChart.data.labels = pred.times;
            predictionChart.data.datasets[0].data = pred.actual_prices;
            predictionChart.data.datasets[1].data = pred.predicted_prices;
            predictionChart.update();
        }

        // อัปเดตค่าต่างๆ
        const formatPrice = (n) => "$" + n.toLocaleString(undefined, { minimumFractionDigits: 2 });
        document.getElementById("pred-current").textContent = formatPrice(pred.current);
        document.getElementById("pred-predicted").textContent = formatPrice(pred.predicted);
        document.getElementById("pred-trend").textContent = pred.predicted > pred.current ? "Uptrend" : "Downtrend";
        document.getElementById("pred-trend").style.color = pred.predicted > pred.current ? "#22c55e" : "#ef4444";
        document.getElementById("pred-errors").textContent = `${bt.mae.toFixed(0)} / ${bt.rmse.toFixed(0)}`;

    } catch (error) {
        console.error("Error:", error);
    }
}

// ===== โหลดข้อมูลประวัติ (History) =====
async function loadHistoryData() {
    const coin = document.getElementById("hist-coin").value;
    const timeframe = document.getElementById("hist-timeframe").value;
    const limit = document.getElementById("hist-limit").value;

    const tbody = document.getElementById("historyTableBody");
    tbody.innerHTML = '<tr><td colspan="8" class="loading-text">Loading...</td></tr>';

    try {
        const res = await fetch(`${API_URL}/ohlcv?coin=${coin}&timeframe=${timeframe}&limit=${limit}`);
        const data = await res.json();

        if (data.data && data.data.length > 0) {
            // อัปเดตจำนวน sync records
            const recordCountEl = document.getElementById("syncRecordCount");
            if (recordCountEl) recordCountEl.textContent = data.data.length;

            tbody.innerHTML = data.data.map(row => `
                <tr>
                    <td>${row.date}</td>
                    <td>${row.time}</td>
                    <td>${row.open.toLocaleString()}</td>
                    <td>${row.high.toLocaleString()}</td>
                    <td>${row.low.toLocaleString()}</td>
                    <td>${row.close.toLocaleString()}</td>
                    <td>${row.volume.toLocaleString()}</td>
                    <td class="${row.change >= 0 ? 'positive' : 'negative'}">${row.change}%</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="8" class="loading-text">No data available</td></tr>';
        }
    } catch (error) {
        console.error("Error:", error);
        tbody.innerHTML = '<tr><td colspan="8" class="loading-text">Error loading data</td></tr>';
    }
}

// ===== โหลดประสิทธิภาพโมเดล (Performance) =====
async function loadPerformance() {
    const coin = document.getElementById("perf-coin").value;

    try {
        const res = await fetch(`${API_URL}/performance?coin=${coin}`);
        const data = await res.json();

        const formatPrice = (n) => "$" + n.toLocaleString(undefined, { maximumFractionDigits: 2 });

        for (const tf of ["5m", "1h", "4h"]) {
            const perf = data.performance[tf];
            if (perf && !perf.error) {
                document.getElementById(`perf-${tf}-mae`).textContent = perf.mae.toFixed(2);
                document.getElementById(`perf-${tf}-rmse`).textContent = perf.rmse.toFixed(2);
                document.getElementById(`perf-${tf}-acc`).textContent = perf.accuracy.toFixed(2) + "%";
                document.getElementById(`perf-${tf}-current`).textContent = formatPrice(perf.current_price);
                document.getElementById(`perf-${tf}-pred`).textContent = formatPrice(perf.predicted_price);
            }
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

// ===== เริ่มต้นทำงาน =====
document.addEventListener("DOMContentLoaded", () => {
    initChart();
    setupCoinSelector();
    updateCoinUI();

    setTimeout(() => loadPrediction(), 500);
});

// ===== ตรรกะ Auto Sync =====
function toggleAutoSync() {
    const toggle = document.getElementById("autoSyncToggle");
    isAutoSyncOn = toggle.checked;

    const statusDot = document.getElementById("syncStatusDot");
    const statusText = document.getElementById("syncStatusText");

    if (isAutoSyncOn) {
        statusDot.classList.add("active");
        statusText.textContent = "Syncing...";
        statusText.style.color = "var(--accent-green)";
        startAutoSync();
    } else {
        statusDot.classList.remove("active");
        statusText.textContent = "Sync Off";
        statusText.style.color = "var(--text-muted)";
        stopAutoSync();
    }
}

function startAutoSync() {
    // Sync ทันที
    syncData();

    // ตั้งเวลาตามที่เลือก
    const intervalSeconds = parseInt(document.getElementById("syncInterval").value);
    nextSyncTime = Date.now() + (intervalSeconds * 1000);

    // ล้าง interval เดิม
    if (autoSyncInterval) clearInterval(autoSyncInterval);
    if (syncCountdownInterval) clearInterval(syncCountdownInterval);

    // เริ่มนับถอยหลัง
    syncCountdownInterval = setInterval(() => {
        const now = Date.now();
        const remaining = Math.max(0, Math.ceil((nextSyncTime - now) / 1000));
        document.getElementById("syncCountdown").textContent = remaining + "s";

        if (remaining <= 0) {
            nextSyncTime = now + (intervalSeconds * 1000);
            syncData();
        }
    }, 1000);
}

function stopAutoSync() {
    if (autoSyncInterval) clearInterval(autoSyncInterval);
    if (syncCountdownInterval) clearInterval(syncCountdownInterval);
    document.getElementById("syncCountdown").textContent = "--";
}

async function syncData() {
    const statusText = document.getElementById("syncStatusText");
    statusText.textContent = "Updating...";

    try {
        // 1. โหลดข้อมูล History (Primary Sync)
        await loadHistoryData();

        // 2. รีเฟรช Prediction หากอยู่ในหน้า prediction
        if (document.getElementById("page-prediction").classList.contains("active")) {
            await runPrediction();
        }

        // 3. รีเฟรช Performance หากอยู่ในหน้า performance
        if (document.getElementById("page-performance").classList.contains("active")) {
            await loadPerformance();
        }

        // อัปเดตสถิติ
        const now = new Date();
        document.getElementById("lastSyncTime").textContent = now.toLocaleTimeString();

        // รีเซ็ตข้อความสถานะ
        if (isAutoSyncOn) {
            statusText.textContent = "Active";
        }

    } catch (error) {
        console.error("Auto Sync Error:", error);
        statusText.textContent = "Error";
        statusText.style.color = "var(--accent-red)";
    }
}

document.getElementById("syncInterval").addEventListener("change", () => {
    if (isAutoSyncOn) {
        startAutoSync();
    }
});

// ===== เริ่มต้นทำงาน =====
document.addEventListener("DOMContentLoaded", () => {
    initChart();
    setupCoinSelector();
    updateCoinUI();

    setTimeout(() => loadPrediction(), 500);
});

document.getElementById("timeframe").addEventListener("change", loadPrediction);

// ==================== AI MANAGEMENT ====================
async function retrainModel() {
    const timeframe = document.getElementById('retrainTimeframe').value;
    const btn = document.getElementById('btnRetrain');
    const statusDiv = document.getElementById('retrainStatus');

    // Disable UI
    btn.disabled = true;
    btn.textContent = 'Training...';
    statusDiv.style.display = 'block';
    statusDiv.style.color = 'var(--accent-orange)';
    statusDiv.textContent = `Training ${timeframe} model in progress... please wait (~20-40s)`;

    try {
        const response = await fetch(`${API_URL}/retrain?timeframe=${timeframe}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.status === 'success') {
            statusDiv.style.color = 'var(--accent-green)';
            statusDiv.textContent = `Success! ${data.message}`;
            alert(`Model ${timeframe} retrained successfully!`);
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (error) {
        console.error('Retrain Error:', error);
        statusDiv.style.color = 'var(--accent-red)';
        statusDiv.textContent = `Error: ${error.message}`;
        alert(`Failed to retrain: ${error.message}`);
    } finally {
        // Re-enable UI
        btn.disabled = false;
        btn.textContent = 'Start Training';
    }
}
