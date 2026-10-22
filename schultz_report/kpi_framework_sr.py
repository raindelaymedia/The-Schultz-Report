"""
Overview — "Are we on track?" (Schultz Report KPI Framework V4, SR-KPI-001) + Top content this week.

Reads:
    from_rdm/content_sr.json   KPIs by week / month and per-upload grades (RDM's pull_content_sr.py)
    data_sr/kpi_targets.csv    season 1, comparable show, '26 base and lean-in per KPI (edit here; provisional
                               until they lock after the first 8–10 organic episodes)
    data_sr/ns_indicators.csv  North Star indicators, entered weekly (week_start,indicator,value,notes)
    data_sr/tests_sr.csv       the current test (CTA / thumbnail / intro), reviewed every ~10 episodes

KPI 3 (revenue per viewer) and the commercial milestones stay "pending" until revenue tracking is set up.
"""

import csv
import json
import os
from datetime import date, datetime, timedelta

from rdm_data import pick

NS = [("NS 1", "Most sought-after player platform", "Players ask to be on the show; we aren't chasing them."),
      ("NS 2", "The league's most respected outsider", "Teams and the league treat us as a partner, not a risk."),
      ("NS 3", "Break-even or better by year two", "≥50% of costs from sponsorship in '26; break-even all-in by end of year two.")]
INDICATORS = {  # indicator key → (North Star, label)
    "guest_requests": ("NS 1", "Inbound guest requests"), "players_booked": ("NS 1", "Active players booked"),
    "collaborations": ("NS 1", "Collaborations published (goal 2/month)"),
    "league_access": ("NS 2", "Team / league access or collaborations"), "league_shares": ("NS 2", "Times the league or teams shared the show"),
}
FORMAT = {"episode": "Episode", "clip": "Clip", "short": "Short"}


def _csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _pct(v, d=1):
    return "—" if v is None else f"{v * 100:.{d}f}%"


def _md(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.strftime('%b')} {d.day}"


def _status(v, base, lean):
    if v is None or base is None:
        return '<span style="color:var(--text2)">no data yet</span>'
    if lean is not None and v >= lean:
        return '<span class="up">at lean-in ✓</span>'
    if v >= base:
        return '<span class="up">at base</span>'
    return f'<span class="down">below base ({(v - base) * 100:+.1f} pts)</span>'


def _bar(v, base, lean, hi):
    """Progress bar with base and lean-in markers. hi = scale max."""
    if v is None:
        return ""
    w = max(0, min(1, v / hi)) * 100
    mk = lambda x, lab: (f'<div style="position:absolute;left:{x / hi * 100:.1f}%;top:-3px;bottom:-3px;width:2px;background:#f2f2f2" '
                         f'title="{lab}"></div>') if x else ""
    return (f'<div style="position:relative;height:8px;border-radius:4px;background:rgba(255,255,255,.12);margin:10px 0 4px">'
            f'<div style="height:100%;width:{w:.1f}%;border-radius:4px;background:var(--brand)"></div>'
            f'{mk(base, "base")}{mk(lean, "lean-in")}</div>'
            f'<div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text2)"><span>0</span>'
            f'<span>base {_pct(base, 1)} · lean-in {_pct(lean, 1)}</span></div>')


def _kpi_card(num, name, sub, defn, headline_label, month_v, week_v, week_lbl, t, extra=""):
    base, lean = _f(t.get("base")), _f(t.get("lean_in"))
    s1 = _pct(_f(t.get("season1"))) if _f(t.get("season1")) is not None else "TBD"
    ref = (f'<div class="metric-delta" style="color:var(--text2);margin-top:6px">Season 1 {s1}'
           f' · comparable RDM show {_pct(_f(t.get("comparable")))} · targets {t.get("status") or "provisional"}</div>')
    return f"""
    <div class="card" style="margin:0">
      <div style="display:flex;gap:10px;align-items:baseline"><span style="font-family:Oswald,sans-serif;font-size:30px;color:var(--brand)">{num}</span>
        <div><div class="card-title" style="margin:0">{name}</div><div class="metric-label">{sub}</div></div></div>
      <div class="metric-delta" style="color:var(--text2);margin:6px 0 10px">{defn}</div>
      <div class="metric-label">{headline_label} · this month</div>
      <div class="metric-value">{_pct(month_v)}</div>
      <div class="metric-delta">{_status(month_v, base, lean)} · last week ({week_lbl}) {_pct(week_v)}</div>
      {_bar(month_v, base, lean, max(lean or 0, month_v or 0) * 1.25 or 1)}
      {extra}{ref}
    </div>"""


def framework_section(data_dir, fmt):
    content = {}
    p = pick(data_dir, "content_sr.json")
    if os.path.exists(p):
        content = json.load(open(p, encoding="utf-8"))
    targets = {r["metric"]: r for r in _csv(os.path.join(data_dir, "kpi_targets.csv"))}
    kw, km = (content.get("kpis") or {}).get("week", {}), (content.get("kpis") or {}).get("month", {})
    today = date.today()
    cur_m = today.strftime("%Y-%m")
    last_w = (today - timedelta(days=today.weekday() + 7)).isoformat()      # last complete Mon–Sun week
    wlbl = f"{_md(last_w)}–{_md((date.fromisoformat(last_w) + timedelta(days=6)).isoformat())}"
    g = lambda src, per, f, k: ((src.get(per) or {}).get(f) or {}).get(k)

    # KPI 1 — retention
    ep_t, cl_t = targets.get("episode_pct_viewed", {}), targets.get("clip_pct_viewed", {})
    cl_m, cl_w = g(km, cur_m, "clip", "pct_viewed"), g(kw, last_w, "clip", "pct_viewed")
    k1_extra = (f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,.1)">'
                f'<div class="metric-label">Clips · % viewed this month</div>'
                f'<div style="font-family:Oswald,sans-serif;font-size:20px">{_pct(cl_m)}</div>'
                f'<div class="metric-delta">{_status(cl_m, _f(cl_t.get("base")), _f(cl_t.get("lean_in")))} · last week {_pct(cl_w)}</div>'
                f'<div class="metric-delta" style="color:var(--text2)">Avg minutes watched: episodes '
                f'{g(km, cur_m, "episode", "avg_minutes") or "—"} · clips {g(km, cur_m, "clip", "avg_minutes") or "—"}</div></div>')
    k1 = _kpi_card("1", "Audience retention", "Content quality",
                   "Long-form % viewed, by format, organic views only (YouTube ads excluded). Headline is full episodes; clips and average minutes underneath.",
                   "Episodes · % viewed", g(km, cur_m, "episode", "pct_viewed"), g(kw, last_w, "episode", "pct_viewed"),
                   wlbl, ep_t, k1_extra)

    # KPI 2 — organic long-form CTR, with first-day CTR per episode
    eps = sorted((dict(v, id=k) for k, v in (content.get("videos") or {}).items()
                  if v.get("format") == "episode" and v.get("first_day_ctr") is not None),
                 key=lambda v: v["published"], reverse=True)[:6]
    ct = targets.get("longform_ctr_organic", {})
    d1 = "".join(f'<tr><td style="text-align:left">{_md(v["published"])}</td><td><b>{_pct(v["first_day_ctr"])}</b></td>'
                 f'<td style="text-align:left"><a href="https://www.youtube.com/watch?v={vid_id(v)}" target="_blank" '
                 f'style="color:var(--brand)">{v["title"][:34]}…</a></td></tr>' for v in eps)
    k2_extra = (f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,.1)">'
                f'<div class="metric-label">First-day CTR · latest episodes (the test read)</div>'
                f'<div class="table-scroll"><table class="data-table" style="font-size:11px"><tbody>{d1 or "<tr><td>—</td></tr>"}</tbody></table></div>'
                f'<div class="metric-delta" style="color:var(--text2)">Publish day + the day after, organic. Episodes {_pct(g(km, cur_m, "episode", "ctr_organic"))}'
                f' · clips {_pct(g(km, cur_m, "clip", "ctr_organic"))} this month.</div></div>')
    k2 = _kpi_card("2", "Impression CTR", "Discovery · packaging",
                   "Long-form impressions CTR, organic traffic only. First-day CTR per episode is the test read.",
                   "Long-form CTR (organic)", g(km, cur_m, "longform", "ctr_organic"), g(kw, last_w, "longform", "ctr_organic"),
                   wlbl, ct, k2_extra)

    # KPI 3 — pending
    rt = targets.get("blended_rpm", {})
    money = lambda v: "—" if _f(v) is None else f"${_f(v):.2f}"
    k3 = f"""
    <div class="card" style="margin:0">
      <div style="display:flex;gap:10px;align-items:baseline"><span style="font-family:Oswald,sans-serif;font-size:30px;color:var(--brand)">3</span>
        <div><div class="card-title" style="margin:0">Revenue per viewer</div><div class="metric-label">Commercial viability</div></div></div>
      <div class="metric-delta" style="color:var(--text2);margin:6px 0 10px">Blended RPM per 1K long-form views, with the revenue mix:
        Fanatics, programmatic, RSS, branded.</div>
      <div class="metric-label">This month</div><div class="metric-value" style="color:var(--text2)">Pending</div>
      <div class="metric-delta" style="color:var(--text2)">Revenue tracking is being set up.</div>
      <div class="metric-delta" style="color:var(--text2);margin-top:6px">Season 1 {money(rt.get("season1"))} · comparable RDM show
        {money(rt.get("comparable"))} · '26 base {money(rt.get("base"))} · lean-in {money(rt.get("lean_in"))}</div>
    </div>"""

    ns = "".join(f'<div class="card" style="margin:0;border-top:3px solid var(--brand)"><div class="metric-label">{k}</div>'
                 f'<div class="card-title" style="margin:4px 0">{n}</div><div class="metric-delta" style="color:var(--text2)">{d}</div></div>'
                 for k, n, d in NS)

    # North Star indicators (manual, weekly)
    ind = _csv(os.path.join(data_dir, "ns_indicators.csv"))
    month_rows = [r for r in ind if (r.get("week_start") or "").startswith(cur_m)]
    tot = {}
    for r in month_rows:
        v = _f(r.get("value"))
        if v is not None:
            tot[r["indicator"]] = tot.get(r["indicator"], 0) + v
    ind_html = "".join(f'<div class="metric"><div class="metric-label">{ns_} · {lab}</div>'
                       f'<div class="metric-value">{fmt(tot.get(key)) if key in tot else "—"}</div>'
                       f'<div class="metric-delta" style="color:var(--text2)">this month</div></div>'
                       for key, (ns_, lab) in INDICATORS.items())
    tests = [r for r in _csv(os.path.join(data_dir, "tests_sr.csv")) if r.get("test")]
    test_html = ("".join(f'<tr><td style="text-align:left">{r["test"]}</td><td>{r.get("variable", "")}</td><td>{r.get("start_date", "")}</td>'
                         f'<td>{r.get("episodes", "")}</td><td>{r.get("status", "")}</td><td style="text-align:left">{r.get("result", "")}</td></tr>'
                         for r in reversed(tests))
                 or '<tr><td colspan="6" style="color:var(--text2)">No test running yet — add one to data_sr/tests_sr.csv</td></tr>')

    return f"""
    <div class="card-title" style="margin:6px 0 10px;font-size:16px">Are we on track? · KPI framework</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-bottom:14px">{ns}</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-bottom:14px">{k1}{k2}{k3}</div>
    <div class="card">
      <div class="card-title">Commercial milestones · NS 3</div>
      <div class="metrics">
        <div class="metric"><div class="metric-label">'26 season</div><div class="metric-value" style="font-size:20px">≥ 50% of opex</div><div class="metric-delta" style="color:var(--text2)">Pending — revenue tracking</div></div>
        <div class="metric"><div class="metric-label">End of year 2</div><div class="metric-value" style="font-size:20px">Break-even +</div><div class="metric-delta" style="color:var(--text2)">Pending — revenue tracking</div></div>
        <div class="metric"><div class="metric-label">12–24 months</div><div class="metric-value" style="font-size:20px">Diversified</div><div class="metric-delta" style="color:var(--text2)">Programmatic YouTube, RSS ad sales and branded content live alongside Fanatics</div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">North Star indicators · evidence we're moving (not KPIs)</div>
      <div class="metrics">{ind_html}</div>
      <div class="metric-delta" style="color:var(--text2)">Entered weekly in data_sr/ns_indicators.csv (week_start, indicator, value, notes).</div>
    </div>
    <div class="card">
      <div class="card-title">Current test · reviewed every ~10 comparable episodes (keep, adjust or stop)</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th style="text-align:left">Test</th><th>Variable</th><th>Started</th>
        <th>Episodes</th><th>Status</th><th style="text-align:left">Result</th></tr></thead><tbody>{test_html}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Targets are provisional: base and lean-in lock after the first
        8–10 organic episodes. Metrics are guideposts, not gotchas.</div>
    </div>"""


def vid_id(v):
    return v.get("id") or v.get("_id", "")


def top_content_section(data_dir, fmt):
    p = pick(data_dir, "content_sr.json")
    if not os.path.exists(p):
        return ""
    content = json.load(open(p, encoding="utf-8"))
    vids = content.get("videos") or {}
    today = date.today()
    last_w = (today - timedelta(days=today.weekday() + 7)).isoformat()
    week = [dict(v, id=k) for k, v in vids.items() if v.get("week") == last_w and (v.get("grade") or {}).get("letter")]
    if not week:
        return ""
    wlbl = f"{_md(last_w)}–{_md((date.fromisoformat(last_w) + timedelta(days=6)).isoformat())}"
    names = {"retention": "% viewed", "ctr": "CTR", "views": "views", "engagement": "engagement", "subs": "subs"}
    color = {"A": "#3BB273", "B": "#8BC34A", "C": "#E8C840", "D": "#E08C2A", "F": "#E05252"}

    def why(gr, fmt_):
        r = {k: x for k, x in (gr.get("ranks") or {}).items() if x is not None}
        if not r:
            return ""
        nm = lambda k: "engaged %" if (k == "ctr" and fmt_ == "short") else names[k]
        best, worst = max(r, key=r.get), min(r, key=r.get)
        return (f'{nm(best)} top {max(1, 100 - round(r[best] * 100))}%'
                + (f' · {nm(worst)} bottom {max(1, round(r[worst] * 100))}%' if r[worst] < .4 else ""))

    rows = ""
    for f in ("episode", "clip", "short"):
        items = sorted((v for v in week if v["format"] == f), key=lambda v: -(v["grade"]["score"] or 0))
        if not items:
            continue
        rows += (f'<tr><td colspan="9" style="text-align:left;font-weight:700;background:#161680">{FORMAT[f]}s · {len(items)}</td></tr>')
        for v in items:
            gr, vals = v["grade"], v["grade"].get("values") or {}
            rate = _pct(vals.get("ctr")) if vals.get("ctr") is not None else "—"
            paid = (v["by_age"][-1] if v.get("by_age") else {}).get("paid_views") or 0
            rows += (f'<tr><td style="width:44px;min-width:44px"><span style="display:inline-block;min-width:22px;text-align:center;border-radius:4px;font-weight:700;'
                     f'color:#11116b;background:{color[gr["letter"]]}">{gr["letter"]}</span></td>'
                     f'<td style="text-align:left;white-space:normal;min-width:300px;max-width:420px"><a href="https://www.youtube.com/watch?v={v["id"]}" '
                     f'target="_blank" style="color:var(--brand)">{v["title"][:80]}</a></td>'
                     f'<td>{_md(v["published"])} · day {gr["age_days"]}</td><td>{fmt(vals.get("views"))}</td>'
                     f'<td style="color:var(--text2)">{fmt(paid) if paid else "—"}</td>'
                     f'<td>{_pct(vals.get("retention"))}</td><td>{rate}</td><td>{_pct(vals.get("engagement"), 2)}</td>'
                     f'<td style="text-align:left;color:var(--text2)">{why(gr, f)}</td></tr>')
    w = content.get("weights") or {}
    return f"""
    <div class="card">
      <div class="card-title">Top content · week of {wlbl}</div>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Grade</th><th style="text-align:left">Upload</th>
        <th>Published · age</th><th>Organic views</th><th>Paid views</th><th>% viewed</th><th>CTR / engaged %</th><th>Engagement</th><th style="text-align:left">Why</th>
        </tr></thead><tbody>{rows}</tbody></table></div>
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Each upload is ranked against the same format's uploads from
        the previous {content.get("peer_days", 90)} days <b>at the same age</b> (a 3-day-old clip vs other clips at day 3).
        Weights: % viewed {w.get("retention", 0):.0%} · CTR {w.get("ctr", 0):.0%} (Shorts: engaged %) · views {w.get("views", 0):.0%}
        · engagement {w.get("engagement", 0):.0%} · subs per 1K views {w.get("subs", 0):.0%}. A = top 20% … F = bottom 20%.
        Everything is organic: views, % viewed and CTR leave out YouTube-ad traffic (paid views shown for reference, not graded).
        Data through {content.get("through", "")}.</div>
    </div>"""
