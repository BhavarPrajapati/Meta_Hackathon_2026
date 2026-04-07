import os
import requests
from agent.agent import CEOAgent

# API URL (Pointed to the environment)
API_URL = os.getenv("API_BASE_URL", "http://localhost:7860")

def run_simulation(task_id="easy"):
    """Main execution loop required for Scaler validation."""
    print(f"[START] Task: {task_id}")
    
    # 1. Initialize Agent
    agent = CEOAgent()
    
    # 2. Reset Env for the task
    resp = requests.post(f"{API_URL}/reset", json={"task": task_id})
    state = resp.json()
    
    done = False
    step = 0
    
    while not done and step < 20:
        step += 1
        # 3. Agent Decision
        action = agent.decide(state)
        
        # 4. Step Environment
        step_resp = requests.post(f"{API_URL}/step", json={"action": action})
        result = step_resp.json()
        
        # 5. Scaler-Spec Logging (DO NOT CHANGE)
        print(f"[STEP] Action: {action}, Reward: {result['reward']}, Observation: {result['observation']}")
        
        state = result["state"]
        done = result["done"]

    # 6. Final Evaluation
    print(f"[END] Final Valuation: ${state['valuation']}")

if __name__ == "__main__":
    # In production, the Scaler bot will pass the task_id
    current_task = os.getenv("TASK_ID", "easy")
    run_simulation(current_task)
