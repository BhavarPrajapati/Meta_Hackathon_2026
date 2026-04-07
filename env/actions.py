from .state import CompanyState
import random

def process_action(state: CompanyState, action: str):
    """Business logic for each CEO decision."""
    msg = ""
    action = action.lower()
    
    # Base costs and effects (optimized)
    if "hire_engineer" in action:
        state.burn_rate += 12000
        state.team_engineers += 1
        state.product_progress += 15 * state.product_market_fit
        msg = "Strategy: Engineering expansion."
    elif "hire_sales" in action:
        state.burn_rate += 9000
        state.team_sales += 1
        msg = "Strategy: Sales force expansion."
    elif "marketing_push" in action:
        if state.cash >= 60000:
            state.cash -= 60000
            state.mrr += 18000
            msg = "Strategy: Marketing aggressive spend."
        else:
            msg = "Failed Marketing: Insufficient Liquidity."
    elif "fundraise" in action:
        state.cash += 1200000
        state.equity_owned *= 0.75 # 25% dilution
        msg = "Strategy: Seed Series raised ($1.2M)."
    else:
        msg = "Strategy: Cash preservation (Passive)."

    # 1. Weekly Burn Calculation
    state.cash -= (state.burn_rate / 4)
    
    # 2. Revenue Growth
    state.mrr += (state.team_sales * 2200) * state.product_market_fit
    
    # 3. Task-Based Volatility (Scaling Difficulty)
    if state.task_id == "hard" and state.step_count % 5 == 0:
        state.mrr *= 0.7 # Market Crash in Hard Mode
        msg += " !!! MARKET RECESSION IMPACT !!!"
    
    # 4. Valuation Update (10x MRR + Cash)
    state.valuation = (state.mrr * 12 * 10) + state.cash
    
    # 5. Runway Calculation
    state.runway_months = state.cash / (state.burn_rate / 12 + 0.001)

    # 6. Bankruptcy check
    if state.cash <= 0:
        state.is_bankrupt = True
        msg += " BANKRUPTCY."

    return msg
