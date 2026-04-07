from fastapi import FastAPI
from pydantic import BaseModel
from .state import CompanyState
from .actions import process_action

app = FastAPI()
current_state = CompanyState()

class StepRequest(BaseModel):
    action: str

class ResetRequest(BaseModel):
    task: str = "easy"

@app.post("/reset")
async def reset(request: ResetRequest):
    global current_state
    # Scaled Start States (Optimization)
    if request.task == "hard":
        current_state = CompanyState(cash=250000.0, mrr=2000.0, task_id="hard")
    elif request.task == "medium":
        current_state = CompanyState(cash=600000.0, mrr=4000.0, task_id="medium")
    else:
        current_state = CompanyState(cash=1000000.0, mrr=5000.0, task_id="easy")
    return current_state

@app.get("/state")
async def get_state():
    return current_state

@app.post("/step")
async def step(request: StepRequest):
    global current_state
    if current_state.is_bankrupt:
        return {"observation": "Terminated (Bankrupt)", "reward": 0.0, "done": True, "state": current_state}
    
    msg = process_action(current_state, request.action)
    current_state.step_count += 1
    
    # 1. Winning Reward Function (Target: $20M Valuation)
    reward = min(1.0, current_state.valuation / 20000000.0)
    
    # 2. Episode Completion Logic (20 Weeks)
    done = current_state.is_bankrupt or current_state.step_count >= 20
    
    return {
        "observation": msg,
        "reward": reward,
        "done": done,
        "state": current_state
    }
