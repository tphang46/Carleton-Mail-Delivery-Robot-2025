const apiUrl = "https://api.github.com/repos/tphang46/Carleton-Mail-Delivery-Robot-2025/contents/src/tools/logs/runs";

let runData = [];

// Fetch list of run files
async function fetchRunFiles() {
    const response = await fetch(apiUrl);
    const files = await response.json();

    const runListDiv = document.getElementById("run-list");
    runListDiv.innerHTML = "";

    for (let file of files) {
        if (file.name.endsWith(".txt")) {
            const btn = document.createElement("button");
            btn.textContent = file.name;
            btn.onclick = () => loadRun(file.download_url, file.name);
            runListDiv.appendChild(btn);
        }
    }
}

// Load a single run file when clicked
async function loadRun(url, runName) {
    const response = await fetch(url);
    const text = await response.text();

    const metrics = parseRunText(text);
    runData.push({run: runName, ...metrics});

    displayCards(metrics);
    displayGraphs();
}

// Parse run text file
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

// Display cards for clicked run
function displayCards(metrics) {
    const cardsDiv = document.getElementById("cards");
    cardsDiv.innerHTML = ""; // clear previous cards

    for (let key in metrics) {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `<strong>${key}</strong>: ${metrics[key]}`;
        cardsDiv.appendChild(card);
    }

    document.getElementById("run-details").style.display = "block";
}

// Display graphs for all runs (each metric vs run)
function displayGraphs() {
    const graphsDiv = document.getElementById("graphs");
    graphsDiv.innerHTML = "";

    if (runData.length === 0) return;

    const metrics = Object.keys(runData[0]).filter(k => k !== "run");

    metrics.forEach(metric => {
        const div = document.createElement("div");
        div.className = "graph";
        graphsDiv.appendChild(div);

        const trace = {
            x: runData.map(d => d.run),
            y: runData.map(d => d[metric]),
            type: 'bar'
        };

        const layout = {
            title: metric,
            xaxis: { title: 'Run' },
            yaxis: { title: metric }
        };

        Plotly.newPlot(div, [trace], layout);
    });
}

// Initial fetch
fetchRunFiles();
