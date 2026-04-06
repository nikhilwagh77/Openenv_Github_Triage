# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Mygithubtriage Environment Implementation.

A GitHub Issue triage environment where the agent learns to
label, assign, and communicate effectively on repo issues.
"""

from uuid import uuid4
import random

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MygithubtriageAction, MygithubtriageObservation
except ImportError:
    from models import MygithubtriageAction, MygithubtriageObservation


AVAILABLE_LABELS = [
    "bug", "ui", "performance", "backend", "needs-info", "enhancement"
]

AVAILABLE_ASSIGNEES = [
    "database-team", "frontend-team", "backend-team"
]

TASKS = [
    {
        "id": 1,
        "difficulty": "easy",
        "title": "Login button is missing down the page",
        "body": "I scrolled down but the login button is completely gone.",
        "author": "randomuser99",
        "expected_labels": ["bug", "ui"],
        "expected_assignees": [],
        "needs_comment": False
    },
    {
        "id": 2,
        "difficulty": "medium",
        "title": "Database query sometimes times out on heavy load",
        "body": "When 1000 users hit it concurrently, Postgres just gives up and times out.",
        "author": "devops-guru",
        "expected_labels": ["performance", "backend"],
        "expected_assignees": ["database-team"],
        "needs_comment": False
    },
    {
        "id": 3,
        "difficulty": "hard",
        "title": "Fix it please it crashed",
        "body": "It crashed yesterday when I clicked it.",
        "author": "angry_customer",
        "expected_labels": ["needs-info"],
        "expected_assignees": [],
        "needs_comment": True
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

    def reset(self) -> MygithubtriageObservation:
        """
        Reset the environment and pick the next task.
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        # Sequentially select task to ensure all 3 are seen
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
                
        # Penalties for extra incorrect labels/assignees
        extra_labels = [l for l in self.current_labels if l not in task["expected_labels"]]
        extra_assignees = [a for a in self.current_assignees if a not in task["expected_assignees"]]
        penalty = 0.1 * (len(extra_labels) + len(extra_assignees))
                
        if total_components > 0:
            score = (earned_components / total_components) - penalty
            
        return max(0.0, min(1.0, score))

    @property
    def state(self) -> State:
        """
        Get the current environment state.
        """
        return self._state
