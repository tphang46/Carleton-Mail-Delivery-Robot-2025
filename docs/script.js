// script.js

console.log("Script loaded");

const apiUrl = "https://api.github.com/repos/tphang46/Mail-Delivery-Robot/contents/src/tools/logs/runs";

async function fetchRunFiles() {
    try {
        const res = await fetch(apiUrl);
        if (!res.ok) throw new Error(`Failed to fetch runs: ${res.status}`);
        const files = await res.json();
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

function parseRunText(text) {
    const lines = text.split('\n').filter(l => l.trim() !== '');
    const data = {};
    for (let line of lines) {
        const [key, value] = line.split('=');
        if (key && value) data[key.trim()] = value.trim();
    }
    return data;
}

async function displayRunList() {
    const runListDiv = document.getElementById('run-list');
    runListDiv.innerHTML = 'Loading runs...';

    const files = await fetchRunFiles();
    if (files.length === 0) {
        runListDiv.textContent = 'No runs found.';
        return;
    }

    runListDiv.innerHTML = '';

    files.forEach(file => {
        const btn = document.createElement('button');
        btn.textContent = file.name;
        btn.onclick = async () => displayRunDetails(file);
        runListDiv.appendChild(btn);
    });
}

async function displayRunDetails(file) {
    const runDetails = document.getElementById('run-details');
    const data = await fetchRunContent(file);
    if (!data) {
        runDetails.textContent = "Failed to load run data.";
        return;
    }

    runDetails.textContent = JSON.stringify(data, null, 2);
    displayBatteryGraph(data);
}

function displayBatteryGraph(data) {
    const batteryPlot = document.getElementById('battery_plot');

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
