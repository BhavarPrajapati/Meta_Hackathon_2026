import os
import sys
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv
from grader.grader import grade

load_dotenv()

API_BASE_URL     = os.getenv("API_BASE_URL", "https://bhavar8094-ai-ceo-simulator.hf.space")
MODEL_NAME       = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
HF_TOKEN         = os.getenv("HF_TOKEN")
API_KEY          = os.getenv("API_KEY", HF_TOKEN or "no-token")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)

ENV_URL = os.getenv("ENV_BASE_URL", "https://bhavar8094-ai-ceo-simulator.hf.space")
TASKS = ["easy", "medium", "hard"]

VALID_ACTIONS = [
    "hire_engineer", "hire_sales", "marketing_push",
    "fundraise", "cut_costs", "improve_product", "do_nothing",
]


def llm_decide(state: dict) -> str:
    prompt = f"""You are a startup CEO. Analyze the state and return ONE action name only.

State:
- Cash: ${state.get('cash', 0):,.0f}
- MRR: ${state.get('mrr', 0):,.0f}
- Burn: ${state.get('burn_rate', 0):,.0f}
- Runway: {state.get('runway_months', 0):.1f} months
- Product: {state.get('product_progress', 0):.0f}%
- PMF: {state.get('product_market_fit', 0):.2f}
- Mode: {state.get('strategic_mode', 'growth')}
- Event: {state.get('active_event', 'none')}

Actions: hire_engineer | hire_sales | marketing_push | fundraise | cut_costs | improve_product | do_nothing

Rules:
- runway < 2 months → fundraise
- product < 50% → hire_engineer
- product >= 60% and pmf >= 0.5 → hire_sales or marketing_push
- burn > 3x mrr → cut_costs

Return ONLY the action name."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=15,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip().lower()
        for action in VALID_ACTIONS:
            if action in raw:
                return action
    except Exception as e:
        print(f"[LLM] Error: {e}")

    return _rule_decide(state)


def _rule_decide(state: dict) -> str:
    runway = state.get("runway_months", 0)
    product = state.get("product_progress", 0)
    pmf = state.get("product_market_fit", 0)
    mrr = state.get("mrr", 0)
    burn = state.get("burn_rate", 1)
    cash = state.get("cash", 0)
    step = state.get("step_count", 0)

    if runway < 2:
        return "fundraise"
    if product < 40:
        return "improve_product" if pmf < 0.35 and cash > 20000 else "hire_engineer"
    if product < 60:
        return "hire_engineer"
    if pmf >= 0.55 and cash > 50000 and mrr < 30000 and step > 3:
        return "marketing_push"
    if mrr < burn * 0.8:
        return "hire_sales"
    if mrr < 60000:
        return "hire_sales"
    return "do_nothing"


def _post(url: str, payload: dict, retries: int = 10, delay: float = 5.0) -> dict:
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"[WARN] attempt {attempt+1}: {e}")
        if attempt < retries - 1:
            time.sleep(delay)
    return {}


def _wait_for_server(base: str, max_wait: int = 60):
    for _ in range(max_wait // 3):
        try:
            r = requests.get(f"{base}/info", timeout=5)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(3)


def run_simulation(task_id: str = "easy") -> dict:
    print(f"[START] Task: {task_id}")

    _wait_for_server(ENV_URL)
    state = _post(f"{ENV_URL}/reset", {"task": task_id})

    if not state:
        print(f"[END] Final Valuation: $0")
        return {"total_score": 0.0, "final_valuation": 0, "final_mrr": 0,
                "customers": 0, "survived": False, "steps_completed": 0,
                "task_id": task_id, "breakdown": {}}

    done = False
    step = 0

    while not done and step < 20:
        step += 1
        action = llm_decide(state)
        result = _post(f"{ENV_URL}/step", {"action": action})
        if not result:
            break

        print(f"[STEP] Action: {action}, Reward: {result.get('reward', 0)}, Observation: {result.get('observation', '')}")

        state = result.get("state", state)
        done = result.get("done", False)

    score = grade(state, task_id=task_id)
    print(f"[END] Final Valuation: ${state.get('valuation', 0):,.0f}")
    return score


def main():
    task_arg = os.getenv("TASK_ID", "easy")

    if task_arg == "all":
        tasks_to_run = TASKS
    elif task_arg in TASKS:
        tasks_to_run = [task_arg]
    else:
        tasks_to_run = ["easy"]

    results = {}
    for task in tasks_to_run:
        try:
            results[task] = run_simulation(task)
        except Exception as e:
            print(f"[WARN] Task {task} error: {e}")
            results[task] = {"total_score": 0.0, "final_valuation": 0,
                             "survived": False, "task_id": task}

    if len(results) > 1:
        for task, score in results.items():
            print(f"[RESULT] {task.upper()} | Score: {score.get('total_score', 0):.4f} | "
                  f"Valuation: ${score.get('final_valuation', 0):,.0f} | "
                  f"Survived: {'YES' if score.get('survived') else 'NO'}")
        scores = [r.get("total_score", 0) for r in results.values()]
        print(f"[RESULT] AVERAGE SCORE: {sum(scores)/len(scores):.4f}")


if __name__ == "__main__":
    main()
