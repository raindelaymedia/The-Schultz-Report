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
            f'<span>target {_pct(base, 1)} · stretch {_pct(lean, 1)}</span></div>')


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


def _chip(v, base, lean):
    """Plain-language status: On target / Close / Below target / No data yet."""
    if v is None or base is None:
        return '<span class="ns-chip" style="background:rgba(255,255,255,.12)">No data yet</span>'
    if lean is not None and v >= lean:
        return '<span class="ns-chip" style="background:#3BB273;color:#11116b">Stretch goal hit ✓</span>'
    if v >= base:
        return '<span class="ns-chip" style="background:#3BB273;color:#11116b">On target ✓</span>'
    if v >= base * 0.9:
        return '<span class="ns-chip" style="background:#E8C840;color:#11116b">Close</span>'
    return '<span class="ns-chip" style="background:#E08C2A;color:#11116b">Below target</span>'


def _kpi_tile(num, name, plain, value, chip, bar, foot, details):
    return f"""
      <div class="ns-tile">
        <div class="metric-label">KPI {num} · {name}</div>
        <div class="metric-delta" style="color:var(--text2);margin:2px 0 6px">{plain}</div>
        <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap"><div class="metric-value" style="margin:0">{value}</div>{chip}</div>
        {bar}
        <div class="metric-delta" style="color:var(--text2)">{foot}</div>
        <details style="margin-top:6px"><summary style="cursor:pointer;color:var(--brand);font-size:12px">Details</summary>
          <div class="metric-delta" style="color:var(--text2);margin-top:6px">{details}</div></details>
      </div>"""


def _count_tile(label, value, sub):
    return (f'<div class="ns-tile"><div class="metric-label">{label}</div><div class="metric-value">{value}</div>'
            f'<div class="metric-delta" style="color:var(--text2)">{sub}</div></div>')


def _ns_row(code, title, desc, status, tiles):
    return f"""
    <div class="ns-row">
      <div class="ns-head"><div class="metric-label" style="color:var(--brand)">{code}</div>
        <div class="card-title" style="margin:4px 0;font-size:16px">{title}</div>
        <div class="metric-delta" style="color:var(--text2);margin-bottom:10px">{desc}</div>{status}</div>
      <div class="ns-tiles">{tiles}</div>
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
    mon = today.strftime("%B")
    last_w = (today - timedelta(days=today.weekday() + 7)).isoformat()
    wlbl = f"{_md(last_w)}–{_md((date.fromisoformat(last_w) + timedelta(days=6)).isoformat())}"
    g = lambda src, per, f, k: ((src.get(per) or {}).get(f) or {}).get(k)
    T = lambda m: (_f(targets.get(m, {}).get("base")), _f(targets.get(m, {}).get("lean_in")))
    s1 = lambda m: _pct(_f(targets.get(m, {}).get("season1"))) if _f(targets.get(m, {}).get("season1")) is not None else "TBD"
    prov = " (provisional — locks after 8–10 organic episodes)"

    # KPI 1 — retention
    eb, el = T("episode_pct_viewed")
    cb, cl = T("clip_pct_viewed")
    ep_m, ep_w = g(km, cur_m, "episode", "pct_viewed"), g(kw, last_w, "episode", "pct_viewed")
    cl_m, cl_w = g(km, cur_m, "clip", "pct_viewed"), g(kw, last_w, "clip", "pct_viewed")
    k1 = _kpi_tile(1, "Audience retention", "How much of each full episode people watch (organic views).",
                   _pct(ep_m), _chip(ep_m, eb, el), _bar(ep_m, eb, el, max(el or 0, ep_m or 0) * 1.25 or 1),
                   f"{mon} so far · last week ({wlbl}) {_pct(ep_w)} · target {_pct(eb, 0)}, stretch {_pct(el, 0)}",
                   f"<b>Clips:</b> {_pct(cl_m)} this month ({_pct(cl_w)} last week) — target {_pct(cb, 0)}, stretch {_pct(cl, 0)} "
                   f"{_chip(cl_m, cb, cl)}<br>Average minutes watched: episodes {g(km, cur_m, 'episode', 'avg_minutes') or '—'}, "
                   f"clips {g(km, cur_m, 'clip', 'avg_minutes') or '—'}<br>Season 1 {s1('episode_pct_viewed')} · comparable RDM show "
                   f"{_pct(_f(targets.get('episode_pct_viewed', {}).get('comparable')), 0)}{prov}. Views from YouTube ads are left out.")

    # KPI 2 — organic long-form CTR
    ctb, ctl = T("longform_ctr_organic")
    ct_m, ct_w = g(km, cur_m, "longform", "ctr_organic"), g(kw, last_w, "longform", "ctr_organic")
    eps = sorted((dict(v, id=k) for k, v in (content.get("videos") or {}).items()
                  if v.get("format") == "episode" and v.get("first_day_ctr") is not None),
                 key=lambda v: v["published"], reverse=True)[:5]
    d1 = "".join(f'<tr><td style="text-align:left">{_md(v["published"])}</td><td><b>{_pct(v["first_day_ctr"])}</b></td>'
                 f'<td style="text-align:left"><a href="https://www.youtube.com/watch?v={v["id"]}" target="_blank" '
                 f'style="color:var(--brand)">{v["title"][:34]}…</a></td></tr>' for v in eps)
    k2 = _kpi_tile(2, "Impression click-through rate", "How often people who see a thumbnail click it (long-form, organic).",
                   _pct(ct_m), _chip(ct_m, ctb, ctl), _bar(ct_m, ctb, ctl, max(ctl or 0, ct_m or 0) * 1.25 or 1),
                   f"{mon} so far · last week {_pct(ct_w)} · target {_pct(ctb)}, stretch {_pct(ctl)}",
                   f"Episodes {_pct(g(km, cur_m, 'episode', 'ctr_organic'))} · clips {_pct(g(km, cur_m, 'clip', 'ctr_organic'))} this month."
                   f"<br><b>First-day CTR, latest episodes</b> (the test read):"
                   f'<table class="data-table" style="font-size:11px;margin-top:4px"><tbody>{d1 or "<tr><td>—</td></tr>"}</tbody></table>'
                   f"Season 1 {s1('longform_ctr_organic')} · comparable RDM show "
                   f"{_pct(_f(targets.get('longform_ctr_organic', {}).get('comparable')))}{prov}.")

    # Manual North Star indicators (weekly entries summed for the month)
    tot = {}
    for r in _csv(os.path.join(data_dir, "ns_indicators.csv")):
        v = _f(r.get("value"))
        if v is not None and (r.get("week_start") or "").startswith(cur_m):
            tot[r["indicator"]] = tot.get(r["indicator"], 0) + v
    cnt = lambda key, label, sub: _count_tile(label, fmt(tot[key]) if key in tot else "—", sub)
    manual = f"{mon} · entered weekly"

    k_status = [x for x in ((ep_m, eb), (ct_m, ctb)) if x[0] is not None and x[1] is not None]
    if not k_status:
        ns1_status = _chip(None, None, None)
    elif all(v >= b for v, b in k_status):
        ns1_status = '<span class="ns-chip" style="background:#3BB273;color:#11116b">KPIs on target ✓</span>'
    elif any(v >= b for v, b in k_status):
        ns1_status = '<span class="ns-chip" style="background:#E8C840;color:#11116b">Mixed</span>'
    else:
        ns1_status = '<span class="ns-chip" style="background:#E08C2A;color:#11116b">KPIs below target</span>'
    pending = '<span class="ns-chip" style="background:rgba(255,255,255,.12)">Waiting on inputs</span>'

    rt = targets.get("blended_rpm", {})
    money = lambda v: "—" if _f(v) is None else f"${_f(v):.2f}"
    k3 = _kpi_tile(3, "Revenue per viewer", "Revenue for every 1,000 long-form views (Fanatics, ads, RSS, branded).",
                   '<span style="color:var(--text2)">Pending</span>', "", "",
                   f"Target {money(rt.get('base'))}, stretch {money(rt.get('lean_in'))} · revenue tracking is being set up",
                   f"Season 1 {money(rt.get('season1'))} (ads ran on 0.46% of views) · comparable RDM show {money(rt.get('comparable'))}.")

    rows = (
        _ns_row("NORTH STAR 1", "Most sought-after player platform", "Players ask to be on the show; we aren't chasing them.", ns1_status,
                k1 + k2 + cnt("guest_requests", "Inbound guest requests", manual)
                + cnt("players_booked", "Active players booked", manual)
                + cnt("collaborations", "Collaborations published", f"goal: 2 a month · {manual}"))
        + _ns_row("NORTH STAR 2", "The league's most respected outsider", "Teams and the league treat us as a partner, not a risk.",
                  pending if not any(k in tot for k in ("league_access", "league_shares")) else "",
                  cnt("league_access", "Team / league access or collaborations", manual)
                  + cnt("league_shares", "Times the league or teams shared the show", manual))
        + _ns_row("NORTH STAR 3", "Break-even or better by year two", "≥50% of costs from sponsorship in '26; break-even all-in by end of year two.",
                  '<span class="ns-chip" style="background:rgba(255,255,255,.12)">Pending revenue tracking</span>',
                  k3 + _count_tile("'26 season", "≥ 50% of costs", "covered by sponsorship · pending")
                  + _count_tile("End of year 2", "Break-even +", "all-in, no paid media · pending")
                  + _count_tile("12–24 months", "Diversified", "YouTube ads, RSS ad sales and branded content live alongside Fanatics"))
    )
    return f"""
    <style>
      .ns-row{{display:grid;grid-template-columns:260px 1fr;gap:16px;padding:18px;margin-bottom:14px;border-radius:12px;
               background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08)}}
      .ns-head{{border-right:1px solid rgba(255,255,255,.08);padding-right:16px}}
      .ns-tiles{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;align-items:start}}
      .ns-tile{{background:rgba(255,255,255,.05);border-radius:10px;padding:14px}}
      .ns-chip{{display:inline-block;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700}}
      @media (max-width:900px){{.ns-row{{grid-template-columns:1fr}}.ns-head{{border-right:0;padding-right:0}}}}
    </style>
    <div class="card-title" style="margin:6px 0 4px;font-size:16px">Are we on track?</div>
    <div class="metric-delta" style="color:var(--text2);margin-bottom:12px">Each North Star with the numbers that show progress toward it.
      KPIs update daily from YouTube; the counts are entered weekly by the team. Metrics are guideposts, not gotchas.</div>
    {rows}"""


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
      <div class="metric-delta" style="color:var(--text2);margin-top:8px">Grades compare each upload with the show's own recent
        uploads of the same kind at the same age — see <b>How the grades work</b> at the bottom of this page. Organic only (views from
        YouTube ads are shown but not graded). Data through {content.get("through", "")}.</div>
    </div>"""
