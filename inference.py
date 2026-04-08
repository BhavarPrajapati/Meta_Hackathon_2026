import os
import sys
import json
import time
import requests
from dotenv import load_dotenv
from grader.grader import grade

load_dotenv()

ENV_URL = os.getenv("ENV_BASE_URL", os.getenv("API_BASE_URL", "http://localhost:7860"))
TASKS = ["easy", "medium", "hard"]

VALID_ACTIONS = [
    "hire_engineer", "hire_sales", "marketing_push",
    "fundraise", "cut_costs", "improve_product", "do_nothing",
]


def _rule_decide(state: dict) -> str:
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
            print(f"[WARN] attempt {attempt+1}: HTTP {resp.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] attempt {attempt+1}: {e}", file=sys.stderr)
        if attempt < retries - 1:
            time.sleep(delay)
    return {}


def _wait_for_server(base: str, max_wait: int = 120):
    print(f"[INFO] Waiting for server at {base}...", file=sys.stderr)
    for i in range(max_wait // 3):
        try:
            r = requests.get(f"{base}/info", timeout=5)
            if r.status_code == 200:
                print(f"[INFO] Server is ready.", file=sys.stderr)
                return True
        except Exception:
            pass
        time.sleep(3)
    print(f"[WARN] Server not ready after {max_wait}s", file=sys.stderr)
    return False


def clamp_score(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive)."""
    if score <= 0.0:
        return 0.001
    if score >= 1.0:
        return 0.999
    return round(score, 4)


def run_simulation(task_id: str = "easy") -> dict:
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[START] Task: {task_id}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    _wait_for_server(ENV_URL)
    state = _post(f"{ENV_URL}/reset", {"task": task_id})

    if not state:
        print(f"[ERROR] Failed to reset environment for task {task_id}", file=sys.stderr)
        return {
            "task_id": task_id,
            "score": 0.001,
            "total_score": 0.001,
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
        action = _rule_decide(state)
        result = _post(f"{ENV_URL}/step", {"action": action})
        if not result:
            print(f"[WARN] Step {step} failed for task {task_id}", file=sys.stderr)
            break

        reward = result.get("reward", 0)
        obs = result.get("observation", "")
        print(f"  [STEP {step:02d}] Action: {action:20s} | Reward: {reward:.4f} | {obs[:60]}", file=sys.stderr)

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

    print(f"\n[END] Task: {task_id} | Score: {clamped_score:.4f} | "
          f"Valuation: ${state.get('valuation', 0):,.0f} | "
          f"Survived: {'YES' if grader_result.get('survived') else 'NO'}", file=sys.stderr)

    return grader_result


def main():
    task_arg = os.getenv("TASK_ID", "all")

    if task_arg == "all":
        tasks_to_run = TASKS
    elif task_arg in TASKS:
        tasks_to_run = [task_arg]
    else:
        tasks_to_run = TASKS  # Default to all tasks

    results = {}
    for task in tasks_to_run:
        try:
            result = run_simulation(task)
            results[task] = result
        except Exception as e:
            print(f"[ERROR] Task {task} failed: {e}", file=sys.stderr)
            results[task] = {
                "task_id": task,
                "score": 0.001,
                "total_score": 0.001,
                "final_valuation": 0,
                "survived": False,
                "steps_completed": 0,
                "breakdown": {},
            }

    # ========================================================
    # OUTPUT STRUCTURED RESULTS
    # Phase 2 validator parses stdout for task results
    # ========================================================

    # Output each task result as a JSON line (for validator parsing)
    for task_id, result in results.items():
        score = clamp_score(result.get("total_score", result.get("score", 0.001)))
        task_output = {
            "task_id": task_id,
            "score": score,
            "total_score": score,
            "breakdown": result.get("breakdown", {}),
            "final_valuation": result.get("final_valuation", 0),
            "final_mrr": result.get("final_mrr", 0),
            "customers": result.get("customers", 0),
            "survived": result.get("survived", False),
            "steps_completed": result.get("steps_completed", 0),
        }
        # Print structured JSON for each task result
        print(json.dumps(task_output))

    # Print summary
    print(json.dumps({
        "type": "summary",
        "num_tasks": len(results),
        "tasks": list(results.keys()),
        "scores": {task: clamp_score(r.get("total_score", r.get("score", 0.001))) for task, r in results.items()},
        "average_score": clamp_score(
            sum(clamp_score(r.get("total_score", r.get("score", 0.001))) for r in results.values()) / max(len(results), 1)
        ),
    }))

    # Also print human-readable summary to stderr
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  AGGREGATE RESULTS", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    for task, result in results.items():
        score = clamp_score(result.get("total_score", result.get("score", 0.001)))
        print(f"  {task.upper():10s} | Score: {score:.4f} | "
              f"Valuation: ${result.get('final_valuation', 0):>12,.0f} | "
              f"Survived: {'YES' if result.get('survived') else 'NO'}", file=sys.stderr)
    scores = [clamp_score(r.get("total_score", r.get("score", 0.001))) for r in results.values()]
    print(f"  {'─'*50}", file=sys.stderr)
    print(f"  AVERAGE SCORE : {sum(scores)/len(scores):.4f}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()
