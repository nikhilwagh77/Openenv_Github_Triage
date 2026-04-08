# Copyright (c) 2026 OpenEnv Contributors.
# FastAPI application for the Mygithubtriage Environment.

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from typing import List, Optional
import sys
import os
import json
import traceback

try:
    from openenv.core.env_server.http_server import create_app
except ImportError:
    raise ImportError("openenv is required. Install with 'uv sync'")

try:
    from ..models import MygithubtriageAction, MygithubtriageObservation
    from .mygithubtriage_environment import MygithubtriageEnvironment, TASKS_LIST
except ImportError:
    from models import MygithubtriageAction, MygithubtriageObservation
    from server.mygithubtriage_environment import MygithubtriageEnvironment, TASKS_LIST

# Create the app
app = create_app(
    MygithubtriageEnvironment,
    MygithubtriageAction,
    MygithubtriageObservation,
    env_name="mygithubtriage",
    max_concurrent_envs=1,
)

@app.get("/tasks")
async def get_tasks():
    """Returns metadata for all available triage tasks."""
    return JSONResponse(content=[t for t in TASKS_LIST])

@app.get("/run-agent-stream")
async def run_agent_stream(ids: Optional[str] = Query(None)):
    """Streams evaluation logs via SSE. Supports selective IDs."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    task_ids = [int(i) for i in ids.split(",")] if ids else None

    try:
        from inference import run_full_evaluation_stream
        return StreamingResponse(
            run_full_evaluation_stream(task_ids=task_ids), 
            media_type="text/event-stream"
        )
    except Exception as e:
        error_msg = str(e) + "\n" + traceback.format_exc()
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'data': error_msg})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")



@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GitHub Triage | AI Simulation</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #0366d6;
                --primary-hover: #0056b3;
                --bg: #f6f8fa;
                --card-bg: #ffffff;
                --text: #24292e;
                --text-muted: #586069;
                --border: #e1e4e8;
                --success: #28a745;
                --error: #d73a49;
                --warning: #f1e05a;
            }

            body {
                margin: 0; padding: 0; font-family: 'Inter', sans-serif;
                background-color: var(--bg); color: var(--text);
                line-height: 1.5;
            }

            header {
                background: #fff; border-bottom: 1px solid var(--border);
                padding: 1rem 2rem; display: flex; align-items: center; justify-content: space-between;
                position: sticky; top: 0; z-index: 100;
            }

            .logo { font-weight: 700; font-size: 1.25rem; color: var(--primary); display: flex; align-items: center; gap: 8px; }
            
            .main-layout {
                display: grid; grid-template-columns: 320px 1fr;
                gap: 2rem; padding: 2rem; max-width: 1440px; margin: 0 auto;
                align-items: start;
            }

            .sidebar { 
                display: flex; flex-direction: column; gap: 1.5rem; 
                position: sticky; top: 80px;
                height: calc(100vh - 100px);
                overflow: hidden;
            }

            main { min-height: 400px; }

            .card {
                background: var(--card-bg); border: 1px solid var(--border);
                border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            }

            .card h2 { font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 1rem; margin-top: 0; }

            .env-info { padding: 1rem; }
            .env-info h2 { margin-bottom: 0.5rem; }
            .env-info p, .env-info ul { font-size: 0.75rem; margin-bottom: 0.25rem; }
            .env-info ul { padding-left: 1rem; }

            .task-card { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; }
            .task-list { flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
            .task-item {
                display: flex; align-items: center; gap: 10px; padding: 8px;
                border-radius: 6px; border: 1px solid transparent; transition: all 0.2s;
                cursor: pointer;
            }
            .task-item:hover { background: #f1f8ff; border-color: var(--primary); }
            .task-item input { margin: 0; cursor: pointer; }
            .task-item label { font-size: 0.85rem; cursor: pointer; flex-grow: 1; }
            
            .badge {
                font-size: 0.7rem; padding: 2px 6px; border-radius: 10px; font-weight: 600; text-transform: uppercase;
            }
            .badge-easy { background: #dafbe1; color: #1a7f37; }
            .badge-medium { background: #fff8c5; color: #8a630d; }
            .badge-hard { background: #ffebe9; color: #cf222e; }

            .controls { display: flex; flex-direction: column; gap: 10px; margin-top: 1rem; }
            .btn {
                background: var(--primary); color: #fff; border: none; padding: 10px;
                border-radius: 6px; font-weight: 600; cursor: pointer; transition: background 0.2s;
                font-size: 0.9rem; text-align: center; text-decoration: none;
            }
            .btn:hover { background: var(--primary-hover); }
            .btn:disabled { background: #959da5; cursor: not-allowed; }
            .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
            .btn-outline:hover { background: #f6f8fa; }

            .stats-bar {
                display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;
            }
            .stat-card { text-align: center; }
            .stat-val { font-size: 1.25rem; font-weight: 700; display: block; }
            .stat-lbl { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; }

            .feed { display: flex; flex-direction: column; gap: 1.5rem; }
            .episode-card {
                border: 1px solid var(--border); border-radius: 8px; background: #fff; overflow: hidden;
                transition: transform 0.2s; display: none;
            }
            .episode-header {
                background: #f6f8fa; padding: 12px 20px; border-bottom: 1px solid var(--border);
                display: flex; align-items: center; justify-content: space-between;
            }
            .episode-body { padding: 20px; }
            
            .task-box { background: #fdfdfd; border: 1px dashed var(--border); border-radius: 6px; padding: 15px; margin-bottom: 15px; }
            .task-box h3 { margin: 0 0 8px 0; font-size: 1rem; color: var(--primary); }
            .task-box p { margin: 0; font-size: 0.9rem; color: var(--text-muted); font-style: italic; }

            .timeline { display: flex; flex-direction: column; gap: 10px; border-left: 2px solid var(--bg); padding-left: 20px; margin-left: 10px; }
            .step-entry { position: relative; font-size: 0.85rem; padding: 8px 0; }
            .step-entry::before {
                content: ''; position: absolute; left: -26px; top: 12px;
                width: 10px; height: 10px; border-radius: 50%; background: var(--primary);
            }
            .action-tag { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #fff; padding: 2px 6px; border-radius: 4px; margin-right: 6px; }
            .tag-label { background: #6f42c1; }
            .tag-assign { background: #d73a49; }
            .tag-comment { background: #28a745; }
            .tag-reward { font-weight: 700; color: var(--primary); background: #f1f8ff; border: 1px solid var(--primary); border-radius: 4px; padding: 1px 5px; }

            .result-banner {
                margin-top: 15px; padding: 10px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 0.9rem;
            }
            .banner-success { background: #dafbe1; color: #1a7f37; border: 1px solid #1a7f37; }
            .banner-fail { background: #ffebe9; color: #cf222e; border: 1px solid #cf222e; }

            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #d1d5da; border-radius: 10px; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
                GitHub Triage AI
            </div>
            <div style="display: flex; gap: 20px;">
                <a href="/docs" target="_blank" class="btn btn-outline" style="padding: 6px 15px; font-size: 0.8rem;">API Docs</a>
                <a href="https://github.com/nikhilwagh77/Openenv_Github_Triage" target="_blank" class="btn btn-outline" style="padding: 6px 15px; font-size: 0.8rem;">Repository</a>
            </div>
        </header>

        <div class="main-layout">
            <aside class="sidebar">
                <div class="card env-info">
                    <h2>Environment</h2>
                    <p><strong>OpenEnv Simulation</strong></p>
                    <p>An interactive RL environment for GitHub issue management.</p>
                    <ul>
                        <li>Action Space: Labels, Assignees, Comments</li>
                        <li>Reward: +0.1 per correct action, -0.05 per error</li>
                        <li>Target: Perfect triage state (Score 1.0)</li>
                    </ul>
                </div>

                <div class="card task-card">
                    <h2>Select Tasks</h2>
                    <div id="taskList" class="task-list">
                        <p style="font-size: 0.8rem; color: var(--text-muted);">Loading tasks...</p>
                    </div>
                    <div class="controls">
                        <button id="toggleBtn" class="btn btn-outline" onclick="toggleAll()" style="font-size: 0.75rem;">Select All</button>
                        <button id="evaluateBtn" class="btn" onclick="startEvaluation()">Run Evaluation</button>
                    </div>
                </div>
            </aside>

            <main>
                <div class="card stats-bar">
                    <div class="stat-card">
                        <span id="avgScore" class="stat-val">0.00</span>
                        <span class="stat-lbl">Avg Score</span>
                    </div>
                    <div class="stat-card">
                        <span id="successRate" class="stat-val">0%</span>
                        <span class="stat-lbl">Success Rate</span>
                    </div>
                    <div class="stat-card">
                        <span id="progressText" class="stat-val">0/0</span>
                        <span class="stat-lbl">Completed</span>
                    </div>
                    <div class="stat-card">
                        <span id="statusText" class="stat-val" style="color: var(--text-muted); font-size: 1rem;">IDLE</span>
                        <span class="stat-lbl">System Status</span>
                    </div>
                </div>

                <div id="feed" class="feed">
                    <div id="emptyState" style="text-align: center; padding: 4rem; color: var(--text-muted); background: #fff; border: 1px dashed var(--border); border-radius: 8px;">
                        Select tasks and click "Run Evaluation" to start the simulation.
                    </div>
                </div>
            </main>
        </div>

        <script>
            let tasks = [];
            let evtSource = null;

            async function loadTasks() {
                const res = await fetch('/tasks');
                tasks = await res.json();
                const list = document.getElementById('taskList');
                list.innerHTML = tasks.map(t => `
                    <div class="task-item">
                        <input type="checkbox" id="task-${t.id}" value="${t.id}" checked>
                        <label for="task-${t.id}">${t.title}</label>
                        <span class="badge badge-${t.difficulty}">${t.difficulty}</span>
                    </div>
                `).join('');
            }

            function toggleAll() {
                const checkedCount = tasks.filter(t => document.getElementById(`task-${t.id}`).checked).length;
                const shouldCheck = checkedCount < tasks.length;
                
                tasks.forEach(t => {
                    document.getElementById(`task-${t.id}`).checked = shouldCheck;
                });
                
                document.getElementById('toggleBtn').innerText = shouldCheck ? 'Deselect All' : 'Select All';
            }

            function startEvaluation() {
                const selected = tasks.filter(t => document.getElementById(`task-${t.id}`).checked).map(t => t.id);
                if (selected.length === 0) return alert('Please select at least one task.');

                const feed = document.getElementById('feed');
                const btn = document.getElementById('evaluateBtn');
                const status = document.getElementById('statusText');
                
                document.getElementById('emptyState').style.display = 'none';
                feed.querySelectorAll('.episode-card').forEach(e => e.remove());
                
                btn.disabled = true;
                status.innerText = 'RUNNING';
                status.style.color = 'var(--primary)';

                if (evtSource) evtSource.close();
                evtSource = new EventSource('/run-agent-stream?ids=' + selected.join(','));

                let currentEpisodeCard = null;
                let currentTimeline = null;

                evtSource.onmessage = (event) => {
                    const payload = JSON.parse(event.data);
                    
                    if (payload.type === 'log') {
                        const msg = payload.data;
                        
                        if (msg.startsWith('--- Episode')) {
                            // Extract episode info
                            const match = msg.match(/Episode (\d+) \(Task ID: (\d+)\)/);
                            const epNum = match ? match[1] : '?';
                            const taskId = match ? match[2] : '?';
                            const task = tasks.find(t => t.id == taskId) || { title: 'Unknown Task', difficulty: 'medium' };

                            const card = document.createElement('div');
                            card.className = 'episode-card';
                            card.style.display = 'block';
                            card.innerHTML = `
                                <div class="episode-header">
                                    <span style="font-weight: 700;">Episode ${epNum}</span>
                                    <span class="badge badge-${task.difficulty}">${task.difficulty}</span>
                                </div>
                                <div class="episode-body">
                                    <div class="task-box">
                                        <h3>${task.title}</h3>
                                        <p id="body-${epNum}">Initializing...</p>
                                    </div>
                                    <div class="timeline" id="timeline-${epNum}"></div>
                                    <div id="result-${epNum}"></div>
                                </div>
                            `;
                            feed.appendChild(card);
                            currentEpisodeCard = card;
                            currentTimeline = document.getElementById(`timeline-${epNum}`);
                        } 
                        else if (msg.startsWith('[OBSERVATION] Body:')) {
                            const bodyText = msg.replace('[OBSERVATION] Body: ', '').replace(/'/g, '');
                            const bodyEl = currentEpisodeCard.querySelector('p[id^="body-"]');
                            if (bodyEl) bodyEl.innerText = bodyText;
                        }
                        else if (msg.startsWith('[STEP]')) {
                            // Parse: [STEP] step=1 action={"..."} reward=+0.10 done=false
                            const match = msg.match(/step=(\d+) action=(.*) reward=(.*) done=(.*)/);
                            if (match) {
                                const step = match[1];
                                const action = JSON.parse(match[2]);
                                const reward = match[3];
                                
                                const entry = document.createElement('div');
                                entry.className = 'step-entry';
                                
                                let actionsHtml = '';
                                if (action.apply_labels.length) actionsHtml += `<span class="action-tag tag-label">LABEL: ${action.apply_labels.join(', ')}</span>`;
                                if (action.assign_to.length) actionsHtml += `<span class="action-tag tag-assign">ASSIGN: ${action.assign_to.join(', ')}</span>`;
                                if (action.leave_comment) actionsHtml += `<span class="action-tag tag-comment">COMMENT: ${action.leave_comment}</span>`;
                                
                                entry.innerHTML = `
                                    <div>${actionsHtml} <span class="tag-reward">${reward}</span></div>
                                `;
                                currentTimeline.appendChild(entry);
                            }
                        }
                    } 
                    else if (payload.type === 'done') {
                        const data = payload.data;
                        document.getElementById('avgScore').innerText = data.average_score.toFixed(2);
                        document.getElementById('progressText').innerText = `${data.episodes.length}/${selected.length}`;
                        
                        const successCount = data.episodes.filter(e => e.success).length;
                        const rate = Math.round((successCount / selected.length) * 100);
                        document.getElementById('successRate').innerText = `${rate}%`;

                        // Add success/fail banners to each episode
                        data.episodes.forEach(ep => {
                            const resDiv = document.getElementById(`result-${ep.episode}`);
                            if (resDiv) {
                                resDiv.className = 'result-banner ' + (ep.success ? 'banner-success' : 'banner-fail');
                                let text = ep.success ? 'SUCCESS' : 'FAILED';
                                text += ' (Score: ' + ep.score.toFixed(2) + ')';
                                if (!ep.success && ep.error) {
                                    text += ' - ' + ep.error;
                                }
                                resDiv.innerText = text;
                            }
                        });

                        status.innerText = 'COMPLETE';
                        status.style.color = 'var(--success)';
                        btn.disabled = false;
                        evtSource.close();
                    }
                };

                evtSource.onerror = () => {
                    status.innerText = 'ERROR';
                    status.style.color = 'var(--error)';
                    btn.disabled = false;
                    evtSource.close();
                };
            }

            loadTasks();
        </script>
    </body>
    </html>
    """)

def main():
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
