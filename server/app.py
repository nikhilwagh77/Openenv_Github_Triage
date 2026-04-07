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
                --bg: #0f172a;
                --card-bg: rgba(30, 41, 59, 0.6);
                --accent: #38bdf8;
                --text: #f1f5f9;
                --terminal-bg: #030712;
                --border: rgba(255, 255, 255, 0.08);
            }

            body {
                margin: 0; padding: 0; font-family: 'Inter', sans-serif;
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: var(--text); min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }

            .container {
                width: 95%; max-width: 1000px;
                background: var(--card-bg); backdrop-filter: blur(25px);
                border: 1px solid var(--border); border-radius: 28px;
                padding: 40px; box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.6);
                position: relative; overflow: hidden;
            }
            
            .container::before {
                content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
                background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
            }

            .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; }
            h1 { font-weight: 800; font-size: 2.5rem; margin: 0; background: linear-gradient(to right, #e2e8f0, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            .run-btn {
                background: linear-gradient(135deg, #38bdf8, #818cf8); color: #fff; border: none; padding: 15px 32px;
                font-size: 1.1rem; font-weight: 700; border-radius: 14px; cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 10px 20px -5px rgba(56, 189, 248, 0.4);
                display: flex; align-items: center; gap: 8px;
            }
            .run-btn:hover { transform: translateY(-2px); box-shadow: 0 15px 25px -5px rgba(56, 189, 248, 0.5); }
            .run-btn:active { transform: scale(0.98); }
            .run-btn:disabled { background: #475569; color: #94a3b8; cursor: not-allowed; transform: none; box-shadow: none; }

            .terminal {
                background: var(--terminal-bg); border-radius: 18px; padding: 24px;
                height: 400px; overflow-y: auto; font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem; line-height: 1.7; border: 1px solid rgba(255,255,255,0.05);
                box-shadow: inset 0 5px 15px rgba(0,0,0,0.5); margin-top: 25px;
                position: relative; scroll-behavior: smooth;
            }
            
            .terminal::-webkit-scrollbar { width: 8px; }
            .terminal::-webkit-scrollbar-track { background: transparent; }
            .terminal::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
            
            .terminal-line { margin-bottom: 6px; padding-left: 12px; border-left: 3px solid transparent; animation: slideIn 0.3s ease-out; opacity: 0.9; }
            @keyframes slideIn { from { opacity: 0; transform: translateX(-5px); } to { opacity: 0.9; transform: translateX(0); } }
            
            .line-start { color: #34d399; border-color: #34d399; font-weight: bold; }
            .line-step { color: #fbbf24; border-color: transparent; }
            .line-action { color: #f87171; }
            .line-end { color: #818cf8; border-color: #818cf8; font-weight: bold; margin-top: 10px; }
            .line-error { color: #ef4444; border-color: #ef4444; background: rgba(239,68,68,0.1); padding: 5px 12px; }

            .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px; }
            .stat-card { 
                background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border); 
                padding: 24px; border-radius: 20px; text-align: center;
                transition: transform 0.3s ease, border-color 0.3s ease;
            }
            .stat-card:hover { transform: translateY(-5px); border-color: rgba(56, 189, 248, 0.3); }
            
            .stat-val { font-size: 2.5rem; font-weight: 800; color: var(--text); display: block; margin-bottom: 5px; }
            .stat-val span { font-size: 1.2rem; color: #64748b; font-weight: 600; }
            .stat-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; font-weight: 600; }
            
            .links { text-align: center; margin-top: 35px; font-size: 0.85rem; font-weight: 500; }
            .links a { color: #64748b; text-decoration: none; margin: 0 15px; transition: color 0.2s; }
            .links a:hover { color: var(--accent); }
            
            .pulse-dot {
                width: 10px; height: 10px; background: #10b981; border-radius: 50%;
                display: inline-block; margin-right: 10px; box-shadow: 0 0 10px #10b981;
            }
            .anim-pulse { animation: pulseAnim 2s infinite; }
            @keyframes pulseAnim { 0% { opacity: 0.4; transform: scale(0.95); } 50% { opacity: 1; transform: scale(1); } 100% { opacity: 0.4; transform: scale(0.95); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>GitHub Triage AI</h1>
                    <div style="display: flex; align-items: center; gap: 10px; margin-top: 8px;">
                        <span style="font-size: 0.75rem; background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 4px 12px; border-radius: 20px; font-weight: 600; letter-spacing: 0.5px;">v1.0.0</span>
                        <span style="font-size: 0.75rem; color: #64748b; display: flex; align-items: center;"><div class="pulse-dot"></div> System Ready</span>
                    </div>
                </div>
                <button id="runBtn" class="run-btn" onclick="runAgent()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    Start Real-time Eval
                </button>
            </div>
            
            <p style="color: #94a3b8; font-size: 1.05rem; line-height: 1.6; max-width: 800px; margin-bottom: 25px;">
                Evaluate model performance across 3 triage complexities (Easy, Medium, Hard). The agent uses dynamic reasoning to assign labels and teams.
            </p>

            <div class="stats-grid">
                <div class="stat-card">
                    <span id="finalScore" class="stat-val">0.00</span>
                    <span class="stat-label">Avg. Score</span>
                </div>
                <div class="stat-card">
                    <span id="episodesCount" class="stat-val">0<span>/3</span></span>
                    <span class="stat-label">Tasks Done</span>
                </div>
                <div class="stat-card">
                    <span id="successRate" class="stat-val">0%</span>
                    <span class="stat-label">Success Rate</span>
                </div>
            </div>

            <div id="terminal" class="terminal">
                <div class="terminal-line" style="color: #475569;">$ Waiting for evaluation trigger...</div>
            </div>

            <div class="links">
                <a href="/docs">API Reference</a> <a href="/health">Health Check</a> <a href="/schema">Schema Definition</a>
            </div>
        </div>

        <script>
            let evtSource = null;

            function updateStats(data) {
                document.getElementById('finalScore').innerText = data.average_score.toFixed(2);
                
                const successCount = data.episodes.filter(e => e.success).length;
                const totalCount = data.episodes.length;
                
                document.getElementById('episodesCount').innerHTML = `${totalCount}<span>/3</span>`;
                
                let rate = totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;
                document.getElementById('successRate').innerText = `${rate}%`;
                
                // Color formatting
                document.getElementById('finalScore').style.color = data.average_score >= 0.8 ? '#10b981' : (data.average_score > 0 ? '#fbbf24' : '#f87171');
            }

            function runAgent() {
                const btn = document.getElementById('runBtn');
                const term = document.getElementById('terminal');
                
                // Reset UI
                btn.disabled = true;
                btn.innerHTML = '<div class="pulse-dot" style="background:#fff; box-shadow:none;"></div> Evaluating...';
                term.innerHTML = '<div class="terminal-line anim-pulse" style="color: var(--accent);">> Initializing Stream via SSE...</div>';
                
                document.getElementById('finalScore').innerText = '0.00';
                document.getElementById('finalScore').style.color = 'var(--text)';
                document.getElementById('episodesCount').innerHTML = '0<span>/3</span>';
                document.getElementById('successRate').innerText = '0%';

                if(evtSource) evtSource.close();
                
                // Use EventSource for real-time streaming
                evtSource = new EventSource('/run-agent-stream');
                
                evtSource.onmessage = function(event) {
                    const payload = JSON.parse(event.data);
                    
                    if (payload.type === 'log') {
                        const line = payload.data;
                        const div = document.createElement('div');
                        div.className = 'terminal-line';
                        
                        if (line.includes('[START]')) div.className += ' line-start';
                        else if (line.includes('[STEP]')) div.className += ' line-step';
                        else if (line.includes('Action:')) div.className += ' line-action';
                        else if (line.includes('[END]')) div.className += ' line-end';
                        
                        div.innerText = line;
                        term.appendChild(div);
                        term.scrollTop = term.scrollHeight; // auto scroll
                    }
                    else if (payload.type === 'error') {
                        const div = document.createElement('div');
                        div.className = 'terminal-line line-error';
                        div.innerText = "[ERROR] " + payload.data;
                        term.appendChild(div);
                        evtSource.close();
                        resetBtn();
                    }
                    else if (payload.type === 'done') {
                        updateStats(payload.data);
                        term.innerHTML += '<div class="terminal-line line-end">> Evaluation Complete. Connection closed.</div>';
                        term.scrollTop = term.scrollHeight;
                        evtSource.close();
                        resetBtn();
                    }
                };

                evtSource.onerror = function() {
                    const div = document.createElement('div');
                    div.className = 'terminal-line line-error';
                    div.innerText = "[SYSTEM] Connection to server lost.";
                    term.appendChild(div);
                    evtSource.close();
                    resetBtn();
                };
                
                function resetBtn() {
                    btn.disabled = false;
                    btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Real-time Eval';
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
