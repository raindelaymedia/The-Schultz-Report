"""
Sponsors section — one sidebar page per sponsor in data_sr/sponsors.csv:
    sponsor,sprout_tag,start,end,impression_goal,notes
Adding a sponsor = adding a row; its page appears on the next build.

Campaign totals come from two places (as they connect):
  • Sprout Social — posts tagged with the sponsor's Sprout tag, on the show accounts and on Jordan
    Schultz's personal accounts (pending the Sprout API).
  • Our show-account pulls — the watermarked post list (fanatics_posts_sr.csv; a `sponsor` column
    once more sponsors use it) and the episode list.
Fanatics also has the monthly delivery history (fanatics_history_sr.csv) and the reports.
"""

import csv
import glob
import os
import re
from datetime import date, datetime

from rdm_data import pick, rdm_dir, sponsor_sprout_section


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


PLATFORM_NAME = {"TIKTOK": "TikTok", "INSTAGRAM": "Instagram", "X": "X", "YOUTUBE": "YouTube"}


def slug(name):
    return "sponsor-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_sponsors(path):
    return [r for r in _read(path) if (r.get("sponsor") or "").strip()]


def _mdy(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def _fanatics_body(s, data_dir, fmt, empty_state):
    hist = sorted(_read(pick(data_dir, "fanatics_history_sr.csv")), key=lambda r: r["period_start"])
    # Only periods inside the campaign (the history may still hold superseded rows)
    hist = [r for r in hist if not s.get("start") or r["period_start"] >= s["start"]]
    posts = [p for p in _read(pick(data_dir, "fanatics_posts_sr.csv"))
             if (p.get("sponsor") or "Fanatics") == "Fanatics"]
    goal = _int(s.get("impression_goal"))
    cum = sum(_int(r.get("impressions")) for r in hist)
    start = datetime.strptime(s["start"], "%Y-%m-%d").date() if s.get("start") else None
    end = datetime.strptime(s["end"], "%Y-%m-%d").date() if s.get("end") else None
    elapsed = None
    if start and end and hist:
        last_end = datetime.strptime(hist[-1]["period_end"], "%Y-%m-%d").date()
        elapsed = ((last_end - start).days + 1) / ((end - start).days + 1)
    rep_root = rdm_dir(data_dir) if os.path.isdir(os.path.join(rdm_dir(data_dir), "reports")) else data_dir
    rep_rel = "data_sr/from_rdm" if rep_root != data_dir else "data_sr"
    reports = sorted(glob.glob(os.path.join(rep_root, "reports", "fanatics", "*.html")))
    rows = "".join(
        f'<tr><td>{_mdy(r["period_start"])} – {_mdy(r["period_end"])}</td><td>{fmt(_int(r["imp_youtube"]))}</td>'
        f'<td>{fmt(_int(r["imp_social"]))}</td><td>{fmt(_int(r["imp_audio"]))}</td><td><b>{fmt(_int(r["impressions"]))}</b></td></tr>'
        for r in hist)
    by_plat = {}
    for p in posts:
        k = f'{p["account"]} · {PLATFORM_NAME.get(p["platform"].upper(), p["platform"].title())}'
        by_plat[k] = by_plat.get(k, 0) + 1
    report_links = "".join(
        f'<li><a href="{rep_rel}/reports/fanatics/{os.path.basename(p)}" target="_blank" style="color:var(--brand)">'
        f'{_report_label(os.path.basename(p))}</a></li>' for p in reports)
    pct = f"{cum / goal * 100:.1f}%" if goal and hist else "—"
    return f"""
    <div class="metrics">
      <div class="metric"><div class="metric-label">Impressions delivered</div><div class="metric-value">{fmt(cum) if hist else '—'}</div>
        <div class="metric-delta" style="color:var(--text2)">{len(hist)} reported period{'s' if len(hist) != 1 else ''}</div></div>
      <div class="metric"><div class="metric-label">Of {fmt(goal)} goal</div><div class="metric-value">{pct}</div>
        <div class="metric-delta" style="color:var(--text2)">{f"{elapsed*100:.1f}% of term elapsed" if elapsed is not None else ''}</div></div>
      <div class="metric"><div class="metric-label">Watermarked posts tracked</div><div class="metric-value">{len(posts)}</div>
        <div class="metric-delta" style="color:var(--text2)">{' · '.join(f'{k} {v}' for k, v in sorted(by_plat.items()))}</div></div>
    </div>
    <div class="card"><div class="card-title">Delivery by Period</div>
      {('<div class="table-scroll"><table class="data-table"><thead><tr><th>Period</th><th>YouTube</th><th>Social</th><th>Audio</th><th>Total</th></tr></thead><tbody>'
        + rows + '</tbody></table></div>') if hist else '<div class="metric-delta">No saved periods yet — the first one is saved when a report is finalized.</div>'}
    </div>
    <div class="card"><div class="card-title">Delivery Reports</div><ul style="margin-left:18px;line-height:1.9">{report_links or '<li>None yet</li>'}</ul></div>"""


def _report_label(name):
    """Schultz_Report_Fanatics_0901_0930_26.html → 'Delivery report · Sep 1 – Sep 30, 2026'."""
    m = re.search(r"_(\d{2})(\d{2})_(\d{2})(\d{2})_(\d{2})\.html$", name)
    if not m:
        return name
    m1, d1, m2, d2, yy = (int(x) for x in m.groups())
    mon = lambda n: datetime(2000, n, 1).strftime("%b")
    return f"Delivery report · {mon(m1)} {d1} – {mon(m2)} {d2}, 20{yy:02d}"


def sponsor_pages(sponsors, data_dir, fmt, empty_state, sprout=None):
    """→ (nav_html, pages_html). Pages use the dashboard's existing classes."""
    nav, pages = "", ""
    for s in sponsors:
        name, sid = s["sponsor"].strip(), slug(s["sponsor"])
        nav += (f'<div class="nav-item" onclick="showPage(\'{sid}\',this)">'
                f'<span class="sponsor-dot"></span><span>{name}</span></div>')
        flight = (f"{_mdy(s['start'])} – {_mdy(s['end'])}" if s.get("start") and s.get("end") else "Flight dates TBD")
        tag = s.get("sprout_tag") or name
        if name == "Fanatics":
            body = _fanatics_body(s, data_dir, fmt, empty_state) + sponsor_sprout_section(tag, sprout, fmt)
        else:
            body = (sponsor_sprout_section(tag, sprout, fmt)
                    + '<div class="card"><div class="card-title">Campaign terms</div><div class="metric-delta" '
                      f'style="color:var(--text2)">Flight, deliverables and goals pending — add them to sponsors.csv.</div></div>')
        pages += f"""
<div class="page" id="page-{sid}">
  <div class="page-header">
    <div class="page-title">{name}</div>
    <div class="page-sub">Sponsor campaign · {flight} · Sprout tag “{s.get('sprout_tag') or name}”</div>
  </div>
  {body}
</div>"""
    return nav, pages
