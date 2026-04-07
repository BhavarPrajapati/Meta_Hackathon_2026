import os
import json
from dotenv import load_dotenv

load_dotenv()

try:
    from huggingface_hub import InferenceClient
    _hf_client = InferenceClient(api_key=os.getenv("HF_TOKEN", ""))
    _LLM_AVAILABLE = True
except Exception:
    _hf_client = None
    _LLM_AVAILABLE = False

LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"

VALID_ACTIONS = [
    "hire_engineer", "hire_sales", "marketing_push",
    "fundraise", "cut_costs", "improve_product", "do_nothing",
]


class CEOAgent:
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and _LLM_AVAILABLE
        self.decision_memory: list = []

    def decide(self, state: dict) -> tuple:
        mode = state.get("strategic_mode", "growth")
        thought = self._ceo_thought(state, mode)

        if self.use_llm and self._is_critical(state):
            try:
                action = self._llm_decide(state, mode)
                if action in VALID_ACTIONS:
                    explanation = self._explain(action, state, "LLM")
                    self._record(action, state)
                    return action, thought, explanation
            except Exception as e:
                print(f"[FALLBACK] LLM error ({type(e).__name__}). Using rule-based logic.")
                self.use_llm = False

        action = self._rule_decide(state, mode)
        explanation = self._explain(action, state, "RULE")
        self._record(action, state)
        return action, thought, explanation

    def _ceo_thought(self, state: dict, mode: str) -> str:
        runway = state.get("runway_months", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 1)
        product = state.get("product_progress", 0)
        pmf = state.get("product_market_fit", 0)
        trend = state.get("mrr_trend", "flat")
        event = state.get("active_event")

        parts = []
        if event:
            parts.append(f"Market event detected: {event}. Adjusting strategy.")

        if mode == "survival":
            parts.append(f"SURVIVAL MODE: {runway:.1f}mo runway. Capital preservation is priority #1.")
        elif mode == "efficiency":
            parts.append(f"EFFICIENCY MODE: Burn is {burn/max(mrr,1):.1f}x MRR. Optimize before scaling.")
        else:
            parts.append("GROWTH MODE: Fundamentals stable. Time to accelerate.")

        if product < 50:
            parts.append(f"Product at {product:.0f}% — engineering is the bottleneck.")
        elif product < 80:
            parts.append(f"Product at {product:.0f}% — approaching launch readiness.")
        else:
            parts.append(f"Product strong ({product:.0f}%). PMF={pmf:.2f}. Revenue is the focus.")

        if trend == "up":
            parts.append("MRR trending up — double down on what's working.")
        elif trend == "down":
            parts.append("MRR declining — investigate before spending more.")

        return " | ".join(parts)

    def _explain(self, action: str, state: dict, source: str) -> str:
        mode = state.get("strategic_mode", "growth")
        runway = state.get("runway_months", 0)
        product = state.get("product_progress", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 1)

        reasons = {
            "hire_engineer":   f"Product at {product:.0f}% — engineering needed to reach launch threshold.",
            "hire_sales":      "Product ready. Sales team converts PMF into revenue.",
            "marketing_push":  "PMF strong. One-time spend for customer acquisition spike.",
            "fundraise":       f"Runway at {runway:.1f}mo — must extend cash to survive.",
            "cut_costs":       f"Burn (${burn:,.0f}) too high vs MRR (${mrr:,.0f}). Cutting to extend runway.",
            "improve_product": "PMF is the bottleneck. Product investment unlocks conversion.",
            "do_nothing":      f"No urgent action in {mode} mode. Preserving capital.",
        }
        tradeoffs = {
            "hire_engineer":   "+burn, +product speed",
            "hire_sales":      "+burn, +MRR growth",
            "marketing_push":  "-cash, +customers (high ROI if PMF > 0.6)",
            "fundraise":       "+cash, -equity (permanent dilution)",
            "cut_costs":       "-burn, -PMF slightly",
            "improve_product": "-cash, +PMF",
            "do_nothing":      "0 cost, 0 growth",
        }
        return (f"[{source}] {action} | "
                f"Reason: {reasons.get(action, '')} | "
                f"Tradeoff: {tradeoffs.get(action, '')}")

    def _is_critical(self, state: dict) -> bool:
        runway = state.get("runway_months", 99)
        step = state.get("step_count", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 1)
        product = state.get("product_progress", 0)
        event = state.get("active_event")

        if runway < 4:              return True
        if event:                   return True
        if 45 <= product <= 60:     return True
        if 0.7 <= mrr / burn <= 1.2: return True
        if step % 5 == 0 and step > 0: return True
        return False

    def _llm_decide(self, state: dict, mode: str) -> str:
        memory_ctx = ""
        if self.decision_memory:
            last = self.decision_memory[-3:]
            memory_ctx = "Recent: " + ", ".join(f"{d['action']}(step {d['step']})" for d in last)

        prompt = f"""You are a startup CEO in {mode.upper()} MODE.
{memory_ctx}

State:
{json.dumps({k: state[k] for k in [
    'cash','mrr','burn_rate','runway_months','product_progress',
    'product_market_fit','customers','strategic_mode','mrr_trend',
    'active_event','step_count'
]}, indent=2)}

Actions (return ONLY the name):
hire_engineer | hire_sales | marketing_push | fundraise | cut_costs | improve_product | do_nothing

Rules:
- survival: fundraise or cut_costs if runway < 3
- efficiency: cut_costs if burn > 3x MRR
- growth: hire_sales or marketing_push if product > 50%

Return ONLY the action name."""

        resp = _hf_client.chat_completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=12,
        )
        return resp.choices[0].message.content.strip().lower()

    def _rule_decide(self, state: dict, mode: str) -> str:
        cash = state.get("cash", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 50_000)
        runway = state.get("runway_months", 0)
        product = state.get("product_progress", 0)
        pmf = state.get("product_market_fit", 0)
        step = state.get("step_count", 0)

        if mode == "survival":
            if runway < 2:
                return "fundraise"
            if burn > mrr * 2:
                return "cut_costs"
            return "do_nothing"

        if mode == "efficiency":
            if burn > mrr * 3:
                return "cut_costs"
            if product < 60:
                return "hire_engineer"
            return "hire_sales"

        if runway < 2:
            return "fundraise"
        if product < 40:
            return "improve_product" if (pmf < 0.4 and cash > 20_000) else "hire_engineer"
        if product < 60:
            return "hire_engineer"
        if cash > 50_000 and mrr < 25_000 and step > 3:
            return "marketing_push"
        if mrr < burn:
            return "hire_sales"
        if runway < 5 and cash < 300_000:
            return "fundraise"

        recent = state.get("action_history", [])
        if len(recent) >= 3 and len(set(recent[-3:])) == 1:
            for alt in ["marketing_push", "hire_sales", "improve_product", "cut_costs"]:
                if alt != recent[-1]:
                    return alt

        if mrr < 60_000:
            return "hire_sales"
        return "do_nothing"

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
