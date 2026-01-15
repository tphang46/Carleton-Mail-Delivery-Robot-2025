import os
import pandas as pd
import json
import re
from datetime import datetime
from github import Github

GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]
GITHUB_EVENT_PATH = os.environ["GITHUB_EVENT_PATH"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
LOG_DIR = "tools/logs/runs"
METADATA_KEYS = ["run", "date", "trip_start_time", "trip_end_time", "docked"]
METRIC_RULES = {"delivery_time": "lower", "battery_used": "lower", "wall_follow_time": "lower"}
EXCLUDE_METRICS = ["battery_start", "battery_end", "voltage_level", "temperature_level"]

runs = []
for file in sorted(os.listdir(LOG_DIR)):
    if file.endswith(".txt"):
        with open(os.path.join(LOG_DIR, file)) as f:
            data = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    try:
                        data[k] = None if v.lower() in ["none", "n/a"] else float(v)
                    except ValueError:
                        data[k] = v
            data["run"] = file
            m = re.search(r"\d{4}-\d{2}-\d{2}", file)
            data["date"] = m.group(0).replace("-", "") if m else "unknown"
            runs.append(data)

if not runs:
    raise SystemExit(0)

df = pd.DataFrame(runs)
metrics = [c for c in df.select_dtypes(include="number").columns if c not in METADATA_KEYS and c not in EXCLUDE_METRICS]
avg = df[metrics].mean()

with open(GITHUB_EVENT_PATH) as f:
    event = json.load(f)

commit_hash = "Unknown"
target_date = datetime.utcnow().strftime("%Y%m%d")

if "pull_request" in event:
    commit_hash = event["pull_request"]["head"]["sha"][:7]
elif "commits" in event:
    commit_hash = event.get("after", event["commits"][-1]["id"])[:7]

if target_date in df["date"].values:
    day_runs = df[df["date"] == target_date]
    is_fallback = False
else:
    day_runs = df.tail(1)
    is_fallback = True

md = f"**Commit:** `{commit_hash}`\n\n"
if is_fallback:
    md += "**NO TEST RUNS TODAY. SHOWING LATEST DATA.**\n\n"

summary = {"Improved": 0, "Worse": 0, "Same": 0}
md += f"## Robot Metrics Report: {day_runs.iloc[0]['date']}\n\n"

for _, r in day_runs.iterrows():
    md += f"### Run: {r['run']}\n"
    md += "| Metric | Value | Average | Status |\n"
    md += "|--------|-------|--------|--------|\n"
    for m in metrics:
        v = r[m]
        if pd.isna(v):
            continue
        a = avg[m]
        rule = METRIC_RULES.get(m, "higher")
        if abs(v - a) < 0.001:
            s = "Same"
        elif (rule == "lower" and v < a) or (rule == "higher" and v > a):
            s = "Improved"
        else:
            s = "Worse"
        summary[s] += 1
        md += f"| {m} | {v:.2f} | {a:.2f} | {s} |\n"
    md += "\n"

md = f"**Summary:** {summary['Improved']} Improved, {summary['Worse']} Worse, {summary['Same']} Same\n\n" + md

g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPOSITORY)

if "pull_request" in event:
    pr = repo.get_pull(event["pull_request"]["number"])
    pr.create_issue_comment(md)
