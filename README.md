# Social Partnership Campaign Planner — Opal custom tools

Custom tools backing an agent workflow built in Optimizely Opal for the FDE
take-home. The workflow turns a campaign request ("create a social partnership
campaign brief for Brand X in the US") into an evidence-based campaign brief
with recommended collaboration partners.

## Where everything lives

The agent side — the Instruction, four Specialized Agents (Campaign Intake
Analyst → Brand Performance Analyst → Trend & Partnership Analyst → Campaign
Brief Generator), and the Workflow that orchestrates them — is configured
inside the Opal instance, not in this repo. Exports of those will land in
`opal-exports/` for the submission.

This repo contains the one part that is real code: a small FastAPI service
exposing two custom tools that Opal calls over HTTP.

## The two tools

| Tool | Called by | Input | Output |
| --- | --- | --- | --- |
| `get_brand_audience_profile` | Brand Performance Analyst | `brand` (required), `date_range` | CDP-style aggregated audience profile: segments with demographics, lifecycle mix, AOV/CLV, motivations, preferred channels |
| `get_social_trends_and_partner_data` | Trend & Partnership Analyst | `market` (required); `brand`, `topics`, `audience_description` | Listening summary + trending topics (volume, sentiment, momentum) + flat list of partner candidates (audience, engagement, credibility, past collabs, cost range) |

Tool 1 answers *who already buys from this brand and what moves them*
(inside-out). Tool 2 answers *what the market is talking about and who carries
those conversations* (outside-in). The Trend & Partnership Analyst joins the
two: it scores candidates on audience fit, trend resonance, channel alignment,
value vs cost, and risk — then buckets them into obvious / niche / watchlist
recommendations. The tool deliberately does **not** pre-bucket candidates;
that judgment belongs to the agent, mirroring how real discovery APIs behave.

## Data design

The mock datasets are shaped after real provider APIs so responses look like
what you'd get from commercial data sources:

- **`db/crm.db`** mimics a CRM/CDP audience layer (HubSpot contact properties
  and lifecycle stages; GA4/Meta-style aggregated segment insights). Tables:
  `brands`, `audience_segments`, `affinities`. Aggregates only — no
  individual PII.
- **`db/social.db`** mimics social listening + influencer discovery
  (Brandwatch topics: volume, `percentage_volume`, `sentiment_score` −100..100,
  trending rate; Modash reports: follower count, engagement rate, audience
  credibility, demographics, past collaborations, cost estimates). Tables:
  `trends`, `partner_candidates`, `past_collaborations`.

The two DBs share one affinity vocabulary and identical age-bracket keys, so
brand segments, trends, and creator audiences are directly comparable — that's
the seam the analyst agent reasons across.

Seed data covers 3 fictional brands (Aurora Athletics, Verdant Living, Lumine
Beauty), US + UK markets, 12 trends, and 12 candidates deliberately spanning
strong fits, niche communities, unvalidated emerging creators, a fake-follower
risk, a competitor conflict, and a poor audience fit — so the agent has real
judgment to exercise. Guardrails are baked into the data: candidate
`availability_status` is always `"unknown"` and pricing is an estimate range,
so agents can't claim a partner is available or priced.

## Layout

```
custom-tool/
  main.py         FastAPI app: /discovery + the two tool endpoints
  data.py         data access layer over the SQLite DBs
  seed_db.py      creates + seeds db/crm.db and db/social.db (auto-runs on startup)
  api/index.py    Vercel serverless entrypoint
  vercel.json     routes all paths to the entrypoint
opal-exports/     Opal agent/workflow exports (added at submission)
instructions.txt  the take-home brief
```

## Run locally

```bash
cd custom-tool
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
curl http://localhost:8000/discovery
```

To test against Opal during development, tunnel with `ngrok http 8000` and
register `<ngrok-url>/discovery` in Opal's Tools Registry.

## Deployment

Deployed on Vercel so the tools stay up for unattended review — the repo is
imported with root directory `custom-tool`, and every push redeploys. On
Vercel the DBs seed into `/tmp` on cold start (the deployment filesystem is
read-only); locally they live in `custom-tool/db/`. The registered registry
URL is `https://<project>.vercel.app/discovery`.

Rebuild the databases anytime with `python seed_db.py`.
