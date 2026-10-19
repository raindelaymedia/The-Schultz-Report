# The Schultz Report — shared dashboard (RDM × Schultz Media)

A collaborative analytics dashboard for **The Schultz Report**, built by Rain Delay Media (RDM) and shared with
Schultz Media. It mirrors RDM's internal SR dashboard (repo `raindelaymedia/roadtrippin`, local folder `data`) plus
metrics Schultz Media will specify (TBD). Mostly API-driven: daily refresh → static HTML on GitHub Pages.
Owner on the RDM side: Andrew Priest (andrew@raindelaymedia.com).

## Status (Oct 2026)

**This repo holds no API keys.** RDM's internal repo (`raindelaymedia/roadtrippin`) owns every SR key and token
refresh. Its daily workflow (09:00 UTC) pulls YouTube, Instagram and Sprout, then pushes the results to
`schultz_report/data_sr/from_rdm/` here. That push triggers `.github/workflows/build.yml`, which rebuilds
`schultz_report/schultz_report.html` (also runs 10:30 UTC daily + manual). Pages serves `index.html` → dashboard.
If the repos go private later, the same model holds (RDM pushes; nothing here needs a key).

Deadline: dashboard + SR Fanatics report done EOD Oct 19 2026.

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
  build_sr_dashboard.py          → schultz_report.html (SR brand). Reads from_rdm/ + manual inputs
  rdm_data.py                    from_rdm/ loaders: socials merge, Sprout → Jordan tab + sponsor sections
  build_fanatics_report_sr.py    SR × Fanatics monthly delivery report (+ fanatics_report_template_sr.py)
  sr_growth_snapshot.py, snapshot_sr_historical.py   one-off analysis scripts
  audio_sr.py                    Audio tab — weekly Simplecast downloads from data_sr/audio_sr.csv
  sponsors.py                    Sponsors section — one page per row in data_sr/sponsors.csv
  data_sr/from_rdm/              pushed daily by RDM — never edit by hand
  data_sr/
    socials_sr.csv               long format period,platform,metric,value (period = YYYY-MM)
    tracker_data_sr.json         generated
    fanatics_episodes_sr.csv     every full episode by type (video_id, date, type, title)
    fanatics_posts_sr.csv        every Fanatics-watermarked social post by URL (views refreshed at build)
    fanatics_history_sr.csv      one row per reported period (cumulative)
    reports/fanatics/            report HTML + saved inputs per period
    sponsors.csv                 sponsor,sprout_tag,start,end,impression_goal,notes (Chime, Fanatics, Hims, Lowe's)
    audio_sr.csv                 week_start,week_end,downloads,listeners,notes (Simplecast, entered weekly)
common/
  yt_period_views.py             views DURING a period per video, for everything posted since a cutoff
  tiktok_auth.py                 TikTok connection + exact per-video stats (link / exchange / test / status / views)
  sync_socials.py                Instagram account metrics → socials_sr.csv (SR only here)
  sprout.py                      Sprout Social API client: status (profiles, tags) / daily / posts --tag
  (no config files here — keys live in RDM's repo)
```

## Data flow + keys

- **No keys here — ever.** No `config*.py`, no tokens, no secrets in this repo's Actions. `.gitignore` blocks them.
  The scripts in `common/` and `build_tracker_sr.py` / `build_fanatics_report_sr.py` are kept for reference and
  local runs only; the live copies run in RDM's repo.
- `data_sr/from_rdm/` — **written only by RDM's workflow; never edit by hand** (it's overwritten daily):
  `tracker_data_sr.json` (YouTube), `socials_sr.csv` (API-synced Instagram rows), `sprout/posts.json` +
  `sprout/daily/*.csv` (sponsor-tagged posts, lifetime views), `tiktok/daily/*.csv` (SR TikTok per-video lifetime
  counts), `fanatics_*.csv`, `reports/fanatics/`. SR TikTok rows in socials come from RDM's API sync from Oct 2026
  (VIEWS = lifetime views of that month's videos; Aug/Sep were Studio views-in-month).
- `data_sr/` (outside `from_rdm/`) — **this repo's own manual inputs**, edited on the dashboard: `socials_sr.csv`
  (X, YouTube engaged views, anything Schultz-side), `audio_sr.csv` (Simplecast weekly), `sponsors.csv`.
- At build, `schultz_report/rdm_data.py` merges socials: platforms in `RDM_PLATFORMS` (Instagram, TikTok) come from
  RDM's file; every manual row comes from ours, falling back to RDM's when we don't have the cell. `pick()` prefers a
  `from_rdm/` copy of a file.
- **Manual SR inputs are entered HERE (this dashboard's editor), not on RDM's.** Every morning RDM's workflow copies
  them back into its own socials_sr.csv (`pull_shared_inputs_sr.py`, shared value wins) before building its SR
  dashboard and Fanatics reports. An X edit made on RDM's dashboard is overwritten the next morning if this repo
  has that cell.
- Overview tab = `schultz_report/overview_sr.py` (show accounts, Jordan's show content, sponsor tag counts, top uploads).
  Audio = `data_sr/audio_sr.csv`; a row longer than a week (e.g. the Sept 2026 monthly total) is shown as a period.
- **Single-refresher rule.** Instagram and TikTok tokens are replaced on every refresh; only RDM's workflow refreshes
  them. Never add IG/TikTok tokens here. Sprout and Google refresh tokens don't rotate, but they still stay in RDM's repo.
- RDM pushes with a fine-grained PAT (`SHARED_REPO_PAT` in roadtrippin, Contents R/W on this repo only).

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

## Dashboard structure

Sidebar: Overview · YouTube · Audio · Socials (tabs: Show accounts | Jordan Schultz · show content) · Revenue ·
**Sponsors** (one page per sponsors.csv row) · Tracker. Jordan's personal accounts come only through Sprout,
filtered to show content = posts tagged with a sponsor tag (Chime, Fanatics, Hims, Lowe's) — confirm if the team
marks show posts another way. Sponsor pages total campaigns from Sprout tags + our show-account pulls. Hims / Lowe's /
Chime deal terms pending. Revenue page: decide whether it stays in the shared view.
Simplecast has an analytics API (key from account settings) — worth checking once access is sorted.

## Decided (Oct 18 2026)

- **Accounts:** show = `theschultzreport` (Instagram, TikTok, X @theschultzreport, Facebook @TheSchultzReport).
  **@Schultz_Report on X is Jordan's personal account** — the Sept 2,771,393 X impressions are his. Sprout's API
  doesn't return that X profile yet (it shows in the app).
- **YouTube = YouTube Analytics only.** All SR channel content is Fanatics-integrated, so Sprout's YouTube profile is
  skipped (it would double count). Revisit Sprout for YouTube once campaigns need per-video tagging.
- **Revenue page stays in the shared view** — Schultz Media needs to audit/verify it; it'll carry more detail
  than RT's revenue reporting. Source: this repo's `data_sr/revenue_sr.csv`.

## Open decisions

1. Access control for the shared site (GitHub Pages is public-with-link; both repos are public today).
2. Schultz Media's metric list.
3. Sprout shows Fanatics-tagged posts on Jordan's Threads and SR Facebook — do they count toward Fanatics?
