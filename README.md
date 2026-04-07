# AI Autonomous Startup CEO Simulator

> An OpenEnv-compliant AI system where an intelligent agent acts as a startup CEO — making strategic decisions under real-world constraints across 20 monthly time steps.

---

## What Is This?

This project simulates a startup's lifecycle. An AI agent plays the role of CEO and must decide each month:

- Should I hire engineers or sales reps?
- Is it time to run a marketing campaign?
- Do I need to fundraise or cut costs?
- How do I survive a market crash?

Every decision includes a **reason**, **impact**, and **tradeoff** — making the system fully explainable and judge-ready.

---

## Live Demo Output

```
══════════════════════════════════════════════════════════════════════
  [START] Task: EASY  |  AI Startup CEO Simulator v3.0
══════════════════════════════════════════════════════════════════════

  Month 06 | Mode: GROWTH
  CEO Thought : GROWTH MODE: Fundamentals stable. | Product at 62%. MRR trending up.
  Decision    : [RULE] marketing_push | Reason: PMF strong. One-time spend for spike.
  Impact      : +16 customers | +$9,600 MRR | -$40,000 cash
  Tradeoff    : One-time cost. High ROI when PMF > 0.6.
  Cash: $1,025,600  |  MRR: $22,000  |  Burn: $115,000  |  Runway: 11.0mo
  Valuation   : $3,665,600  |  Reward: 0.3554

[STEP] Action: marketing_push, Reward: 0.3554, Observation: Marketing SUCCESS. +16 customers.
```

---

## Project Structure

```
├── env/
│   ├── environment.py     OpenEnv FastAPI server (reset, step, state)
│   ├── state.py           CompanyState Pydantic model with computed properties
│   ├── actions.py         7 CEO actions — each with impact + tradeoff metadata
│   ├── reward.py          Multi-component reward shaping
│   └── events.py          Deterministic market event engine
├── agent/
│   └── agent.py           CEO agent — rule-based + optional LLM
├── grader/
│   └── grader.py          Deterministic 0.0–1.0 scorer
├── tasks/
│   ├── easy.py            Task config: easy
│   ├── medium.py          Task config: medium
│   └── hard.py            Task config: hard
├── inference.py           Main runner — all 3 tasks, structured output
├── openenv.yaml           OpenEnv specification
├── Dockerfile             HuggingFace Spaces deployment
├── requirements.txt       Pinned dependencies
└── README.md
```

---

## Quickstart

**1. Clone and install**
```bash
git clone https://github.com/your-username/ai-startup-ceo-simulator
cd ai-startup-ceo-simulator
pip install -r requirements.txt
```

**2. Start the environment server**
```bash
uvicorn env.environment:app --host 0.0.0.0 --port 7860
```

**3. Run simulation**
```bash
# All 3 tasks
TASK_ID=all python inference.py

# Single task
TASK_ID=easy python inference.py
TASK_ID=medium python inference.py
TASK_ID=hard python inference.py
```

**4. With LLM (optional)**
```bash
# Create .env file
echo "HF_TOKEN=your_huggingface_token" > .env

# Run
TASK_ID=all python inference.py
```

---

## Tasks

| Task   | Cash    | Burn/mo | PMF  | Risk   | Challenge                            |
|--------|---------|---------|------|--------|--------------------------------------|
| Easy   | $1,000k | $40k    | 0.60 | Low    | Grow to $20M in a favorable market   |
| Medium | $500k   | $55k    | 0.50 | Medium | Survive competitor surge + crash     |
| Hard   | $200k   | $70k    | 0.30 | High   | Survive 4 market crashes, low runway |

---

## Available Actions

| Action           | Cost            | Effect                                    |
|------------------|-----------------|-------------------------------------------|
| `hire_engineer`  | +$15k/mo burn   | +product progress, +PMF +0.02             |
| `hire_sales`     | +$10k/mo burn   | +customers, +MRR                          |
| `marketing_push` | -$40k cash      | Big customer spike (requires PMF > 0.3)   |
| `fundraise`      | -20% equity     | +$1.5M cash                               |
| `cut_costs`      | -PMF -0.03      | -20% burn rate                            |
| `improve_product`| -$20k cash      | +10% product progress, +PMF +0.05         |
| `do_nothing`     | none            | Preserve cash                             |

---

## Strategic Modes

The agent dynamically switches modes every step based on company health:

| Mode         | Trigger Condition              | Priority                        |
|--------------|--------------------------------|---------------------------------|
| `growth`     | Default — stable fundamentals  | Hire, market, scale             |
| `survival`   | Runway < 3 months              | Fundraise or cut costs          |
| `efficiency` | Burn > 3x MRR, product ready   | Optimize before scaling         |

---

## Decision Intelligence

Every step the agent outputs a full reasoning trace:

```
CEO Thought : SURVIVAL MODE: 1.8mo runway. Capital preservation is priority #1.
Decision    : [RULE] fundraise | Reason: Runway at 1.8mo — must extend cash to survive.
Impact      : +$1,500,000 cash | Equity → 80.0%
Tradeoff    : Permanent dilution. Best at high valuation.
```

The agent uses:
- **Rule-based engine** — deterministic, mode-aware, always available
- **LLM enhancement** — called only at critical junctions (low runway, market events, pivot moments, every 5th step) to conserve API credits
- **Memory** — tracks last 10 decisions to detect stagnation and avoid repetition

---

## Market Events (Deterministic)

Events are scheduled by `(task_id, step)` — fully reproducible, no randomness:

| Event               | Effect                          | When                        |
|---------------------|---------------------------------|-----------------------------|
| `VIRAL GROWTH`      | MRR +20%, sentiment +0.10       | Easy step 4, Hard step 17   |
| `INVESTOR INTEREST` | Sentiment +0.10                 | Easy step 8, Medium step 15 |
| `MARKET BOOM`       | MRR +15%, sentiment +0.20       | Easy step 14                |
| `COMPETITOR SURGE`  | MRR -10%, competition +0.20     | Medium step 5, Hard step 6  |
| `MARKET CRASH`      | MRR -25%, sentiment -0.15       | Hard steps 3, 10, 14        |

---

## Reward System

Each step returns a shaped reward (0.0 – 1.0):

| Component    | Weight | Formula                                  |
|--------------|--------|------------------------------------------|
| Survival     | +0.10  | Alive bonus every step                   |
| Valuation    | +0.45  | `valuation / $20M * 0.45`                |
| MRR Growth   | +0.20  | `mrr_delta / $40k * 0.20`                |
| Efficiency   | +0.15  | `mrr / burn_rate * 0.12`                 |
| Runway       | +0.10  | +0.10 if runway ≥ 6mo, -0.10 if < 2mo   |
| Reckless     | -0.10  | Burn > 3x MRR after product complete     |
| Stagnation   | -0.05  | MRR flat for 3+ steps after month 5      |

---

## Scoring (Grader)

Final deterministic score (0.0 – 1.0) at episode end:

| Component  | Weight | Criteria                              |
|------------|--------|---------------------------------------|
| Survival   | 30%    | Steps completed / 20                  |
| Valuation  | 40%    | Final valuation / $20M target         |
| Growth     | 20%    | MRR growth ratio (10x = full score)   |
| Efficiency | 10%    | Final MRR / burn rate                 |

---

## Sample Results

```
══════════════════════════════════════════════════════════════════════
  AGGREGATE RESULTS
══════════════════════════════════════════════════════════════════════
  EASY     | Score: 0.8608 | Valuation: $15,680,200 | Survived: YES
  MEDIUM   | Score: 0.6074 | Valuation: $ 5,944,875 | Survived: YES
  HARD     | Score: 0.5451 | Valuation: $ 3,405,001 | Survived: YES
  ──────────────────────────────────────────────────
  AVERAGE SCORE : 0.6711
══════════════════════════════════════════════════════════════════════
```

---

## OpenEnv API Reference

| Endpoint | Method | Body                  | Description                     |
|----------|--------|-----------------------|---------------------------------|
| `/reset` | POST   | `{"task": "easy"}`    | Reset environment for a task    |
| `/step`  | POST   | `{"action": "..."}`   | Apply action, advance one month |
| `/state` | GET    | —                     | Get current state               |

**Step response:**
```json
{
  "observation": "Hired sales rep #3. +2 customers, +$1,000 MRR.",
  "reward": 0.3778,
  "done": false,
  "state": { "cash": 1122000, "mrr": 39000, "valuation": 5802000, "..." },
  "info": {
    "action": "hire_sales",
    "reason": "Product ready. Sales team converts PMF into revenue.",
    "impact": "+2 customers | +$1,000 MRR | +$10,000/mo burn",
    "tradeoff": "+burn, +MRR growth",
    "strategic_mode": "growth",
    "runway_months": 10.6,
    "event": null
  }
}
```

---

## Docker / HuggingFace Spaces

```bash
# Build
docker build -t ceo-simulator .

# Run environment server
docker run -p 7860:7860 ceo-simulator

# Run inference (separate terminal)
TASK_ID=all python inference.py
```

The `Dockerfile` uses `python:3.10-slim`, installs pinned dependencies, and exposes port `7860` — fully compatible with HuggingFace Spaces.

---

## Environment Variables

| Variable        | Default                  | Description                    |
|-----------------|--------------------------|--------------------------------|
| `HF_TOKEN`      | —                        | HuggingFace token (optional)   |
| `API_BASE_URL`  | `http://localhost:7860`  | Environment server URL         |
| `TASK_ID`       | `all`                    | Task to run: easy/medium/hard/all |

---

## Tech Stack

- **FastAPI** — OpenEnv environment server
- **Pydantic v2** — typed state model with computed properties
- **huggingface_hub** — optional LLM inference (Qwen2.5-7B)
- **Python 3.10** — core runtime
- **Docker** — HuggingFace Spaces deployment
