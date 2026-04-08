VALID_ACTIONS = [
    "hire_engineer", "hire_sales", "marketing_push",
    "fundraise", "cut_costs", "improve_product", "do_nothing",
]


class CEOAgent:
    def __init__(self):
        self.decision_memory: list = []
        self.step_scores: list = []

    def decide(self, state: dict) -> tuple:
        mode = state.get("strategic_mode", "growth")
        thought = self._ceo_thought(state, mode)
        action = self._decide(state, mode)
        explanation = self._explain(action, state)
        self._record(action, state)
        return action, thought, explanation

    def _decide(self, state: dict, mode: str) -> str:
        cash = state.get("cash", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 50_000)
        runway = state.get("runway_months", 0)
        product = state.get("product_progress", 0)
        pmf = state.get("product_market_fit", 0)
        step = state.get("step_count", 0)
        trend = state.get("mrr_trend", "flat")
        event = state.get("active_event", "")
        customers = state.get("customers", 0)
        recent = state.get("action_history", [])

        # ── SURVIVAL MODE ─────────────────────────────────────────────
        if mode == "survival":
            if runway < 1.5:
                return "fundraise"
            if burn > mrr * 3:
                return "cut_costs"
            if runway < 3 and cash < 150_000:
                return "fundraise"
            return "do_nothing"

        # ── EFFICIENCY MODE ────────────────────────────────────────────
        if mode == "efficiency":
            if burn > mrr * 4:
                return "cut_costs"
            if product < 70:
                return "hire_engineer"
            if mrr < burn * 0.5:
                return "hire_sales"
            return "cut_costs"

        # ── GROWTH MODE ────────────────────────────────────────────────

        # Hard rule: never go bankrupt
        if runway < 2:
            return "fundraise"

        # React to negative market events — don't spend, stabilize
        if event and any(x in event for x in ["CRASH", "SURGE"]):
            if runway < 5:
                return "fundraise"
            if burn > mrr * 2.5:
                return "cut_costs"

        # Phase 1: Build product (0-40%)
        if product < 40:
            if pmf < 0.35 and cash > 20_000:
                return "improve_product"
            return "hire_engineer"

        # Phase 2: Reach launch threshold (40-60%)
        if product < 60:
            # If PMF is weak, improve it before hiring more
            if pmf < 0.45 and cash > 20_000:
                return "improve_product"
            return "hire_engineer"

        # Phase 3: Product ready — grow revenue
        # Marketing push is highest ROI when PMF is strong
        if product >= 60 and pmf >= 0.55 and cash > 50_000 and mrr < 30_000 and step > 3:
            return "marketing_push"

        # Hire sales when MRR is below burn
        if mrr < burn * 0.8:
            return "hire_sales"

        # Fundraise if runway is getting short
        if runway < 4 and cash < 250_000:
            return "fundraise"

        # Positive event — capitalize with marketing
        if event and any(x in event for x in ["VIRAL", "BOOM", "INVESTOR"]):
            if cash > 50_000 and mrr < 80_000:
                return "marketing_push"

        # Avoid stagnation — break repetitive patterns
        if len(recent) >= 4 and len(set(recent[-4:])) == 1:
            last = recent[-1]
            if last == "hire_sales" and cash > 50_000:
                return "marketing_push"
            if last == "hire_engineer" and product >= 60:
                return "hire_sales"
            if last == "marketing_push":
                return "hire_sales"

        # Scale sales team aggressively when product is strong
        if mrr < 60_000 and pmf >= 0.5:
            return "hire_sales"

        # MRR growing fast — keep hiring sales
        if trend == "up" and mrr < 100_000:
            return "hire_sales"

        # Late game: maximize valuation
        if step >= 15 and mrr < burn:
            return "hire_sales"

        return "do_nothing"

    def _ceo_thought(self, state: dict, mode: str) -> str:
        runway = state.get("runway_months", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 1)
        product = state.get("product_progress", 0)
        pmf = state.get("product_market_fit", 0)
        trend = state.get("mrr_trend", "flat")
        event = state.get("active_event")
        step = state.get("step_count", 0)

        parts = []

        if event:
            parts.append(f"Market event: {event}. Adjusting strategy.")

        if mode == "survival":
            parts.append(f"SURVIVAL MODE: {runway:.1f}mo runway. Capital preservation is priority #1.")
        elif mode == "efficiency":
            ratio = round(burn / max(mrr, 1), 1)
            parts.append(f"EFFICIENCY MODE: Burn is {ratio}x MRR. Must optimize before scaling.")
        else:
            coverage = round(mrr / max(burn, 1) * 100, 0)
            parts.append(f"GROWTH MODE: MRR covers {coverage:.0f}% of burn. Accelerating.")

        if product < 40:
            parts.append(f"Product at {product:.0f}% — engineering is the bottleneck.")
        elif product < 60:
            parts.append(f"Product at {product:.0f}% — approaching launch. PMF={pmf:.2f}.")
        elif product < 80:
            parts.append(f"Product at {product:.0f}% — launch ready. Shifting to revenue growth.")
        else:
            parts.append(f"Product strong ({product:.0f}%). PMF={pmf:.2f}. Revenue is the focus.")

        if trend == "up":
            parts.append("MRR trending up — momentum building. Double down.")
        elif trend == "down":
            parts.append("MRR declining — stabilize before spending more.")

        if step >= 15:
            parts.append(f"Month {step}/20 — final stretch. Maximizing valuation.")

        return " | ".join(parts)

    def _explain(self, action: str, state: dict) -> str:
        mode = state.get("strategic_mode", "growth")
        runway = state.get("runway_months", 0)
        product = state.get("product_progress", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 1)
        pmf = state.get("product_market_fit", 0)

        reasons = {
            "hire_engineer":   f"Product at {product:.0f}% — need engineering to reach launch threshold.",
            "hire_sales":      f"Product ready (PMF={pmf:.2f}). Sales team converts demand into revenue.",
            "marketing_push":  f"PMF={pmf:.2f} is strong. One-time spend for customer acquisition spike.",
            "fundraise":       f"Runway at {runway:.1f}mo — extending cash to survive and grow.",
            "cut_costs":       f"Burn (${burn:,.0f}) too high vs MRR (${mrr:,.0f}). Cutting to extend runway.",
            "improve_product": f"PMF={pmf:.2f} is the bottleneck. Product investment unlocks conversion.",
            "do_nothing":      f"No urgent action in {mode} mode. Preserving capital.",
        }
        tradeoffs = {
            "hire_engineer":   "+burn, +product speed, +PMF",
            "hire_sales":      "+burn, +MRR, +customers",
            "marketing_push":  "-$40k cash, +customers spike (best ROI when PMF > 0.55)",
            "fundraise":       "+$1.5M cash, -20% equity (permanent dilution)",
            "cut_costs":       "-20% burn, -PMF slightly",
            "improve_product": "-$20k cash, +PMF +0.05, +10% product",
            "do_nothing":      "0 cost, 0 growth — opportunity cost",
        }
        return (f"[AGENT] {action} | "
                f"Reason: {reasons.get(action, '')} | "
                f"Tradeoff: {tradeoffs.get(action, '')}")

    def _record(self, action: str, state: dict):
        self.decision_memory.append({
            "step": state.get("step_count", 0),
            "action": action,
            "mrr": state.get("mrr", 0),
            "runway": state.get("runway_months", 0),
            "mode": state.get("strategic_mode", "growth"),
        })
        if len(self.decision_memory) > 10:
            self.decision_memory.pop(0)
