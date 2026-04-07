from .state import CompanyState
import random

def process_action(state: CompanyState, action: str):
    """Business logic for each CEO decision."""
    msg = ""
    action = action.lower()
    
    if "hire_engineer" in action:
        state.burn_rate += 10000
        state.team_engineers += 1
        state.product_progress += 15
        msg = "Hired an engineer. Development speed increased."
    elif "hire_sales" in action:
        state.burn_rate += 8000
        state.team_sales += 1
        msg = "Hired sales rep. Revenue growth accelerated."
    elif "marketing_push" in action:
        if state.cash >= 50000:
            state.cash -= 50000
            state.mrr += 12000
            msg = "Executed marketing push. Spent $50k, MRR up."
        else:
            msg = "Insufficient cash for marketing."
    elif "fundraise" in action:
        state.cash += 1000000
        state.equity_owned *= 0.8
        msg = "Raised $1M seed funding. 20% equity diluted."
    else:
        msg = "No major action taken."

    # Simulation Updates
    state.cash -= (state.burn_rate / 4) # 1 step = 1 week
    state.mrr += (state.team_sales * 1500)
    state.valuation = (state.mrr * 12 * 8) + state.cash
    
    # Check for bankruptcy
    if state.cash <= 0:
        state.is_bankrupt = True
        msg += " Company went bankrupt!"

    return msg
