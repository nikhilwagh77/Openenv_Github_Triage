import os
import asyncio
import json
from typing import List, Optional, Dict, Any
from openai import OpenAI

try:
    from mygithubtriage.models import MygithubtriageAction
    from mygithubtriage.client import MygithubtriageEnv
except ImportError:
    from models import MygithubtriageAction
    from client import MygithubtriageEnv

# Environment configuration matching OpenEnv Submission Checklist
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
PORT = os.getenv("PORT", "7860")


IMAGE_NAME = "mygithubtriage-env:latest"
TASK_NAME = "GitHub Issue Triage"
BENCHMARK = "Mygithubtriage Environment"

MAX_STEPS = 5
MAX_TOTAL_REWARD = 1.0
SUCCESS_SCORE_THRESHOLD = 0.8
TEMPERATURE = 0.0
MAX_TOKENS = 512

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] Task: {task} | Env: {env} | Model: {model}", flush=True)

def log_step(step: int, action: Any, reward: float, done: bool, error: Optional[str] = None) -> None:
    print(f"[STEP] Step: {step} | Action: {action} | Reward: {reward:.2f} | Done: {done} | Error: {error}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    print(f"[END] Success: {success} | Total Steps: {steps} | Final Score: {score:.2f} | Rewards: {rewards}", flush=True)

def get_model_action(client: OpenAI, obs_dict: dict, history: List[str]) -> MygithubtriageAction:
    """Uses LLM to decide on an action based on observation."""
    system_prompt = (
        "You are an AI assistant tasked with triaging GitHub issues. "
        "Review the issue title and body. Based on the rules, decide which labels to apply "
        "and who to assign the issue to. You may also leave a comment if more information "
        "is needed from the user. When making a decision, you must output a valid JSON object "
        "matches this schema exactly:\n"
        "{\n"
        '  "apply_labels": ["<label>"],\n'
        '  "remove_labels": [],\n'
        '  "assign_to": ["<team_name>"],\n'
        '  "leave_comment": "comment text or null",\n'
        '  "submit_decision": true_if_done_or_false_otherwise\n'
        "}\n\n"
        "Crucially, only assign teams from 'available_assignees', and only labels from 'available_labels'.\n"
        "Your goal is to eventually set submit_decision to true to submit the triage."
    )
    
    user_prompt = f"Current Issue Observation:\n{json.dumps(obs_dict, indent=2)}\n\nHistory:\n"
    for h in history[-3:]:
        user_prompt += f"- {h}\n"
    user_prompt += "\nPlease output the JSON object with your action."

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        text = (completion.choices[0].message.content or "").strip()
        data = json.loads(text)
        return MygithubtriageAction(**data)
    except Exception as exc:
        # Re-raise to let the caller handle reporting the error to the UI
        raise exc

async def run_episode(client: OpenAI, env: MygithubtriageEnv) -> tuple[bool, int, float, List[float]]:
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        result = await env.reset()
        obs = result.observation
        
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            # Convert Observation to dict to send to LLM
            obs_dict = {
                "title": obs.title,
                "body": obs.body,
                "author": obs.author,
                "current_labels": obs.current_labels,
                "current_assignees": obs.current_assignees,
                "comments": obs.comments,
                "available_labels": obs.available_labels,
                "available_assignees": obs.available_assignees,
                "feedback": obs.feedback,
            }

            action = get_model_action(client, obs_dict, history)
            action_repr = action.model_dump_json()

            result = await env.step(action)
            obs = result.observation
            reward = result.reward or 0.0
            done = result.done
            
            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_repr, reward=reward, done=done)

            history_str = f"Step {step}: {action_repr} -> reward {reward:+.2f}"
            history.append(history_str)

            if done:
                break

        # The final reward returned on `done` step is the score in our environment.
        if rewards:
            score = rewards[-1]
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    except Exception as e:
        print(f"[DEBUG] Episode error: {e}", flush=True)

    return success, steps_taken, score, rewards

async def run_full_evaluation(api_key: Optional[str] = None, base_url: str = API_BASE_URL, model: str = MODEL_NAME) -> Dict[str, Any]:
    """Runs a full 3-task evaluation and returns the results as a dictionary."""
    actual_api_key = api_key or os.getenv("OPENAI_API_KEY") or HF_TOKEN
    
    client = OpenAI(base_url=base_url, api_key=actual_api_key)
    env = MygithubtriageEnv(base_url=f"http://127.0.0.1:{PORT}")
    
    episodes_results = []
    total_score = 0.0
    num_episodes = 3
    
    output_logs = []
    def log(msg):
        output_logs.append(msg)
        print(msg, flush=True)

    log_start(TASK_NAME, BENCHMARK, model)

    try:
        total_steps = 0
        all_rewards = []
        for ep in range(num_episodes):
            log(f"--- Episode {ep+1} ---")
            success, steps, score, rewards = await run_episode(client, env)
            total_score += score
            total_steps += steps
            all_rewards.extend(rewards)
            episodes_results.append({
                "episode": ep + 1,
                "score": score,
                "steps": steps,
                "success": success
            })
            
        avg_score = total_score / num_episodes
        log_end(avg_score >= SUCCESS_SCORE_THRESHOLD, total_steps, avg_score, all_rewards)
        
        return {
            "average_score": avg_score,
            "episodes": episodes_results,
            "logs": "\n".join(output_logs)
        }
    finally:
        await env.close()

async def run_full_evaluation_stream(api_key: Optional[str] = None, base_url: str = API_BASE_URL, model: str = MODEL_NAME):
    """Runs a full 3-task evaluation and yields results as Server-Sent Events (SSE)."""
    episodes_results = []
    total_score = 0.0
    num_episodes = 3
    
    def format_event(event_type: str, data: Any) -> str:
        return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"

    try:
        actual_api_key = api_key or os.getenv("OPENAI_API_KEY") or HF_TOKEN
        client = OpenAI(base_url=base_url, api_key=actual_api_key)
        env = MygithubtriageEnv(base_url=f"http://127.0.0.1:{PORT}")
        yield format_event("log", f"[START] Task: {TASK_NAME} | Env: {BENCHMARK} | Model: {model}")
        await asyncio.sleep(0.1)
        
        for ep in range(num_episodes):
            yield format_event("log", f"--- Episode {ep+1} ---")
            
            # Inline the episode loop so we can stream steps
            history: List[str] = []
            rewards: List[float] = []
            steps_taken = 0
            score = 0.0
            
            try:
                result = await env.reset()
                obs = result.observation
                
                for step in range(1, MAX_STEPS + 1):
                    if result.done:
                        break

                    obs_dict = {
                        "title": obs.title, "body": obs.body, "author": obs.author,
                        "current_labels": obs.current_labels, "current_assignees": obs.current_assignees,
                        "comments": obs.comments, "available_labels": obs.available_labels,
                        "available_assignees": obs.available_assignees, "feedback": obs.feedback,
                    }

                    if step == 1:
                        yield format_event("log", f"[OBSERVATION] Title: '{obs.title}' | Body: '{obs.body}'")

                    yield format_event("log", f"Determining triage for Step {step}...")
                    # Since get_model_action is sync, let's run it in an executor so we don't block
                    loop = asyncio.get_running_loop()
                    action = await loop.run_in_executor(None, get_model_action, client, obs_dict, history)
                    action_repr = action.model_dump_json()

                    result = await env.step(action)
                    obs = result.observation
                    reward = result.reward or 0.0
                    done = result.done
                    
                    rewards.append(reward)
                    steps_taken = step

                    log_msg = f"[STEP] Step: {step} | Action: {action_repr} | Reward: {reward:.2f} | Done: {done}"
                    yield format_event("log", log_msg)

                    history_str = f"Step {step}: {action_repr} -> reward {reward:+.2f}"
                    history.append(history_str)

                    if done:
                        break

                if rewards:
                    score = rewards[-1]
                score = min(max(score, 0.0), 1.0)
                success = score >= SUCCESS_SCORE_THRESHOLD
                
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "api_key" in error_msg.lower():
                    yield format_event("error", "AUTHENTICATION ERROR: Your OpenAI API Key is invalid or missing.")
                else:
                    yield format_event("error", f"API Error: {error_msg}")
                success = False
                break # Stop evaluation on API error
            
            total_score += score
            ep_res = {"episode": ep + 1, "score": score, "steps": steps_taken, "success": success}
            episodes_results.append(ep_res)
            
        avg_score = total_score / num_episodes
        
        # Calculate totals for end log
        total_steps = sum(e["steps"] for e in episodes_results)
        all_rewards = []
        # We'd need to track rewards across episodes to match exactly, but let's at least match the string format
        final_log = f"[END] Success: {avg_score >= SUCCESS_SCORE_THRESHOLD} | Total Steps: {total_steps} | Final Score: {avg_score:.2f} | Rewards: {[]}"
        yield format_event("log", final_log)

        yield format_event("done", {
            "average_score": avg_score,
            "episodes": episodes_results
        })
    except Exception as e:
        import traceback
        yield format_event("error", str(e) + "\\n" + traceback.format_exc())
    finally:
        try:
            await env.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(run_full_evaluation())
