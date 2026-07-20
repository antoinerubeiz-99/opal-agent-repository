# Social Partnership Campaign Planner — custom tools

A small FastAPI service exposing two custom tools for an Opal agent workflow.
Given a brand and a market, they provide the evidence a partnership-campaign
workflow needs: who the brand's audience actually is, and which social
trends and creator/community candidates fit that audience.

## The two tools

| Tool | Input | Output |
| --- | --- | --- |
| `get_brand_audience_profile` | `brand` (required), `date_range` | CDP-style aggregated audience profile: segments with demographics, lifecycle mix, AOV/CLV, motivations, preferred channels |
| `get_social_trends_and_partner_data` | `market` (required); `brand`, `topics`, `audience_description` | Listening summary + trending topics (volume, sentiment, momentum) + flat list of partner candidates (audience, engagement, credibility, past collaborations, cost range) |

Tool 1 answers *who already buys from this brand and what moves them*
(inside-out, first-party data). Tool 2 answers *what the market is talking
about and who carries those conversations* (outside-in, third-party data). A
calling agent joins the two: scoring candidates on audience fit, trend
resonance, channel alignment, value vs cost, and risk. Tool 2 deliberately
returns a **flat, unranked** candidate list rather than pre-sorted
recommendation tiers, that judgment belongs to the calling agent, mirroring
how real discovery APIs behave.

## Data design

The mock datasets are shaped after real provider APIs so responses look like
what you'd get from commercial data sources:

- **`db/crm.db`** mimics a CRM/CDP audience layer (HubSpot contact properties
  and lifecycle stages; GA4/Meta-style aggregated segment insights). Tables:
  `brands`, `audience_segments`, `affinities`. Aggregates only, no
  individual PII.
- **`db/social.db`** mimics social listening + influencer discovery
  (Brandwatch topics: volume, `percentage_volume`, `sentiment_score` -100..100,
  trending rate; Modash reports: follower count, engagement rate, audience
  credibility, demographics, past collaborations, cost estimates). Tables:
  `trends`, `partner_candidates`, `past_collaborations`.

The two DBs share one affinity vocabulary and identical age-bracket keys, so
brand segments, trends, and creator audiences are directly comparable.

Seed data covers 3 fictional brands (Aurora Athletics, Verdant Living, Lumine
Beauty), US + UK markets, 12 trends, and 12 candidates deliberately spanning
strong fits, niche communities, unvalidated emerging creators, a
fake-follower risk, a competitor conflict, and a poor audience fit. Guardrails
are baked into the data: candidate `availability_status` is always
`"unknown"` and pricing is an estimate range only.

## Layout

```
custom-tool/
  main.py         FastAPI app: /discovery + the two tool endpoints
  data.py         data access layer over the SQLite DBs
  seed_db.py      creates + seeds db/crm.db and db/social.db (auto-runs on startup)
  api/index.py    Vercel serverless entrypoint
  vercel.json     routes all paths to the entrypoint
```

## Run locally

```bash
cd custom-tool
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
curl http://localhost:8000/discovery
```

Rebuild the databases anytime with `python seed_db.py`.

## Deployment

Deployed on Vercel (root directory `custom-tool`) so the tools stay up
independently of any local machine. On Vercel the DBs seed into `/tmp` on
cold start, since the deployment filesystem is read-only; locally they live
in `custom-tool/db/`.

Discovery endpoint: `https://<project>.vercel.app/discovery`
