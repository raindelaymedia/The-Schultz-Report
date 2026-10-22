"""
Content tab — everything about individual pieces of content:
    1. YouTube uploads from last week, graded (from RDM's content_sr.json)
    2. Top 3 posts per social platform last week — show accounts (Instagram / TikTok APIs) and Jordan's
       accounts + the show's Facebook (Sprout Social, sponsor/show-tagged posts). Not graded yet.
    3. The current test (CTA / thumbnail / intro), from data_sr/tests_sr.csv
    4. How grading works — plain-English methodology
"""

import csv
import json
import os
from datetime import date, datetime, timedelta

from kpi_framework_sr import top_content_section, _csv, _md
from rdm_data import pick, rdm_dir

NET = {"INSTAGRAM": "Instagram", "TIKTOK": "TikTok", "X": "X", "THREADS": "Threads", "FACEBOOK": "Facebook"}


def _last_week():
    today = date.today()
    s = today - timedelta(days=today.weekday() + 7)
    return s.isoformat(), (s + timedelta(days=6)).isoformat()


def _posts_card(title, sub, posts, fmt, metric="views"):
    if posts:
        rows = "".join(
            f'<tr><td style="width:24px;color:var(--text2)">{i}</td><td style="text-align:left;white-space:normal">'
            f'<a href="{p["url"]}" target="_blank" style="color:var(--brand)">{(p.get("text") or "View post").strip()[:90] or "View post"}</a>'
            f'<div style="color:var(--text2);font-size:11px">{_md(p["created"])}</div></td>'
            f'<td style="font-weight:700">{fmt(p.get(metric))}</td></tr>' for i, p in enumerate(posts, 1))
        body = f'<table class="data-table" style="width:100%;font-family:inherit;white-space:normal"><tbody>{rows}</tbody></table>'
    else:
        body = '<div class="metric-delta" style="color:var(--text2)">No posts last week.</div>'
    return (f'<div class="card" style="margin:0"><div class="card-title" style="margin-bottom:2px">{title}</div>'
            f'<div class="metric-label" style="margin-bottom:8px">{sub}</div>{body}</div>')


def top_posts_section(data_dir, fmt):
    ws, we = _last_week()
    in_week = lambda p: ws <= (p.get("created") or "") <= we
    top3 = lambda ps, k="views": sorted([p for p in ps if in_week(p) and p.get(k) is not None], key=lambda p: -p[k])[:3]
    cards = []

    # Show accounts — APIs
    g = {}
    gp = pick(data_dir, "growth_sr.json")
    if os.path.exists(gp):
        g = json.load(open(gp, encoding="utf-8"))
    cards.append(_posts_card("Instagram · @theschultzreport", "Show account · views", top3((g.get("instagram") or {}).get("posts") or []), fmt))
    tdir = os.path.join(rdm_dir(data_dir), "tiktok", "daily")
    tt = []
    if os.path.isdir(tdir) and os.listdir(tdir):
        latest = sorted(os.listdir(tdir))[-1]
        for r in csv.DictReader(open(os.path.join(tdir, latest), encoding="utf-8-sig")):
            tt.append({"url": r["url"].split("?")[0], "created": r["created"], "views": int(float(r["views"] or 0)), "text": "TikTok video"})
    cards.append(_posts_card("TikTok · @theschultzreport", "Show account · views", top3(tt), fmt))

    # Sprout — Jordan's accounts + the show's Facebook
    sp = {}
    spp = os.path.join(rdm_dir(data_dir), "sprout", "posts.json")
    if os.path.exists(spp):
        sp = json.load(open(spp, encoding="utf-8"))
    posts = sp.get("posts") or []
    for owner, net in (("JS", "INSTAGRAM"), ("JS", "TIKTOK"), ("JS", "X"), ("JS", "THREADS"), ("SR", "FACEBOOK")):
        ps = [p for p in posts if p.get("owner") == owner and p.get("network") == net]
        who = "Jordan Schultz" if owner == "JS" else "Show account"
        unit = "impressions" if net == "X" else "views"
        cards.append(_posts_card(f'{NET[net]} · {"Jordan" if owner == "JS" else "The Schultz Report"}',
                                 f"{who} · {unit} · tagged in Sprout", top3(ps), fmt))
    return f"""
    <div class="card-title" style="margin:22px 0 10px;font-size:16px">Top posts by platform · week of {_md(ws)}–{_md(we)}</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px">{''.join(cards)}</div>
    <div class="metric-delta" style="color:var(--text2);margin-top:8px">Posts published last week, ranked by lifetime views so far
      (X: impressions). Jordan's accounts show only posts tagged as show content in Sprout. Not graded yet.</div>"""


def tests_section(data_dir):
    tests = [r for r in _csv(os.path.join(data_dir, "tests_sr.csv")) if r.get("test")]
    rows = ("".join(f'<tr><td style="text-align:left">{r["test"]}</td><td>{r.get("variable", "")}</td><td>{r.get("start_date", "")}</td>'
                    f'<td>{r.get("episodes", "")}</td><td>{r.get("status", "")}</td><td style="text-align:left">{r.get("result", "")}</td></tr>'
                    for r in reversed(tests))
            or '<tr><td colspan="6" style="color:var(--text2)">No test running yet.</td></tr>')
    return f"""
    <div class="card" style="margin-top:22px">
      <div class="card-title">Current test · one change at a time</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th style="text-align:left">Test</th><th>What changes</th><th>Started</th>
        <th>Episodes so far</th><th>Status</th><th style="text-align:left">Result</th></tr></thead><tbody>{rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Each test (a call to action, thumbnail style or intro) runs for about
        10 comparable episodes, then we keep it, adjust it or stop it.</div>
    </div>"""


def methodology_section(data_dir):
    content = {}
    p = pick(data_dir, "content_sr.json")
    if os.path.exists(p):
        content = json.load(open(p, encoding="utf-8"))
    w = content.get("weights") or {"retention": .35, "ctr": .35, "views": .15, "engagement": .10, "subs": .05}
    pct = lambda x: f"{x * 100:.0f}%"
    return f"""
    <div class="card" style="margin-top:22px;border-left:3px solid var(--brand)">
      <div class="card-title">How the grades work</div>
      <div style="font-size:13px;line-height:1.6">
        <p style="margin:0 0 10px"><b>The short version:</b> every YouTube upload is compared with the show's own recent uploads of the
          same kind, at the same age. A grade of <b>A</b> means it's doing better than about 80% of them; <b>C</b> is about average;
          <b>F</b> means it's behind about 80% of them. It's a comparison with ourselves, not with other channels.</p>
        <p style="margin:0 0 6px"><b>1. Like for like.</b> Episodes are only compared with episodes, clips with clips and Shorts with
          Shorts. A 3-day-old clip is compared with how other clips were doing on <i>their</i> day 3, so a brand-new upload isn't
          punished for being new.</p>
        <p style="margin:0 0 6px"><b>2. The comparison group.</b> Uploads of the same kind from the {content.get("peer_days", 90)} days
          before it was published (at least 5 of them; if there aren't enough yet, everything comparable is used).</p>
        <p style="margin:0 0 6px"><b>3. Five measures, each ranked against that group, then combined:</b></p>
        <table class="data-table" style="margin:4px 0 10px;font-family:inherit;white-space:normal"><thead><tr><th style="text-align:left">Measure</th>
          <th>Weight</th><th style="text-align:left">What it tells us</th></tr></thead><tbody>
          <tr><td style="text-align:left">% viewed</td><td>{pct(w["retention"])}</td><td style="text-align:left">How much of it people watch.
            KPI 1 (content quality).</td></tr>
          <tr><td style="text-align:left">Click-through rate</td><td>{pct(w["ctr"])}</td><td style="text-align:left">How often people who see
            the thumbnail click. KPI 2 (packaging). For Shorts, which don't have thumbnails in the feed, we use the share of views where
            people kept watching instead of swiping away ("engaged %").</td></tr>
          <tr><td style="text-align:left">Views</td><td>{pct(w["views"])}</td><td style="text-align:left">How many people it reached.</td></tr>
          <tr><td style="text-align:left">Engagement</td><td>{pct(w["engagement"])}</td><td style="text-align:left">Likes, comments and shares
            per view.</td></tr>
          <tr><td style="text-align:left">Subscribers</td><td>{pct(w["subs"])}</td><td style="text-align:left">New subscribers per 1,000 views.</td></tr>
        </tbody></table>
        <p style="margin:0 0 6px"><b>4. Grade bands.</b> The combined score (0–100) becomes a letter: A = 80+ (top 20%), B = 60–80,
          C = 40–60, D = 20–40, F = under 20. If a measure isn't available yet (e.g. too few impressions to judge CTR), the others are
          re-weighted.</p>
        <p style="margin:0 0 6px"><b>5. Organic only.</b> The show runs YouTube ads on some uploads. Views from ads behave very
          differently, so everything graded leaves them out. Paid views are shown in the table for reference.</p>
        <p style="margin:0"><b>Good to know:</b> grades move during the week as an upload ages and data settles (YouTube data runs about two days
          behind). Weights favour % viewed and CTR because those are KPI 1 and 2. They're a starting point to tune with the strategy
          team.</p>
      </div>
    </div>"""


def content_page(data_dir, fmt):
    graded = top_content_section(data_dir, fmt)
    return ((graded or '<div class="card"><div class="metric-delta" style="color:var(--text2)">No graded uploads for last week yet.</div></div>')
            + top_posts_section(data_dir, fmt) + tests_section(data_dir) + methodology_section(data_dir))
