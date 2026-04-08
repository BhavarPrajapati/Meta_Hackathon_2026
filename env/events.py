from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .state import CompanyState

EVENT_SCHEDULE = {
    ("easy",   4):  "viral_growth",
    ("easy",   8):  "investor_interest",
    ("easy",  14):  "market_boom",
    ("medium", 5):  "competitor_surge",
    ("medium",10):  "market_crash",
    ("medium",15):  "investor_interest",
    ("hard",   3):  "market_crash",
    ("hard",   6):  "competitor_surge",
    ("hard",  10):  "market_crash",
    ("hard",  14):  "market_crash",
    ("hard",  17):  "viral_growth",
}

EVENT_DEFINITIONS = {
    "market_crash": {
        "label": "MARKET CRASH",
        "description": "Economic downturn. MRR -25%, sentiment falls.",
        "mrr_multiplier": 0.75,
        "sentiment_delta": -0.15,
        "competition_delta": 0.0,
    },
    "competitor_surge": {
        "label": "COMPETITOR SURGE",
        "description": "Funded competitor enters. MRR -10%, competition rises.",
        "mrr_multiplier": 0.90,
        "sentiment_delta": -0.05,
        "competition_delta": 0.20,
    },
    "viral_growth": {
        "label": "VIRAL GROWTH",
        "description": "Product goes viral. MRR +20%, sentiment improves.",
        "mrr_multiplier": 1.20,
        "sentiment_delta": 0.10,
        "competition_delta": 0.0,
    },
    "investor_interest": {
        "label": "INVESTOR INTEREST",
        "description": "VCs are watching. Sentiment +10%.",
        "mrr_multiplier": 1.0,
        "sentiment_delta": 0.10,
        "competition_delta": 0.0,
    },
    "market_boom": {
        "label": "MARKET BOOM",
        "description": "Industry tailwind. MRR +15%, sentiment peaks.",
        "mrr_multiplier": 1.15,
        "sentiment_delta": 0.20,
        "competition_delta": 0.0,
    },
}


def apply_events(state: "CompanyState") -> Optional[str]:
    state.active_event = None
    ev_key = EVENT_SCHEDULE.get((state.task_id, state.step_count))

    if not ev_key:
        if state.product_progress >= 100:
            state.product_market_fit = min(1.0, state.product_market_fit + 0.01)
        return None

    ev = EVENT_DEFINITIONS[ev_key]
    state.mrr *= ev["mrr_multiplier"]
    state.market_sentiment = round(max(0.3, min(1.5, state.market_sentiment + ev["sentiment_delta"])), 2)
    state.competition_level = round(max(0.0, min(1.0, state.competition_level + ev["competition_delta"])), 2)
    state.active_event = ev["label"]

    return f"{ev['label']}: {ev['description']}"
