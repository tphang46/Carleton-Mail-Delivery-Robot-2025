const fs = require("fs");
const path = require("path");

const template = fs.readFileSync("dashboard/template.html", "utf8");

const data = {
  repo: process.env.GITHUB_REPOSITORY,
  branch: process.env.GITHUB_REF_NAME,
  sha: process.env.GITHUB_SHA,
  actor: process.env.GITHUB_ACTOR,
  runId: process.env.GITHUB_RUN_ID,
  time: new Date().toISOString()
};

const output = template
  .replace(/{{REPO}}/g, data.repo)
  .replace(/{{BRANCH}}/g, data.branch)
  .replace(/{{SHA}}/g, data.sha)
  .replace(/{{ACTOR}}/g, data.actor)
  .replace(/{{TIME}}/g, data.time);

const branchFolder = path.join("dist", data.branch);
fs.mkdirSync(branchFolder, { recursive: true });
fs.writeFileSync(path.join(branchFolder, "index.html"), output);

const distDir = "dist";
const branches = fs.readdirSync(distDir).filter(f => fs.lstatSync(path.join(distDir,f)).isDirectory());

const indexHtml = `
<h1>Branch Reports</h1>
<ul>
${branches.map(b => `<li><a href="${b}/">${b}</a></li>`).join("\n")}
</ul>
`;

fs.writeFileSync(path.join(distDir, "index.html"), indexHtml);

console.log("Dashboard generated for branch:", data.branch);
