"""
Growth section for the Overview. Jordan Schultz's accounts lead (that's where the audience is); the show's YouTube and
podcast follow. Mon–Sun windows since the start of the RDM term (Aug 18 2026), plus a plain-language read of the latest
complete week. The show's own Instagram / TikTok / X live on the Socials tab (RDM tracks them internally).

Sources (all pushed by RDM to data_sr/from_rdm/):
    sprout/profiles_daily.csv   Jordan's accounts, whole account, per day: followers, X impressions,
                                Instagram views, TikTok video views (Sprout Social)
    sprout/posts.json           show content on Jordan's accounts (posts tagged in Sprout), lifetime views
    tracker_data_sr.json        daily_yt: YouTube views + subscribers gained/lost per day
    audio_sr.csv (this repo)    weekly Simplecast downloads
"""

import csv
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

from rdm_data import pick, rdm_dir

START = date(2026, 8, 18)
NETS = [("X", "X", "impressions"), ("INSTAGRAM", "Instagram", "views"), ("TIKTOK", "TikTok", "video_views")]
NAME = {n: name for n, name, _ in NETS}
COLORS = {"X": "#F2F2F2", "INSTAGRAM": "#E08C2A", "TIKTOK": "#9B7BEA"}


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


def _pct_txt(p):
    return f' ({"+" if p >= 0 else ""}{p * 100:.0f}% vs the week before)' if p is not None else ""


def _windows(through):
    """Monday–Sunday weeks from START (first one Aug 18–23); the current week is partial."""
    out, s = [], START
    while s <= through:
        e = s + timedelta(days=6 - s.weekday())
        out.append({"start": s.isoformat(), "end": min(e, through).isoformat(), "partial": e > through})
        s = e + timedelta(days=1)
    return out


def _num(v):
    try:
        return float(v) if (v or "").strip() else None
    except ValueError:
        return None


def _jordan_daily(data_dir):
    """{network: {date: {reach, followers}}} for Jordan's accounts (Sprout daily profile metrics)."""
    p = os.path.join(rdm_dir(data_dir), "sprout", "profiles_daily.csv")
    out = defaultdict(dict)
    if not os.path.exists(p):
        return out
    field = {n: f for n, _, f in NETS}
    for r in csv.DictReader(open(p, encoding="utf-8-sig", newline="")):
        if r.get("owner") != "JS" or r["network"] not in field and r["network"] != "THREADS":
            continue
        out[r["network"]][r["date"]] = {"reach": _num(r.get(field.get(r["network"], ""))) or 0,
                                        "followers": _num(r.get("followers"))}
    return out


def _followers_on(series, day):
    """Latest follower count on or before `day`."""
    ks = [k for k in series if k <= day and series[k]["followers"] is not None]
    return series[max(ks)]["followers"] if ks else None


def growth_section(data_dir, socials, fmt):
    """(top, detail): headline cards + the week's read for the top of the Overview, chart + table further down."""
    tracker = _load(pick(data_dir, "tracker_data_sr.json"))
    daily = tracker.get("daily_yt", {})
    jd = _jordan_daily(data_dir)
    sprout = _load(os.path.join(rdm_dir(data_dir), "sprout", "posts.json"))
    show_posts = [p for p in sprout.get("posts", []) if p.get("owner") == "JS" and p.get("network") != "YOUTUBE"]
    if not daily and not jd:
        return "", ""
    j_through = max((max(s) for s in jd.values() if s), default=None)
    through = max([d for d in (max(daily) if daily else None, j_through) if d])
    wins = _windows(date.fromisoformat(through))

    # ── Per window ──
    for w in wins:
        days = [v for k, v in daily.items() if w["start"] <= k <= w["end"]]
        w["yt_views"] = sum(v.get("total_views", 0) for v in days) if days else None
        w["yt_subs"] = sum(v.get("subs_gained", 0) - v.get("subs_lost", 0) for v in days) if days else None
        w["j"] = {}
        for n, _, _ in NETS:
            vals = [v["reach"] for k, v in jd.get(n, {}).items() if w["start"] <= k <= w["end"]]
            w["j"][n] = sum(vals) if vals else None
        have = [v for v in w["j"].values() if v is not None]
        w["j_total"] = sum(have) if have else None
        prev_day = (date.fromisoformat(w["start"]) - timedelta(days=1)).isoformat()
        f0 = [_followers_on(jd[n], prev_day) for n in jd]
        f1 = [_followers_on(jd[n], w["end"]) for n in jd]
        w["j_fol"] = int(sum(f1) - sum(f0)) if all(x is not None for x in f0 + f1) and jd else None
        sp = [p for p in show_posts if w["start"] <= (p.get("created") or "")[:10] <= w["end"]]
        w["sc_posts"], w["sc_views"] = len(sp), sum(p.get("views") or 0 for p in sp)

    # ── Since Aug 18 / last full month ──
    j_reach_since = sum(v["reach"] for n, _, _ in NETS for v in jd.get(n, {}).values())
    fol_now = {n: _followers_on(s, through) for n, s in jd.items()}
    first = lambda s: min((k for k in s if k >= START.isoformat() and s[k]["followers"] is not None), default=None)
    fol_start = {n: s[first(s)]["followers"] for n, s in jd.items() if first(s)}   # Threads starts Sep 4
    fol_total = sum(v for v in fol_now.values() if v)
    fol_gain = int(sum((fol_now[n] or 0) - (fol_start.get(n) or 0) for n in fol_now if fol_now[n] and fol_start.get(n)))
    last_month = (date.fromisoformat(through).replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    lm_lbl = datetime.strptime(last_month, "%Y-%m").strftime("%B")
    lm_reach = {n: sum(v["reach"] for k, v in jd.get(n, {}).items() if k.startswith(last_month)) for n, _, _ in NETS}
    lm_total = sum(lm_reach.values())
    lm_sc = [p for p in show_posts if (p.get("created") or "").startswith(last_month)]
    lm_sc_views = sum(p.get("views") or 0 for p in lm_sc)
    sc_views_since = sum(p.get("views") or 0 for p in show_posts)
    # the month before, for the one-line summary
    pm = (date.fromisoformat(last_month + "-01") - timedelta(days=1)).strftime("%Y-%m")
    pm_lbl = datetime.strptime(pm, "%Y-%m").strftime("%B")
    pm_total = sum(v["reach"] for n, _, _ in NETS for k, v in jd.get(n, {}).items() if k.startswith(pm))
    pm_sc = [p for p in show_posts if (p.get("created") or "").startswith(pm)]
    pm_sc_views = sum(p.get("views") or 0 for p in pm_sc)
    yt_m = lambda m: sum(v.get("total_views", 0) for k, v in daily.items() if k.startswith(m))
    subs_now = tracker.get("current_subs") or 0
    net_since = sum(v.get("subs_gained", 0) - v.get("subs_lost", 0) for k, v in daily.items() if k >= START.isoformat())
    subs_start = subs_now - net_since
    yt_views_since = sum(v.get("total_views", 0) for k, v in daily.items() if k >= START.isoformat())
    audio = []
    ap = os.path.join(data_dir, "audio_sr.csv")
    if os.path.exists(ap):
        audio = [r for r in csv.DictReader(open(ap, encoding="utf-8-sig")) if (r.get("downloads") or "").strip()]
    dl_since = sum(int(float(r["downloads"])) for r in audio)

    # ── Story: latest complete week vs the one before ──
    done = [w for w in wins if not w["partial"] and w["j_total"] is not None]
    story = []
    if len(done) >= 2:
        c, p_ = done[-1], done[-2]
        lbl = f'{_md(c["start"])}–{_md(c["end"])}'
        parts = ", ".join(f'{name} {fmt(c["j"][n])}' for n, name, _ in NETS if c["j"][n] is not None)
        story.append(f'<b>Jordan\'s accounts</b>: {fmt(c["j_total"])} impressions in {lbl}'
                     f'{_pct_txt(_pct(c["j_total"], p_["j_total"]))} · {parts}'
                     + (f'; followers {c["j_fol"]:+,}' if c["j_fol"] is not None else "") + ".")
        wk_sc = sorted((p for p in show_posts if c["start"] <= (p.get("created") or "")[:10] <= c["end"]),
                       key=lambda p: -(p.get("views") or 0))
        if wk_sc:
            top = wk_sc[0]
            story.append(f'<b>Show content on Jordan\'s accounts</b>: {c["sc_posts"]} posts, {fmt(c["sc_views"])} views so far. '
                         f'Top: <a href="{top["url"]}" target="_blank" style="color:var(--brand)">'
                         f'{(top.get("text") or "post").strip().splitlines()[0][:70]}</a> ({fmt(top.get("views"))}).')
        yw = [w for w in wins if not w["partial"] and w["yt_views"] is not None]
        if len(yw) >= 2:
            story.append(f'<b>YouTube</b>: {fmt(yw[-1]["yt_views"])} views'
                         f'{_pct_txt(_pct(yw[-1]["yt_views"], yw[-2]["yt_views"]))}, {yw[-1]["yt_subs"]:+,} subscribers.')
    story.append(f'<b>Since Aug 18</b>: Jordan\'s accounts {fmt(j_reach_since)} impressions, '
                 f'{fol_gain:+,} followers to {fmt(fol_total)}; YouTube {net_since:+,} subscribers and {fmt(yt_views_since)} views'
                 + (f'; {fmt(dl_since)} podcast downloads.' if dl_since else "."))
    cur = wins[-1]
    if cur["partial"]:
        story.append(f'<span style="color:var(--text2)">The current week ({_md(cur["start"])}–{_md(cur["end"])}) is still '
                     f'in progress. Sprout and YouTube data lag one to two days.</span>')
    story_html = "".join(f"<li style='margin:4px 0'>{s}</li>" for s in story)

    # ── Headline cards ──
    def card(name, big, sub1, sub2="", accent=False):
        return (f'<div class="metric"{" style=\"border-color:var(--brand)\"" if accent else ""}>'
                f'<div class="metric-label">{name}</div><div class="metric-value">{big}</div>'
                f'<div class="metric-delta" style="color:var(--text2)">{sub1}</div>'
                + (f'<div class="metric-delta" style="color:var(--text2)">{sub2}</div>' if sub2 else "") + '</div>')
    split = " · ".join(f'{name} {fmt(lm_reach[n])}' for n, name, _ in NETS if lm_reach[n])
    share = f'≈{lm_sc_views / lm_total * 100:.0f}% of his {lm_lbl} impressions' if lm_total and lm_sc_views else ""
    cards = (
        card(f"Jordan's impressions · {lm_lbl}", fmt(lm_total), split, f'{fmt(j_reach_since)} since Aug 18', accent=True)
        + card("Jordan's followers", fmt(fol_total), f'{fol_gain:+,} since Aug 18',
               " · ".join(f'{NAME.get(n, n.title())} {fmt(v)}' for n, v in sorted(fol_now.items(), key=lambda x: -(x[1] or 0)) if v))
        + card(f"Show content on Jordan's accounts · {lm_lbl}", fmt(lm_sc_views), f'{len(lm_sc)} tagged posts', share)
        + card("YouTube · since Aug 18", f'{net_since:+,}',
               f'subscribers · {fmt(subs_start)} → {fmt(subs_now)}' if subs_start else "subscribers", f'{fmt(yt_views_since)} views')
        + (card("Podcast · since Aug 18", fmt(dl_since), "downloads (Simplecast)") if dl_since else "")
    )

    # ── One-line summary: last full month vs the month before ──
    chg = lambda a, b: f' ({"+" if a >= b else ""}{(a - b) / b * 100:.0f}% on {pm_lbl})' if b else ""
    summary = ""
    if lm_total:
        summary = (f'<b>{lm_lbl} in one line:</b> Jordan\'s accounts did {fmt(lm_total)} impressions{chg(lm_total, pm_total)}'
                   + (f', and Schultz Report content on them grew from {fmt(pm_sc_views)} to {fmt(lm_sc_views)} views '
                      f'({len(pm_sc)} → {len(lm_sc)} posts), now ≈{lm_sc_views / lm_total * 100:.0f}% of his audience'
                      if pm_sc_views and lm_sc_views else "")
                   + (f'. YouTube: {fmt(yt_m(last_month))} views{chg(yt_m(last_month), yt_m(pm))}.' if yt_m(last_month) else "."))
    summary_html = (f'<div class="card" style="border-left:3px solid var(--brand);font-size:15px;line-height:1.55">{summary}</div>'
                    if summary else "")

    top = f"""
    {summary_html}
    <div class="card-title" style="margin:4px 0 10px;font-size:15px">The Schultz network · led by Jordan's accounts</div>
    <div class="metrics">{cards}</div>
    <div class="card" style="border-left:3px solid var(--brand)">
      <div class="card-title">What the data says · week over week</div>
      <ul style="margin:0;padding-left:18px;line-height:1.5;font-size:13px">{story_html}</ul>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Impressions = X impressions + Instagram views + TikTok video views
        on Jordan's whole accounts (Sprout Social): every time a post is shown or viewed, not unique people. Show content = posts tagged as show content in Sprout, lifetime views.</div>
    </div>"""

    # ── Chart + table ──
    rows, prev = "", None
    for w in wins:
        lbl = f'{_md(w["start"])}–{_md(w["end"])}' + (" *" if w["partial"] else "")
        jp = _pct(w["j_total"], prev["j_total"]) if prev and not w["partial"] else None
        yp = _pct(w["yt_views"], prev["yt_views"]) if prev and not w["partial"] else None
        cells = "".join(f'<td>{fmt(w["j"][n])}</td>' for n, _, _ in NETS)
        signed = lambda v: f"{v:+,}" if v is not None else "—"
        rows = (f'<tr><td style="text-align:left">{lbl}</td><td><b>{fmt(w["j_total"])}</b>{_pct_html(jp)}</td>{cells}'
                f'<td>{signed(w["j_fol"])}</td><td>{w["sc_posts"]} · {fmt(w["sc_views"])}</td>'
                f'<td>{fmt(w["yt_views"])}{_pct_html(yp)}</td><td>{signed(w["yt_subs"])}</td></tr>') + rows
        prev = w
    labels = [f'{_md(w["start"])}–{_md(w["end"])}' + (" *" if w["partial"] else "") for w in wins]
    chart = json.dumps({"labels": labels, "series": [
        {"label": f"Jordan · {name}", "data": [w["j"][n] for w in wins], "color": COLORS[n]} for n, name, _ in NETS]})
    net_heads = "".join(f'<th>{name}</th>' for _, name, _ in NETS)

    detail = f"""
    <div class="card">
      <div class="card-title">Jordan's impressions by week · since Aug 18</div>
      <div style="height:280px"><canvas id="growth-chart"></canvas></div>
      <div class="table-scroll" style="margin-top:14px"><table class="data-table"><thead><tr><th style="text-align:left">Week</th>
        <th>Jordan · impressions</th>{net_heads}<th>Jordan · followers</th><th>Show content · posts · views</th>
        <th>YouTube views</th><th>YouTube subs</th></tr></thead><tbody>{rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">* in progress. % = change vs the previous week (weeks run Mon–Sun).
        Jordan: X impressions, Instagram views, TikTok video views, whole account (Sprout Social). Show content = posts published that week
        and tagged as show content, lifetime views. The show's own Instagram, TikTok and X are on the Socials tab.</div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const G = {chart}, el = document.getElementById('growth-chart');
      if (!el || typeof Chart === 'undefined') return;
      new Chart(el, {{ type:'bar', data:{{ labels:G.labels, datasets:G.series.map(s => ({{ label:s.label, data:s.data,
          backgroundColor:s.color, borderRadius:4, maxBarThickness:34, borderColor:'rgba(17,17,107,1)', borderWidth:2 }})) }},
        options:{{ responsive:true, maintainAspectRatio:false,
          plugins:{{ legend:{{ labels:{{ color:'#f2f2f2' }} }},
            tooltip:{{ callbacks:{{ label: c => c.dataset.label + ': ' + (c.raw == null ? '—' : c.raw.toLocaleString()) }} }} }},
          scales:{{ x:{{ stacked:true, grid:{{ display:false }}, ticks:{{ color:'#f2f2f2' }} }},
                   y:{{ stacked:true, beginAtZero:true, grid:{{ color:'rgba(255,255,255,.08)' }},
                        ticks:{{ color:'#f2f2f2', callback: v => v >= 1e6 ? (v/1e6)+'M' : v >= 1e3 ? (v/1e3)+'K' : v }} }} }} }} }});
    }});
    </script>"""
    return top, detail


def jordan_monthly(data_dir, fmt):
    """Socials tab: Jordan's whole accounts month by month (Sprout daily profile metrics), with the show content
    carried on them (posts tagged in Sprout, by month published, lifetime views)."""
    jd = _jordan_daily(data_dir)
    if not jd:
        return ""
    sprout = _load(os.path.join(rdm_dir(data_dir), "sprout", "posts.json"))
    show_posts = [p for p in sprout.get("posts", []) if p.get("owner") == "JS" and p.get("network") != "YOUTUBE"]
    months = sorted({d[:7] for s in jd.values() for d in s}, reverse=True)
    rows = ""
    for m in months:
        reach = {n: sum(v["reach"] for k, v in jd.get(n, {}).items() if k.startswith(m)) for n, _, _ in NETS}
        total = sum(reach.values())
        end = max(d for s in jd.values() for d in s if d.startswith(m))
        prev_end = (date.fromisoformat(m + "-01") - timedelta(days=1)).isoformat()
        fol_end = sum(_followers_on(s, end) or 0 for s in jd.values())
        pairs = [(_followers_on(s, prev_end), _followers_on(s, end)) for s in jd.values()]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]   # accounts with data at both ends
        gain = f'{int(sum(y - x for x, y in pairs)):+,}' if pairs else "—"
        sp = [p for p in show_posts if (p.get("created") or "").startswith(m)]
        scv = sum(p.get("views") or 0 for p in sp)
        month_end = (date.fromisoformat(m + "-28") + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        partial = " *" if date.fromisoformat(end) < month_end else ""
        lbl = datetime.strptime(m, "%Y-%m").strftime("%b %Y") + (" (from Aug 18)" if m == "2026-08" else "") + partial
        rows += (f'<tr><td style="text-align:left">{lbl}</td><td><b>{fmt(total)}</b></td>'
                 + "".join(f'<td>{fmt(reach[n])}</td>' for n, _, _ in NETS)
                 + f'<td>{fmt(fol_end)}</td><td>{gain}</td><td>{len(sp)} · {fmt(scv)}</td>'
                 f'<td>{f"{scv / total * 100:.0f}%" if total and scv else "—"}</td></tr>')
    heads = "".join(f'<th>{name}</th>' for _, name, _ in NETS)
    return f"""
    <div class="card"><div class="card-title">Jordan Schultz · whole accounts by month</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th style="text-align:left">Month</th><th>Impressions</th>{heads}
        <th>Followers</th><th>Follower change</th><th>Show content · posts · views</th><th>Show share</th></tr></thead>
        <tbody>{rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">* month in progress. Impressions = X impressions + Instagram views +
        TikTok video views across Jordan's whole accounts; followers include Threads (Sprout Social). Show content = posts tagged as
        show content in Sprout, by month published, lifetime views; show share = those views ÷ that month's impressions (approximate). X impressions are credited to the day a post went up, so the latest days fill in over time.</div>
    </div>"""
