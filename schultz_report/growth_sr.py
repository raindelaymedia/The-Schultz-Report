"""
Growth section for the Overview — every platform since the start of the RDM term (Aug 18 2026), in two-week
windows, plus a short plain-language read of the latest complete window.

Sources (all pushed by RDM to data_sr/from_rdm/):
    tracker_data_sr.json   daily_yt: YouTube views + subscribers gained/lost per day
    growth_sr.json         Instagram per window: views, interactions, follows, unfollows
    tiktok/account_daily.csv   TikTok followers + lifetime views per day (from Oct 18 2026)
    socials (merged)       X: monthly, entered by hand
"""

import csv
import json
import os
from datetime import date, datetime, timedelta

from rdm_data import pick, rdm_dir

START = date(2026, 8, 18)
WINDOW = 14
COLORS = {"YouTube": "#5B8DEF", "Instagram": "#E08C2A", "TikTok": "#9B7BEA"}


def _load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _md(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.strftime('%b')} {d.day}"


def _pct(cur, prev):
    if cur is None or not prev:
        return None
    return (cur - prev) / prev


def _pct_html(p):
    if p is None:
        return ""
    return f' <span class="{"up" if p >= 0 else "down"}" style="font-size:11px">{"+" if p >= 0 else ""}{p * 100:.0f}%</span>'


def _windows(through):
    out, s = [], START
    while s <= through:
        e = s + timedelta(days=WINDOW - 1)
        out.append({"start": s.isoformat(), "end": min(e, through).isoformat(), "partial": e > through})
        s = e + timedelta(days=1)
    return out


def growth_section(data_dir, socials, fmt):
    tracker = _load(pick(data_dir, "tracker_data_sr.json"))
    growth = _load(pick(data_dir, "growth_sr.json"))
    daily = tracker.get("daily_yt", {})
    if not daily:
        return ""
    through = max([max(daily)] + ([growth["through"]] if growth.get("through") else []))
    wins = _windows(date.fromisoformat(through))

    # ── YouTube per window ──
    for w in wins:
        days = [v for k, v in daily.items() if w["start"] <= k <= w["end"]]
        w["yt_views"] = sum(v.get("total_views", 0) for v in days)
        w["yt_subs"] = sum(v.get("subs_gained", 0) - v.get("subs_lost", 0) for v in days)
    subs_now = tracker.get("current_subs") or 0
    net_since = sum(v.get("subs_gained", 0) - v.get("subs_lost", 0) for k, v in daily.items() if k >= START.isoformat())
    subs_start = subs_now - net_since
    yt_views_since = sum(v.get("total_views", 0) for k, v in daily.items() if k >= START.isoformat())

    # ── Instagram per window ──
    ig = growth.get("instagram", {})
    ig_by = {w["start"]: w for w in ig.get("windows", [])}
    for w in wins:
        g = ig_by.get(w["start"])
        if g:
            w.update(ig_views=g["views"], ig_net=g["net_followers"], ig_follows=g["follows"], ig_unfollows=g["unfollows"])
    ig_views_since = sum(g["views"] for g in ig.get("windows", []))

    # ── TikTok per window (from daily account snapshots) ──
    tt_rows = []
    p = os.path.join(rdm_dir(data_dir), "tiktok", "account_daily.csv")
    if os.path.exists(p):
        tt_rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    tt = {r["date"]: r for r in tt_rows}
    for w in wins:
        a = tt.get((date.fromisoformat(w["start"]) - timedelta(days=1)).isoformat())
        b = tt.get(w["end"]) or (tt.get(max(tt)) if w["partial"] and tt else None)
        if a and b:
            w["tt_views"] = int(b["lifetime_views"]) - int(a["lifetime_views"])
    tt_last = tt[max(tt)] if tt else None

    # ── X (monthly, by hand) ──
    months = socials.get("months", [])
    xv = socials.get("data", {}).get(("X", "VIEWS"), [None] * len(months))
    x_views_since = sum(v for m, v in zip(months, xv) if m >= "2026-08" and isinstance(v, (int, float)))
    xf = [(m, v) for m, v in zip(months, socials.get("data", {}).get(("X", "FOLLOWERS"), [None] * len(months)))
          if isinstance(v, (int, float))]

    # ── Story: latest complete window vs the one before ──
    done = [w for w in wins if not w["partial"]]
    story = []
    if len(done) >= 2:
        c, p_ = done[-1], done[-2]
        lbl = f'{_md(c["start"])}–{_md(c["end"])}'
        yp = _pct(c["yt_views"], p_["yt_views"])
        story.append(f'<b>YouTube</b>: {fmt(c["yt_views"])} views in {lbl}'
                     + (f' ({"+" if yp >= 0 else ""}{yp * 100:.0f}% vs the two weeks before)' if yp is not None else "")
                     + f', {c["yt_subs"]:+,} subscribers.')
        if "ig_views" in c:
            ip = _pct(c["ig_views"], p_.get("ig_views"))
            story.append(f'<b>Instagram</b>: {fmt(c["ig_views"])} views'
                         + (f' ({"+" if ip >= 0 else ""}{ip * 100:.0f}%)' if ip is not None else "")
                         + f', followers {c["ig_net"]:+,} ({c["ig_follows"]:,} follows, {c["ig_unfollows"]:,} unfollows).')
            if c["ig_follows"] and c["ig_unfollows"] / c["ig_follows"] > 0.6:
                story.append(f'Instagram follower churn is high: {c["ig_unfollows"]:,} unfollows for every '
                             f'{c["ig_follows"]:,} new follows.')
    story.append(f'<b>Since Aug 18</b>: YouTube {net_since:+,} subscribers'
                 + (f' ({net_since / subs_start * 100:+.1f}%)' if subs_start else "")
                 + f' and {fmt(yt_views_since)} views; Instagram and TikTok launched Aug 18 and are at '
                 f'{fmt(ig.get("followers_now"))} and {fmt(int(tt_last["followers"])) if tt_last else "—"} followers.')
    cur = wins[-1]
    if cur["partial"]:
        story.append(f'<span style="color:var(--text2)">Current window ({_md(cur["start"])}–{_md(cur["end"])}) is still '
                     f'in progress. YouTube and Instagram data lag about two days.</span>')
    story_html = "".join(f"<li style='margin:4px 0'>{s}</li>" for s in story)

    # ── Cards: since Aug 18 ──
    def card(name, big, sub1, sub2):
        return (f'<div class="metric"><div class="metric-label">{name} · since Aug 18</div><div class="metric-value">{big}</div>'
                f'<div class="metric-delta" style="color:var(--text2)">{sub1}</div>'
                f'<div class="metric-delta" style="color:var(--text2)">{sub2}</div></div>')
    cards = (
        card("YouTube", f'{net_since:+,}',
             f'subscribers ({net_since / subs_start * 100:+.1f}%) · {fmt(subs_start)} → {fmt(subs_now)}' if subs_start else "subscribers",
             f'{fmt(yt_views_since)} views')
        + card("Instagram", fmt(ig.get("followers_now")), "followers (new account)", f'{fmt(ig_views_since)} views')
        + card("TikTok", fmt(int(tt_last["followers"])) if tt_last else "—", "followers (new account)",
               f'{fmt(int(tt_last["lifetime_views"]))} views' if tt_last else "")
        + card("X", fmt(xf[-1][1]) if xf else "—",
               f'followers ({datetime.strptime(xf[-1][0], "%Y-%m").strftime("%b")}, entered by hand)' if xf else "entered by hand",
               f'{fmt(x_views_since)} views' if x_views_since else "")
    )

    # ── Table + chart ──
    rows = ""
    prev = None
    for w in wins:
        lbl = f'{_md(w["start"])}–{_md(w["end"])}' + (" *" if w["partial"] else "")
        yp = _pct(w["yt_views"], prev["yt_views"]) if prev and not w["partial"] else None
        ip = _pct(w.get("ig_views"), prev.get("ig_views")) if prev and not w["partial"] else None
        igf = (f'{w["ig_net"]:+,} <span style="color:var(--text2);font-size:11px">(+{w["ig_follows"]:,} / −{w["ig_unfollows"]:,})</span>'
               if "ig_net" in w else "—")
        rows = (f'<tr><td style="text-align:left">{lbl}</td><td>{fmt(w["yt_views"])}{_pct_html(yp)}</td><td>{w["yt_subs"]:+,}</td>'
                f'<td>{fmt(w.get("ig_views"))}{_pct_html(ip)}</td><td>{igf}</td><td>{fmt(w.get("tt_views"))}</td></tr>') + rows
        prev = w
    labels = [f'{_md(w["start"])}–{_md(w["end"])}' + (" *" if w["partial"] else "") for w in wins]
    chart = json.dumps({"labels": labels, "series": [
        {"label": "YouTube", "data": [w["yt_views"] for w in wins], "color": COLORS["YouTube"]},
        {"label": "Instagram", "data": [w.get("ig_views") for w in wins], "color": COLORS["Instagram"]},
        {"label": "TikTok", "data": [w.get("tt_views") for w in wins], "color": COLORS["TikTok"]}]})
    if not any(w.get("tt_views") for w in wins):      # TikTok windows start once two daily snapshots bracket one
        chart = chart.replace(f', {{"label": "TikTok", "data": {json.dumps([None] * len(wins))}, "color": "{COLORS["TikTok"]}"}}', "")

    return f"""
    <div class="card" style="border-left:3px solid var(--brand)">
      <div class="card-title">What the data says · two-week read</div>
      <ul style="margin:0;padding-left:18px;line-height:1.5;font-size:13px">{story_html}</ul>
    </div>
    <div class="metrics">{cards}</div>
    <div class="card">
      <div class="card-title">Views every two weeks · since Aug 18</div>
      <div style="height:260px"><canvas id="growth-chart"></canvas></div>
      <div class="table-scroll" style="margin-top:14px"><table class="data-table"><thead><tr><th style="text-align:left">Window</th>
        <th>YouTube views</th><th>YouTube subs</th><th>Instagram views</th><th>Instagram followers (follows / unfollows)</th>
        <th>TikTok views</th></tr></thead><tbody>{rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">* in progress. % = change vs the previous two weeks.
        TikTok views by window start Oct 18 (daily account snapshots); Aug–Sep TikTok and X are monthly totals on the Socials tab.</div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const G = {chart}, el = document.getElementById('growth-chart');
      if (!el || typeof Chart === 'undefined') return;
      new Chart(el, {{ type:'bar', data:{{ labels:G.labels, datasets:G.series.map(s => ({{ label:s.label, data:s.data,
          backgroundColor:s.color, borderRadius:4, maxBarThickness:28, borderColor:'rgba(17,17,107,1)', borderWidth:2 }})) }},
        options:{{ responsive:true, maintainAspectRatio:false,
          plugins:{{ legend:{{ labels:{{ color:'#f2f2f2' }} }},
            tooltip:{{ callbacks:{{ label: c => c.dataset.label + ': ' + (c.raw == null ? '—' : c.raw.toLocaleString()) }} }} }},
          scales:{{ x:{{ grid:{{ display:false }}, ticks:{{ color:'#f2f2f2' }} }},
                   y:{{ beginAtZero:true, grid:{{ color:'rgba(255,255,255,.08)' }},
                        ticks:{{ color:'#f2f2f2', callback: v => v >= 1e6 ? (v/1e6)+'M' : v >= 1e3 ? (v/1e3)+'K' : v }} }} }} }} }});
    }});
    </script>"""
