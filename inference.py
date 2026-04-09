import os
import sys
import time
import requests
from dotenv import load_dotenv
from grader.grader import grade

load_dotenv()

ENV_URL = os.getenv("ENV_BASE_URL", os.getenv("API_BASE_URL", "http://localhost:7860"))
TASKS = ["easy", "medium", "hard"]

# ============================================================
# LLM PROXY CONFIG — Use the validator's injected env vars
# ============================================================
LLM_BASE_URL = os.getenv("API_BASE_URL", "")
LLM_API_KEY = os.getenv("API_KEY", "")

VALID_ACTIONS = [
    "hire_engineer", "hire_sales", "marketing_push",
    "fundraise", "cut_costs", "improve_product", "do_nothing",
]


def _get_llm_client():
    """Initialize OpenAI client using the validator's LLM proxy."""
    try:
        from openai import OpenAI
        if LLM_BASE_URL and LLM_API_KEY:
            return OpenAI(
                base_url=LLM_BASE_URL,
                api_key=LLM_API_KEY,
            )
    except Exception:
        pass
    return None


def _llm_decide(state: dict, task_id: str, client) -> str:
    """Use LLM through the validator's proxy to decide the next action."""
    if client is None:
        return ""

    try:
        cash = state.get("cash", 0)
        mrr = state.get("mrr", 0)
        burn = state.get("burn_rate", 0)
        runway = state.get("runway_months", 0)
        valuation = state.get("valuation", 0)
        product = state.get("product_progress", 0)
        pmf = state.get("product_market_fit", 0)
        customers = state.get("customers", 0)
        step = state.get("step_count", 0)
        mode = state.get("strategic_mode", "growth")

        prompt = f"""You are an AI startup CEO. Analyze the current state and choose ONE action.

Current State (Month {step}/20):
- Cash: ${cash:,.0f} | MRR: ${mrr:,.0f} | Burn Rate: ${burn:,.0f}/month
- Runway: {runway:.1f} months | Valuation: ${valuation:,.0f}
- Product Progress: {product:.0f}% | Product-Market Fit: {pmf:.2f}
- Customers: {customers} | Mode: {mode} | Task: {task_id}

Available actions: {', '.join(VALID_ACTIONS)}

Rules:
- If runway < 3, prioritize fundraise or cut_costs
- If product < 50, prioritize hire_engineer or improve_product
- If product > 60 and pmf > 0.5, consider marketing_push or hire_sales
- Balance growth vs survival

Respond with ONLY the action name, nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strategic AI CEO advisor. Respond with only the action name."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=20,
            temperature=0.3,
        )

        action = response.choices[0].message.content.strip().lower().replace("'", "").replace('"', '')
        if action in VALID_ACTIONS:
            return action
    except Exception:
        pass

    return ""


def _rule_decide(state: dict) -> str:
    """Rule-based fallback decision logic."""
    runway = state.get("runway_months", 0)
    product = state.get("product_progress", 0)
    pmf = state.get("product_market_fit", 0)
    mrr = state.get("mrr", 0)
    burn = state.get("burn_rate", 1)
    cash = state.get("cash", 0)
    step = state.get("step_count", 0)
    mode = state.get("strategic_mode", "growth")
    event = state.get("active_event", "")
    customers = state.get("customers", 0)
    recent = state.get("action_history", [])

    # SURVIVAL MODE
    if mode == "survival":
        if runway < 1.5:
            return "fundraise"
        if burn > mrr * 3:
            return "cut_costs"
        if runway < 3 and cash < 150_000:
            return "fundraise"
        return "do_nothing"

    # EFFICIENCY MODE
    if mode == "efficiency":
        if burn > mrr * 4:
            return "cut_costs"
        if product < 70:
            return "hire_engineer"
        if mrr < burn * 0.5:
            return "hire_sales"
        return "cut_costs"

    # GROWTH MODE
    if runway < 2:
        return "fundraise"

    if event and any(x in str(event) for x in ["CRASH", "SURGE"]):
        if runway < 5:
            return "fundraise"
        if burn > mrr * 2.5:
            return "cut_costs"

    if product < 40:
        if pmf < 0.35 and cash > 20_000:
            return "improve_product"
        return "hire_engineer"

    if product < 60:
        if pmf < 0.45 and cash > 20_000:
            return "improve_product"
        return "hire_engineer"

    if product >= 60 and pmf >= 0.55 and cash > 50_000 and mrr < 30_000 and step > 3:
        return "marketing_push"

    if mrr < burn * 0.8:
        return "hire_sales"

    if runway < 4 and cash < 250_000:
        return "fundraise"

    if event and any(x in str(event) for x in ["VIRAL", "BOOM", "INVESTOR"]):
        if cash > 50_000 and mrr < 80_000:
            return "marketing_push"

    if len(recent) >= 4 and len(set(recent[-4:])) == 1:
        last = recent[-1]
        if last == "hire_sales" and cash > 50_000:
            return "marketing_push"
        if last == "hire_engineer" and product >= 60:
            return "hire_sales"
        if last == "marketing_push":
            return "hire_sales"

    if mrr < 60_000 and pmf >= 0.5:
        return "hire_sales"

    if step >= 15 and mrr < burn:
        return "hire_sales"

    return "do_nothing"


def _post(url: str, payload: dict, retries: int = 10, delay: float = 5.0) -> dict:
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(delay)
    return {}


def _wait_for_server(base: str, max_wait: int = 120):
    for i in range(max_wait // 3):
        try:
            r = requests.get(f"{base}/info", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def clamp_score(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive)."""
    if score <= 0.0:
        return 0.001
    if score >= 1.0:
        return 0.999
    return round(score, 4)


def run_simulation(task_id: str = "easy", llm_client=None) -> dict:
    # ============================================================
    # [START] — printed to stdout with flush=True
    # ============================================================
    print(f"[START] task={task_id}", flush=True)

    _wait_for_server(ENV_URL)
    state = _post(f"{ENV_URL}/reset", {"task": task_id})

    if not state:
        score = 0.001
        print(f"[END] task={task_id} score={score} steps=0", flush=True)
        return {
            "task_id": task_id,
            "score": score,
            "total_score": score,
            "final_valuation": 0,
            "final_mrr": 0,
            "customers": 0,
            "survived": False,
            "steps_completed": 0,
            "breakdown": {},
        }

    done = False
    step = 0

    while not done and step < 20:
        step += 1

        # Try LLM decision first, fall back to rule-based
        action = ""
        if llm_client is not None:
            action = _llm_decide(state, task_id, llm_client)

        # Fallback to rule-based if LLM didn't return a valid action
        if not action:
            action = _rule_decide(state)

        result = _post(f"{ENV_URL}/step", {"action": action})
        if not result:
            break

        reward = result.get("reward", 0)

        # ============================================================
        # [STEP] — printed to stdout with flush=True
        # ============================================================
        print(f"[STEP] task={task_id} step={step} reward={reward}", flush=True)

        state = result.get("state", state)
        done = result.get("done", False)

    # Grade the final state
    grader_result = grade(state, task_id=task_id)

    # Ensure score is strictly between 0 and 1
    raw_score = grader_result.get("total_score", 0.001)
    clamped_score = clamp_score(raw_score)

    grader_result["total_score"] = clamped_score
    grader_result["score"] = clamped_score
    grader_result["task_id"] = task_id
    grader_result["steps_completed"] = step

    # ============================================================
    # [END] — printed to stdout with flush=True
    # ============================================================
    print(f"[END] task={task_id} score={clamped_score} steps={step}", flush=True)

    return grader_result


def main():
    task_arg = os.getenv("TASK_ID", "all")

    if task_arg == "all":
        tasks_to_run = TASKS
    elif task_arg in TASKS:
        tasks_to_run = [task_arg]
    else:
        tasks_to_run = TASKS

    # Initialize LLM client using validator's proxy
    llm_client = _get_llm_client()

    results = {}
    for task in tasks_to_run:
        try:
            result = run_simulation(task, llm_client=llm_client)
            results[task] = result
        except Exception as e:
            score = 0.001
            print(f"[START] task={task}", flush=True)
            print(f"[END] task={task} score={score} steps=0", flush=True)
            results[task] = {
                "task_id": task,
                "score": score,
                "total_score": score,
                "final_valuation": 0,
                "survived": False,
                "steps_completed": 0,
                "breakdown": {},
            }


if __name__ == "__main__":
    main()
