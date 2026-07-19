"""Creates and seeds the two SQLite databases backing the custom tools.

Schemas follow docs/data-design/README.md:
  - db/crm.db     : brands, audience_segments, affinities   (Tool 1)
  - db/social.db  : trends, partner_candidates, past_collaborations (Tool 2)

Run directly (`python seed_db.py`) to rebuild from scratch, or let data.py
call ensure_dbs() on startup. All data is fictional but shaped like real
provider responses (HubSpot/GA4 for CRM, Brandwatch/Modash for social).

The seam that makes the two datasets composable: affinity ids and age-bracket
keys are IDENTICAL across both DBs, so the downstream agent can match brand
segments to trends and partner audiences.
"""

import json
import os
import sqlite3
from pathlib import Path

# On Vercel the deployment filesystem is read-only; only /tmp is writable.
# Locally we keep the DBs next to the code in ./db. DB_DIR env var overrides.
_default_dir = (
    Path("/tmp/opal-tool-db") if os.environ.get("VERCEL") else Path(__file__).parent / "db"
)
DB_DIR = Path(os.environ.get("DB_DIR", _default_dir))
CRM_DB = DB_DIR / "crm.db"
SOCIAL_DB = DB_DIR / "social.db"

# Shared controlled vocabulary (mirrors Modash/GA4 interest dictionaries)
AFFINITIES = {
    "fitness": "Fitness & Training",
    "wellness": "Wellness & Mindfulness",
    "running": "Running",
    "outdoors": "Outdoors & Hiking",
    "sustainability": "Sustainability",
    "home_garden": "Home & Garden",
    "beauty": "Beauty",
    "skincare": "Skincare",
    "fashion": "Fashion",
    "food_drink": "Food & Drink",
    "parenting": "Family & Parenting",
    "deal_hunting": "Deals & Value Shopping",
    "tech": "Tech & Gaming",
}

BRANDS = [
    {
        "brand_id": "aurora_athletics",
        "name": "Aurora Athletics",
        "industry": "activewear",
        "brand_values": ["performance", "inclusivity", "sustainability"],
        "home_market": "us",
    },
    {
        "brand_id": "verdant_living",
        "name": "Verdant Living",
        "industry": "sustainable home goods",
        "brand_values": ["sustainability", "craftsmanship", "transparency"],
        "home_market": "us",
    },
    {
        "brand_id": "lumine_beauty",
        "name": "Lumine Beauty",
        "industry": "clean beauty",
        "brand_values": ["clean ingredients", "transparency", "confidence"],
        "home_market": "uk",
    },
]

# One row per brand x segment. Age-bracket keys are the standard 5 buckets
# everywhere: 18-24, 25-34, 35-44, 45-54, 55+.
SEGMENTS = [
    # --- Aurora Athletics ---
    {
        "brand_id": "aurora_athletics", "segment_id": "performance_athletes",
        "segment_name": "Performance athletes", "size": 38200,
        "age_brackets": {"18-24": 0.22, "25-34": 0.46, "35-44": 0.22, "45-54": 0.08, "55+": 0.02},
        "gender_split": {"female": 0.51, "male": 0.47, "unknown": 0.02},
        "top_locations": [
            {"country": "United States", "country_code": "us", "region": "California", "pct": 0.17},
            {"country": "United States", "country_code": "us", "region": "Colorado", "pct": 0.11},
            {"country": "United States", "country_code": "us", "region": "New York", "pct": 0.09},
        ],
        "lifecycle_mix": {"subscriber": 0.14, "lead": 0.16, "customer": 0.58, "evangelist": 0.12},
        "avg_order_value": 96.0, "purchase_freq_per_yr": 4.2, "estimated_clv": 810.0,
        "motivations": ["performance", "quality", "progress tracking"],
        "affinity_ids": ["fitness", "running", "wellness"],
        "preferred_channels": [
            {"channel": "instagram", "engagement_rate": 0.049},
            {"channel": "youtube", "engagement_rate": 0.036},
            {"channel": "email", "engagement_rate": 0.31},
        ],
        "content_formats": ["training breakdowns", "athlete stories", "product deep-dives"],
        "device_split": {"mobile": 0.74, "desktop": 0.21, "tablet": 0.05},
    },
    {
        "brand_id": "aurora_athletics", "segment_id": "wellness_lifestylers",
        "segment_name": "Wellness lifestylers", "size": 45900,
        "age_brackets": {"18-24": 0.18, "25-34": 0.39, "35-44": 0.28, "45-54": 0.11, "55+": 0.04},
        "gender_split": {"female": 0.71, "male": 0.27, "unknown": 0.02},
        "top_locations": [
            {"country": "United States", "country_code": "us", "region": "Texas", "pct": 0.12},
            {"country": "United States", "country_code": "us", "region": "Florida", "pct": 0.10},
            {"country": "United Kingdom", "country_code": "gb", "region": "London", "pct": 0.07},
        ],
        "lifecycle_mix": {"subscriber": 0.33, "lead": 0.24, "customer": 0.40, "evangelist": 0.03},
        "avg_order_value": 64.0, "purchase_freq_per_yr": 2.6, "estimated_clv": 340.0,
        "motivations": ["wellbeing", "community", "style"],
        "affinity_ids": ["wellness", "fitness", "sustainability"],
        "preferred_channels": [
            {"channel": "tiktok", "engagement_rate": 0.061},
            {"channel": "instagram", "engagement_rate": 0.043},
            {"channel": "email", "engagement_rate": 0.22},
        ],
        "content_formats": ["short-form video", "day-in-the-life", "challenges"],
        "device_split": {"mobile": 0.82, "desktop": 0.14, "tablet": 0.04},
    },
    {
        "brand_id": "aurora_athletics", "segment_id": "value_fitness_starters",
        "segment_name": "Value fitness starters", "size": 27400,
        "age_brackets": {"18-24": 0.35, "25-34": 0.37, "35-44": 0.17, "45-54": 0.08, "55+": 0.03},
        "gender_split": {"female": 0.55, "male": 0.42, "unknown": 0.03},
        "top_locations": [
            {"country": "United States", "country_code": "us", "region": "Ohio", "pct": 0.09},
            {"country": "United States", "country_code": "us", "region": "Georgia", "pct": 0.08},
        ],
        "lifecycle_mix": {"subscriber": 0.48, "lead": 0.31, "customer": 0.20, "evangelist": 0.01},
        "avg_order_value": 38.0, "purchase_freq_per_yr": 1.4, "estimated_clv": 95.0,
        "motivations": ["price", "beginner-friendliness", "social proof"],
        "affinity_ids": ["fitness", "deal_hunting"],
        "preferred_channels": [
            {"channel": "tiktok", "engagement_rate": 0.055},
            {"channel": "search", "engagement_rate": 0.041},
        ],
        "content_formats": ["beginner guides", "before-and-after", "deals"],
        "device_split": {"mobile": 0.88, "desktop": 0.10, "tablet": 0.02},
    },
    # --- Verdant Living ---
    {
        "brand_id": "verdant_living", "segment_id": "eco_conscious_nesters",
        "segment_name": "Eco-conscious nesters", "size": 31800,
        "age_brackets": {"18-24": 0.06, "25-34": 0.34, "35-44": 0.36, "45-54": 0.17, "55+": 0.07},
        "gender_split": {"female": 0.66, "male": 0.32, "unknown": 0.02},
        "top_locations": [
            {"country": "United States", "country_code": "us", "region": "Washington", "pct": 0.14},
            {"country": "United States", "country_code": "us", "region": "Oregon", "pct": 0.11},
            {"country": "United States", "country_code": "us", "region": "Vermont", "pct": 0.06},
        ],
        "lifecycle_mix": {"subscriber": 0.20, "lead": 0.18, "customer": 0.52, "evangelist": 0.10},
        "avg_order_value": 142.0, "purchase_freq_per_yr": 2.9, "estimated_clv": 980.0,
        "motivations": ["sustainability", "durability", "provenance"],
        "affinity_ids": ["sustainability", "home_garden", "parenting"],
        "preferred_channels": [
            {"channel": "instagram", "engagement_rate": 0.038},
            {"channel": "pinterest", "engagement_rate": 0.052},
            {"channel": "email", "engagement_rate": 0.34},
        ],
        "content_formats": ["home tours", "material stories", "how-to"],
        "device_split": {"mobile": 0.63, "desktop": 0.28, "tablet": 0.09},
    },
    {
        "brand_id": "verdant_living", "segment_id": "design_forward_professionals",
        "segment_name": "Design-forward professionals", "size": 22600,
        "age_brackets": {"18-24": 0.09, "25-34": 0.48, "35-44": 0.29, "45-54": 0.10, "55+": 0.04},
        "gender_split": {"female": 0.57, "male": 0.41, "unknown": 0.02},
        "top_locations": [
            {"country": "United States", "country_code": "us", "region": "New York", "pct": 0.19},
            {"country": "United States", "country_code": "us", "region": "Illinois", "pct": 0.09},
        ],
        "lifecycle_mix": {"subscriber": 0.36, "lead": 0.27, "customer": 0.35, "evangelist": 0.02},
        "avg_order_value": 189.0, "purchase_freq_per_yr": 1.8, "estimated_clv": 720.0,
        "motivations": ["aesthetics", "status", "quality"],
        "affinity_ids": ["home_garden", "fashion"],
        "preferred_channels": [
            {"channel": "instagram", "engagement_rate": 0.044},
            {"channel": "pinterest", "engagement_rate": 0.047},
        ],
        "content_formats": ["styled interiors", "designer collabs", "trend edits"],
        "device_split": {"mobile": 0.69, "desktop": 0.26, "tablet": 0.05},
    },
    # --- Lumine Beauty ---
    {
        "brand_id": "lumine_beauty", "segment_id": "clean_beauty_devotees",
        "segment_name": "Clean beauty devotees", "size": 29100,
        "age_brackets": {"18-24": 0.24, "25-34": 0.41, "35-44": 0.23, "45-54": 0.09, "55+": 0.03},
        "gender_split": {"female": 0.83, "male": 0.14, "unknown": 0.03},
        "top_locations": [
            {"country": "United Kingdom", "country_code": "gb", "region": "London", "pct": 0.22},
            {"country": "United Kingdom", "country_code": "gb", "region": "Manchester", "pct": 0.09},
        ],
        "lifecycle_mix": {"subscriber": 0.18, "lead": 0.17, "customer": 0.55, "evangelist": 0.10},
        "avg_order_value": 54.0, "purchase_freq_per_yr": 4.8, "estimated_clv": 620.0,
        "motivations": ["ingredient transparency", "ethics", "efficacy"],
        "affinity_ids": ["beauty", "skincare", "sustainability"],
        "preferred_channels": [
            {"channel": "instagram", "engagement_rate": 0.051},
            {"channel": "tiktok", "engagement_rate": 0.058},
            {"channel": "email", "engagement_rate": 0.29},
        ],
        "content_formats": ["ingredient explainers", "routines", "reviews"],
        "device_split": {"mobile": 0.85, "desktop": 0.12, "tablet": 0.03},
    },
    {
        "brand_id": "lumine_beauty", "segment_id": "sensitive_skin_seekers",
        "segment_name": "Sensitive-skin seekers", "size": 18700,
        "age_brackets": {"18-24": 0.15, "25-34": 0.33, "35-44": 0.30, "45-54": 0.16, "55+": 0.06},
        "gender_split": {"female": 0.76, "male": 0.21, "unknown": 0.03},
        "top_locations": [
            {"country": "United Kingdom", "country_code": "gb", "region": "Birmingham", "pct": 0.08},
            {"country": "Ireland", "country_code": "ie", "region": "Dublin", "pct": 0.06},
        ],
        "lifecycle_mix": {"subscriber": 0.29, "lead": 0.25, "customer": 0.42, "evangelist": 0.04},
        "avg_order_value": 47.0, "purchase_freq_per_yr": 3.6, "estimated_clv": 410.0,
        "motivations": ["gentle formulations", "dermatologist approval", "trust"],
        "affinity_ids": ["skincare", "wellness"],
        "preferred_channels": [
            {"channel": "search", "engagement_rate": 0.062},
            {"channel": "email", "engagement_rate": 0.27},
        ],
        "content_formats": ["expert Q&A", "patch-test diaries", "reviews"],
        "device_split": {"mobile": 0.77, "desktop": 0.19, "tablet": 0.04},
    },
]

# Brandwatch-Topics-style trend rows, one per market x topic.
TRENDS = [
    # --- US ---
    {"trend_id": "us_75_soft", "market": "us", "topic": "75 soft challenge", "topic_type": "phrase",
     "volume": 18400, "percentage_volume": 22.1, "sentiment_score": 34,
     "sentiment_split": {"positive": 0.52, "neutral": 0.41, "negative": 0.07}, "trending": 2.1,
     "platforms": ["TikTok", "Instagram Reels"],
     "sample_mention": "day 40 of 75 soft — realistic habits over punishment, and my runs finally feel good",
     "affinity_ids": ["fitness", "wellness"]},
    {"trend_id": "us_runtok", "market": "us", "topic": "#RunTok", "topic_type": "hashtag",
     "volume": 12900, "percentage_volume": 15.5, "sentiment_score": 41,
     "sentiment_split": {"positive": 0.58, "neutral": 0.37, "negative": 0.05}, "trending": 1.7,
     "platforms": ["TikTok"],
     "sample_mention": "run clubs are the new dating apps and honestly the vibes are immaculate",
     "affinity_ids": ["running", "fitness"]},
    {"trend_id": "us_sustainable_swaps", "market": "us", "topic": "sustainable swaps", "topic_type": "phrase",
     "volume": 9800, "percentage_volume": 11.8, "sentiment_score": 28,
     "sentiment_split": {"positive": 0.47, "neutral": 0.46, "negative": 0.07}, "trending": 1.2,
     "platforms": ["Instagram", "TikTok"],
     "sample_mention": "5 swaps that actually lasted: wool dryer balls, refill cleaner, glass storage...",
     "affinity_ids": ["sustainability", "home_garden"]},
    {"trend_id": "us_home_gym_corners", "market": "us", "topic": "home gym corners", "topic_type": "phrase",
     "volume": 5400, "percentage_volume": 6.5, "sentiment_score": 31,
     "sentiment_split": {"positive": 0.49, "neutral": 0.45, "negative": 0.06}, "trending": 0.9,
     "platforms": ["Instagram", "Pinterest"],
     "sample_mention": "turned the reading nook into a lifting corner and it sparks more joy tbh",
     "affinity_ids": ["fitness", "home_garden"]},
    {"trend_id": "us_quiet_luxury_basics", "market": "us", "topic": "quiet luxury basics", "topic_type": "phrase",
     "volume": 7700, "percentage_volume": 9.2, "sentiment_score": 18,
     "sentiment_split": {"positive": 0.38, "neutral": 0.54, "negative": 0.08}, "trending": 0.4,
     "platforms": ["Instagram"],
     "sample_mention": "capsule wardrobe, neutral palette, zero logos — investment pieces only",
     "affinity_ids": ["fashion"]},
    {"trend_id": "us_protein_coffee", "market": "us", "topic": "protein coffee", "topic_type": "phrase",
     "volume": 6100, "percentage_volume": 7.3, "sentiment_score": 5,
     "sentiment_split": {"positive": 0.31, "neutral": 0.47, "negative": 0.22}, "trending": -0.8,
     "platforms": ["TikTok"],
     "sample_mention": "proffee was fun for a month but I'm going back to regular espresso",
     "affinity_ids": ["fitness", "food_drink"]},
    # --- UK ---
    {"trend_id": "uk_parkrun", "market": "uk", "topic": "parkrun culture", "topic_type": "phrase",
     "volume": 8900, "percentage_volume": 16.8, "sentiment_score": 47,
     "sentiment_split": {"positive": 0.63, "neutral": 0.33, "negative": 0.04}, "trending": 1.4,
     "platforms": ["Instagram", "X"],
     "sample_mention": "300th parkrun this saturday — the community is the whole point",
     "affinity_ids": ["running", "fitness", "outdoors"]},
    {"trend_id": "uk_cleanbeauty", "market": "uk", "topic": "#CleanBeautyUK", "topic_type": "hashtag",
     "volume": 7600, "percentage_volume": 14.3, "sentiment_score": 37,
     "sentiment_split": {"positive": 0.54, "neutral": 0.39, "negative": 0.07}, "trending": 1.6,
     "platforms": ["Instagram", "TikTok"],
     "sample_mention": "ingredient lists you can actually read — my whole shelf is fragrance-free now",
     "affinity_ids": ["beauty", "skincare"]},
    {"trend_id": "uk_refill_revolution", "market": "uk", "topic": "refill revolution", "topic_type": "phrase",
     "volume": 5200, "percentage_volume": 9.8, "sentiment_score": 44,
     "sentiment_split": {"positive": 0.59, "neutral": 0.37, "negative": 0.04}, "trending": 1.1,
     "platforms": ["Instagram"],
     "sample_mention": "the refill shop opened on our high street and the queue was out the door",
     "affinity_ids": ["sustainability"]},
    {"trend_id": "uk_skin_minimalism", "market": "uk", "topic": "skin minimalism", "topic_type": "phrase",
     "volume": 6800, "percentage_volume": 12.8, "sentiment_score": 26,
     "sentiment_split": {"positive": 0.44, "neutral": 0.49, "negative": 0.07}, "trending": 0.7,
     "platforms": ["TikTok", "Instagram"],
     "sample_mention": "3-step routine, no actives cocktail — my skin barrier says thank you",
     "affinity_ids": ["skincare", "beauty"]},
    {"trend_id": "uk_beige_backlash", "market": "uk", "topic": "sad beige home backlash", "topic_type": "phrase",
     "volume": 4100, "percentage_volume": 7.7, "sentiment_score": -12,
     "sentiment_split": {"positive": 0.22, "neutral": 0.41, "negative": 0.37}, "trending": 1.9,
     "platforms": ["TikTok", "X"],
     "sample_mention": "bring back colour — my house is not a greige showroom",
     "affinity_ids": ["home_garden"]},
    {"trend_id": "uk_airfryer_teatime", "market": "uk", "topic": "air fryer teatime", "topic_type": "phrase",
     "volume": 5900, "percentage_volume": 11.1, "sentiment_score": 22,
     "sentiment_split": {"positive": 0.43, "neutral": 0.49, "negative": 0.08}, "trending": -0.5,
     "platforms": ["TikTok", "Facebook"],
     "sample_mention": "another week of air fryer dinners, though the novelty is wearing off",
     "affinity_ids": ["food_drink"]},
]

# Modash-report-style candidates. Deliberately spans strong fits, niche fits,
# emerging/unvalidated profiles, credibility risks, competitor conflicts, and
# one poor audience fit — so the analyst agent has real judgment to exercise.
CANDIDATES = [
    {"candidate_id": "creator_maya_torres", "name": "Maya Torres", "handle": "@mayamovesdaily",
     "type": "creator", "platform": "Instagram", "markets": ["us"],
     "follower_count": 480000, "engagement_rate": 0.038, "avg_views": 152000,
     "credibility_score": 0.93,
     "audience_age_brackets": {"18-24": 0.21, "25-34": 0.44, "35-44": 0.24, "45-54": 0.08, "55+": 0.03},
     "audience_gender_split": {"female": 0.68, "male": 0.30, "unknown": 0.02},
     "audience_top_geos": [{"country": "United States", "pct": 0.62}, {"country": "Canada", "pct": 0.09}],
     "content_topics": ["fitness", "running", "wellness"],
     "est_cost_min": 4000, "est_cost_max": 7500},
    {"candidate_id": "community_trailhead", "name": "Trailhead Collective", "handle": "@trailheadcollective",
     "type": "community", "platform": "Instagram", "markets": ["us"],
     "follower_count": 45000, "engagement_rate": 0.082, "avg_views": 21000,
     "credibility_score": 0.95,
     "audience_age_brackets": {"18-24": 0.14, "25-34": 0.42, "35-44": 0.29, "45-54": 0.11, "55+": 0.04},
     "audience_gender_split": {"female": 0.49, "male": 0.49, "unknown": 0.02},
     "audience_top_geos": [{"country": "United States", "pct": 0.81}],
     "content_topics": ["running", "outdoors", "fitness"],
     "est_cost_min": 800, "est_cost_max": 2000},
    {"candidate_id": "creator_jax_rivera", "name": "Jax Rivera", "handle": "@jaxruns",
     "type": "creator", "platform": "TikTok", "markets": ["us"],
     "follower_count": 28000, "engagement_rate": 0.11, "avg_views": 95000,
     "credibility_score": 0.71,
     "audience_age_brackets": {"18-24": 0.47, "25-34": 0.35, "35-44": 0.12, "45-54": 0.04, "55+": 0.02},
     "audience_gender_split": {"female": 0.52, "male": 0.45, "unknown": 0.03},
     "audience_top_geos": [{"country": "United States", "pct": 0.58}, {"country": "Mexico", "pct": 0.12}],
     "content_topics": ["running", "fitness"],
     "est_cost_min": 500, "est_cost_max": 1200},
    {"candidate_id": "athlete_dre_coleman", "name": "Dre Coleman", "handle": "@drecoleman400m",
     "type": "athlete", "platform": "Instagram", "markets": ["us"],
     "follower_count": 210000, "engagement_rate": 0.029, "avg_views": 64000,
     "credibility_score": 0.90,
     "audience_age_brackets": {"18-24": 0.31, "25-34": 0.38, "35-44": 0.20, "45-54": 0.08, "55+": 0.03},
     "audience_gender_split": {"female": 0.44, "male": 0.54, "unknown": 0.02},
     "audience_top_geos": [{"country": "United States", "pct": 0.71}],
     "content_topics": ["running", "fitness"],
     "est_cost_min": 6000, "est_cost_max": 12000},
    {"candidate_id": "creator_elena_marsh", "name": "Elena Marsh", "handle": "@marshmadehome",
     "type": "creator", "platform": "Instagram", "markets": ["us"],
     "follower_count": 620000, "engagement_rate": 0.033, "avg_views": 180000,
     "credibility_score": 0.90,
     "audience_age_brackets": {"18-24": 0.08, "25-34": 0.37, "35-44": 0.34, "45-54": 0.15, "55+": 0.06},
     "audience_gender_split": {"female": 0.74, "male": 0.24, "unknown": 0.02},
     "audience_top_geos": [{"country": "United States", "pct": 0.66}, {"country": "United Kingdom", "pct": 0.08}],
     "content_topics": ["home_garden", "sustainability"],
     "est_cost_min": 6000, "est_cost_max": 10000},
    {"candidate_id": "community_slow_home", "name": "The Slow Home", "handle": "@theslowhome",
     "type": "community", "platform": "Instagram", "markets": ["us"],
     "follower_count": 38000, "engagement_rate": 0.09, "avg_views": 16000,
     "credibility_score": 0.96,
     "audience_age_brackets": {"18-24": 0.05, "25-34": 0.33, "35-44": 0.38, "45-54": 0.17, "55+": 0.07},
     "audience_gender_split": {"female": 0.78, "male": 0.20, "unknown": 0.02},
     "audience_top_geos": [{"country": "United States", "pct": 0.72}],
     "content_topics": ["sustainability", "home_garden"],
     "est_cost_min": 600, "est_cost_max": 1500},
    {"candidate_id": "creator_brandon_kole", "name": "Brandon Kole", "handle": "@bkolestyle",
     "type": "creator", "platform": "TikTok", "markets": ["us"],
     "follower_count": 1200000, "engagement_rate": 0.021, "avg_views": 210000,
     "credibility_score": 0.62,
     "audience_age_brackets": {"18-24": 0.41, "25-34": 0.33, "35-44": 0.16, "45-54": 0.07, "55+": 0.03},
     "audience_gender_split": {"female": 0.51, "male": 0.46, "unknown": 0.03},
     "audience_top_geos": [{"country": "United States", "pct": 0.44}, {"country": "Brazil", "pct": 0.18}],
     "content_topics": ["fashion", "deal_hunting"],
     "est_cost_min": 15000, "est_cost_max": 25000},
    {"candidate_id": "creator_pixel_pete", "name": "Pixel Pete", "handle": "@pixelpeteplays",
     "type": "creator", "platform": "YouTube", "markets": ["us"],
     "follower_count": 900000, "engagement_rate": 0.045, "avg_views": 320000,
     "credibility_score": 0.91,
     "audience_age_brackets": {"18-24": 0.52, "25-34": 0.31, "35-44": 0.11, "45-54": 0.04, "55+": 0.02},
     "audience_gender_split": {"female": 0.18, "male": 0.79, "unknown": 0.03},
     "audience_top_geos": [{"country": "United States", "pct": 0.55}],
     "content_topics": ["tech"],
     "est_cost_min": 10000, "est_cost_max": 18000},
    {"candidate_id": "creator_priya_shah", "name": "Priya Shah", "handle": "@priyaglow",
     "type": "creator", "platform": "Instagram", "markets": ["uk"],
     "follower_count": 350000, "engagement_rate": 0.047, "avg_views": 110000,
     "credibility_score": 0.92,
     "audience_age_brackets": {"18-24": 0.26, "25-34": 0.43, "35-44": 0.21, "45-54": 0.07, "55+": 0.03},
     "audience_gender_split": {"female": 0.81, "male": 0.16, "unknown": 0.03},
     "audience_top_geos": [{"country": "United Kingdom", "pct": 0.64}, {"country": "Ireland", "pct": 0.07}],
     "content_topics": ["beauty", "skincare"],
     "est_cost_min": 3000, "est_cost_max": 6000},
    {"candidate_id": "community_glowlab", "name": "GlowLab Collective", "handle": "@glowlabcollective",
     "type": "community", "platform": "Instagram", "markets": ["uk"],
     "follower_count": 52000, "engagement_rate": 0.077, "avg_views": 19000,
     "credibility_score": 0.94,
     "audience_age_brackets": {"18-24": 0.29, "25-34": 0.40, "35-44": 0.20, "45-54": 0.08, "55+": 0.03},
     "audience_gender_split": {"female": 0.85, "male": 0.12, "unknown": 0.03},
     "audience_top_geos": [{"country": "United Kingdom", "pct": 0.77}],
     "content_topics": ["skincare", "beauty", "sustainability"],
     "est_cost_min": 700, "est_cost_max": 1800},
    {"candidate_id": "creator_freya_nilsen", "name": "Freya Nilsen", "handle": "@freyafaces",
     "type": "creator", "platform": "TikTok", "markets": ["uk"],
     "follower_count": 19000, "engagement_rate": 0.13, "avg_views": 71000,
     "credibility_score": 0.78,
     "audience_age_brackets": {"18-24": 0.51, "25-34": 0.32, "35-44": 0.10, "45-54": 0.05, "55+": 0.02},
     "audience_gender_split": {"female": 0.73, "male": 0.23, "unknown": 0.04},
     "audience_top_geos": [{"country": "United Kingdom", "pct": 0.53}, {"country": "Norway", "pct": 0.11}],
     "content_topics": ["beauty", "fashion"],
     "est_cost_min": 300, "est_cost_max": 900},
    {"candidate_id": "creator_marcus_reed", "name": "Marcus Reed", "handle": "@marcusreedkitchen",
     "type": "creator", "platform": "YouTube", "markets": ["uk"],
     "follower_count": 275000, "engagement_rate": 0.041, "avg_views": 98000,
     "credibility_score": 0.89,
     "audience_age_brackets": {"18-24": 0.13, "25-34": 0.36, "35-44": 0.31, "45-54": 0.14, "55+": 0.06},
     "audience_gender_split": {"female": 0.58, "male": 0.40, "unknown": 0.02},
     "audience_top_geos": [{"country": "United Kingdom", "pct": 0.69}],
     "content_topics": ["food_drink", "wellness"],
     "est_cost_min": 2500, "est_cost_max": 5000},
]

PAST_COLLABORATIONS = [
    {"collab_id": "c001", "candidate_id": "creator_maya_torres", "brand_name": "StrideWear",
     "campaign_type": "ambassador", "year": 2025,
     "performance": {"total_likes": 412000, "total_views": 3900000, "posts": 12}},
    {"collab_id": "c002", "candidate_id": "creator_maya_torres", "brand_name": "HydraFuel",
     "campaign_type": "sponsored_post", "year": 2024,
     "performance": {"total_likes": 96000, "total_views": 850000, "posts": 3}},
    {"collab_id": "c003", "candidate_id": "athlete_dre_coleman", "brand_name": "Peak Performance Co",
     "campaign_type": "ambassador", "year": 2025,
     "performance": {"total_likes": 188000, "total_views": 1600000, "posts": 8}},
    {"collab_id": "c004", "candidate_id": "creator_elena_marsh", "brand_name": "NestWell",
     "campaign_type": "sponsored_post", "year": 2025,
     "performance": {"total_likes": 240000, "total_views": 2100000, "posts": 5}},
    {"collab_id": "c005", "candidate_id": "creator_brandon_kole", "brand_name": "FlashThreads",
     "campaign_type": "sponsored_post", "year": 2025,
     "performance": {"total_likes": 310000, "total_views": 5200000, "posts": 9}},
    {"collab_id": "c006", "candidate_id": "creator_priya_shah", "brand_name": "PureGlow",
     "campaign_type": "sponsored_post", "year": 2024,
     "performance": {"total_likes": 154000, "total_views": 1250000, "posts": 4}},
    {"collab_id": "c007", "candidate_id": "community_trailhead", "brand_name": "TrailBrew Coffee",
     "campaign_type": "event_partnership", "year": 2025,
     "performance": {"total_likes": 21000, "total_views": 140000, "posts": 6}},
    {"collab_id": "c008", "candidate_id": "creator_marcus_reed", "brand_name": "OakField Pantry",
     "campaign_type": "sponsored_post", "year": 2025,
     "performance": {"total_likes": 88000, "total_views": 720000, "posts": 3}},
]


def _j(value) -> str:
    return json.dumps(value)


def seed() -> None:
    """(Re)create both databases from scratch."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    CRM_DB.unlink(missing_ok=True)
    SOCIAL_DB.unlink(missing_ok=True)

    # --- crm.db ---
    con = sqlite3.connect(CRM_DB)
    con.executescript(
        """
        CREATE TABLE brands (
          brand_id      TEXT PRIMARY KEY,
          name          TEXT NOT NULL,
          industry      TEXT,
          brand_values  TEXT,
          home_market   TEXT
        );
        CREATE TABLE audience_segments (
          segment_id            TEXT,
          brand_id              TEXT REFERENCES brands(brand_id),
          segment_name          TEXT NOT NULL,
          size                  INTEGER,
          age_brackets          TEXT,
          gender_split          TEXT,
          top_locations         TEXT,
          lifecycle_mix         TEXT,
          avg_order_value       REAL,
          purchase_freq_per_yr  REAL,
          estimated_clv         REAL,
          motivations           TEXT,
          affinity_ids          TEXT,
          preferred_channels    TEXT,
          content_formats       TEXT,
          device_split          TEXT,
          PRIMARY KEY (brand_id, segment_id)
        );
        CREATE TABLE affinities (
          affinity_id  TEXT PRIMARY KEY,
          label        TEXT NOT NULL
        );
        """
    )
    con.executemany(
        "INSERT INTO affinities VALUES (?, ?)", list(AFFINITIES.items())
    )
    con.executemany(
        "INSERT INTO brands VALUES (?, ?, ?, ?, ?)",
        [(b["brand_id"], b["name"], b["industry"], _j(b["brand_values"]), b["home_market"]) for b in BRANDS],
    )
    con.executemany(
        "INSERT INTO audience_segments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                s["segment_id"], s["brand_id"], s["segment_name"], s["size"],
                _j(s["age_brackets"]), _j(s["gender_split"]), _j(s["top_locations"]),
                _j(s["lifecycle_mix"]), s["avg_order_value"], s["purchase_freq_per_yr"],
                s["estimated_clv"], _j(s["motivations"]), _j(s["affinity_ids"]),
                _j(s["preferred_channels"]), _j(s["content_formats"]), _j(s["device_split"]),
            )
            for s in SEGMENTS
        ],
    )
    con.commit()
    con.close()

    # --- social.db ---
    con = sqlite3.connect(SOCIAL_DB)
    con.executescript(
        """
        CREATE TABLE trends (
          trend_id           TEXT PRIMARY KEY,
          market             TEXT NOT NULL,
          topic              TEXT NOT NULL,
          topic_type         TEXT,
          volume             INTEGER,
          percentage_volume  REAL,
          sentiment_score    INTEGER,
          sentiment_split    TEXT,
          trending           REAL,
          platforms          TEXT,
          sample_mention     TEXT,
          affinity_ids       TEXT
        );
        CREATE TABLE partner_candidates (
          candidate_id           TEXT PRIMARY KEY,
          name                   TEXT NOT NULL,
          handle                 TEXT,
          type                   TEXT,
          platform               TEXT,
          markets                TEXT,
          follower_count         INTEGER,
          engagement_rate        REAL,
          avg_views              INTEGER,
          credibility_score      REAL,
          audience_age_brackets  TEXT,
          audience_gender_split  TEXT,
          audience_top_geos      TEXT,
          content_topics         TEXT,
          est_cost_min           INTEGER,
          est_cost_max           INTEGER,
          cost_currency          TEXT DEFAULT 'USD'
        );
        CREATE TABLE past_collaborations (
          collab_id     TEXT PRIMARY KEY,
          candidate_id  TEXT REFERENCES partner_candidates(candidate_id),
          brand_name    TEXT NOT NULL,
          campaign_type TEXT,
          year          INTEGER,
          performance   TEXT
        );
        """
    )
    con.executemany(
        "INSERT INTO trends VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                t["trend_id"], t["market"], t["topic"], t["topic_type"], t["volume"],
                t["percentage_volume"], t["sentiment_score"], _j(t["sentiment_split"]),
                t["trending"], _j(t["platforms"]), t["sample_mention"], _j(t["affinity_ids"]),
            )
            for t in TRENDS
        ],
    )
    con.executemany(
        "INSERT INTO partner_candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                c["candidate_id"], c["name"], c["handle"], c["type"], c["platform"],
                _j(c["markets"]), c["follower_count"], c["engagement_rate"], c["avg_views"],
                c["credibility_score"], _j(c["audience_age_brackets"]),
                _j(c["audience_gender_split"]), _j(c["audience_top_geos"]),
                _j(c["content_topics"]), c["est_cost_min"], c["est_cost_max"], "USD",
            )
            for c in CANDIDATES
        ],
    )
    con.executemany(
        "INSERT INTO past_collaborations VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                p["collab_id"], p["candidate_id"], p["brand_name"], p["campaign_type"],
                p["year"], _j(p["performance"]),
            )
            for p in PAST_COLLABORATIONS
        ],
    )
    con.commit()
    con.close()


def ensure_dbs() -> None:
    """Seed the databases if they don't exist yet (called on app startup)."""
    if not (CRM_DB.exists() and SOCIAL_DB.exists()):
        seed()


if __name__ == "__main__":
    seed()
    print(f"Seeded {CRM_DB} and {SOCIAL_DB}")
