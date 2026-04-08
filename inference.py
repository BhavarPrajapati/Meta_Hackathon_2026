import os
import sys
import requests
from agent.agent import CEOAgent
from grader.grader import grade

API_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
TASKS = ["easy", "medium", "hard"]
SEP = "─" * 70


def run_simulation(task_id: str = "easy") -> dict:
    print(f"\n{'═' * 70}")
    print(f"  [START] Task: {task_id.upper()}  |  AI Startup CEO Simulator v3.0")
    print(f"{'═' * 70}")

    agent = CEOAgent()

    resp = requests.post(f"{API_URL}/reset", json={"task": task_id}, timeout=10)
    resp.raise_for_status()
    state = resp.json()

    _print_initial_state(state)

    done = False
    step = 0
    step_log = []

    while not done and step < 20:
        step += 1
        action, thought, explanation = agent.decide(state)

        step_resp = requests.post(f"{API_URL}/step", json={"action": action}, timeout=10)
        step_resp.raise_for_status()
        result = step_resp.json()
        info = result.get("info", {})

        print(f"\n{SEP}")
        print(f"  Month {step:02d} | Mode: {state.get('strategic_mode','growth').upper()}")
        print(SEP)
        print(f"  CEO Thought : {thought}")
        print(f"  Decision    : {explanation}")
        print(f"  Impact      : {info.get('impact', result['observation'])}")
        print(f"  Tradeoff    : {info.get('tradeoff', '-')}")
        if info.get("event"):
            print(f"  Market Event: {info['event']}")
        print(f"  Cash: ${result['state']['cash']:>12,.0f}  |  MRR: ${result['state']['mrr']:>8,.0f}  |  "
              f"Burn: ${result['state']['burn_rate']:>8,.0f}  |  Runway: {result['state']['runway_months']:.1f}mo")
        print(f"  Valuation   : ${result['state']['valuation']:>12,.0f}  |  Reward: {result['reward']:.4f}")

        print(f"\n[STEP] Action: {action}, Reward: {result['reward']}, Observation: {result['observation']}")

        step_log.append({
            "step": step,
            "action": action,
            "mode": state.get("strategic_mode", "growth"),
            "reward": result["reward"],
            "mrr": result["state"]["mrr"],
            "event": info.get("event"),
        })

        state = result["state"]
        done = result["done"]

    score = grade(state, task_id=task_id)
    _print_final_report(task_id, state, score, step_log)

    print(f"\n[END] Final Valuation: ${state['valuation']:,.0f}")
    return score


def _print_initial_state(state: dict):
    print(f"\n  Initial State:")
    print(f"  Cash: ${state['cash']:,.0f}  |  MRR: ${state['mrr']:,.0f}  |  "
          f"Burn: ${state['burn_rate']:,.0f}  |  Runway: {state['runway_months']:.1f}mo")
    print(f"  Product: {state['product_progress']:.0f}%  |  PMF: {state['product_market_fit']:.2f}  |  "
          f"Customers: {state['customers']}  |  Valuation: ${state['valuation']:,.0f}")


def _print_final_report(task_id, state, score, step_log):
    print(f"\n{'═' * 70}")
    print(f"  FINAL REPORT — Task: {task_id.upper()}")
    print(f"{'═' * 70}")

    actions = [s["action"] for s in step_log]
    action_counts = {a: actions.count(a) for a in set(actions)}
    dominant = max(action_counts, key=action_counts.get)
    modes = {m: [s["mode"] for s in step_log].count(m) for m in set(s["mode"] for s in step_log)}

    print(f"\n  Strategy Summary")
    print(f"  Dominant action : {dominant} ({action_counts[dominant]}x)")
    print(f"  Action breakdown: {action_counts}")
    print(f"  Mode breakdown  : {modes}")

    print(f"\n  Strengths")
    if state["mrr"] > 30_000:
        print(f"  + Strong MRR: ${state['mrr']:,.0f}/mo")
    if not state["is_bankrupt"]:
        print(f"  + Survived all {state['step_count']} months")
    if state["product_progress"] >= 80:
        print(f"  + Product complete ({state['product_progress']:.0f}%)")
    if state["customers"] > 20:
        print(f"  + Customer base: {state['customers']} customers")

    print(f"\n  Areas to Improve")
    if state["burn_rate"] > state["mrr"] * 2:
        print(f"  - Burn (${state['burn_rate']:,.0f}) still 2x+ MRR")
    if state["equity_owned"] < 60:
        print(f"  - Heavy dilution: {state['equity_owned']:.1f}% equity remaining")
    events = list(set(s["event"] for s in step_log if s["event"]))
    if events:
        print(f"  - Market events hit: {len(events)} unique events")

    bd = score["breakdown"]
    print(f"\n  Score Breakdown")
    print(f"  Survival    : {bd['survival']:.4f} / 0.30")
    print(f"  Valuation   : {bd['valuation']:.4f} / 0.40")
    print(f"  Growth      : {bd['growth']:.4f} / 0.20")
    print(f"  Efficiency  : {bd['efficiency']:.4f} / 0.10")
    print(f"  {'─' * 30}")
    print(f"  Total Score : {score['total_score']:.4f} / 1.00")
    print(f"\n  Final Valuation : ${state['valuation']:>12,.0f}")
    print(f"  Final MRR       : ${state['mrr']:>12,.0f}")
    print(f"  Customers       : {state['customers']}")
    print(f"  Survived        : {'YES' if score['survived'] else 'NO'}")
    print(f"{'═' * 70}")


def main():
    task_arg = os.getenv("TASK_ID", "all")

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
        print(f"\n{'═' * 70}")
        print("  AGGREGATE RESULTS")
        print(f"{'═' * 70}")
        for task, score in results.items():
            print(f"  {task.upper():8s} | Score: {score['total_score']:.4f} | "
                  f"Valuation: ${score['final_valuation']:>12,.0f} | "
                  f"Survived: {'YES' if score['survived'] else 'NO'}")
        avg = sum(r["total_score"] for r in results.values()) / len(results)
        print(f"  {'─' * 50}")
        print(f"  AVERAGE SCORE : {avg:.4f}")
        print(f"{'═' * 70}\n")


if __name__ == "__main__":
    main()
