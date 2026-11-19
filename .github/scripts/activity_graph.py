"""Render assets/activity-graph.svg: this repo's commits per week.

Reads history from `git log`, so it needs no API token and no third-party
packages. Run from the repo root (CI checks out with full history):

    python3 .github/scripts/activity_graph.py
"""
import datetime as dt
import pathlib
import subprocess

OUT = pathlib.Path("assets/activity-graph.svg")
REPO = "Home-Lab-Project"

W, H = 900, 260
LEFT, RIGHT, TOP, BOTTOM = 45, 880, 45, 230
BG, FG, MUTED, GRID, LINE = "#0d1117", "#c9d1d9", "#8b949e", "#21262d", "#58a6ff"


def commit_dates():
    out = subprocess.run(
        ["git", "log", "--format=%ad", "--date=short"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [dt.date.fromisoformat(line) for line in out.split()]


def week_start(d):
    return d - dt.timedelta(days=d.weekday())


def main():
    dates = commit_dates()
    first = week_start(min(dates))
    last = week_start(dt.date.today())
    weeks = [first + dt.timedelta(weeks=i) for i in range((last - first).days // 7 + 1)]
    counts = {w: 0 for w in weeks}
    for d in dates:
        counts[week_start(d)] += 1
    values = [counts[w] for w in weeks]

    step = 4
    ymax = max(step, -(-max(values) // step) * step)
    span = max(len(weeks) - 1, 1)

    def x(i):
        return LEFT + (RIGHT - LEFT) * i / span

    def y(v):
        return BOTTOM - (BOTTOM - TOP) * v / ymax

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        'font-family="Segoe UI,Helvetica,Arial,sans-serif">',
        f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
        f'<text x="{LEFT}" y="26" fill="{FG}" font-size="15">'
        f"{REPO} — commits per week ({len(dates)} total)</text>",
    ]
    for v in range(0, ymax + 1, ymax // 3 if ymax >= 3 else 1):
        svg.append(f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{GRID}"/>')
        svg.append(f'<text x="{LEFT - 8}" y="{y(v) + 4:.1f}" fill="{MUTED}" '
                   f'font-size="11" text-anchor="end">{v}</text>')

    seen = set()
    for i, w in enumerate(weeks):
        key = (w.year, w.month)
        if key not in seen:
            seen.add(key)
            svg.append(f'<text x="{x(i):.1f}" y="250" fill="{MUTED}" '
                       f'font-size="11" text-anchor="middle">{w:%b}</text>')

    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))
    svg.append(f'<polygon points="{x(0):.1f},{BOTTOM:.1f} {pts} {x(len(values) - 1):.1f},{BOTTOM:.1f}" '
               f'fill="{LINE}" fill-opacity="0.15"/>')
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{LINE}" '
               'stroke-width="2.5" stroke-linejoin="round"/>')
    for i, v in enumerate(values):
        if v:
            svg.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3.5" fill="{LINE}"/>')
    svg.append("</svg>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(svg) + "\n")
    print(f"Wrote {OUT}: {len(dates)} commits over {len(weeks)} weeks")


if __name__ == "__main__":
    main()
