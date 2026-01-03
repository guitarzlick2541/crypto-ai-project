async function loadData() {
    const res = await fetch("http://127.0.0.1:8000/history");
    const data = await res.json();

    const labels = data.map(r => r[3]).reverse();
    const actual = data.map(r => r[1]).reverse();
    const predicted = data.map(r => r[2]).reverse();

    const ctx = document.getElementById("chart").getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Actual Price",
                    data: actual,
                },
                {
                    label: "AI Predicted Price",
                    data: predicted,
                }
            ]
        }
    });
}
