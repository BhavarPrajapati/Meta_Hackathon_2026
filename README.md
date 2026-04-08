---
title: AI Startup CEO Simulator
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: OpenEnv RL environment — AI agent acts as a startup CEO
---

# AI Autonomous Startup CEO Simulator

> OpenEnv 0.1 compliant RL environment — Meta × Hugging Face × PyTorch Hackathon submission

An agentic environment where an AI agent acts as a startup CEO, making strategic decisions under real-world constraints across 20 monthly time steps. Built for reinforcement learning training and evaluation using the OpenEnv standard.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-0.1-blue)](https://huggingface.co/openenv)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-yellow)](https://huggingface.co/spaces)
[![Python](https://img.shields.io/badge/Python-3.10-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)](https://fastapi.tiangolo.com)

---

## Why This Environment?

Most RL benchmarks test agents on games or toy problems. This environment simulates **real business decision-making under uncertainty** — the kind of multi-step, high-stakes reasoning that separates good AI agents from great ones.

The agent must:
- Allocate limited capital across competing priorities
- Respond to unpredictable market events (crashes, viral growth, competitor surges)
- Switch strategic modes dynamically (Growth → Survival → Efficiency)
- Reason about long-term tradeoffs, not just immediate rewards
- Explain every decision with reason + impact + tradeoff

---

## OpenEnv Compliance

This environment fully implements the **OpenEnv 0.1 spec**:

| Requirement         | Status | Details                                      |
|---------------------|--------|----------------------------------------------|
| `POST /reset`       | ✅     | Session-aware, multi-task support            |
| `POST /step`        | ✅     | Returns `observation, reward, done, truncated, info` |
| `GET /state`        | ✅     | Full state snapshot                          |
| `POST /close`       | ✅     | Session cleanup                              |
| `GET /info`         | ✅     | Environment metadata, action/obs spaces      |
| WebSocket `/ws`     | ✅     | Concurrent sessions for RL training          |
| Gymnasium-style API | ✅     | `reset()`, `step()`, `close()` client        |
| Docker deployment   | ✅     | HuggingFace Spaces compatible                |
| Deterministic       | ✅     | Seeded events, reproducible output           |

---

## Quickstart

```bash
# 1. Install
pip install -r requirements.txt

# 2. Start environment server
uvicorn env.environment:app --host 0.0.0.0 --port 7860

# 3. Run simulation (all 3 tasks)
TASK_ID=all python inference.py

# 4. Use the OpenEnv client
python openenv_client.py
```

**With LLM enhancement:**
```bash
HF_TOKEN=your_token TASK_ID=all python inference.py
```

---

## OpenEnv Client Usage

```python
from openenv_client import StartupEnv

# Gymnasium-style interface
with StartupEnv(base_url="http://localhost:7860") as env:
    obs = env.reset(task="hard")

    done = False
    while not done:
        action = your_agent.decide(obs)
        obs_str, reward, done, truncated, info = env.step(action)
        print(f"Reward: {reward:.4f} | Mode: {info['strategic_mode']}")
```

**WebSocket (for concurrent RL training):**
```python
import websockets, asyncio, json

async def run():
    async with websockets.connect("ws://localhost:7860/ws") as ws:
        await ws.send(json.dumps({"type": "reset", "task": "easy"}))
        obs = json.loads(await ws.recv())

        await ws.send(json.dumps({"type": "step", "action": "hire_engineer"}))
        result = json.loads(await ws.recv())
        print(result["data"]["reward"])

asyncio.run(run())
```

---

## Project Structure

```
├── env/
│   ├── environment.py     FastAPI server — OpenEnv endpoints + WebSocket
│   ├── state.py           CompanyState Pydantic model with computed properties
│   ├── actions.py         7 CEO actions — each with reason, impact, tradeoff
│   ├── reward.py          Multi-component reward shaping (7 components)
│   └── events.py          Deterministic market event engine
├── agent/
│   └── agent.py           CEO agent — rule-based + LLM + memory + modes
├── grader/
│   └── grader.py          Deterministic 0.0–1.0 scorer
├── tasks/
│   ├── easy.py            Task config: easy
│   ├── medium.py          Task config: medium
│   └── hard.py            Task config: hard
├── openenv_client.py      Gymnasium-style Python client
├── inference.py           Main runner — structured output, all 3 tasks
├── openenv.yaml           OpenEnv 0.1 specification
├── Dockerfile             HuggingFace Spaces deployment
└── requirements.txt
```

---

## Tasks

| Task   | Cash    | Burn/mo | PMF  | Events                              | Goal              |
|--------|---------|---------|------|-------------------------------------|-------------------|
| Easy   | $1,000k | $40k    | 0.60 | Viral growth, investor interest, boom | $20M valuation  |
| Medium | $500k   | $55k    | 0.50 | Competitor surge, market crash      | Survive + grow    |
| Hard   | $200k   | $70k    | 0.30 | 4 market crashes, competitor surge  | Survive 20 months |

---

## Action Space

| Action           | Cost            | Effect                                    |
|------------------|-----------------|-------------------------------------------|
| `hire_engineer`  | +$15k/mo burn   | +product progress, +PMF +0.02             |
| `hire_sales`     | +$10k/mo burn   | +customers, +MRR                          |
| `marketing_push` | -$40k cash      | Big customer spike (requires product > 30%) |
| `fundraise`      | -20% equity     | +$1.5M cash                               |
| `cut_costs`      | -PMF -0.03      | -20% burn rate                            |
| `improve_product`| -$20k cash      | +10% product progress, +PMF +0.05         |
| `do_nothing`     | none            | Preserve cash                             |

---

## Observation Space

```json
{
  "cash": 1000000.0,
  "mrr": 8000.0,
  "burn_rate": 40000.0,
  "runway_months": 31.2,
  "valuation": 2000000.0,
  "equity_owned": 100.0,
  "product_progress": 20.0,
  "product_market_fit": 0.6,
  "customers": 10,
  "team_engineers": 2,
  "team_sales": 1,
  "market_sentiment": 1.1,
  "competition_level": 0.2,
  "strategic_mode": "growth",
  "mrr_trend": "flat",
  "monthly_growth_rate": 0.0,
  "step_count": 0,
  "is_bankrupt": false,
  "active_event": null
}
```

---

## Strategic Modes

The agent dynamically switches modes every step:

| Mode         | Trigger                        | Strategy                        |
|--------------|--------------------------------|---------------------------------|
| `growth`     | Default — stable fundamentals  | Hire, market, scale             |
| `survival`   | Runway < 3 months              | Fundraise or cut costs          |
| `efficiency` | Burn > 3x MRR, product ready   | Optimize before scaling         |

---

## Decision Intelligence Output

Every step produces a full reasoning trace:

```
Month 09 | Mode: SURVIVAL
CEO Thought : SURVIVAL MODE: 1.8mo runway. Capital preservation is priority #1.
Decision    : [RULE] fundraise | Reason: Runway at 1.8mo — must extend cash to survive.
Impact      : +$1,500,000 cash | Equity → 80.0%
Tradeoff    : Permanent dilution. Best at high valuation.
Cash: $1,635,200  |  MRR: $1,350  |  Burn: $74,800  |  Runway: 22.3mo
Valuation   : $1,797,200  |  Reward: 0.1926

[STEP] Action: fundraise, Reward: 0.192603, Observation: Raised $1,500,000.
```

---

## Market Events (Deterministic)

All events are scheduled by `(task_id, step)` — fully reproducible:

| Event               | Effect                          | Schedule                        |
|---------------------|---------------------------------|---------------------------------|
| `VIRAL GROWTH`      | MRR +20%, sentiment +0.10       | Easy step 4, Hard step 17       |
| `INVESTOR INTEREST` | Sentiment +0.10                 | Easy step 8, Medium step 15     |
| `MARKET BOOM`       | MRR +15%, sentiment +0.20       | Easy step 14                    |
| `COMPETITOR SURGE`  | MRR -10%, competition +0.20     | Medium step 5, Hard step 6      |
| `MARKET CRASH`      | MRR -25%, sentiment -0.15       | Hard steps 3, 10, 14            |

---

## Reward System

```
reward = survival(0.10) + valuation(0.45) + mrr_growth(0.20)
       + efficiency(0.15) + runway(±0.10)
       - reckless_burn(0.10) - stagnation(0.05)
```

| Component    | Weight | Condition                                |
|--------------|--------|------------------------------------------|
| Survival     | +0.10  | Alive bonus every step                   |
| Valuation    | +0.45  | `valuation / $20M * 0.45`                |
| MRR Growth   | +0.20  | `mrr_delta / $40k * 0.20`                |
| Efficiency   | +0.15  | `mrr / burn_rate * 0.12`                 |
| Runway       | ±0.10  | +0.10 if ≥6mo, -0.10 if <2mo            |
| Reckless     | -0.10  | Burn > 3x MRR after product complete     |
| Stagnation   | -0.05  | MRR flat 3+ steps after month 5          |

---

## Grader (Deterministic Scoring)

```python
from grader.grader import grade
score = grade(final_state, task_id="easy")
# {"total_score": 0.86, "breakdown": {...}, "survived": True}
```

| Component  | Weight | Formula                              |
|------------|--------|--------------------------------------|
| Survival   | 30%    | `steps_completed / 20 * 0.30`        |
| Valuation  | 40%    | `valuation / $20M * 0.40`            |
| Growth     | 20%    | `(mrr/initial_mrr - 1) / 9 * 0.20`  |
| Efficiency | 10%    | `mrr / burn_rate * 0.10`             |

---

## Benchmark Results

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

## API Reference

| Endpoint   | Method    | Body                              | Response                              |
|------------|-----------|-----------------------------------|---------------------------------------|
| `/`        | GET       | —                                 | Environment metadata                  |
| `/info`    | GET       | —                                 | Full spec: obs/action space, tasks    |
| `/reset`   | POST      | `{"task": "easy"}`                | Initial observation (state dict)      |
| `/step`    | POST      | `{"action": "hire_engineer"}`     | `{observation, reward, done, truncated, state, info}` |
| `/state`   | GET       | —                                 | Current state snapshot                |
| `/close`   | POST      | `{"session_id": "default"}`       | `{"status": "closed"}`                |
| `/ws`      | WebSocket | JSON messages                     | Concurrent session support            |

**Step response:**
```json
{
  "observation": "Hired engineer #3. Product: 27.9%",
  "reward": 0.2657,
  "done": false,
  "truncated": false,
  "state": { "cash": 1008000, "mrr": 8400, "valuation": 2016000 },
  "info": {
    "action": "hire_engineer",
    "reason": "Product at 20% — engineering needed to reach launch threshold.",
    "impact": "+7.9% product | +$15,000/mo burn | PMF +0.02",
    "tradeoff": "Higher burn. Justified only while product is incomplete.",
    "strategic_mode": "growth",
    "runway_months": 21.6,
    "event": null
  }
}
```

---

## RL Training Integration

This environment is compatible with TRL, verl, and TorchForge via the OpenEnv standard:

```python
from openenv_client import StartupEnv

env = StartupEnv(base_url="https://your-space.hf.space")
obs = env.reset(task="medium")

# Standard RL training loop
for episode in range(num_episodes):
    obs = env.reset(task="medium")
    done = False
    while not done:
        action = policy.select_action(obs)
        obs, reward, done, truncated, info = env.step(action)
        replay_buffer.add(obs, action, reward, done)
    policy.update(replay_buffer)
```

---

## Docker / HuggingFace Spaces

```bash
docker build -t ceo-simulator .
docker run -p 7860:7860 ceo-simulator
```

Health check: `GET /info` — returns 200 when ready.

---

## Environment Variables

| Variable       | Default                 | Description                          |
|----------------|-------------------------|--------------------------------------|
| `HF_TOKEN`     | —                       | HuggingFace token for LLM (optional) |
| `API_BASE_URL` | `http://localhost:7860` | Environment server URL               |
| `TASK_ID`      | `all`                   | Task: `easy` / `medium` / `hard` / `all` |

---

## Tech Stack

| Component     | Technology              |
|---------------|-------------------------|
| Environment   | FastAPI + Pydantic v2   |
| Agent         | Rule-based + Qwen2.5-7B |
| RL Interface  | OpenEnv 0.1 (HTTP + WS) |
| Deployment    | Docker + HF Spaces      |
| Runtime       | Python 3.10             |
