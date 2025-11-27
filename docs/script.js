const apiUrl = "https://api.github.com/repos/tphang46/Carleton-Mail-Delivery-Robot-2025/contents/src/tools/logs/runs";

let allRunsData = [];
let metricsKeys = [];

// Fetch list of run files and all data upfront
async function fetchRunFiles() {
    const response = await fetch(apiUrl);
    const files = await response.json();

    const runListDiv = document.getElementById("run-list");
    runListDiv.innerHTML = "";

    const runPromises = [];

    for (let file of files) {
        if (file.name.endsWith(".txt")) {
            const btn = document.createElement("button");
            btn.textContent = file.name;
            btn.onclick = () => displayCards(allRunsData.find(d => d.run === file.name));
            runListDiv.appendChild(btn);

            // load all runs upfront
            runPromises.push(fetch(file.download_url).then(res => res.text()).then(text => {
                const metrics = parseRunText(text);
                metrics.run = file.name;
                allRunsData.push(metrics);
            }));
        }
    }

    // wait for all runs to load, then plot graphs
    await Promise.all(runPromises);

    if (allRunsData.length > 0) {
        metricsKeys = Object.keys(allRunsData[0]).filter(k => k !== "run");
        displayGraphs();
    }
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
        if (key === "run") continue;
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

    metricsKeys.forEach(metric => {
        const div = document.createElement("div");
        div.className = "graph";
        graphsDiv.appendChild(div);

        const trace = {
            x: allRunsData.map(d => d.run),
            y: allRunsData.map(d => d[metric]),
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

fetchRunFiles();
