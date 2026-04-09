import requests
import json

BASE_URL = "http://127.0.0.1:7860"

def debug_step():
    print(f"--- Debugging /reset and /step at {BASE_URL} ---")
    
    # 1. Reset
    print("\n[1] Resetting...")
    reset_resp = requests.post(f"{BASE_URL}/reset", json={"task_id": "1"})
    print(f"Status: {reset_resp.status_code}")
    print(f"Response JSON: {json.dumps(reset_resp.json(), indent=2)}")
    
    # 2. Step
    print("\n[2] Stepping...")
    step_resp = requests.post(f"{BASE_URL}/step", json={
        "apply_labels": ["bug"],
        "remove_labels": [],
        "assign_to": [],
        "leave_comment": "Testing reward",
        "submit_decision": True
    })
    print(f"Status: {step_resp.status_code}")
    if step_resp.status_code == 200:
        print(f"Response JSON: {json.dumps(step_resp.json(), indent=2)}")
    else:
        print(f"Error Response: {step_resp.text}")

if __name__ == "__main__":
    debug_step()
