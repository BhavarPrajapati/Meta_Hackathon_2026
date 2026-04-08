from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grader.grader import grade as compute_grade

from .state import CompanyState
from .actions import process_action
from .reward import compute_reward
from .events import apply_events

app = FastAPI(title="AI Startup CEO Simulator", version="3.0.0")

_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

current_state = CompanyState()
_sessions: Dict[str, CompanyState] = {}

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
    session_id: str = "default"


class StepRequest(BaseModel):
    action: str
    session_id: str = "default"


class CloseRequest(BaseModel):
    session_id: str = "default"


@app.get("/")
async def root():
    index = os.path.join(_static_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {
        "name": "AI Startup CEO Simulator",
        "version": "3.0.0",
        "spec": "OpenEnv 0.1",
        "endpoints": ["/reset", "/step", "/state", "/close", "/info", "/ws"],
        "tasks": list(TASK_CONFIGS.keys()),
    }


@app.get("/info")
async def info():
    return {
        "name": "AI Startup CEO Simulator",
        "description": "RL environment where an AI agent acts as a startup CEO making strategic decisions.",
        "version": "3.0.0",
        "spec_version": "openenv-0.1",
        "observation_space": {
            "type": "dict",
            "fields": ["cash", "mrr", "burn_rate", "runway_months", "valuation",
                       "product_progress", "product_market_fit", "customers",
                       "team_engineers", "team_sales", "strategic_mode", "step_count"],
        },
        "action_space": {
            "type": "discrete",
            "actions": ["hire_engineer", "hire_sales", "marketing_push",
                        "fundraise", "cut_costs", "improve_product", "do_nothing"],
        },
        "tasks": [
            {"id": "easy",   "description": "Well-funded startup, low risk, growing market."},
            {"id": "medium", "description": "Lean startup, competitive market, mid-game crisis."},
            {"id": "hard",   "description": "Underfunded, high burn, recurring market crashes."},
        ],
        "max_steps": MAX_STEPS,
        "reward_range": [0.0, 1.0],
    }


@app.post("/reset")
async def reset(request: ResetRequest = None):
    global current_state
    if request is None:
        request = ResetRequest()
    cfg = TASK_CONFIGS.get(request.task, TASK_CONFIGS["easy"])
    state = CompanyState(
        task_id=request.task,
        mrr_history=[cfg["mrr"]],
        cash_history=[cfg["cash"]],
        **cfg,
    )
    _sessions[request.session_id] = state
    current_state = state
    return state.snapshot()


@app.get("/state")
async def get_state():
    return current_state.snapshot()


@app.post("/close")
async def close(request: CloseRequest):
    if request.session_id in _sessions:
        del _sessions[request.session_id]
    return {"status": "closed", "session_id": request.session_id}


class GradeRequest(BaseModel):
    state: dict
    task_id: str = "easy"


@app.post("/grade")
async def grade_episode(request: GradeRequest):
    return compute_grade(request.state, task_id=request.task_id)


@app.post("/step")
async def step(request: StepRequest):
    global current_state
    state = _sessions.get(request.session_id, current_state)

    if state.is_bankrupt:
        return {
            "observation": "Episode terminated: company is bankrupt.",
            "reward": 0.0,
            "done": True,
            "truncated": False,
            "state": state.snapshot(),
            "info": {"reason": "bankrupt"},
        }

    prev_mrr = state.mrr
    prev_cash = state.cash

    _update_strategic_mode(state)
    result = process_action(state, request.action)

    state.action_history.append(result.action)
    if len(state.action_history) > 6:
        state.action_history.pop(0)

    state.cash += state.mrr

    organic = int(state.team_sales * 1.5 * state.product_market_fit * state.market_sentiment)
    state.customers += organic
    state.mrr += organic * 400

    event_msg = apply_events(state)

    state.valuation = (state.mrr * 12 * 10) + state.cash

    state.mrr_history.append(round(state.mrr, 2))
    state.cash_history.append(round(state.cash, 2))
    if len(state.mrr_history) > 6:
        state.mrr_history.pop(0)
    if len(state.cash_history) > 6:
        state.cash_history.pop(0)

    if state.cash <= 0:
        state.is_bankrupt = True
        state.cash = 0.0

    state.step_count += 1

    reward = compute_reward(state, prev_mrr, prev_cash)
    done = state.is_bankrupt or state.step_count >= MAX_STEPS
    truncated = state.step_count >= MAX_STEPS and not state.is_bankrupt

    observation = result.message
    if event_msg:
        observation += f" | EVENT: {event_msg}"

    if request.session_id in _sessions:
        _sessions[request.session_id] = state
    current_state = state

    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "truncated": truncated,
        "state": state.snapshot(),
        "info": {
            "action": result.action,
            "reason": result.reason,
            "impact": result.impact,
            "tradeoff": result.tradeoff,
            "action_success": result.success,
            "strategic_mode": state.strategic_mode,
            "step": state.step_count,
            "runway_months": state.runway_months,
            "event": event_msg,
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = f"ws_{id(websocket)}"
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action_type = msg.get("type", "step")

            if action_type == "reset":
                req = ResetRequest(task=msg.get("task", "easy"), session_id=session_id)
                result = await reset(req)
                await websocket.send_text(json.dumps({"type": "reset", "data": result}))

            elif action_type == "step":
                req = StepRequest(action=msg.get("action", "do_nothing"), session_id=session_id)
                result = await step(req)
                await websocket.send_text(json.dumps({"type": "step", "data": result}))

            elif action_type == "close":
                req = CloseRequest(session_id=session_id)
                await close(req)
                await websocket.send_text(json.dumps({"type": "closed"}))
                break

    except WebSocketDisconnect:
        if session_id in _sessions:
            del _sessions[session_id]


def _update_strategic_mode(state: CompanyState):
    runway = state.runway_months
    burn_to_mrr = state.burn_rate / max(state.mrr, 1)
    if runway < 3:
        state.strategic_mode = "survival"
    elif burn_to_mrr > 3.0 and state.product_progress >= 70:
        state.strategic_mode = "efficiency"
    else:
        state.strategic_mode = "growth"
