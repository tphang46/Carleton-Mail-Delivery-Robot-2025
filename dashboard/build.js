const fs = require("fs");
const path = require("path");

const template = fs.readFileSync("dashboard/template.html", "utf8");

const OWNER = "ConnorYelle";
const REPO = "Carleton-Mail-Delivery-Robot";
const headers = {};
if (process.env.GITHUB_TOKEN) {
  headers["Authorization"] = `token ${process.env.GITHUB_TOKEN}`;
}

async function fetchBranches() {
  const res = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/branches`, { headers });
  const data = await res.json();
  return data.map(b => b.name);
}

async function fetchLatestCommit(branch) {
  const res = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/commits?sha=${branch}&per_page=1`, { headers });
  const data = await res.json();
  return data[0];
}

async function fetchLatestPR(branch) {
  const res = await fetch(`https://api.github.com/search/issues?q=repo:${OWNER}/${REPO}+type:pr+is:merged+base:${branch}&sort=updated&order=desc&per_page=1`, { headers });
  const data = await res.json();
  return data.items?.[0] || null;
}

async function generateDashboardForBranch(branch) {
  const latestCommit = await fetchLatestCommit(branch);
  const latestPR = await fetchLatestPR(branch);
  const SHA = latestCommit?.sha || "N/A";
  const TIME = new Date().toISOString();
  const ACTOR = latestCommit?.author?.login || "N/A";

  const commitsHtml = latestCommit
    ? `<a href="${latestCommit.html_url}" target="_blank">${latestCommit.commit.message}</a>`
    : "No commits found";

  const prsHtml = latestPR
    ? `<a href="${latestPR.html_url}" target="_blank">#${latestPR.number} ${latestPR.title}</a>`
    : "No PRs found";

  const output = template
    .replace(/{{REPO}}/g, `${OWNER}/${REPO}`)
    .replace(/{{BRANCH}}/g, branch)
    .replace(/{{SHA}}/g, SHA)
    .replace(/{{ACTOR}}/g, ACTOR)
    .replace(/{{TIME}}/g, TIME)
    .replace(/{{COMMITS}}/g, commitsHtml)
    .replace(/{{PRS}}/g, prsHtml);

  const branchFolder = path.join("dist", branch);
  fs.mkdirSync(branchFolder, { recursive: true });
  fs.writeFileSync(path.join(branchFolder, "index.html"), output);
  console.log(`Dashboard generated for branch: ${branch}`);
}

async function generateIndex() {
  const branches = fs.readdirSync("dist").filter(f => fs.lstatSync(path.join("dist", f)).isDirectory());
  const indexHtml = `
    <h1>Branch Dashboards</h1>
    <ul>
      ${branches.map(b => `<li><a href="${b}/">${b}</a></li>`).join("\n")}
    </ul>
  `;
  fs.writeFileSync(path.join("dist", "index.html"), indexHtml);
}

async function main() {
  if (!fs.existsSync("dist")) fs.mkdirSync("dist");
  const branches = await fetchBranches();
  for (const branch of branches) {
    await generateDashboardForBranch(branch);
  }
  await generateIndex();
}

main();
