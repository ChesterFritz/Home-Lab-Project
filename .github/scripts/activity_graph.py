"""Draw a contribution line graph for the last 31 days as an SVG.

Runs in GitHub Actions. Reads GITHUB_TOKEN and GH_USER from the environment.
"""
import datetime as dt
import json
import os
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

USER = os.environ["GH_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]
DAYS = 31
OUT = "assets/activity-graph.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    payload = json.load(resp)

if "errors" in payload:
    raise SystemExit(f"GraphQL error: {payload['errors']}")

weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
days = [d for w in weeks for d in w["contributionDays"]][-DAYS:]
dates = [dt.date.fromisoformat(d["date"]) for d in days]
counts = [d["contributionCount"] for d in days]

BG, FG, GRID, LINE = "#0d1117", "#c9d1d9", "#21262d", "#58a6ff"

fig, ax = plt.subplots(figsize=(12, 3.6), dpi=100)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.plot(dates, counts, color=LINE, linewidth=2.2, marker="o", markersize=4)
ax.fill_between(dates, counts, color=LINE, alpha=0.15)

ax.set_title(f"{USER} \u2014 contributions, last {DAYS} days", color=FG, fontsize=13, loc="left", pad=12)
ax.set_ylabel("Contributions", color=FG)
ax.set_ylim(bottom=0, top=max(max(counts), 1) * 1.15)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.tick_params(colors=FG, labelsize=9)
ax.grid(axis="y", color=GRID, linewidth=1)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(GRID)

fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, format="svg", facecolor=BG)
print(f"Wrote {OUT}: {sum(counts)} contributions over {DAYS} days")
