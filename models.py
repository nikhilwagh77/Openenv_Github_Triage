"""Data models for the Mygithubtriage Environment."""

"""
Data models for the Mygithubtriage Environment.

The mygithubtriage environment is a GitHub Issue triage environment where
an agent must review issues and take appropriate actions (label, assign, comment, etc.).
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import List, Optional


class MygithubtriageAction(Action):
    """Action for the Mygithubtriage environment."""

    apply_labels: List[str] = Field(default_factory=list, description="Labels to add to the issue.")
    remove_labels: List[str] = Field(default_factory=list, description="Labels to remove from the issue.")
    assign_to: List[str] = Field(default_factory=list, description="Users to assign to the issue.")
    leave_comment: Optional[str] = Field(default=None, description="Comment text to leave on the issue.")
    submit_decision: bool = Field(default=False, description="Set to True when you are finished triaging the issue.")


class MygithubtriageObservation(Observation):
    """Observation from the Mygithubtriage environment."""

    issue_id: int = Field(default=0, description="The ID of the current issue.")
    title: str = Field(default="", description="The title of the issue.")
    body: str = Field(default="", description="The main description body of the issue.")
    author: str = Field(default="", description="The user who created the issue.")
    
    current_labels: List[str] = Field(default_factory=list, description="Labels currently applied to this issue.")
    current_assignees: List[str] = Field(default_factory=list, description="Users currently assigned to this issue.")
    comments: List[str] = Field(default_factory=list, description="List of comments left on the issue.")
    
    available_labels: List[str] = Field(default_factory=list, description="The valid labels you can apply.")
    available_assignees: List[str] = Field(default_factory=list, description="The valid users you can assign.")
    
    task_difficulty: str = Field(default="", description="The difficulty of the current task: 'easy', 'medium', or 'hard'")
    feedback: str = Field(default="", description="Immediate feedback on the action you just took.")
    done: bool = Field(default=False, description="Whether the episode is finished.")
    reward: float = Field(default=0.0, description="The reward/score for the current state.")
