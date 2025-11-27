// script.js

const apiUrl = "https://api.github.com/repos/tphang46/Mail-Delivery-Robot/contents/src/tools/logs/runs";

async function fetchRunFiles() {
    try {
        const res = await fetch(apiUrl);
        if (!res.ok) throw new Error(`Failed to fetch runs: ${res.status}`);
        const files = await res.json();
        // Only .txt files
        return files.filter(f => f.name.endsWith(".txt"));
    } catch (err) {
        console.error(err);
        return [];
    }
}

async function fetchRunContent(file) {
    try {
        const res = await fetch(file.download_url);
        if (!res.ok) throw new Error(`Failed to fetch ${file.name}`);
        const text = await res.text();
        return parseRunText(text);
    } catch (err) {
        console.error(err);
        return null;
    }
}

// Parse the txt file into a JS object
function parseRunText(text) {
    const lines = text.split('\n').filter(l => l.trim() !== '');
    const data = {};
    for (let line of lines) {
        const [key, value] = line.split('=');
        data[key.trim()] = value.trim();
    }
    return data;
}

// Display list of runs
async function displayRunList() {
    const runListDiv = document.getElementById('run-list');
    runListDiv.innerHTML = '';

    const files = await fetchRunFiles();
    if (files.length === 0) {
        runListDiv.textContent = 'No runs found.';
        return;
    }

    files.forEach(file => {
        const btn = document.createElement('button');
        btn.textContent = file.name;
        btn.style.display = 'block';
        btn.style.margin = '5px 0';
        btn.onclick = async () => displayRunDetails(file);
        runListDiv.appendChild(btn);
    });
}

// Display selected run details
async function displayRunDetails(file) {
    const runDetails = document.getElementById('run-details');
    const data = await fetchRunContent(file);
    if (!data) return;

    runDetails.textContent = JSON.stringify(data, null, 2);

    // Update graph
    displayBatteryGraph(data);
}

// Display battery graph
function displayBatteryGraph(data) {
    const batteryPlot = document.getElementById('battery_plot');

    // Battery % at start and end
    const batteryStart = parseFloat(data['battery_start']);
    const batteryEnd = parseFloat(data['battery_end']);

    const trace = {
        x: ['Start', 'End'],
        y: [batteryStart, batteryEnd],
        type: 'bar',
        marker: { color: ['green', 'red'] }
    };

    const layout = {
        title: 'Battery % for this run',
        yaxis: { range: [0, 100], title: 'Battery %' }
    };

    Plotly.newPlot(batteryPlot, [trace], layout);
}

// Initialize
displayRunList();
