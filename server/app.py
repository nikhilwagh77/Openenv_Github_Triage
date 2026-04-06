# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Mygithubtriage Environment.

This module creates an HTTP server that exposes the MygithubtriageEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import MygithubtriageAction, MygithubtriageObservation
    from .mygithubtriage_environment import MygithubtriageEnvironment
except ImportError:
    from models import MygithubtriageAction, MygithubtriageObservation
    from server.mygithubtriage_environment import MygithubtriageEnvironment


# Create the app with web interface and README integration
app = create_app(
    MygithubtriageEnvironment,
    MygithubtriageAction,
    MygithubtriageObservation,
    env_name="mygithubtriage",
    max_concurrent_envs=1,
)

@app.post("/run-agent")
async def run_agent():
    """Triggers the AI agent to evaluate all 3 tasks."""
    try:
        from inference import run_full_evaluation
        # This will take several seconds as it calls the LLM for 3 episodes
        results = await run_full_evaluation()
        return results
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GitHub Triage | AI Agent Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0f172a;
                --card-bg: rgba(30, 41, 59, 0.7);
                --accent: #38bdf8;
                --text: #f1f5f9;
                --terminal-bg: #000000;
                --border: rgba(255, 255, 255, 0.1);
            }

            body {
                margin: 0; padding: 0; font-family: 'Inter', sans-serif;
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: var(--text); min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }

            .container {
                width: 90%; max-width: 900px;
                background: var(--card-bg); backdrop-filter: blur(20px);
                border: 1px solid var(--border); border-radius: 24px;
                padding: 40px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }

            .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; }
            h1 { font-weight: 800; font-size: 2.5rem; margin: 0; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            .run-btn {
                background: var(--accent); color: #0f172a; border: none; padding: 14px 28px;
                font-size: 1.1rem; font-weight: 700; border-radius: 12px; cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
            }
            .run-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(56, 189, 248, 0.5); }
            .run-btn:active { transform: scale(0.98); }
            .run-btn:disabled { background: #475569; cursor: wait; transform: none; box-shadow: none; }

            .terminal {
                background: var(--terminal-bg); border-radius: 16px; padding: 20px;
                height: 350px; overflow-y: auto; font-family: 'Fira Code', monospace;
                font-size: 0.9rem; line-height: 1.6; border: 1px solid var(--border);
                box-shadow: inset 0 2px 10px rgba(0,0,0,0.5); margin-top: 20px;
            }
            .terminal-line { margin-bottom: 4px; border-left: 3px solid transparent; padding-left: 10px; }
            .line-start { color: #10b981; border-color: #10b981; }
            .line-step { color: #f59e0b; border-color: #f59e0b; }
            .line-end { color: #38bdf8; border-color: #38bdf8; font-weight: bold; }
            .line-error { color: #ef4444; border-color: #ef4444; }

            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 30px; display: none; }
            .stat-card { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 20px; border-radius: 16px; text-align: center; }
            .stat-val { font-size: 2rem; font-weight: 800; color: var(--accent); display: block; }
            .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; }
            
            .links { text-align: center; margin-top: 30px; opacity: 0.6; font-size: 0.8rem; }
            .links a { color: var(--accent); text-decoration: none; margin: 0 10px; }
            .links a:hover { text-decoration: underline; }
            
            /* Animation */
            .pulse { animation: pulse 2s infinite; }
            @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>GitHub Triage Agent</h1>
                    <span style="font-size: 0.8rem; background: rgba(56, 189, 248, 0.2); color: var(--accent); padding: 4px 10px; border-radius: 20px; border: 1px solid var(--accent); margin-top: 5px; display: inline-block;">v1.0.0 • OpenEnv Verified ✅</span>
                </div>
                <button id="runBtn" class="run-btn" onclick="runAgent()">Run Full Evaluation</button>
            </div>
            
            <p style="opacity: 0.7; font-size: 1.1rem; line-height: 1.6;">
                Evaluate AI performance on 3 tasks (Easy, Medium, Hard). The agent will use the OpenAI API to triaging incoming issues, applying labels, and assigning teams.
            </p>

            <div id="terminal" class="terminal">
                <div class="terminal-line" style="color: #64748b;">Ready to begin evaluation. Click "Run" to start.</div>
            </div>

            <div id="stats" class="stats-grid">
                <div class="stat-card">
                    <span id="finalScore" class="stat-val">0.00</span>
                    <span class="stat-label">Average Score</span>
                </div>
                <div class="stat-card">
                    <span id="episodesCount" class="stat-val">0 / 3</span>
                    <span class="stat-label">Tasks Completed</span>
                </div>
                <div class="stat-card">
                    <span id="successRate" class="stat-val">0%</span>
                    <span class="stat-label">Success Rate</span>
                </div>
            </div>

            <div class="links">
                <a href="/docs">Swagger Docs</a> | <a href="/health">Health Check</a> | <a href="/schema">Spec Schema</a>
            </div>
        </div>

        <script>
            async function runAgent() {
                const btn = document.getElementById('runBtn');
                const term = document.getElementById('terminal');
                const stats = document.getElementById('stats');
                
                btn.disabled = true;
                btn.innerText = 'Evaluating...';
                term.innerHTML = '<div class="terminal-line pulse" style="color: var(--accent)">> Connecting to OpenAI and Environment...</div>';
                stats.style.display = 'none';

                try {
                    const response = await fetch('/run-agent', { method: 'POST' });
                    const result = await response.json();

                    if (result.error) throw new Error(result.error);

                    // Process Logs
                    term.innerHTML = '';
                    result.logs.split('\\n').forEach(line => {
                        const div = document.createElement('div');
                        div.className = 'terminal-line';
                        if (line.includes('[START]')) div.className += ' line-start';
                        else if (line.includes('[STEP]')) div.className += ' line-step';
                        else if (line.includes('[END]')) div.className += ' line-end';
                        div.innerText = line;
                        term.appendChild(div);
                    });
                    term.scrollTop = term.scrollHeight;

                    // Update Stats
                    document.getElementById('finalScore').innerText = result.average_score.toFixed(2);
                    const successCount = result.episodes.filter(e => e.success).length;
                    document.getElementById('episodesCount').innerText = `${result.episodes.length} / 3`;
                    document.getElementById('successRate').innerText = `${Math.round((successCount / 3) * 100)}%`;
                    
                    stats.style.display = 'grid';

                } catch (err) {
                    const div = document.createElement('div');
                    div.className = 'terminal-line line-error';
                    div.innerText = `[ERROR] ${err.message}`;
                    term.appendChild(div);
                } finally {
                    btn.disabled = false;
                    btn.innerText = 'Run Full Evaluation';
                }
            }
        </script>
    </body>
    </html>
    """)


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m mygithubtriage.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn mygithubtriage.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.port == 8000:
        main()
    else:
        main(port=args.port)
