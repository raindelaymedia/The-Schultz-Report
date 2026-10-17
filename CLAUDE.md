# The Schultz Report — shared dashboard (RDM × Schultz Media)

A collaborative analytics dashboard for **The Schultz Report**, built by Rain Delay Media (RDM) and shared with
Schultz Media. It mirrors RDM's internal SR dashboard (repo `raindelaymedia/roadtrippin`, local folder `data`) plus
metrics Schultz Media will specify (TBD). Mostly API-driven: daily refresh → static HTML on GitHub Pages.
Owner on the RDM side: Andrew Priest (andrew@raindelaymedia.com).

## Status (handoff, Oct 2026)

Seeded from the internal repo: the SR pipeline is copied in and repointed to this layout, but **nothing is wired
up yet** — no workflow, no Pages, no secrets. Next steps, in order:
1. Andrew adds local keys (see Keys) — never commit them.
2. Get the existing scripts running locally here: tracker → dashboard → Fanatics report (`--no-write`).
3. Decide the single-refresher question (below), then write `.github/workflows/daily.yml`.
4. Enable GitHub Pages; decide access control before sharing the link.
5. Sprout Social API once Schultz Media provides a token; then the Schultz-specific metrics.

## Working style

- Numbers forward; outside-facing text short. Andrew writes the prose — give him tight figures.
- Flag problems before acting (wrong account, numbers that don't reconcile, data that would be overwritten).
- Test with `--dry-run` / `--no-write` first. Never commit test files/outputs. Never print, echo or commit keys.
- Windows, **PowerShell** (no `&&` chaining). Python 3.12. Deps: google-api-python-client, google-auth-*,
  requests, openpyxl, python-dateutil.

## Layout

```
schultz_report/
  build_tracker_sr.py            YouTube Analytics + Data API → data_sr/tracker_data_sr.json
  build_sr_dashboard.py          → schultz_report.html (SR brand). Its sidebar still links "← RDM Network"
                                 (../../../index.html) — remove/replace for the shared version.
  build_fanatics_report_sr.py    SR × Fanatics monthly delivery report (+ fanatics_report_template_sr.py)
  sr_growth_snapshot.py, snapshot_sr_historical.py   one-off analysis scripts
  config_sr.py                   YouTube OAuth (gitignored — create locally)
  data_sr/
    socials_sr.csv               long format period,platform,metric,value (period = YYYY-MM)
    tracker_data_sr.json         generated
    fanatics_episodes_sr.csv     every full episode by type (video_id, date, type, title)
    fanatics_posts_sr.csv        every Fanatics-watermarked social post by URL (views refreshed at build)
    fanatics_history_sr.csv      one row per reported period (cumulative)
    reports/fanatics/            report HTML + saved inputs per period
common/
  yt_period_views.py             views DURING a period per video, for everything posted since a cutoff
  tiktok_auth.py                 TikTok connection + exact per-video stats (link / exchange / test / status / views)
  sync_socials.py                Instagram account metrics → socials_sr.csv (SR only here)
  config_socials.py              IG / TikTok / Sprout keys (gitignored — create locally)
```

## Keys (local files + GitHub secrets, same names)

- `schultz_report/config_sr.py`: `YT_CHANNEL_ID = "UCD50DP5meQbRD0ug-dm1p1g"`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
  `YT_REFRESH_TOKEN` (OAuth for the SR channel; Google project in **Published** mode, refresh tokens don't rotate).
- `common/config_socials.py`: `IG_TOKEN_SR` (Instagram API with Instagram Login, account `theschultzreport`,
  graph.instagram.com v25.0; 60-day token, refreshed on use), `TT_CLIENT_KEY` / `TT_CLIENT_SECRET` (TikTok app
  **RDM SOCIALS**, sandbox keys start with `sb`), `TT_TOKEN_SR` (connected), `TT_TOKEN_JS` (Jordan — pending),
  later `SPROUT_TOKEN`.
- **Single-refresher rule — important.** Instagram and TikTok tokens are replaced every time they're refreshed. If
  this repo's workflow and the internal repo's workflow both refresh the same token, they invalidate each other.
  Only ONE place may refresh each token. Plan: make this repo the SR data source (it refreshes IG_TOKEN_SR /
  TT_TOKEN_*), and the internal repo reads SR files from here. Until that switch is agreed, do not put
  `IG_TOKEN_SR` in this repo's secrets and don't schedule refreshes here. Local runs never refresh IG tokens.

## Data rules (SR × Fanatics)

- Term **Sep 1 2026 – Aug 31 2027** (no Fanatics content before Sep 1). Minimum Impression Target **87,915,000**.
- **Only Fanatics-watermarked content counts.** SR Instagram + Keyshawn = URL list in `fanatics_posts_sr.csv`;
  SR TikTok = per-video exact views via the TikTok API; SR X = account total (all watermarked).
- **Jordan Schultz's personal accounts**: Fanatics-tagged posts from **Sprout Social** (monthly totals per platform
  for now; per-post via the Sprout API later). Instagram/TikTok = views, X = impressions.
- **YouTube**: every view DURING the period on all SR channel videos published on/after **2026-09-01**, per video
  (YouTube Analytics, `common/yt_period_views.py`). New-upload counts = videos published in the period.
  Analytics lags ~2 days — run reports 2–3 days after a period ends.
- **Multipliers** (impressions per view/download = Fanatics elements in it): full episodes **4×** (top-of-show
  shoutout, ad read, branded segment — Risers & Fallers Tue / SNF Parlay Fri — and branded imagery); podcast
  downloads **3×**; clips & Shorts **2×**; social **1×**.
- Pending (shown "Pending", counted 0): FanCash, in-app weeks, Keyshawn X — a producer is verifying.
- Instagram collabs between @JordanSchultz and SR share one view count → counted under Jordan.
- Report wording: never say "API" in reports sent to Fanatics.
- September 2026 report (v1.1) is built but not final: after RDM's review, rerun without `--no-write` — that saves
  September and drops the old Aug 18 – Sep 30 history row.

## Platform notes

- TikTok: public pages round view counts — always use `common/tiktok_auth.py views`. A video can only be read
  with its own account's token. The app's redirect page, terms and privacy pages live on RDM's site
  (raindelaymedia.github.io/roadtrippin/master/…) — keep those URLs; they're registered with TikTok.
- Instagram account insights: 30-day max per call (chunk), data lags ~48h.
- YouTube Analytics `month` dimension needs 1st-of-month dates; `day` must end yesterday. `.execute(num_retries=3)`.
- Sprout API: Advanced plan or above; 60 req/min, 250K/month; daily profile metrics + per-post metrics filterable
  by tag (Fanatics tag already applied by Schultz's team).

## Dashboard conventions (carried over)

- Engaged vs all YouTube views are entered by hand (API doesn't expose engaged views): YOUTUBE rows
  `VIEWS_<T>` / `ENGAGED_VIEWS_<T>` for T in VIDS / SHORTS / LIVES.
- The socials editor saves **only the cells edited**, applied to the current file on GitHub — never rewrite the
  whole file from the page (an outdated tab once deleted 54 rows that way).
- Generated files (dashboard HTML, tracker JSON) are rebuilt by the workflow — don't hand-edit them.
- SR brand: deep blue `#11116b`, yellow `#E8C840`, Oswald (dashboard) / Barlow Condensed (report).
  Sticky table columns need solid backgrounds.

## Open decisions

1. Which repo owns SR data collection + token refresh (recommendation: this one).
2. Access control for the shared site (GitHub Pages is public-with-link).
3. Schultz Media's metric list.
