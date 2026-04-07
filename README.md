---
title: GitHub Issue Triage Environment
emoji: 🛡️
colorFrom: gray
colorTo: slate
sdk: docker
tags:
  - openenv
app_port: 7860
pinned: false
license: bsd-3-clause
---

# 🛡️ GitHub Issue Triage Environment

A high-fidelity **OpenEnv v1** simulation for evaluating autonomous agents on developer-centric triage and repository maintenance tasks.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-v1.0-blue)](https://openenv.org)
[![Python](https://img.shields.io/badge/Python-3.12-gray)](https://python.org)
[![License](https://img.shields.io/badge/License-BSD--3--Clause-lightgrey)](https://opensource.org/licenses/BSD-3-Clause)

---

## 💡 Overview

Maintaining large-scale open-source repositories is a complex, multi-dimensional challenge. Traditional coding benchmarks often focus on isolated bugs, but ignore the **organizational intelligence** required for effective project management. 

This environment simulates a **Repository Maintainer** persona. Agents must analyze incoming issues, determine their technical scope, apply appropriate metadata, and route them to the correct engineering teams—all while maintaining professional communication with the author.

---

## 🏗️ Technical Architecture

### **1. Action Space (`MygithubtriageAction`)**

| Action | Fields | Purpose |
| :--- | :--- | :--- |
| `apply_labels` | `List[str]` | Add categories like `bug`, `ui`, `performance`. |
| `remove_labels` | `List[str]` | Correct existing or incorrect metadata. |
| `assign_to` | `List[str]` | Route to teams like `database-team` or `frontend-team`. |
| `leave_comment` | `str` | Request info or provide status to the author. |
| `submit_decision` | `bool` | Seal the triage and trigger automated grading. |

### **2. Observation Space (`MygithubtriageObservation`)**

| Field | Type | Description |
| :--- | :--- | :--- |
| `title` | `str` | The headline of the reported issue. |
| `body` | `str` | Full technical description and reproduction steps. |
| `author` | `str` | The GitHub username of the reporter. |
| `current_labels` | `List[str]` | Labels currently attached to the issue. |
| `current_assignees`| `List[str]` | Teams or users currently assigned. |
| `available_labels` | `List[str]` | Valid label vocabulary for this environment. |
| `available_assignees`| `List[str]` | Valid team identifiers for routing. |
| `feedback` | `str` | Response from the system about the last action taken. |

---

## 🎯 Evaluation Scenarios

The environment includes a 3-task suite for automated benchmarking:

| Difficulty | Scenario Description | Core Triage Challenge |
| :--- | :--- | :--- |
| **Easy** | Missing login button UI bug. | Precise labeling according to maintainer policy. |
| **Medium** | Database latency/timeout issue. | Multi-labeling + Correct team routing. |
| **Hard** | Vague "it doesn't work" report. | Interactive triage (Needs-info/Comment). |

---

## 📊 Grading & Metrics

The grading system implements a **Dense Reward Function** to evaluate maintenance quality.

### **Reward Components**

| Component | Max Reward | Success Condition |
| :--- | :--- | :--- |
| **Labeling** | 0.40 | All required labels are present and correct. |
| **Routing** | 0.40 | Issue is assigned to the correct technical team. |
| **Communication** | 0.20 | Appropriate label (e.g., `needs-info`) is used if required. |

**Final Score Calculation**: `Score = (Label_Reward + Routing_Reward + Comm_Reward)`
**Passing Bar**: A total score of **0.80** or higher is required for an episode to be "Successful."

---

## 🕹️ Getting Started

Ensure you have [uv](https://github.com/astral-sh/uv) and [openenv](https://openenv.org) installed.

### **Local Setup**
```bash
# Clone and sync
git clone https://github.com/nikhilwagh77/github_triage.git
cd github_triage
uv sync

# Validate the OpenEnv specification
openenv validate
```

### **Run Evaluation Benchmark**
```bash
# Start the backend server
uv run server

# In a new terminal, run the agent stream
uv run python inference.py
```

---

## 📡 API Reference

| Method | Path | Purpose |
| :--- | :--- | :--- |
| **POST** | `/reset` | Initialize a new task environment. |
| **POST** | `/step` | Submit an action and receive the next observation. |
| **GET** | `/state` | Retrieve the current raw state of the environment. |
| **GET** | `/run-agent-stream` | Stream real-time evaluation logs (SSE). |

---

## 📜 License
This project is licensed under the **BSD 3-Clause License**.

**Status: Submission Ready** 🏁🛡️🌌