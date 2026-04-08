# Copyright (c) 2026 OpenEnv Contributors.
# Mygithubtriage Environment Implementation.

from uuid import uuid4
import random
from typing import List, Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MygithubtriageAction, MygithubtriageObservation
except ImportError:
    from models import MygithubtriageAction, MygithubtriageObservation


# Available labels and assignees for the triage task
AVAILABLE_LABELS = [
    "bug", "ui", "performance", "backend", "needs-info", "enhancement", "security", "documentation"
]

AVAILABLE_ASSIGNEES = [
    "database-team", "frontend-team", "backend-team", "security-team", "docs-team"
]

# Expanded dataset of 15 tasks for comprehensive evaluation
# Expanded dataset of 15 realistic GitHub tasks for comprehensive evaluation
TASKS = [
    {
        "id": 1, "difficulty": "easy",
        "title": "Broken link in footer",
        "body": "The link to 'Privacy Policy' in the footer returns a 404 error. Please fix.",
        "author": "web_surfer",
        "expected_labels": ["bug", "ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    },
    {
        "id": 2, "difficulty": "medium",
        "title": "Dependency vulnerability in lodash",
        "body": "Github security scan found a high-severity vulnerability in lodash < 4.17.21. We need to upgrade.",
        "author": "dep-bot",
        "expected_labels": ["security", "backend"], "expected_assignees": ["backend-team", "security-team"], "needs_comment": False
    },
    {
        "id": 3, "difficulty": "easy",
        "title": "Typo in installation command",
        "body": "In README.md, it says 'npm instll' instead of 'npm install'.",
        "author": "first_timer",
        "expected_labels": ["documentation"], "expected_assignees": ["docs-team"], "needs_comment": False
    },
    {
        "id": 4, "difficulty": "medium",
        "title": "Add search bar to navigation",
        "body": "Users are finding it hard to navigate. We should add a global search bar in the header.",
        "author": "ux_researcher",
        "expected_labels": ["enhancement", "ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    },
    {
        "id": 5, "difficulty": "hard",
        "title": "Site crashes on login attempt",
        "body": "Everytime I click login, the screen goes white. I don't see any error messages.",
        "author": "confused_user",
        "expected_labels": ["bug", "needs-info"], "expected_assignees": ["frontend-team"], "needs_comment": True
    },
    {
        "id": 6, "difficulty": "easy",
        "title": "Update logo to new version",
        "body": "The marketing team has released a new logo. We need to swap logo.png with the new asset.",
        "author": "designer_01",
        "expected_labels": ["ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    },
    {
        "id": 7, "difficulty": "medium",
        "title": "Slow API response on /dashboard",
        "body": "The dashboard takes 8 seconds to load for users with more than 10 projects.",
        "author": "power_user",
        "expected_labels": ["performance", "backend"], "expected_assignees": ["backend-team"], "needs_comment": False
    },
    {
        "id": 8, "difficulty": "hard",
        "title": "SQL Injection in user profile",
        "body": "I can bypass the name length check and run arbitrary SQL in the 'bio' field.",
        "author": "pwn_master",
        "expected_labels": ["security", "backend"], "expected_assignees": ["security-team", "backend-team"], "needs_comment": False
    },
    {
        "id": 9, "difficulty": "easy",
        "title": "Change theme to dark mode by default",
        "body": "Most users prefer dark mode. Let's make it the default for new signups.",
        "author": "night_mode_fan",
        "expected_labels": ["enhancement", "ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    },
    {
        "id": 10, "difficulty": "medium",
        "title": "Broken CSS on Safari mobile",
        "body": "The layout totally breaks on Safari on iPhone. Buttons are overlapping.",
        "author": "apple_user",
        "expected_labels": ["bug", "ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    },
    {
        "id": 11, "difficulty": "easy",
        "title": "Add API documentation section",
        "body": "We need a new page explaining how to use our REST API endpoints.",
        "author": "api_integrator",
        "expected_labels": ["documentation", "enhancement"], "expected_assignees": ["docs-team"], "needs_comment": False
    },
    {
        "id": 12, "difficulty": "medium",
        "title": "Concurrent login issue",
        "body": "Logging in from two devices at once sometimes deletes the session of the first device.",
        "author": "multi_tasker",
        "expected_labels": ["bug", "backend"], "expected_assignees": ["backend-team"], "needs_comment": False
    },
    {
        "id": 13, "difficulty": "hard",
        "title": "It's not working properly",
        "body": "I tried to use the app and it didn't do what I expected.",
        "author": "vague_reporter",
        "expected_labels": ["needs-info"], "expected_assignees": [], "needs_comment": True
    },
    {
        "id": 14, "difficulty": "medium",
        "title": "Optimize image uploads",
        "body": "Uploading a 5MB image hangs the UI for several seconds.",
        "author": "photographer",
        "expected_labels": ["performance", "ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    },
    {
        "id": 15, "difficulty": "easy",
        "title": "Add 'Help' link to navigation",
        "body": "People are getting lost. A link to the support page in the header would help.",
        "author": "support_agent",
        "expected_labels": ["enhancement", "ui"], "expected_assignees": ["frontend-team"], "needs_comment": False
    }
]


class MygithubtriageEnvironment(Environment):
    """
    A GitHub Issue Triage environment.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the mygithubtriage environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0
        self._current_task = None
        
        self.current_labels = []
        self.current_assignees = []
        self.comments = []

    def reset(self, task_id: int = None) -> MygithubtriageObservation:
        """
        Reset the environment and pick a task.
        If task_id is provided, use that specific task. Otherwise select sequentially.
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        if task_id is not None:
            # Find the task by ID (handle both int and str from validator)
            task = next((t for t in TASKS if str(t["id"]) == str(task_id)), TASKS[0])
            self._current_task = task
        else:
            # Sequential fallback
            task_idx = self._reset_count % len(TASKS)
            self._current_task = TASKS[task_idx]
            self._reset_count += 1
        
        self.current_labels = []
        self.current_assignees = []
        self.comments = []

        return self._generate_observation(feedback="Environment reset. Ready for triage.", done=False, reward=0.0)

    def _generate_observation(self, feedback: str, done: bool, reward: float) -> MygithubtriageObservation:
        task = self._current_task
        
        return MygithubtriageObservation(
            issue_id=task["id"],
            title=task["title"],
            body=task["body"],
            author=task["author"],
            current_labels=list(self.current_labels),
            current_assignees=list(self.current_assignees),
            comments=list(self.comments),
            available_labels=AVAILABLE_LABELS,
            available_assignees=AVAILABLE_ASSIGNEES,
            task_difficulty=task["difficulty"],
            feedback=feedback,
            done=done,
            reward=reward,
        )

    def step(self, action: MygithubtriageAction) -> MygithubtriageObservation:  # type: ignore[override]
        """
        Execute an action.
        """
        self._state.step_count += 1
        feedback_parts = []
        step_reward = 0.0

        # Processing comments
        if action.leave_comment:
            if action.leave_comment.strip():
                self.comments.append(action.leave_comment)
                feedback_parts.append("Comment added.")
                if self._current_task["needs_comment"] and len(self.comments) == 1:
                    step_reward += 0.1 # Small dense reward for making progress
            
        # Processing assignees
        for assignee in action.assign_to:
            if assignee in AVAILABLE_ASSIGNEES and assignee not in self.current_assignees:
                self.current_assignees.append(assignee)
                feedback_parts.append(f"Assigned to {assignee}.")
                if assignee in self._current_task["expected_assignees"]:
                    step_reward += 0.1
                else:
                    step_reward -= 0.05

        # Processing labels
        for label in action.apply_labels:
            if label in AVAILABLE_LABELS and label not in self.current_labels:
                self.current_labels.append(label)
                feedback_parts.append(f"Added label {label}.")
                if label in self._current_task["expected_labels"]:
                    step_reward += 0.1
                else:
                    step_reward -= 0.05
                    
        for label in action.remove_labels:
            if label in self.current_labels:
                self.current_labels.remove(label)
                feedback_parts.append(f"Removed label {label}.")

        if not feedback_parts:
            feedback_parts.append("No changes made.")
            
        done = action.submit_decision
        
        # Calculate final grader score linearly scaled to 0-1
        if done:
            final_score = self._grade_task()
            step_reward = final_score
            feedback_parts.append(f"Task submitted! Final score: {final_score:.2f}")

        feedback = " ".join(feedback_parts)
        
        return self._generate_observation(feedback=feedback, done=done, reward=step_reward)

    def _grade_task(self) -> float:
        """
        Grades the current state against the task's expected state.
        Returns a score between 0.0 and 1.0.
        """
        score = 0.0
        task = self._current_task
        
        total_components = 0
        earned_components = 0
        
        # Check Labels
        if task["expected_labels"]:
            total_components += len(task["expected_labels"])
            for label in task["expected_labels"]:
                if label in self.current_labels:
                    earned_components += 1
        
        # Check Assignees
        if task["expected_assignees"]:
            total_components += len(task["expected_assignees"])
            for assignee in task["expected_assignees"]:
                if assignee in self.current_assignees:
                    earned_components += 1
                    
        # Check Comment
        if task["needs_comment"]:
            total_components += 1
            if len(self.comments) > 0:
                earned_components += 1
                
        # Balanced penalty for extra incorrect labels/assignees
        extra_labels = [l for l in self.current_labels if l not in task["expected_labels"]]
        extra_assignees = [a for a in self.current_assignees if a not in task["expected_assignees"]]
        penalty = 0.05 * (len(extra_labels) + len(extra_assignees))
                
        if total_components > 0:
            score = (earned_components / total_components) - penalty
        else:
            score = 1.0 - penalty
            
        # Ensure score is strictly in (0, 1) as required by Phase 2 validation.
        # Maps [0, 1] range to [0.01, 0.99]
        clamped_score = max(0.0, min(1.0, score))
        return round(0.01 + (clamped_score * 0.98), 3)

    @property
    def state(self) -> State:
        """
        Get the current environment state.
        """
        return self._state
