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

    for (const file of files) {
        const data = await fetchRunContent(file);
        if (!data) continue;

        const runContainer = document.createElement('div');
        runContainer.className = 'run-container';

        const runTitle = document.createElement('h2');
        runTitle.textContent = file.name;
        runContainer.appendChild(runTitle);

        for (const [key, value] of Object.entries(data)) {
            const card = document.createElement('div');
            card.className = 'metric-card';
            card.innerHTML = `<strong>${key.replace(/_/g, ' ')}:</strong> ${value}`;
            runContainer.appendChild(card);
        }

        runListDiv.appendChild(runContainer);
    }
}

// Initialize
displayRunList();
