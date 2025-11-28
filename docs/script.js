const OWNER = "tphang46";
const REPO = "Carleton-Mail-Delivery-Robot-2025";
const BRANCH = "main";

// Fetch all run log files from the repository
async function fetchRunFiles() {
    const apiUrl = `https://api.github.com/repos/${OWNER}/${REPO}/contents/src/tools/logs/runs?ref=${BRANCH}`;
    console.log("Fetching run files from:", apiUrl);
    const res = await fetch(apiUrl);
    console.log("Response status:", res.status);
    const files = await res.json();
    console.log("Fetched files:", files);
    return files.filter(f => f.name.endsWith(".txt"));
}

// Fetch content of a single run file
async function fetchRunFileContent(url) {
    const res = await fetch(url);
    return await res.text();
}

// Parse raw run file text into key/value pairs
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

// Extract date string from run filename
function extractRunDate(filename) {
    return filename.split("_")[1];
}

// Group run files by their date
function groupByDate(files) {
    const groups = {};
    files.forEach(f => {
        const date = extractRunDate(f.name);
        if (!groups[date]) groups[date] = [];
        groups[date].push(f);
    });
    return groups;
}

// Fetch commits for a specific date
async function fetchCommitsByDate(date) {
    const since = `${date}T00:00:00Z`;
    const until = `${date}T23:59:59Z`;
    const url = `https://api.github.com/repos/${OWNER}/${REPO}/commits?since=${since}&until=${until}`;
    const res = await fetch(url);
    return await res.json();
}

// Fetch PRs merged on a specific date
async function fetchPRsByDate(date) {
    const url = `https://api.github.com/search/issues?q=repo:${OWNER}/${REPO}+type:pr+merged:${date}`;
    const res = await fetch(url);
    const data = await res.json();
    return data.items || [];
}

// Display run data, commits, and PRs for a day
function showDailySummary(date, runDataList, commits, prs) {
    const details = {
        date,
        runs: runDataList,
        commits: commits.map(c => ({ sha: c.sha, message: c.commit.message })),
        prs: prs.map(p => ({ title: p.title, number: p.number }))
    };
    document.getElementById("run-details").textContent =
        JSON.stringify(details, null, 2);
    drawDailyBatteryGraph(runDataList);
}

// Draw battery levels for all runs of the day
function drawDailyBatteryGraph(allRuns) {
    const x = [];
    const y = [];
    allRuns.forEach(run => {
        x.push(`${run.filename} (start)`);
        y.push(parseFloat(run.battery_start));
        x.push(`${run.filename} (end)`);
        y.push(parseFloat(run.battery_end));
    });
    const trace = {
        x,
        y,
        type: "scatter",
        mode: "lines+markers",
        marker: { size: 8 }
    };
    Plotly.newPlot("battery_plot", [trace], {
        title: "Battery Levels for the Entire Day"
    });
}

// Build clickable list of run dates and attach handlers
async function buildRunList() {
    const div = document.getElementById("run-list");
    div.innerHTML = "<p>Loading...</p>";
    const files = await fetchRunFiles();
    if (!files.length) {
        div.innerHTML = "<p>No runs found.</p>";
        return;
    }
    const groups = groupByDate(files);
    console.log("Grouped runs by date:", groups);
    div.innerHTML = "<h3>Runs by Day</h3>";
    Object.keys(groups).forEach(date => {
        const btn = document.createElement("button");
        btn.textContent = `${date} (${groups[date].length} runs)`;
        btn.style.display = "block";
        btn.style.margin = "5px 0";
        btn.onclick = async () => {
            const runFiles = groups[date];
            const runDataList = [];
            for (const f of runFiles) {
                const raw = await fetchRunFileContent(f.download_url);
                const parsed = parseRunData(raw);
                parsed.filename = f.name;
                runDataList.push(parsed);
            }
            const [commits, prs] = await Promise.all([
                fetchCommitsByDate(date),
                fetchPRsByDate(date)
            ]);
            showDailySummary(date, runDataList, commits, prs);
        };
        div.appendChild(btn);
    });
}

buildRunList();
