import requests
import json
import os
import sys

# Configuration
PORT = int(os.getenv("PORT") or 7860)
BASE_URL = f"http://127.0.0.1:{PORT}"

def check_requirements():
    print(f"\n--- Checking Deep Validation Requirements at {BASE_URL} ---")
    
    # 1. Check Task Discovery
    print("\n[1/3] Checking Task Discovery...")
    try:
        # Check /tasks endpoint (used by our UI)
        tasks_resp = requests.get(f"{BASE_URL}/tasks")
        tasks = tasks_resp.json()
        print(f"  Found {len(tasks)} tasks via /tasks")
        
        if len(tasks) < 3:
            print("  ❌ FAIL: Less than 3 tasks found!")
        else:
            print(f"  ✅ PASS: {len(tasks)} tasks exposed.")
            
    except Exception as e:
        print(f"  ❌ FAIL: Could not reach /tasks: {e}")

    # 2. Check Task Graders (Reset and Score)
    print("\n[2/3] Checking Task Graders and Score Range...")
    test_ids = ["1", "2", "3"]
    passed_graders = 0
    
    for tid in test_ids:
        try:
            # Reset task
            print(f"  Testing Task ID: {tid}...")
            reset_resp = requests.post(f"{BASE_URL}/reset", json={"task_id": tid})
            if reset_resp.status_code != 200:
                 # Try integer ID if string fails
                 reset_resp = requests.post(f"{BASE_URL}/reset", json={"task_id": int(tid)})
            
            if reset_resp.status_code == 200:
                print(f"    Reset successful for task {tid}")
                
                # Take an empty step to get a score
                step_resp = requests.post(f"{BASE_URL}/step", json={
                    "apply_labels": [], "remove_labels": [], "assign_to": [], "leave_comment": None, "submit_decision": True
                })
                step_data = step_resp.json()
                
                # OpenEnv 'Observation' contains 'reward' (score)
                score = step_data.get("reward")
                print(f"    Reward (Score) received: {score}")
                
                if score is not None:
                    # STRICT check: 0 < score < 1
                    if 0.0 < score < 1.0:
                        print(f"    ✅ PASS: Score {score} is strictly within (0, 1)")
                        passed_graders += 1
                    else:
                        print(f"    ❌ FAIL: Score {score} is OUT OF RANGE (must be strictly between 0 and 1)")
                else:
                    print("    ❌ FAIL: No reward found in observation")
            else:
                print(f"    ❌ FAIL: Could not reset task {tid} (HTTP {reset_resp.status_code})")
                
        except Exception as e:
            print(f"    ❌ FAIL: Error testing task {tid}: {e}")

    # Final Summary
    print("\n--- Summary ---")
    if passed_graders >= 3:
        print(f"✅ FOUND {passed_graders} VALID GRADERS. This submission should pass Step 2!")
    else:
        print(f"❌ ONLY FOUND {passed_graders} VALID GRADERS. It will fail the validator!")

if __name__ == "__main__":
    check_requirements()
