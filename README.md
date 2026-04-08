---
title: GitHub Triage OpenEnv
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# GitHub Triage | OpenEnv Environment

A high-fidelity simulation environment for training and evaluating AI agents on GitHub Issue Triage tasks. Built on the **OpenEnv** specification .

## 🚀 The Problem
Open-source maintainers are often overwhelmed by the volume of incoming issues. Manual triaging—labeling, assigning to teams, and requesting missing information—is a significant bottleneck. **GitHub Triage Lite** provides a sandbox to develop AI agents that can automate this process with human-like precision.

## 🛠️ How It Works
The environment simulates a repository with 15 distinct, real-world issue scenarios (Bugs, Features, Security, Documentation). 

### The Interaction Loop:
1.  **Observation**: The agent receives the issue title, body, author, and current repo state.
2.  **Action**: The agent can:
    -   `apply_labels`: Categorize the issue (e.g., `bug`, `security`).
    -   `assign_to`: Direct the issue to the right team (e.g., `frontend-team`).
    -   `leave_comment`: Request more details or explain reasoning.
3.  **Reward**: The agent is graded on accuracy. 
    -   `+0.1` for correct labels/assignments.
    -   `-0.05` for incorrect or extra labels.
    -   Target Score: `0.8` or higher for a "Success" state.

## 💻 Local Setup

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Recommended for dependency management)
- OpenAI API Key or other LLM

### Installation
1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    cd github_triage
    ```
2.  Install dependencies:
    ```bash
    uv sync
    ```
3.  Set your environment variables:
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    export MODEL_NAME="gpt-4o"
    ```

### Running the Environment
Start the FastAPI server and the Lite Dashboard:
```bash
uv run server
```
Visit `http://localhost:7860` to interact with the dashboard and run evaluations.

### Evaluation
To run the agent evaluation script:
```bash
uv run python inference.py
```

-   **OpenEnv Specification**: Confirmed via `validate-submission.sh`.
-   **Custom Logic**: Programmatic grading with dense rewards.