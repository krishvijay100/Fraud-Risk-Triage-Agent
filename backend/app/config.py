from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_FILE = ROOT_DIR / "data" / "mock_cases.json"
OUT_DIR = ROOT_DIR / "out"

SCORING_VERSION = "1.0.0"
RULES_VERSION = "1.0.0"
NARRATIVE_MODEL = "claude-haiku-4-5-20251001"

# Scoring thresholds
AUTO_CLEAR_SCORE_THRESHOLD = 20
AUTO_CLEAR_COMPLETENESS_THRESHOLD = 0.85

# Tier score boundaries
TIER_URGENT_MIN = 75
TIER_HIGH_MIN = 55
TIER_MEDIUM_MIN = 35
TIER_LOW_MIN = 15

# SLA in minutes by tier
SLA_MAP = {
    "AUTO_CLEAR": 0,
    "LOW": 1440,
    "MEDIUM": 240,
    "HIGH": 60,
    "URGENT": 15,
}

# Recommendation by tier
RECOMMENDATION_MAP = {
    "AUTO_CLEAR": "CLEAR",
    "LOW": "MONITOR",
    "MEDIUM": "STEP_UP",
    "HIGH": "ESCALATE_L2",
    "URGENT": "HOLD_RECOMMENDED",
}

# Geo risk sets
HIGH_RISK_COUNTRIES = {"NG", "RU", "KP", "IR", "SY"}
MEDIUM_RISK_COUNTRIES = {"PH", "VE", "BY", "UA", "CN", "PK", "MM", "VN"}

# Amount threshold for HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE rule
LARGE_AMOUNT_THRESHOLD = 1000

# Ring cluster threshold: device shared by N+ different customers triggers no-go
RING_CLUSTER_THRESHOLD = 2
