"""
Data pushed in from RDM's internal repo (raindelaymedia/roadtrippin) every day.

All SR API keys live in RDM's repo. Its daily workflow pulls YouTube, Instagram and Sprout and copies
the results to data_sr/from_rdm/ here — this repo holds no keys and only builds from those files plus
its own manual inputs:

    from_rdm/tracker_data_sr.json      YouTube tracker (RDM)
    from_rdm/socials_sr.csv            socials incl. API-synced Instagram rows (RDM)
    from_rdm/sprout/posts.json         sponsor-tagged posts (Chime, Fanatics, Hims, Lowe's) with lifetime views
    from_rdm/sprout/daily/*.csv        daily snapshots of those views
    from_rdm/tiktok/daily/*.csv        SR TikTok per-video lifetime counts, one file per day
    from_rdm/fanatics_*.csv, reports/  Fanatics delivery data + reports (RDM builds the Fanatics report)

Ownership in socials: RDM_PLATFORMS rows come from RDM (API); every other row (X, YouTube engaged views,
anything Schultz-side) comes from this repo's own data_sr/socials_sr.csv, edited on the dashboard.
"""

import csv
import json
import os
from collections import defaultdict
from datetime import date

RDM_PLATFORMS = {"INSTAGRAM", "TIKTOK"}   # API-synced on RDM's side
NETWORK_NAME = {"INSTAGRAM": "Instagram", "TIKTOK": "TikTok", "X": "X", "YOUTUBE": "YouTube",
                "THREADS": "Threads", "FACEBOOK": "Facebook"}


def rdm_dir(data_dir):
    return os.path.join(data_dir, "from_rdm")


def pick(data_dir, name):
    """RDM's copy of a file if it has been pushed, otherwise this repo's own."""
    p = os.path.join(rdm_dir(data_dir), name)
    return p if os.path.exists(p) else os.path.join(data_dir, name)


def merged_socials(data_dir):
    """socials_sr.csv rows: RDM_PLATFORMS from RDM's file, everything else from ours. Returns a path."""
    own, rdm = os.path.join(data_dir, "socials_sr.csv"), os.path.join(rdm_dir(data_dir), "socials_sr.csv")
    if not os.path.exists(rdm):
        return own
    rows = {}
    for path, keep in ((own, lambda pl: pl not in RDM_PLATFORMS), (rdm, lambda pl: pl in RDM_PLATFORMS)):
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    pl = (r.get("platform") or "").strip().upper()
                    if keep(pl):
                        rows[(r["period"].strip(), pl, r["metric"].strip().upper())] = r["value"]
    out = os.path.join(data_dir, ".socials_merged.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["period", "platform", "metric", "value"])
        w.writerows([*k, v] for k, v in sorted(rows.items()))
    return out


def load_sprout(data_dir):
    p = os.path.join(rdm_dir(data_dir), "sprout", "posts.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    # YouTube comes from the channel itself (all of it is integrated) — Sprout's copy would double count
    d["posts"] = [x for x in d["posts"] if x.get("network") != "YOUTUBE"]
    return d


def _rollup(posts):
    """{network: {posts, views}} plus month-to-date."""
    month = date.today().strftime("%Y-%m")
    agg = defaultdict(lambda: {"posts": 0, "views": 0, "mtd_posts": 0, "mtd_views": 0})
    for p in posts:
        a = agg[p["network"]]
        a["posts"] += 1
        a["views"] += p.get("views") or 0
        if (p.get("created") or "").startswith(month):
            a["mtd_posts"] += 1
            a["mtd_views"] += p.get("views") or 0
    return agg


def _cards(agg, fmt, since):
    order = ["INSTAGRAM", "TIKTOK", "X", "YOUTUBE", "THREADS", "FACEBOOK"]
    out = ""
    for n in sorted(agg, key=lambda k: order.index(k) if k in order else 99):
        a = agg[n]
        out += (f'<div class="card soc-card"><div class="soc-card-head" style="border-color:var(--brand)">'
                f'<span class="soc-name">{NETWORK_NAME.get(n, n.title())}</span>'
                f'<span class="soc-followers">{fmt(a["views"])}</span></div>'
                f'<div class="soc-stats">'
                f'<div><div class="soc-stat-lbl">Posts since {since}</div><div class="soc-stat-val">{a["posts"]}</div></div>'
                f'<div><div class="soc-stat-lbl">This month</div><div class="soc-stat-val">{fmt(a["mtd_views"])} · {a["mtd_posts"]} posts</div></div>'
                f'</div></div>')
    return out


def jordan_pane(sprout, fmt):
    """Jordan Schultz's personal accounts — show content only (sponsor-tagged posts)."""
    if not sprout:
        return None
    posts = [p for p in sprout["posts"] if p.get("owner") == "JS"]
    if not posts:
        return None
    since = sprout.get("campaign_start", "")
    note = ('<div class="metric-delta" style="color:var(--text2);margin:-4px 0 4px;grid-column:1/-1">Show content only: posts tagged '
            'Chime, Fanatics, Hims or Lowe\'s in Sprout Social · lifetime views · updated '
            f'{sprout.get("pulled", "")} (through {sprout.get("through", "")})</div>')
    return note + _cards(_rollup(posts), fmt, since)


def sponsor_sprout_section(sponsor, sprout, fmt):
    """Per-sponsor totals from Sprout tags, split by account owner and network, with top posts."""
    if not sprout:
        return ('<div class="card"><div class="card-title">Sprout Social</div><div class="metric-delta" '
                'style="color:var(--text2)">Waiting on the first Sprout sync from RDM.</div></div>')
    posts = [p for p in sprout["posts"] if sponsor in (p.get("sponsors") or [])]
    if not posts:
        return (f'<div class="card"><div class="card-title">Sprout Social · tag “{sponsor}”</div><div class="metric-delta" '
                f'style="color:var(--text2)">No posts tagged {sponsor} since {sprout.get("campaign_start", "")}.</div></div>')
    rows = defaultdict(lambda: [0, 0])
    for p in posts:
        k = ("Jordan Schultz" if p["owner"] == "JS" else "The Schultz Report", NETWORK_NAME.get(p["network"], p["network"]))
        rows[k][0] += 1
        rows[k][1] += p.get("views") or 0
    table = "".join(f"<tr><td>{o}</td><td>{n}</td><td>{c}</td><td>{fmt(v)}</td></tr>"
                    for (o, n), (c, v) in sorted(rows.items(), key=lambda x: -x[1][1]))
    top = sorted(posts, key=lambda p: -(p.get("views") or 0))[:5]
    top_html = "".join(
        f'<tr><td>{fmt(p.get("views"))}</td><td style="text-align:left"><a href="{p["url"]}" target="_blank" '
        f'style="color:var(--brand)">{(p.get("text") or p["url"])[:80]}</a></td>'
        f'<td>{NETWORK_NAME.get(p["network"], p["network"])} · {p.get("created", "")}</td></tr>' for p in top)
    total = sum(p.get("views") or 0 for p in posts)
    return f"""
    <div class="card"><div class="card-title">Sprout Social · tag “{sponsor}” · {len(posts)} posts · {fmt(total)} views</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Account</th><th>Network</th><th>Posts</th><th>Views</th></tr></thead>
      <tbody>{table}</tbody></table></div>
      <div class="card-title" style="margin-top:16px">Top posts</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Views</th><th>Post</th><th>Where</th></tr></thead>
      <tbody>{top_html}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Lifetime views as of {sprout.get('pulled', '')} · since {sprout.get('campaign_start', '')}</div>
    </div>"""
