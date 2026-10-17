"""
Audio tab — The Schultz Report podcast (hosted on Simplecast).

No API access yet, so Simplecast numbers are entered weekly into data_sr/audio_sr.csv:
    week_start,week_end,downloads,listeners,notes
    2026-10-05,2026-10-11,4210,,
(dates YYYY-MM-DD; listeners optional). One row per week; re-entering a week replaces it.
"""

import csv
import json
import os
from datetime import datetime


def _num(v):
    try:
        return int(float(str(v).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


def load_audio(path):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if not (r.get("week_start") or "").strip():
                    continue
                rows.append({"start": r["week_start"].strip(), "end": (r.get("week_end") or "").strip(),
                             "downloads": _num(r.get("downloads")), "listeners": _num(r.get("listeners")),
                             "notes": (r.get("notes") or "").strip()})
    by_start = {r["start"]: r for r in rows}          # last entry for a week wins
    return [by_start[k] for k in sorted(by_start)]


def _md(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.strftime('%b')} {d.day}"


def audio_page(weeks, fmt, empty_state):
    """HTML for the Audio tab (uses the dashboard's metric/card classes)."""
    if not weeks:
        return empty_state("No podcast data yet",
                           "Add weekly Simplecast downloads to data_sr/audio_sr.csv (week_start,week_end,downloads)")
    last = weeks[-1]
    prev = weeks[-2] if len(weeks) > 1 else None
    delta = ""
    if prev and last["downloads"] is not None and prev["downloads"]:
        d = last["downloads"] - prev["downloads"]
        delta = f'<span class="{"up" if d >= 0 else "down"}">{"+" if d >= 0 else ""}{fmt(d)} vs prior week</span>'
    total = sum(w["downloads"] or 0 for w in weeks)
    recent = [w["downloads"] for w in weeks[-4:] if w["downloads"] is not None]
    avg4 = round(sum(recent) / len(recent)) if recent else None
    label = lambda w: f'{_md(w["start"])}–{_md(w["end"])}' if w["end"] else _md(w["start"])
    rows = "".join(f'<tr><td>{label(w)}</td><td>{fmt(w["downloads"])}</td><td>{fmt(w["listeners"])}</td>'
                   f'<td style="text-align:left">{w["notes"]}</td></tr>' for w in reversed(weeks))
    data = json.dumps({"labels": [label(w) for w in weeks], "downloads": [w["downloads"] for w in weeks]})
    return f"""
    <div class="metrics">
      <div class="metric"><div class="metric-label">Downloads · week of {_md(last['start'])}</div><div class="metric-value">{fmt(last['downloads'])}</div><div class="metric-delta">{delta}</div></div>
      <div class="metric"><div class="metric-label">4-week average</div><div class="metric-value">{fmt(avg4)}</div><div class="metric-delta" style="color:var(--text2)">per week</div></div>
      <div class="metric"><div class="metric-label">Total tracked</div><div class="metric-value">{fmt(total)}</div><div class="metric-delta" style="color:var(--text2)">{len(weeks)} week{'s' if len(weeks) != 1 else ''} · since {_md(weeks[0]['start'])}</div></div>
    </div>
    <div class="card">
      <div class="card-title">Weekly Downloads · Simplecast</div>
      <div style="height:280px"><canvas id="audio-weekly-chart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">Weekly Detail</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Week</th><th>Downloads</th><th>Listeners</th><th>Notes</th></tr></thead>
      <tbody>{rows}</tbody></table></div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const A = {data}, el = document.getElementById('audio-weekly-chart');
      if (!el || typeof Chart === 'undefined') return;
      new Chart(el, {{ type:'bar', data:{{ labels:A.labels, datasets:[{{ label:'Downloads', data:A.downloads,
        backgroundColor:'#E8C840', borderRadius:3, maxBarThickness:48 }}] }},
        options:{{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{ display:false }} }},
          scales:{{ x:{{ grid:{{ display:false }}, ticks:{{ color:'#f2f2f2' }} }},
                   y:{{ beginAtZero:true, grid:{{ color:'rgba(255,255,255,.08)' }}, ticks:{{ color:'#f2f2f2' }} }} }} }} }});
    }});
    </script>"""
