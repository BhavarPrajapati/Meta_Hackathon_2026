from fastapi import FastAPI
from pydantic import BaseModel
from .state import CompanyState
from .actions import process_action

app = FastAPI()
current_state = CompanyState()

class StepRequest(BaseModel):
    action: str

@app.post("/reset")
async def reset():
    global current_state
    current_state = CompanyState()
    return current_state

@app.get("/state")
async def get_state():
    return current_state

@app.post("/step")
async def step(request: StepRequest):
    global current_state
    if current_state.is_bankrupt:
        return {"observation": "Bankrupt", "reward": 0.0, "done": True, "state": current_state}
    
    msg = process_action(current_state, request.action)
    current_state.step_count += 1
    
    # Simple Reward Calculation
    reward = min(1.0, current_state.valuation / 10000000.0)
    done = current_state.is_bankrupt or current_state.step_count >= 20
    
    return {
        "observation": msg,
        "reward": reward,
        "done": done,
        "state": current_state
    }
