"""
Deterministic grader for AI Startup CEO Simulator.
Scores a completed episode between 0.0 and 1.0.
"""

VALUATION_TARGET = 20_000_000.0
MAX_STEPS = 20


def grade(final_state: dict, task_id: str = "easy") -> dict:
    """
    Score a completed simulation episode.

    Components:
      - survival_score  (0.30): Did the company survive all 20 steps?
      - valuation_score (0.40): Final valuation vs $20M target
      - growth_score    (0.20): MRR growth over the episode
      - efficiency_score(0.10): MRR/burn ratio at end
    """
    is_bankrupt = final_state.get("is_bankrupt", False)
    valuation = final_state.get("valuation", 0.0)
    mrr = final_state.get("mrr", 0.0)
    burn_rate = final_state.get("burn_rate", 1.0)
    step_count = final_state.get("step_count", 0)
    customers = final_state.get("customers", 0)

    initial_mrr = {"easy": 8_000.0, "medium": 5_000.0, "hard": 2_000.0}.get(task_id, 5_000.0)

    # 1. Survival score
    if is_bankrupt:
        survival_score = 0.0
    else:
        survival_score = min(1.0, step_count / MAX_STEPS) * 0.30

    # 2. Valuation score
    valuation_score = min(1.0, valuation / VALUATION_TARGET) * 0.40

    # 3. MRR growth score (10x = full marks)
    if initial_mrr > 0:
        growth_ratio = mrr / initial_mrr
        growth_score = min(1.0, (growth_ratio - 1.0) / 9.0) * 0.20
    else:
        growth_score = 0.0

    # 4. Efficiency score
    if burn_rate > 0:
        coverage = min(1.0, mrr / burn_rate)
        efficiency_score = coverage * 0.10
    else:
        efficiency_score = 0.10

    total = round(survival_score + valuation_score + growth_score + efficiency_score, 4)

    return {
        "total_score": total,
        "breakdown": {
            "survival": round(survival_score, 4),
            "valuation": round(valuation_score, 4),
            "growth": round(growth_score, 4),
            "efficiency": round(efficiency_score, 4),
        },
        "final_valuation": valuation,
        "final_mrr": mrr,
        "customers": customers,
        "survived": not is_bankrupt,
        "steps_completed": step_count,
        "task_id": task_id,
    }
