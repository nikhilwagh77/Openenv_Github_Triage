import requests
import json
import time

BASE_URL = "http://127.0.0.1:7860"

def verify_grader_logic():
    print(f"--- Verifying Grader Logic at {BASE_URL} ---")
    
    # 1. Reset Task 1
    print("\n[1] Resetting Task 1: 'Broken Link Triage'...")
    reset_resp = requests.post(f"{BASE_URL}/reset", json={"task_id": "1"})
    print(f"    Initial Observation Reward: {reset_resp.json().get('reward')}")
    
    # 2. Take a 'Perfect' Action
    print("\n[2] Performing perfect triage (labels: bug, ui; assignee: frontend-team)...")
    action_payload = {
        "action": {
            "apply_labels": ["bug", "ui"],
            "remove_labels": [],
            "assign_to": ["frontend-team"],
            "leave_comment": "Fixing the broken link in footer.",
            "submit_decision": True
        }
    }
    
    step_resp = requests.post(f"{BASE_URL}/step", json=action_payload)
    if step_resp.status_code == 200:
        data = step_resp.json()
        reward = data.get("reward")
        print(f"    Step Reward Received: {reward}")
        
        # In our mapping, a perfect score (1.0) maps to 0.9 (plus noise)
        if 0.88 <= reward <= 0.92:
            print(f"    \u2705 SUCCESS: Grader recognized perfect action! Score: {reward}")
        else:
            print(f"    \u274c ERROR: Grader returned unexpected score: {reward}")
    else:
        print(f"    \u274c ERROR: Step failed: {step_resp.text}")

    # 3. Take a 'Partial' Action
    print("\n[3] Testing Partial Action (only 1 label)...")
    requests.post(f"{BASE_URL}/reset", json={"task_id": "1"})
    partial_payload = {
        "action": {
            "apply_labels": ["bug"],
            "remove_labels": [],
            "assign_to": [],
            "submit_decision": True
        }
    }
    partial_resp = requests.post(f"{BASE_URL}/step", json=partial_payload)
    partial_reward = partial_resp.json().get("reward")
    print(f"    Partial Reward Received: {partial_reward}")
    
    # Task 1 has 3 components (2 labels + 1 assignee). 
    # Applying 1 label gives 1/3 = 0.33 raw score.
    # Mapping: 0.1 + (0.33 * 0.8) = 0.36
    if 0.3 <= partial_reward <= 0.45:
         print(f"    \u2705 SUCCESS: Grader recognized partial progress! Score: {partial_reward}")

if __name__ == "__main__":
    verify_grader_logic()
