"""Data access layer for the custom tools, backed by two SQLite databases.

  - db/crm.db     -> get_profile()             (Tool 1, CRM/CDP-style)
  - db/social.db  -> get_trends_and_partners() (Tool 2, listening + discovery)

Databases are created and seeded automatically on first import (see
seed_db.py). Unknown brands/markets fall back gracefully so the workflow
always gets a usable response, with an explicit flag saying a fallback
happened.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

import seed_db

seed_db.ensure_dbs()

FALLBACK_MARKET = "us"

_MARKET_ALIASES = {
    "us": "us", "usa": "us", "united states": "us", "north america": "us",
    "uk": "uk", "gb": "uk", "united kingdom": "uk", "great britain": "uk",
}


def _connect(path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Tool 1: brand audience profile (crm.db)
# ---------------------------------------------------------------------------

def get_profile(brand: str, date_range: str | None = None) -> dict[str, Any]:
    """Return a CDP-style aggregated audience profile for a brand."""
    con = _connect(seed_db.CRM_DB)
    try:
        key = (brand or "").strip().lower()
        row = con.execute(
            "SELECT * FROM brands WHERE lower(name) = ? OR brand_id = ?",
            (key, key.replace(" ", "_")),
        ).fetchone()

        # Fallback: unknown brand -> first seeded brand, flagged explicitly.
        is_fallback = row is None
        if is_fallback:
            row = con.execute("SELECT * FROM brands ORDER BY brand_id LIMIT 1").fetchone()

        affinity_labels = dict(
            con.execute("SELECT affinity_id, label FROM affinities").fetchall()
        )

        segments = []
        seg_rows = con.execute(
            "SELECT * FROM audience_segments WHERE brand_id = ? ORDER BY size DESC",
            (row["brand_id"],),
        ).fetchall()
        total_size = sum(s["size"] for s in seg_rows)
        for s in seg_rows:
            segments.append({
                "segment_id": s["segment_id"],
                "segment_name": s["segment_name"],
                "size": s["size"],
                "size_pct": round(s["size"] / total_size, 3) if total_size else 0,
                "demographics": {
                    "age_brackets": json.loads(s["age_brackets"]),
                    "gender_split": json.loads(s["gender_split"]),
                },
                "top_locations": json.loads(s["top_locations"]),
                "lifecycle_mix": json.loads(s["lifecycle_mix"]),
                "commerce": {
                    "avg_order_value": s["avg_order_value"],
                    "purchase_frequency_per_year": s["purchase_freq_per_yr"],
                    "estimated_clv": s["estimated_clv"],
                },
                "motivations": json.loads(s["motivations"]),
                "affinities": [
                    affinity_labels.get(a, a) for a in json.loads(s["affinity_ids"])
                ],
                "preferred_channels": json.loads(s["preferred_channels"]),
                "preferred_content_formats": json.loads(s["content_formats"]),
                "device_split": json.loads(s["device_split"]),
            })

        return {
            "brand": brand,
            "matched_brand": row["name"],
            "brand_fallback_used": is_fallback,
            "industry": row["industry"],
            "brand_values": json.loads(row["brand_values"]),
            "home_market": row["home_market"],
            "date_range": date_range,
            "generated_at": _now(),
            "data_sources": ["crm_contacts", "web_analytics", "email_engagement", "commerce"],
            "currency": "USD",
            "audience_size": total_size,
            "segments": segments,
        }
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Tool 2: social trends + partner candidates (social.db)
# ---------------------------------------------------------------------------

def get_trends_and_partners(
    market: str,
    brand: str | None = None,
    topics: list[str] | None = None,
) -> dict[str, Any]:
    """Return listening trends and a FLAT list of partner candidates.

    Bucketing into obvious/niche/watchlist is deliberately NOT done here —
    that judgment belongs to the Trend & Partnership Analyst agent.
    """
    con = _connect(seed_db.SOCIAL_DB)
    try:
        key = _MARKET_ALIASES.get((market or "").strip().lower(), (market or "").strip().lower())
        known = {r["market"] for r in con.execute("SELECT DISTINCT market FROM trends")}
        is_fallback = key not in known
        if is_fallback:
            key = FALLBACK_MARKET

        # --- trends ---
        trend_rows = con.execute(
            "SELECT * FROM trends WHERE market = ? ORDER BY volume DESC", (key,)
        ).fetchall()
        trends = [{
            "topic": t["topic"],
            "type": t["topic_type"],
            "volume": t["volume"],
            "percentage_volume": t["percentage_volume"],
            "sentiment_score": t["sentiment_score"],
            "sentiment": json.loads(t["sentiment_split"]),
            "trending": t["trending"],
            "platforms": json.loads(t["platforms"]),
            "sample_mention": t["sample_mention"],
            "related_affinities": json.loads(t["affinity_ids"]),
        } for t in trend_rows]

        # Listening summary (volume-weighted across trends)
        total_volume = sum(t["volume"] for t in trends) or 1
        sentiment = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        platform_volume: dict[str, int] = {}
        for t in trends:
            for k in sentiment:
                sentiment[k] += t["sentiment"][k] * t["volume"]
            for p in t["platforms"]:
                platform_volume[p] = platform_volume.get(p, 0) + t["volume"]
        sentiment = {k: round(v / total_volume, 3) for k, v in sentiment.items()}
        platform_total = sum(platform_volume.values()) or 1
        top_platforms = [
            {"platform": p, "mention_share": round(v / platform_total, 3)}
            for p, v in sorted(platform_volume.items(), key=lambda kv: -kv[1])
        ]

        # --- partner candidates (flat; agent does the bucketing) ---
        cand_rows = con.execute("SELECT * FROM partner_candidates").fetchall()
        collab_rows = con.execute("SELECT * FROM past_collaborations").fetchall()
        collabs_by_candidate: dict[str, list[dict[str, Any]]] = {}
        for c in collab_rows:
            collabs_by_candidate.setdefault(c["candidate_id"], []).append({
                "brand_name": c["brand_name"],
                "campaign_type": c["campaign_type"],
                "year": c["year"],
                "performance": json.loads(c["performance"]),
            })

        wanted_topics = {t.strip().lower() for t in (topics or []) if t.strip()}
        candidates = []
        for c in cand_rows:
            if key not in json.loads(c["markets"]):
                continue
            content_topics = json.loads(c["content_topics"])
            candidates.append({
                "candidate_id": c["candidate_id"],
                "name": c["name"],
                "handle": c["handle"],
                "type": c["type"],
                "platform": c["platform"],
                "follower_count": c["follower_count"],
                "engagement_rate": c["engagement_rate"],
                "avg_views": c["avg_views"],
                "audience_credibility_score": c["credibility_score"],
                "audience": {
                    "age_brackets": json.loads(c["audience_age_brackets"]),
                    "gender_split": json.loads(c["audience_gender_split"]),
                    "top_geos": json.loads(c["audience_top_geos"]),
                },
                "content_topics": content_topics,
                "topic_match_count": len(wanted_topics & {t.lower() for t in content_topics}),
                "past_brand_collaborations": collabs_by_candidate.get(c["candidate_id"], []),
                "estimated_cost_per_post": {
                    "currency": c["cost_currency"],
                    "min": c["est_cost_min"],
                    "max": c["est_cost_max"],
                },
                "availability_status": "unknown",
            })
        # Most topically relevant first, then by reach; nothing is dropped.
        candidates.sort(key=lambda c: (-c["topic_match_count"], -c["follower_count"]))

        return {
            "market": market,
            "matched_market": key,
            "market_fallback_used": is_fallback,
            "brand": brand,
            "query_topics": sorted(wanted_topics) or None,
            "generated_at": _now(),
            "listening": {
                "total_mentions": total_volume,
                "sentiment": sentiment,
                "top_platforms": top_platforms,
                "trends": trends,
            },
            "partner_candidates": candidates,
        }
    finally:
        con.close()
