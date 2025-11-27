const apiUrl = "https://api.github.com/repos/tphang46/Carleton-Mail-Delivery-Robot-2025/contents/src/tools/logs/runs";

let allRunsData = [];
let metricsKeys = [];

const colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
    '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
    '#bcbd22', '#17becf'
];

// Fetch all run files
async function fetchRunFiles() {
    const response = await fetch(apiUrl);
    const files = await response.json();

    const runListDiv = document.getElementById("run-list");
    runListDiv.innerHTML = "";

    const runPromises = files
        .filter(file => file.name.endsWith(".txt"))
        .map(async file => {
            const text = await fetch(file.download_url).then(res => res.text());
            const metrics = parseRunText(text);
            metrics.run = file.name;
            allRunsData.push(metrics);

            // create a button for this run
            const btn = document.createElement("button");
            btn.textContent = file.name;
            btn.className = "run-btn";
            btn.onclick = () => displayCards(metrics);
            runListDiv.appendChild(btn);
        });

    await Promise.all(runPromises);

    if (allRunsData.length > 0) {
        metricsKeys = Object.keys(allRunsData[0]).filter(k => k !== "run");
        displayGraphs();
    } else {
        console.warn("No run data loaded!");
    }
}

// Parse run txt
function parseRunText(text) {
    const lines = text.split("\n");
    const data = {};
    lines.forEach(line => {
        if (line.includes("=")) {
            const [key, value] = line.split("=");
            data[key.trim()] = isNaN(parseFloat(value)) ? value : parseFloat(value);
        }
    });
    return data;
}

// Display metric cards for a single run
function displayCards(metrics) {
    const cardsDiv = document.getElementById("cards");
    cardsDiv.innerHTML = "";

    for (let key in metrics) {
        if (key === "run") continue;
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `<strong>${key}</strong>: ${metrics[key]}`;
        cardsDiv.appendChild(card);
    }

    document.getElementById("run-details").style.display = "block";
}

// Display graphs
function displayGraphs() {
    const graphsDiv = document.getElementById("graphs");
    graphsDiv.innerHTML = "";

    metricsKeys.forEach((metric, index) => {
        const div = document.createElement("div");
        div.className = "graph";
        graphsDiv.appendChild(div);

        const trace = {
            x: allRunsData.map(d => d.run),
            y: allRunsData.map(d => d[metric]),
            type: 'scatter',
            mode: 'lines+markers',
            name: metric,
            line: { color: colors[index % colors.length], width: 3 },
            marker: { size: 6 },
            text: allRunsData.map(d => `${metric}: ${d[metric]}`),
            hoverinfo: 'x+text'
        };

        const layout = {
            title: metric,
            xaxis: { title: 'Run', tickangle: -45 },
            yaxis: { title: metric },
            margin: { t: 50, l: 60, r: 30, b: 60 }
        };

        Plotly.newPlot(div, [trace], layout, { responsive: true });
    });
}

// Initial fetch
fetchRunFiles();
