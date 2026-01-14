
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
