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

    runListDiv.innerHTML = ''; // clear loading message

    for (const file of files) {
        const data = await fetchRunContent(file);
        if (!data) continue;

        const card = document.createElement('div');
        card.className = 'run-card';

        card.innerHTML = `
            <h3>${file.name}</h3>
            <p><strong>Battery Start:</strong> ${data['battery_start']}%</p>
            <p><strong>Battery End:</strong> ${data['battery_end']}%</p>
            <p><strong>Battery Used:</strong> ${data['battery_used']}%</p>
            <p><strong>Delivery Time:</strong> ${data['delivery_time']} s</p>
            <p><strong>Wall Follow Time:</strong> ${data['wall_follow_time']}</p>
            <p><strong>Voltage:</strong> ${data['voltage_level']} V</p>
            <p><strong>Temperature:</strong> ${data['temperature_level']} °C</p>
            <p><strong>Trip Start:</strong> ${data['trip_start_time']}</p>
            <p><strong>Trip End:</strong> ${data['trip_end_time']}</p>
        `;

        runListDiv.appendChild(card);
    }
}

// Initialize
displayRunList();
