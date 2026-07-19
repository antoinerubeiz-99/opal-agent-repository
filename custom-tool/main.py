"""Custom Opal Tools for the Social Partnership Campaign Planner workflow.

Exposes two tools that Opal's Specialized Agents call over HTTP:

  1. get_brand_audience_profile         -> "who shops at this brand" snapshot
  2. get_social_trends_and_partner_data -> social trends + candidate collaborators

Opal's Tools Registry needs:
  - GET  /discovery          -> metadata describing every tool (see instructions.txt)
  - POST /tools/<tool-name>  -> one endpoint per tool, called with {"parameters": {...}}

Data comes from two seeded SQLite databases (db/crm.db, db/social.db) via
`data.py`; see seed_db.py and docs/data-design/README.md for the schemas.
"""

from fastapi import FastAPI
from pydantic import BaseModel

import data

app = FastAPI(title="Social Partnership Campaign Planner Tools")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_brand_audience_profile",
        "description": (
            "Returns a snapshot of who shops at a given brand: audience segments "
            "with their share, age range and motivations, top locations, and "
            "preferred channels. Use this to ground a campaign in the brand's "
            "actual audience before choosing partners or messaging."
        ),
        "parameters": [
            {
                "name": "brand",
                "type": "string",
                "description": "The brand or product name to profile, e.g. 'Brand X'.",
                "required": True,
            },
            {
                "name": "date_range",
                "type": "string",
                "description": (
                    "Optional reporting window for the profile, e.g. "
                    "'last_90_days' or '2026-01-01..2026-03-31'."
                ),
                "required": False,
            },
        ],
        "endpoint": "/tools/get-brand-audience-profile",
        "http_method": "POST",
        "auth_requirements": [],
    },
    {
        "name": "get_social_trends_and_partner_data",
        "description": (
            "Returns social-listening data for a market (trending topics with "
            "volume, sentiment and momentum, plus an overall listening summary) "
            "and a flat list of partnership candidates (creators, communities, "
            "athletes) with audience demographics, engagement, credibility "
            "scores, past brand collaborations, and estimated cost ranges. "
            "Candidates are NOT pre-ranked into recommendation buckets - the "
            "calling agent should assess fit and group them itself."
        ),
        "parameters": [
            {
                "name": "market",
                "type": "string",
                "description": "The target market or region, e.g. 'US' or 'UK'.",
                "required": True,
            },
            {
                "name": "brand",
                "type": "string",
                "description": (
                    "Optional brand name for context, echoed back in the "
                    "response for traceability."
                ),
                "required": False,
            },
            {
                "name": "topics",
                "type": "string",
                "description": (
                    "Optional comma-separated content topics or themes (e.g. "
                    "'fitness, sustainability'). Candidates are sorted by how "
                    "many of these topics they match; none are filtered out."
                ),
                "required": False,
            },
            {
                "name": "audience_description",
                "type": "string",
                "description": (
                    "Optional concise description of the target audience, "
                    "echoed back for traceability in the workflow."
                ),
                "required": False,
            },
        ],
        "endpoint": "/tools/get-social-trends-and-partner-data",
        "http_method": "POST",
        "auth_requirements": [],
    },
]


@app.get("/discovery")
def discovery():
    return {"functions": TOOLS}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

class ToolRequest(BaseModel):
    parameters: dict = {}


@app.post("/tools/get-brand-audience-profile")
def get_brand_audience_profile(body: ToolRequest):
    brand = body.parameters.get("brand", "")
    date_range = body.parameters.get("date_range")
    return data.get_profile(brand, date_range)


@app.post("/tools/get-social-trends-and-partner-data")
def get_social_trends_and_partner_data(body: ToolRequest):
    market = body.parameters.get("market", "")
    brand = body.parameters.get("brand")
    topics_raw = body.parameters.get("topics") or ""
    topics = [t for t in topics_raw.split(",") if t.strip()]
    result = data.get_trends_and_partners(market, brand=brand, topics=topics)
    audience_description = body.parameters.get("audience_description")
    if audience_description:
        result["audience_description"] = audience_description
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
