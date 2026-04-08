import os
import sys
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv
from agent.agent import CEOAgent
from grader.grader import grade

load_dotenv()

API_BASE_URL     = os.getenv("API_BASE_URL", "https://bhavar8094-ai-ceo-simulator.hf.space")
MODEL_NAME       = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

client = OpenAI(
    api_key=HF_TOKEN or "no-token",
    base_url="https://router.huggingface.co/v1/",
)

API_URL = API_BASE_URL.rstrip("/")
TASKS = ["easy", "medium", "hard"]


def _wait_for_server(max_wait: int = 60) -> bool:
    for _ in range(max_wait // 3):
        try:
            r = requests.get(f"{API_URL}/info", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def _post(url: str, payload: dict, retries: int = 10, delay: float = 5.0) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            last_err = str(e)
        if attempt < retries - 1:
            time.sleep(delay)
    print(f"[WARN] _post failed after {retries} attempts: {last_err}")
    return {}


def run_simulation(task_id: str = "easy") -> dict:
    print(f"[START] Task: {task_id}")

    agent = CEOAgent()
    state = _post(f"{API_URL}/reset", {"task": task_id})

    if not state:
        print(f"[END] Final Valuation: $0")
        return {"total_score": 0.0, "breakdown": {}, "final_valuation": 0,
                "final_mrr": 0, "customers": 0, "survived": False,
                "steps_completed": 0, "task_id": task_id}

    done = False
    step = 0

    while not done and step < 20:
        step += 1
        try:
            action, thought, explanation = agent.decide(state)
        except Exception:
            action = "do_nothing"

        result = _post(f"{API_URL}/step", {"action": action})
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

    _wait_for_server(max_wait=60)

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
            print(f"[WARN] Task {task} failed: {e}")
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
