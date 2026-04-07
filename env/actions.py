from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import CompanyState

VALID_ACTIONS = {
    "hire_engineer", "hire_sales", "marketing_push",
    "fundraise", "cut_costs", "improve_product", "do_nothing",
}


@dataclass
class ActionResult:
    action: str
    message: str
    reason: str
    impact: str
    tradeoff: str
    success: bool = True


def process_action(state: "CompanyState", raw_action: str) -> ActionResult:
    action = _parse_action(raw_action)
    dispatch = {
        "hire_engineer":   _hire_engineer,
        "hire_sales":      _hire_sales,
        "marketing_push":  _marketing_push,
        "fundraise":       _fundraise,
        "cut_costs":       _cut_costs,
        "improve_product": _improve_product,
        "do_nothing":      _do_nothing,
    }
    return dispatch[action](state)


def _hire_engineer(state: "CompanyState") -> ActionResult:
    cost = 15_000
    state.burn_rate += cost
    state.team_engineers += 1
    gain = round(12.0 * state.product_market_fit * state.market_sentiment, 1)
    state.product_progress = min(100.0, state.product_progress + gain)
    state.product_market_fit = min(1.0, state.product_market_fit + 0.02)
    return ActionResult(
        action="hire_engineer",
        message=f"Hired engineer #{state.team_engineers}. Product: {state.product_progress:.1f}%",
        reason="Product progress below threshold. Engineering capacity needed.",
        impact=f"+{gain:.1f}% product | +${cost:,}/mo burn | PMF +0.02",
        tradeoff="Higher burn. Justified only while product is incomplete.",
    )


def _hire_sales(state: "CompanyState") -> ActionResult:
    cost = 10_000
    state.burn_rate += cost
    state.team_sales += 1
    new_customers = max(1, int(3 * state.product_market_fit * state.market_sentiment))
    state.customers += new_customers
    mrr_gain = new_customers * 500
    state.mrr += mrr_gain
    return ActionResult(
        action="hire_sales",
        message=f"Hired sales rep #{state.team_sales}. +{new_customers} customers, +${mrr_gain:,} MRR.",
        reason="Product ready. Sales expansion converts demand into revenue.",
        impact=f"+{new_customers} customers | +${mrr_gain:,} MRR | +${cost:,}/mo burn",
        tradeoff="Higher burn. Efficient only when PMF is strong.",
    )


def _marketing_push(state: "CompanyState") -> ActionResult:
    cost = 40_000
    if state.cash < cost:
        return ActionResult(
            action="marketing_push",
            message="Marketing FAILED — insufficient cash.",
            reason="Attempted campaign but cash too low.",
            impact="No impact.",
            tradeoff="N/A — blocked.",
            success=False,
        )
    if state.product_progress < 30:
        state.cash -= cost
        return ActionResult(
            action="marketing_push",
            message=f"Marketing WASTED — product not ready ({state.product_progress:.1f}%). Lost ${cost:,}.",
            reason="Premature marketing before product readiness causes churn.",
            impact=f"-${cost:,} cash | No MRR gain",
            tradeoff="Capital destroyed with no return.",
            success=False,
        )
    state.cash -= cost
    effectiveness = state.product_market_fit * state.market_sentiment
    new_customers = int(20 * effectiveness)
    mrr_gain = new_customers * 600
    state.customers += new_customers
    state.mrr += mrr_gain
    return ActionResult(
        action="marketing_push",
        message=f"Marketing SUCCESS. +{new_customers} customers, +${mrr_gain:,} MRR.",
        reason="Product market-ready. One-time spend to spike customer acquisition.",
        impact=f"+{new_customers} customers | +${mrr_gain:,} MRR | -${cost:,} cash",
        tradeoff="One-time cost. High ROI when PMF > 0.6.",
    )


def _fundraise(state: "CompanyState") -> ActionResult:
    amount = 1_500_000
    state.cash += amount
    state.equity_owned *= 0.80
    return ActionResult(
        action="fundraise",
        message=f"Raised ${amount:,}. Equity: {state.equity_owned:.1f}%. Cash: ${state.cash:,.0f}.",
        reason="Runway critically low. Fundraising extends survival window.",
        impact=f"+${amount:,} cash | Equity → {state.equity_owned:.1f}%",
        tradeoff="Permanent dilution. Best at high valuation.",
    )


def _cut_costs(state: "CompanyState") -> ActionResult:
    reduction = round(state.burn_rate * 0.20, 2)
    state.burn_rate = max(20_000, state.burn_rate - reduction)
    state.product_market_fit = max(0.1, state.product_market_fit - 0.03)
    return ActionResult(
        action="cut_costs",
        message=f"Cut costs. Burn: ${state.burn_rate:,.0f}/mo (saved ${reduction:,.0f}/mo).",
        reason="Burn unsustainable vs revenue. Cutting extends runway.",
        impact=f"-${reduction:,.0f}/mo burn | PMF -0.03",
        tradeoff="Slight product quality hit. Necessary in survival mode.",
    )


def _improve_product(state: "CompanyState") -> ActionResult:
    cost = 20_000
    if state.cash < cost:
        return ActionResult(
            action="improve_product",
            message="Product improvement FAILED — insufficient cash.",
            reason="Cash too low for product investment.",
            impact="No impact.",
            tradeoff="N/A — blocked.",
            success=False,
        )
    state.cash -= cost
    state.product_progress = min(100.0, state.product_progress + 10.0)
    state.product_market_fit = min(1.0, state.product_market_fit + 0.05)
    return ActionResult(
        action="improve_product",
        message=f"Product improved. PMF: {state.product_market_fit:.2f}, Progress: {state.product_progress:.1f}%.",
        reason="Low PMF is limiting growth. Targeted investment unlocks conversion.",
        impact=f"+10% product | PMF +0.05 | -${cost:,} cash",
        tradeoff="One-time cost. High leverage when PMF is the bottleneck.",
    )


def _do_nothing(state: "CompanyState") -> ActionResult:
    return ActionResult(
        action="do_nothing",
        message="Conserving cash. No action taken.",
        reason="No high-priority action identified. Capital preservation optimal.",
        impact="No change.",
        tradeoff="Opportunity cost — growth may stagnate.",
    )


def _parse_action(raw: str) -> str:
    raw = raw.lower().strip()
    for action in VALID_ACTIONS:
        if action in raw:
            return action
    return "do_nothing"
