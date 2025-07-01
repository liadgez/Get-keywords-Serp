# MVP Specification: Keyword-Driven Competitor Discovery Tool

## 1. Objective

Deliver a lightweight, repeatable system that converts a small list of high-intent keywords into a ranked list of competitor domains—without requiring paid SEO suites. The MVP should be usable by a marketer in one sitting, take <10 minutes per keyword batch, and output results to a shareable format (Google Sheet or CSV).

## 2. Core User Stories

| # | As a (marketer) I want to… | So that… | Acceptance Criteria |
|---|---------------------------|----------|-------------------|
| 1 | Enter or upload 5-15 high-intent keywords | I can define the competitive lens | Keywords accepted via simple text box or CSV upload |
| 2 | Fetch the top 20 organic Google (or Bing) results for each keyword | I see who actually ranks in SERPs | Script/API returns ≥95% of requests within 30s; handles CAPTCHA/429 gracefully |
| 3 | Auto-extract root domains from each result | Brand aggregation is consistent | Domains normalized (e.g., https://store.nike.com → nike.com) |
| 4 | Count how often each domain appears across keywords | I know which brands are most visible | Frequency table produced; ties resolved by sum of SERP positions |
| 5 | View a ranked competitor list and export it | I can share or analyze further | Single-click export to CSV and auto-sync to a Google Sheet |

*Out of scope for MVP*: historical trend tracking, clustering by brand type, UI styling beyond functional needs, multi-language scraping.

## 3. System Architecture & Data Flow

```
┌──────────┐     ┌────────────┐   (requests, BeautifulSoup / SERP API)
│ Keyword  │──►  │ Scraper Fn │────────────────────┐
│  List    │     └────────────┘                    │
└──────────┘                                        ▼
          ┌───────────────────┐    ┌───────────────┐
          │ Raw SERP Results  │──► │ Domain Parser │ (tldextract)
          └───────────────────┘    └───────────────┘
                       ▼
           ┌────────────────────┐
           │ Frequency Counter  │ (collections.Counter, rank weighting)
           └────────────────────┘
                       ▼
         ┌─────────────────────────┐
         │ Results Store (SQLite)  │
         └─────────────────────────┘
                       ▼
               ┌─────────────┐
               │ Export Layer│ (CSV/GSheet API)
               └─────────────┘
```

*Deploy locally* (Python v3.11 virtual-env) or on a free-tier VPS/Render.com job if hands-off scheduling is desired.

## 4. Tech Stack Choices

| Layer | MVP Choice | Rationale |
|-------|------------|-----------|
| Scraping | **SerpApi free tier** (100 searches/mo) *or* `requests + BeautifulSoup` in incognito-like mode | Handles CAPTCHA & geo; fallback to DIY if quota hit |
| Parsing | `tldextract` | Accurate root-domain extraction |
| Storage | **SQLite** | Zero-config, allows simple joins if you log runs |
| Data manipulation | `pandas` | Easiest to pivot and weight scores |
| Export | **Google Sheets API** *plus* CSV | Instant sharing; CSV for automation |
| CLI / launcher | `typer` or `argparse` | Single file `main.py` keeps onboarding trivial |

## 5. Functional Requirements

1. **Keyword Input**
   * Accept stdin list, `.txt`, or `.csv` with one keyword per line.

2. **SERP Fetch**
   * `depth` parameter (default = 20 results).
   * `engine` flag (`google` | `bing`).

3. **Domain Extraction & Weighting**
   * Weight = `(depth + 1) – rank`. Example: rank 1 → 20 pts if depth = 20.
   * Store both raw count and weighted score.

4. **Output**
   * `results_<timestamp>.csv` with columns: `domain`, `count`, `weighted_score`, plus per-keyword 0/1 flags.
   * Auto-append/overwrite tab called **"SERP Audit <date>"** in a user-specified Google Sheet.

5. **CLI Flags**
   ```
   python main.py --keywords keywords.csv --engine google --depth 20 --sheet_id <id>
   ```

## 6. Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| Performance | <2s per SERP call (API) or <5s (HTML scrape) |
| Reliability | Graceful retry (max 3) on HTTP 429/5xx |
| Logging | Print progress bar; write `run_<timestamp>.log` |
| Legal/Compliance | Respect Google ToS—use official API where possible; provide "Use at your own risk" disclaimer |
| Security | Store API keys in `.env`; never commit to repo |

## 7. Project Plan & Effort Estimate

| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 1 | Repo scaffolding, `.env` pattern, requirements.txt | Dev | GitHub repo |
| 2 | Keyword input & validation module | Dev | `input.py` |
| 3-4 | SERP fetcher (API + fallback HTML) | Dev | `serp.py`; unit tests |
| 5 | Domain parser + weighting logic | Dev | `parser.py` |
| 6 | SQLite schema & basic CRUD | Dev | `db.py` |
| 7 | Export layer (CSV & Sheets) | Dev | `export.py` |
| 8 | CLI wrapper & end-to-end test | Dev | `main.py`, demo run |
| 9 | README with usage GIF; deploy guide | Dev | Docs |
| 10 | Buffer / bug-fix & hand-off session | Dev | v0.1 tag |

Total: **~40 dev-hours** (~1.5 sprints for one engineer).

## 8. KPIs for MVP Success

1. **Time-to-insight**: <10 min from keyword list to ranked table.
2. **Coverage**: ≥90% of keywords return 20 results without manual retry.
3. **Accuracy**: ≥95% correct root-domain extraction (spot-check sample).
4. **User satisfaction**: ≥4/5 rating from initial testers on ease of use.

## 9. Future Enhancements (Post-MVP Backlog)

| Priority | Feature | Notes |
|----------|---------|-------|
| ★★★ | Scheduled re-runs & trend chart | Cron + append mode |
| ★★ | Brand-type classifier (brand vs reseller vs media) | Simple rules or GPT tagging |
| ★★ | Weight by search volume | Integrate Keyword Planner API |
| ★ | Web UI (Streamlit) | For non-technical users |
| ★ | Geo-specific SERPs | `gl` & `hl` params in API |

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Google blocks scraping | High | Prefer SERP API; rotate user-agents / sleep jitter |
| Personalized results skew data | Medium | Use `num=20`, `pws=0`, or remote proxy location |
| Keyword bias | Medium | Periodic keyword list review; track "missing" competitors manually |

## 11. Deliverables Checklist

* [ ] GitHub repository (MIT license)
* [ ] `main.py` CLI tool with docstring help
* [ ] `README.md` incl. setup, .env sample, GIF demo
* [ ] Example `keywords_sample.csv`
* [ ] Google Sheet template with pivot & conditional color-scale
* [ ] One-page quick-start PDF for stakeholders