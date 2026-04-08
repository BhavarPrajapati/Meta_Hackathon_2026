from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import CompanyState

VALUATION_TARGET = 20_000_000.0


def compute_reward(state: "CompanyState", prev_mrr: float, prev_cash: float) -> float:
    if state.is_bankrupt:
        return 0.0

    survival = 0.10
    valuation_score = min(0.45, state.valuation / VALUATION_TARGET * 0.45)

    mrr_growth = state.mrr - prev_mrr
    growth_score = min(0.20, max(0.0, mrr_growth / 40_000 * 0.20))

    coverage = state.mrr / state.burn_rate if state.burn_rate > 0 else 1.0
    efficiency_score = min(0.15, coverage * 0.12)

    runway = state.runway_months
    if runway < 2:
        runway_score = -0.10
    elif runway >= 6:
        runway_score = 0.10
    elif runway >= 3:
        runway_score = 0.05
    else:
        runway_score = 0.0

    reckless = -0.10 if (state.burn_rate > state.mrr * 3 and state.product_progress >= 80) else 0.0
    stagnation = -0.05 if (state.mrr_trend == "flat" and state.step_count > 5) else 0.0

    total = survival + valuation_score + growth_score + efficiency_score + runway_score + reckless + stagnation
    return round(min(1.0, max(0.0, total)), 6)
