import os
import pandas as pd
import json
from github import Github

GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]
GITHUB_EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH")
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

LOG_DIR = "src/tools/logs/runs"

EXEMPT_KEYS = [
    "temperature_level",
    "voltage_level",
    "lidar_front_avg",
    "lidar_front_min",
    "lidar_left_avg",
    "lidar_left_min",
    "lidar_right_avg",
    "lidar_right_min",
    "wall_distance_avg",
    "wall_angle_avg"
]

METRIC_RULES = {"delivery_time": "lower", "battery_used": "lower"}

runs = []
for file in sorted(os.listdir(LOG_DIR)):
    if file.endswith(".txt"):
        with open(os.path.join(LOG_DIR, file)) as f:
            data = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=")
                    try:
                        data[k.strip()] = float(v.strip())
                    except ValueError:
                        data[k.strip()] = v.strip()
            data["run"] = file
            parts = file.split("_")
            data["date"] = parts[1] if len(parts) > 1 else "unknown"
            runs.append(data)

if not runs:
    exit(0)

df = pd.DataFrame(runs)

metrics = [c for c in df.columns if
           c not in EXEMPT_KEYS + ["run", "trip_start_time", "trip_end_time", "battery_start", "battery_end", "date"]]

with open(GITHUB_EVENT_PATH) as f:
    event = json.load(f)

target_date = None
if "pull_request" in event:
    target_date = event["pull_request"]["created_at"][:10].replace("-", "")
elif "commits" in event:
    target_date = event["commits"][-1]["timestamp"][:10].replace("-", "")

if target_date in df["date"].values:
    day_runs = df[df["date"] == target_date].copy()
    report_date = target_date
else:
    day_runs = pd.DataFrame([df.iloc[-1]])
    report_date = day_runs.iloc[0]["date"]

avg = df[metrics].mean()

md_body = f"## Robot Metrics Report - Run Date: {report_date}\n\n"
summary_counts = {"Improved": 0, "Worse": 0, "Same": 0}

for _, run in day_runs.iterrows():
    md_body += f"### Run: {run['run']}\n"
    md_body += "| Metric | Value | Average | Status |\n"
    md_body += "|--------|-------|--------|--------|\n"
    for m in metrics:
        val = run[m]
        avg_val = avg[m]

        if not isinstance(val, (int, float)):
            continue

        rule = METRIC_RULES.get(m, "higher")
        if rule == "higher":
            status = "Improved" if val > avg_val else "Worse" if val < avg_val else "Same"
        else:
            status = "Improved" if val < avg_val else "Worse" if val > avg_val else "Same"

        summary_counts[status] += 1
        md_body += f"| {m} | {val:.2f} | {avg_val:.2f} | {status} |\n"
    md_body += "\n"

md_header = f"**Summary for {report_date}:** {summary_counts['Improved']} Improved, {summary_counts['Worse']} Worse, {summary_counts['Same']} Same\n\n"
full_md = md_header + md_body

g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPOSITORY)

pr_number = None
if "pull_request" in event:
    pr_number = event["pull_request"]["number"]
elif "ref" in event and event["ref"].startswith("refs/heads/"):
    branch = event["ref"].split("/")[-1]
    prs = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}")
    pr_number = prs[0].number if prs.totalCount > 0 else None

if pr_number:
    pr = repo.get_pull(pr_number)
    marker = ""
    existing_comments = pr.get_issue_comments()
    metrics_comment = None
    for c in existing_comments:
        if marker in c.body:
            metrics_comment = c
            break
    md_with_marker = f"{marker}\n\n{full_md}"
    if metrics_comment:
        metrics_comment.edit(md_with_marker)
    else:
        pr.create_issue_comment(md_with_marker)