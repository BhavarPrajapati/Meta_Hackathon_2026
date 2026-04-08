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


def _post(url: str, payload: dict, retries: int = 5, delay: float = 3.0) -> dict:
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if attempt < retries - 1:
                time.sleep(delay)
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def run_simulation(task_id: str = "easy") -> dict:
    print(f"[START] Task: {task_id}")

    agent = CEOAgent()
    state = _post(f"{API_URL}/reset", {"task": task_id})

    done = False
    step = 0

    while not done and step < 20:
        step += 1
        action, thought, explanation = agent.decide(state)
        result = _post(f"{API_URL}/step", {"action": action})

        print(f"[STEP] Action: {action}, Reward: {result['reward']}, Observation: {result['observation']}")

        state = result["state"]
        done = result["done"]

    score = grade(state, task_id=task_id)
    print(f"[END] Final Valuation: ${state['valuation']:,.0f}")
    return score


def main():
    task_arg = os.getenv("TASK_ID", "easy")

    if task_arg == "all":
        tasks_to_run = TASKS
    elif task_arg in TASKS:
        tasks_to_run = [task_arg]
    else:
        print(f"Unknown TASK_ID '{task_arg}'. Use: easy | medium | hard | all")
        sys.exit(1)

    results = {}
    for task in tasks_to_run:
        results[task] = run_simulation(task)

    if len(results) > 1:
        for task, score in results.items():
            print(f"[RESULT] {task.upper()} | Score: {score['total_score']:.4f} | "
                  f"Valuation: ${score['final_valuation']:,.0f} | "
                  f"Survived: {'YES' if score['survived'] else 'NO'}")
        avg = sum(r["total_score"] for r in results.values()) / len(results)
        print(f"[RESULT] AVERAGE SCORE: {avg:.4f}")


if __name__ == "__main__":
    main()
