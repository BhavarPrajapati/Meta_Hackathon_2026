from pydantic import BaseModel
from typing import Optional

class CompanyState(BaseModel):
    cash: float = 1000000.0
    mrr: float = 5000.0
    burn_rate: float = 50000.0
    runway_months: float = 20.0
    product_progress: float = 10.0
    valuation: float = 2000000.0
    team_engineers: int = 2
    team_sales: int = 1
    equity_owned: float = 100.0
    step_count: int = 0
    is_bankrupt: bool = False
    active_crisis: Optional[str] = None
