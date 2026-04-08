VALUATION_TARGET = 20_000_000.0
MAX_STEPS = 20


def grade(final_state: dict, task_id: str = "easy") -> dict:
    is_bankrupt = final_state.get("is_bankrupt", False)
    valuation = final_state.get("valuation", 0.0)
    mrr = final_state.get("mrr", 0.0)
    burn_rate = final_state.get("burn_rate", 1.0)
    step_count = final_state.get("step_count", 0)
    customers = final_state.get("customers", 0)

    initial_mrr = {"easy": 8_000.0, "medium": 5_000.0, "hard": 2_000.0}.get(task_id, 5_000.0)

    survival_score = 0.0 if is_bankrupt else min(0.99, step_count / MAX_STEPS) * 0.30
    valuation_score = min(0.99, valuation / VALUATION_TARGET) * 0.40
    growth_score = min(0.99, max(0.0, (mrr / initial_mrr - 1.0) / 9.0)) * 0.20 if initial_mrr > 0 else 0.01
    efficiency_score = min(0.99, mrr / burn_rate) * 0.10 if burn_rate > 0 else 0.01

    raw = survival_score + valuation_score + growth_score + efficiency_score

    # Score must be strictly between 0 and 1 (not 0.0, not 1.0)
    # Ensure total_score is strictly between 0 and 1 (not 0.0, not 1.0)
    total = max(0.001, min(0.999, round(raw, 4)))

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
