from pydantic import BaseModel, Field
from typing import Optional, List


class CompanyState(BaseModel):
    cash: float = Field(default=1_000_000.0)
    mrr: float = Field(default=5_000.0)
    burn_rate: float = Field(default=50_000.0)
    valuation: float = Field(default=2_000_000.0)
    equity_owned: float = Field(default=100.0)
    team_engineers: int = Field(default=2)
    team_sales: int = Field(default=1)
    product_progress: float = Field(default=10.0)
    product_market_fit: float = Field(default=0.5)
    customers: int = Field(default=5)
    market_sentiment: float = Field(default=1.0)
    competition_level: float = Field(default=0.3)
    step_count: int = Field(default=0)
    is_bankrupt: bool = Field(default=False)
    active_event: Optional[str] = Field(default=None)
    task_id: str = Field(default="easy")
    strategic_mode: str = Field(default="growth")
    mrr_history: List[float] = Field(default_factory=list)
    cash_history: List[float] = Field(default_factory=list)
    action_history: List[str] = Field(default_factory=list)

    @property
    def runway_months(self) -> float:
        net_burn = max(self.burn_rate - self.mrr, 0)
        if net_burn == 0:
            return 999.0
        return round(self.cash / net_burn, 2)

    @property
    def monthly_growth_rate(self) -> float:
        if len(self.mrr_history) < 2:
            return 0.0
        prev = self.mrr_history[-2]
        if prev == 0:
            return 0.0
        return round((self.mrr_history[-1] - prev) / prev, 4)

    @property
    def mrr_trend(self) -> str:
        if len(self.mrr_history) < 3:
            return "flat"
        if self.mrr_history[-1] > self.mrr_history[-3] * 1.05:
            return "up"
        if self.mrr_history[-1] < self.mrr_history[-3] * 0.95:
            return "down"
        return "flat"

    def snapshot(self) -> dict:
        return {
            "cash": round(self.cash, 2),
            "mrr": round(self.mrr, 2),
            "burn_rate": round(self.burn_rate, 2),
            "runway_months": self.runway_months,
            "valuation": round(self.valuation, 2),
            "equity_owned": round(self.equity_owned, 2),
            "team_engineers": self.team_engineers,
            "team_sales": self.team_sales,
            "product_progress": round(self.product_progress, 2),
            "product_market_fit": round(self.product_market_fit, 2),
            "customers": self.customers,
            "market_sentiment": round(self.market_sentiment, 2),
            "competition_level": round(self.competition_level, 2),
            "step_count": self.step_count,
            "is_bankrupt": self.is_bankrupt,
            "active_event": self.active_event,
            "task_id": self.task_id,
            "strategic_mode": self.strategic_mode,
            "monthly_growth_rate": self.monthly_growth_rate,
            "mrr_trend": self.mrr_trend,
            "action_history": self.action_history[-5:],
        }
