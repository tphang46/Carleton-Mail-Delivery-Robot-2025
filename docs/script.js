async function fetchRunFiles() {
    const apiUrl = "https://api.github.com/repos/tphang46/Mail-Delivery-Robot/contents/src/tools/logs/runs"

    const res = await fetch(apiUrl);
    const files = await res.json();

    // Only keep .txt files
    return files.filter(f => f.name.endsWith(".txt"));
}

async function fetchRunFileContent(url) {
    const res = await fetch(url);
    return await res.text();
}

function parseRunData(text) {
    const data = {};
    text.split("\n").forEach(line => {
        const [key, value] = line.split("=");
        if (key && value !== undefined) {
            data[key.trim()] = value.trim();
        }
    });
    return data;
}

function showRunDetails(data) {
    document.getElementById("run-details").textContent =
        JSON.stringify(data, null, 2);

    // battery graph
    const trace = {
        x: ["Start", "End"],
        y: [
            parseFloat(data.battery_start),
            parseFloat(data.battery_end)
        ],
        type: "scatter",
        mode: "lines+markers",
        marker: { size: 10 }
    };

    Plotly.newPlot("battery_plot", [trace], {
        title: "Battery Level (Start → End)"
    });
}

async function buildRunList() {
    const div = document.getElementById("run-list");

    const files = await fetchRunFiles();
    if (!files.length) {
        div.innerHTML = "<p>No runs found.</p>";
        return;
    }

    files.forEach(file => {
        const link = document.createElement("a");
        link.href = "#";
        link.textContent = file.name;
        link.style.display = "block";

        link.onclick = async () => {
            const text = await fetchRunFileContent(file.download_url);
            const data = parseRunData(text);
            showRunDetails(data);
        };

        div.appendChild(link);
    });
}

buildRunList();
