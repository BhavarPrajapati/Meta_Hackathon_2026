from pydantic import BaseModel
from typing import Optional

class CompanyState(BaseModel):
    # Financials
    cash: float = 1000000.0
    mrr: float = 5000.0
    burn_rate: float = 50000.0
    runway_months: float = 20.0
    valuation: float = 2000000.0
    equity_owned: float = 100.0
    
    # Team
    team_engineers: int = 2
    team_sales: int = 1
    
    # Product
    product_progress: float = 10.0
    product_market_fit: float = 0.5
    
    # Context
    step_count: int = 0
    is_bankrupt: bool = False
    active_crisis: Optional[str] = None
    task_id: str = "easy"
