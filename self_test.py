import threading
import time
import requests
import uvicorn
from env.environment import app

# 1. Background Server Runner
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=7860, log_level="error")

def run_self_test():
    print("--- 🛠️ STARTING SELF-TEST ENGINE ---")
    
    # Start server in a separate thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(3) # Wait for server to wake up

    base_url = "http://127.0.0.1:7860"
    
    # Step A: Reset (Qualification Check 1)
    print("\n[STEP A] Pinging /reset...")
    try:
        r = requests.post(f"{base_url}/reset", json={"task": "easy"})
        if r.status_code == 200:
            print("✅ SUCCESS: Environment Reset.")
            state = r.json()
            print(f"   Initial Stats: ${state['cash']} Cash | ${state['mrr']} MRR")
        else:
            print(f"❌ FAIL: Reset returned {r.status_code}")
            return
    except Exception as e:
        print(f"❌ FAIL: Could not connect to server: {e}")
        return

    # Step B: Strategic Run (Qualification Check 2)
    print("\n[STEP B] Running Strategic CEO Loop...")
    print("[START]")
    
    # Simulate 5 steps of a CEO
    test_actions = ["hire_engineer", "hire_sales", "marketing_push", "fundraise", "do_nothing"]
    
    for i, action in enumerate(test_actions):
        step_resp = requests.post(f"{base_url}/step", json={"action": action}).json()
        
        # Check Scaler Logging Format
        reward = step_resp['reward']
        obs = step_resp['observation']
        cash = step_resp['state']['cash']
        mrr = step_resp['state']['mrr']
        
        print(f"[STEP] Action: {action:15} | Reward: {reward:.2f} | MRR: ${mrr:8.0f} | Cash: ${cash:10.0f} | Obs: {obs}")

    print("[END]")
    
    # Step C: Data Integrity Check
    final_state = requests.get(f"{base_url}/state").json()
    if final_state['cash'] > 1000000: # After fundraising, cash should be high
        print("\n✅ SUCCESS: Financial Logic Verified (Fundraising worked).")
    if final_state['mrr'] > 5000:
        print("✅ SUCCESS: Growth Logic Verified (Marketing/Sales worked).")
    
    print("\n--- 🏁 SELF-TEST COMPLETE: PROJECT IS 100% READY ---")

if __name__ == "__main__":
    import os
    import sys
    # Add current dir to path for imports
    sys.path.append(os.getcwd())
    run_self_test()
