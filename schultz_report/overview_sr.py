"""
Overview tab — headline numbers across the show accounts, Jordan's show content and the sponsors.

Everything here is read from data the other tabs already use (tracker JSON, merged socials, audio CSV,
Sprout posts, sponsors.csv) — nothing new to maintain.
"""

from collections import defaultdict
from datetime import date, datetime

from growth_sr import growth_section

NET = {"INSTAGRAM": "Instagram", "TIKTOK": "TikTok", "X": "X", "YOUTUBE": "YouTube",
       "THREADS": "Threads", "FACEBOOK": "Facebook"}


def _mon(ym):
    return datetime.strptime(ym, "%Y-%m").strftime("%b")


def _soc(socials, plat, metric, ym):
    months = socials.get("months", [])
    if ym not in months:
        return None
    v = socials.get("data", {}).get((plat, metric), [None] * len(months))[months.index(ym)]
    return v if isinstance(v, (int, float)) else None


def _delta(cur, prev, fmt, label):
    if cur is None or not prev:
        return f'<div class="metric-delta" style="color:var(--text2)">{label}</div>'
    d = cur - prev
    return (f'<div class="metric-delta"><span class="{"up" if d >= 0 else "down"}">{"+" if d >= 0 else ""}{fmt(d)}</span> '
            f'<span style="color:var(--text2)">{label}</span></div>')


def _metric(label, value, sub):
    return f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div>{sub}</div>'


def overview_page(d, socials, audio, sponsors, sprout, fmt, data_dir="."):
    today = date.today()
    cur = today.strftime("%Y-%m")
    prev = (today.replace(day=1).toordinal() - 1)
    prev = date.fromordinal(prev).strftime("%Y-%m")
    cm, pm = _mon(cur), _mon(prev)

    # ── YouTube ──
    yt_months = d.get("months", [])
    def yt(key, ym):
        return d[key][yt_months.index(ym)] if ym in yt_months and d.get(key) else None
    yt_views = lambda ym: sum(v or 0 for v in (yt("vids", ym), yt("shorts", ym), yt("lives", ym))) if ym in yt_months else None
    uploads = lambda ym: sum(1 for v in d.get("all_videos", []) if v.get("month") == ym)
    gained = (yt("subs_gained", cur) or 0) - (yt("subs_lost", cur) or 0) if yt("subs_gained", cur) is not None else None

    # ── Show socials (Instagram, TikTok, X) ──
    soc_plats = [p for p in ("INSTAGRAM", "TIKTOK", "X") if p in socials.get("platforms", [])]
    soc_views = lambda ym: sum(_soc(socials, p, "VIEWS", ym) or 0 for p in soc_plats)

    # ── Audio ──
    last_audio = audio[-1] if audio else None

    metrics = '<div class="metrics">' + "".join([
        _metric("YouTube subscribers", fmt(d.get("current_subs")) if d.get("current_subs") else "—",
                f'<div class="metric-delta"><span class="{"up" if (gained or 0) >= 0 else "down"}">'
                f'{"+" if (gained or 0) >= 0 else ""}{fmt(gained)}</span> <span style="color:var(--text2)">in {cm}</span></div>'
                if gained is not None else '<div class="metric-delta" style="color:var(--text2)">live count</div>'),
        _metric(f"YouTube views · {cm}", fmt(yt_views(cur)), _delta(None, None, fmt, f"{pm}: {fmt(yt_views(prev))}")),
        _metric(f"Show social views · {cm}", fmt(soc_views(cur)),
                _delta(None, None, fmt, f"{pm}: {fmt(soc_views(prev))} · " + " + ".join(NET[p] for p in soc_plats))),
        _metric("Podcast downloads", fmt(last_audio["downloads"]) if last_audio else "—",
                f'<div class="metric-delta" style="color:var(--text2)">'
                f'{(last_audio["notes"] or (last_audio["start"] + " – " + last_audio["end"])) if last_audio else "Simplecast · not entered yet"}</div>'),
    ]) + "</div>"

    # ── Show accounts table ──
    def row(name, followers, gain, v_cur, v_prev, posts):
        g = "" if gain is None else f' <span class="{"up" if gain >= 0 else "down"}" style="font-size:11px">({"+" if gain >= 0 else ""}{fmt(gain)})</span>'
        return (f'<tr><td style="text-align:left">{name}</td><td>{fmt(followers)}{g}</td><td>{fmt(v_cur)}</td>'
                f'<td>{fmt(v_prev)}</td><td>{fmt(posts)}</td></tr>')
    rows = row("YouTube", d.get("current_subs"), gained, yt_views(cur), yt_views(prev), uploads(cur))
    for p in soc_plats:
        fol = _soc(socials, p, "FOLLOWERS", cur) or _soc(socials, p, "FOLLOWERS", prev)
        rows += row(NET[p], fol, _soc(socials, p, "FOLLOWER_GAIN", cur), _soc(socials, p, "VIEWS", cur),
                    _soc(socials, p, "VIEWS", prev), _soc(socials, p, "POSTS", cur))
    show_table = f"""
    <div class="card"><div class="card-title">Show accounts · {cm} to date</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th style="text-align:left">Account</th>
        <th>Followers / subs</th><th>Views · {cm}</th><th>Views · {pm}</th><th>Posts · {cm}</th></tr></thead>
      <tbody>{rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">YouTube, Instagram and TikTok update daily; X is entered by hand
        (blank until this month's numbers are in). TikTok views = growth in all videos' lifetime views during the month.</div>
    </div>"""

    # ── Sponsors (Sprout tags) + Jordan's show content ──
    posts = (sprout or {}).get("posts", [])
    by_s = defaultdict(lambda: {"mtd": 0, "all": 0, "views": 0, "js": 0, "sr": 0})
    for p in posts:
        for s in p.get("sponsors") or []:
            a = by_s[s]
            a["all"] += 1
            a["views"] += p.get("views") or 0
            a["mtd"] += (p.get("created") or "").startswith(cur)
            a["js" if p.get("owner") == "JS" else "sr"] += 1
    sp_rows = ""
    for s in sponsors or []:
        name = s.get("sponsor", "").strip()
        a = by_s.get(s.get("sprout_tag") or name, {"mtd": 0, "all": 0, "views": 0, "js": 0, "sr": 0})
        flight = (f'{s["start"]} – {s["end"]}' if s.get("start") else "terms pending")
        goal = f' · goal {fmt(int(float(s["impression_goal"])))}' if (s.get("impression_goal") or "").strip() else ""
        sp_rows += (f'<tr><td style="text-align:left">{name}</td><td>{a["mtd"]}</td><td>{a["all"]}</td>'
                    f'<td>{a["js"]} / {a["sr"]}</td><td>{fmt(a["views"])}</td>'
                    f'<td style="text-align:left;color:var(--text2)">{flight}{goal}</td></tr>')
    since = (sprout or {}).get("campaign_start", "")
    sponsor_table = f"""
    <div class="card"><div class="card-title">Sponsors · tagged posts (Sprout Social)</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th style="text-align:left">Sponsor</th>
        <th>Posts · {cm}</th><th>Posts since {since}</th><th>Jordan / show</th><th>Lifetime views</th>
        <th style="text-align:left">Campaign</th></tr></thead>
      <tbody>{sp_rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Posts tagged in Sprout on Jordan's accounts and the show's
        Facebook. YouTube is counted from the channel itself. Updated {(sprout or {}).get("pulled", "—")}.</div>
    </div>""" if sponsors else ""

    js = defaultdict(lambda: [0, 0, 0])          # network → [posts this month, posts total, views]
    for p in posts:
        if p.get("owner") == "JS":
            a = js[p["network"]]
            a[0] += (p.get("created") or "").startswith(cur)
            a[1] += 1
            a[2] += p.get("views") or 0
    js_x_m = next((m for m in (cur, prev) if _soc(socials, "JS_X", "FANATICS_IMPRESSIONS", m)), None)
    js_x = _soc(socials, "JS_X", "FANATICS_IMPRESSIONS", js_x_m) if js_x_m else None
    js_cards = "".join(
        f'<div class="metric"><div class="metric-label">Jordan · {NET.get(n, n.title())}</div>'
        f'<div class="metric-value">{fmt(v)}</div><div class="metric-delta" style="color:var(--text2)">'
        f'{c} posts · {m} in {cm}</div></div>' for n, (m, c, v) in sorted(js.items(), key=lambda x: -x[1][2]))
    if js_x and "X" not in js:                 # manual figure only until Sprout covers X
        js_cards += (f'<div class="metric"><div class="metric-label">Jordan · X</div><div class="metric-value">{fmt(js_x)}</div>'
                     f'<div class="metric-delta" style="color:var(--text2)">impressions · {_mon(js_x_m)} (entered by hand)</div></div>')
    jordan = (f'<div class="card-title" style="margin:8px 0 10px">Jordan Schultz · show content (sponsor-tagged posts, lifetime views)</div>'
              f'<div class="metrics">{js_cards}</div>') if js_cards else ""

    # ── Top YouTube this month ──
    top = sorted((v for v in d.get("all_videos", []) if v.get("month") == cur), key=lambda v: -(v.get("views") or 0))[:5]
    top_rows = "".join(
        f'<tr><td>{fmt(v.get("views"))}</td><td style="text-align:left"><a href="https://www.youtube.com/watch?v={v["id"]}" '
        f'target="_blank" style="color:var(--brand)">{(v.get("title") or "")[:80]}</a></td>'
        f'<td>{"Short" if v.get("type") == "short" else "Video"} · {v.get("published", "")}</td></tr>' for v in top)
    top_card = f"""
    <div class="card"><div class="card-title">Top YouTube uploads · {cm}</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Views</th><th style="text-align:left">Video</th><th>Type · published</th></tr></thead>
      <tbody>{top_rows}</tbody></table></div></div>""" if top else ""

    this_month = (f'<div class="card-title" style="margin:22px 0 10px;font-size:15px">This month · {cm} to date</div>')
    return growth_section(data_dir, socials, fmt) + this_month + metrics + show_table + jordan + sponsor_table + top_card
