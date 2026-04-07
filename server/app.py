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

@app.get("/run-agent-stream")
async def run_agent_stream():
    """Streams evaluation logs via Server-Sent Events (SSE)."""
    from fastapi.responses import StreamingResponse
    try:
        from inference import run_full_evaluation_stream
        return StreamingResponse(run_full_evaluation_stream(), media_type="text/event-stream")
    except Exception as e:
        import traceback
        import json
        
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'data': str(e) + repr(traceback.format_exc())})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0d1117;
                --card-bg: #161b22;
                --accent: #58a6ff;
                --text: #c9d1d9;
                --subtext: #8b949e;
                --terminal-bg: #010409;
                --border: #30363d;
            }

            body {
                margin: 0; padding: 0; font-family: 'Inter', -apple-system, blinkmacsystemfont, sans-serif;
                background-color: var(--bg); color: var(--text); min-height: 100vh;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
            }

            .container {
                width: 90%; max-width: 1100px; background: var(--card-bg);
                border: 1px solid var(--border); border-radius: 12px;
                padding: 32px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                display: flex; flex-direction: column; gap: 24px;
            }

            .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
            h1 { font-weight: 600; font-size: 1.5rem; margin: 0; color: #fff; }
            
            .run-btn {
                background: var(--accent); color: #fff; border: none; padding: 10px 24px;
                font-size: 0.95rem; font-weight: 600; border-radius: 6px; cursor: pointer;
                transition: background 0.2s; display: flex; align-items: center; gap: 8px;
            }
            .run-btn:hover { background: #1f6feb; }
            .run-btn:disabled { background: #21262d; color: #8b949e; cursor: not-allowed; }

            .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
            .stat-box { 
                background: var(--bg); border: 1px solid var(--border); 
                padding: 16px; border-radius: 8px; text-align: center;
            }
            .stat-val { font-size: 1.5rem; font-weight: 600; color: #fff; display: block; margin-bottom: 4px; }
            .stat-label { font-size: 0.75rem; color: var(--subtext); text-transform: uppercase; font-weight: 600; }

            .terminal {
                background: var(--terminal-bg); border-radius: 8px; padding: 16px;
                height: 350px; overflow-y: auto; font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 0.8rem; line-height: 1.6; border: 1px solid var(--border);
            }
            .terminal-line { margin-bottom: 4px; color: #8b949e; border-left: 2px solid transparent; padding-left: 8px; }
            .line-start { color: #58a6ff; font-weight: 600; }
            .line-step { color: #f2cc60; }
            .line-end { color: #79c0ff; font-weight: 600; border-left-color: #58a6ff; }
            .line-error { color: #ff7b72; background: rgba(248,81,73,0.1); border-left-color: #ff7b72; }
            
            .links { display: flex; gap: 16px; font-size: 0.8rem; justify-content: center; }
            .links a { color: var(--accent); text-decoration: none; }
            .links a:hover { text-decoration: underline; }
            
            .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #238636; display: inline-block; margin-right: 6px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>Evaluation Console</h1>
                    <div style="font-size: 0.85rem; color: var(--subtext); margin-top: 4px;">
                        <span class="status-dot"></span> github_triage | environment ready
                    </div>
                </div>
                <button id="runBtn" class="run-btn" onclick="runAgent()">
                    Evaluate Environment
                </button>
            </div>
            
            <div class="stats-row">
                <div class="stat-box">
                    <span id="finalScore" class="stat-val">0.00</span>
                    <span class="stat-label">Avg Score</span>
                </div>
                <div class="stat-box">
                    <span id="episodesCount" class="stat-val">0/3</span>
                    <span class="stat-label">Progress</span>
                </div>
                <div class="stat-box">
                    <span id="successRate" class="stat-val">0%</span>
                    <span class="stat-label">Success</span>
                </div>
                <div class="stat-box">
                    <span id="envStatus" class="stat-val" style="font-size: 1rem;">IDLE</span>
                    <span class="stat-label">Status</span>
                </div>
            </div>

            <div id="terminal" class="terminal">
                <div class="terminal-line">$ System initialized. Ready for evaluation.</div>
            </div>

            <div class="links">
                <a href="/docs" target="_blank">docs</a>
                <a href="/health" target="_blank">health</a>
                <a href="/schema" target="_blank">schema</a>
            </div>
        </div>

        <script>
            let evtSource = null;

            function runAgent() {
                const btn = document.getElementById('runBtn');
                const term = document.getElementById('terminal');
                const envStatus = document.getElementById('envStatus');
                
                btn.disabled = true;
                envStatus.innerText = 'RUNNING';
                envStatus.style.color = '#f2cc60';
                
                term.innerHTML = '<div class="terminal-line" style="color: #58a6ff;">> Initializing Evaluation Stream...</div>';
                
                if(evtSource) evtSource.close();
                evtSource = new EventSource('/run-agent-stream');
                
                evtSource.onmessage = function(event) {
                    const payload = JSON.parse(event.data);
                    
                    if (payload.type === 'log') {
                        const line = payload.data;
                        const div = document.createElement('div');
                        div.className = 'terminal-line';
                        
                        if (line.includes('[START]')) div.className += ' line-start';
                        else if (line.includes('[STEP]')) div.className += ' line-step';
                        else if (line.includes('[END]')) {
                            div.className += ' line-end';
                        }
                        
                        div.innerText = line;
                        term.appendChild(div);
                        term.scrollTop = term.scrollHeight;
                    }
                    else if (payload.type === 'error') {
                        const div = document.createElement('div');
                        div.className = 'terminal-line line-error';
                        div.innerText = "[ERROR] " + payload.data;
                        term.appendChild(div);
                        envStatus.innerText = 'FAILED';
                        envStatus.style.color = '#ff7b72';
                        evtSource.close();
                        btn.disabled = false;
                    }
                    else if (payload.type === 'done') {
                        const data = payload.data;
                        document.getElementById('finalScore').innerText = data.average_score.toFixed(2);
                        document.getElementById('episodesCount').innerText = `${data.episodes.length}/3`;
                        
                        const successCount = data.episodes.filter(e => e.success).length;
                        const rate = Math.round((successCount / 3) * 100);
                        document.getElementById('successRate').innerText = `${rate}%`;
                        
                        envStatus.innerText = 'COMPLETE';
                        envStatus.style.color = '#238636';
                        evtSource.close();
                        btn.disabled = false;
                    }
                };

                evtSource.onerror = function() {
                    const div = document.createElement('div');
                    div.className = 'terminal-line line-error';
                    div.innerText = "[SYSTEM] Stream disconnected.";
                    term.appendChild(div);
                    evtSource.close();
                    btn.disabled = false;
                    envStatus.innerText = 'OFFLINE';
                };
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
