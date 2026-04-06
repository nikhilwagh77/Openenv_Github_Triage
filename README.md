---
title: GitHub Issue Triage Environment
emoji: ⌨️
colorFrom: indigo
colorTo: red
sdk: docker
pinned: false
tags:
  - openenv
---

# 🛡️ GitHub Issue Triage Environment

A real-world OpenEnv simulation for evaluating LLM agents on developer triage tasks. 

## 💡 Environment Description and Motivation
**Motivation**: Maintaining large open-source repositories is a complex, multi-modal task. Most AI benchmarks test isolated coding bugs but ignore the "human" and "organizational" side of development—triaging. We built this environment to test an agent's ability to act as a **Repository Maintainer**, requiring not just technical knowledge, but decision-making and communication skills.

In this environment, an agent reviews incoming issues and must decide the correct labels, the appropriate team to assign, and whether to ask the user for more information.

---

## 🏗️ Action and Observation Spaces

### **Action Space (`MygithubtriageAction`)**
The agent interacts with the environment through the following typed actions:
- `apply_labels` (List[str]): Add specific labels (bug, ui, performance, backend, needs-info, enhancement).
- `remove_labels` (List[str]): Remove labels if they were incorrectly applied.
- `assign_to` (List[str]): Route the issue to the correct team (database-team, frontend-team, backend-team).
- `leave_comment` (str): Provide textual feedback or request more info from the author.
- `submit_decision` (bool): Set to `True` when triage is finished to trigger the grader.

### **Observation Space (`MygithubtriageObservation`)**
The agent receives the following state updates:
- **Issue Details**: `title`, `body`, `author`, `issue_id`.
- **Current State**: `current_labels`, `current_assignees`, `comments`.
- **Environment Metadata**: `available_labels`, `available_assignees`, `task_difficulty`.
- **Immediate Feedback**: `feedback` string describing the result of the last action taken.

---

## 🎯 Task Scenarios & Difficulty

The environment provides a sequential 3-task suite for evaluation:

| Task ID | Scenario | Difficulty | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **1** | Missing Login Button | **Easy** | Add labels: ["bug", "ui"] |
| **2** | Database Timeout | **Medium** | Add labels: ["performance", "backend"], Assign: ["database-team"] |
| **3** | Vague "It crashed" | **Hard** | Add label: ["needs-info"], Leave a comment requesting logs. |

---

## 🕹️ Setup and Usage

### **Local Deployment**
1.  **Sync**: `uv sync`
2.  **Validate**: `openenv validate`
3.  **Run Locally**: `uv run server`
4.  **Test**: `uv run python inference.py`

### **Hugging Face Deployment**
- Select **Docker SDK** and push this repository.
- Ensure your `OPENAI_API_KEY` is added under **Settings -> Secrets**.

---

## 📊 Baseline Scores (GPT-4o-mini)

| Metric | Score | Note |
| :--- | :--- | :--- |
| **Avg. Reward (0.0-1.0)** | **0.87** | Average score across all tasks when funded. |
| **Success Rate** | **100%** | When provided with clear decision criteria. |

*(Note: If no credits are provided, the baseline score will default to 0.0 due to API quota errors.)*

---

## 🔐 OpenEnv Specification
This environment is fully compliant with the **OpenEnv v1** specification and can be integrated into any `openenv` compatible benchmark runner.

**Status: Ready for Submission.** 🏁🛡️✨
