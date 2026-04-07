from fastapi import FastAPI
from pydantic import BaseModel

from .state import CompanyState
from .actions import process_action
from .reward import compute_reward
from .events import apply_events

app = FastAPI(title="AI Startup CEO Simulator", version="3.0.0")
current_state = CompanyState()

TASK_CONFIGS = {
    "easy": dict(
        cash=1_000_000.0, mrr=8_000.0, burn_rate=40_000.0,
        product_progress=20.0, product_market_fit=0.6, customers=10,
        market_sentiment=1.1, competition_level=0.2, valuation=2_000_000.0,
    ),
    "medium": dict(
        cash=500_000.0, mrr=5_000.0, burn_rate=55_000.0,
        product_progress=10.0, product_market_fit=0.5, customers=5,
        market_sentiment=1.0, competition_level=0.5, valuation=1_000_000.0,
    ),
    "hard": dict(
        cash=200_000.0, mrr=2_000.0, burn_rate=70_000.0,
        product_progress=5.0, product_market_fit=0.3, customers=2,
        market_sentiment=0.8, competition_level=0.8, valuation=500_000.0,
    ),
}

MAX_STEPS = 20


class ResetRequest(BaseModel):
    task: str = "easy"


class StepRequest(BaseModel):
    action: str


@app.post("/reset")
async def reset(request: ResetRequest):
    global current_state
    cfg = TASK_CONFIGS.get(request.task, TASK_CONFIGS["easy"])
    current_state = CompanyState(
        task_id=request.task,
        mrr_history=[cfg["mrr"]],
        cash_history=[cfg["cash"]],
        **cfg,
    )
    return current_state.snapshot()


@app.get("/state")
async def get_state():
    return current_state.snapshot()


@app.post("/step")
async def step(request: StepRequest):
    global current_state

    if current_state.is_bankrupt:
        return {
            "observation": "Episode terminated: company is bankrupt.",
            "reward": 0.0,
            "done": True,
            "state": current_state.snapshot(),
            "info": {"reason": "bankrupt"},
        }

    prev_mrr = current_state.mrr
    prev_cash = current_state.cash

    _update_strategic_mode(current_state)
    result = process_action(current_state, request.action)

    current_state.action_history.append(result.action)
    if len(current_state.action_history) > 6:
        current_state.action_history.pop(0)

    current_state.cash += current_state.mrr

    organic = int(current_state.team_sales * 1.5 * current_state.product_market_fit * current_state.market_sentiment)
    current_state.customers += organic
    current_state.mrr += organic * 400

    event_msg = apply_events(current_state)

    current_state.valuation = (current_state.mrr * 12 * 10) + current_state.cash

    current_state.mrr_history.append(round(current_state.mrr, 2))
    current_state.cash_history.append(round(current_state.cash, 2))
    if len(current_state.mrr_history) > 6:
        current_state.mrr_history.pop(0)
    if len(current_state.cash_history) > 6:
        current_state.cash_history.pop(0)

    if current_state.cash <= 0:
        current_state.is_bankrupt = True
        current_state.cash = 0.0

    current_state.step_count += 1

    reward = compute_reward(current_state, prev_mrr, prev_cash)
    done = current_state.is_bankrupt or current_state.step_count >= MAX_STEPS

    observation = result.message
    if event_msg:
        observation += f" | EVENT: {event_msg}"

    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "state": current_state.snapshot(),
        "info": {
            "action": result.action,
            "reason": result.reason,
            "impact": result.impact,
            "tradeoff": result.tradeoff,
            "action_success": result.success,
            "strategic_mode": current_state.strategic_mode,
            "step": current_state.step_count,
            "runway_months": current_state.runway_months,
            "event": event_msg,
        },
    }


def _update_strategic_mode(state: CompanyState):
    runway = state.runway_months
    burn_to_mrr = state.burn_rate / max(state.mrr, 1)
    if runway < 3:
        state.strategic_mode = "survival"
    elif burn_to_mrr > 3.0 and state.product_progress >= 70:
        state.strategic_mode = "efficiency"
    else:
        state.strategic_mode = "growth"
